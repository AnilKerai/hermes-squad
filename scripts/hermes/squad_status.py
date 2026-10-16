#!/usr/bin/env python3
"""Read-only snapshot of the Hermes kanban squads, shared by squad_digest.py
and squad_dashboard.py.

Reads every board DB (sqlite, read-only) plus Langfuse cost per role
(v2 metrics API, grouped by environment hermes-<profile>). Never writes to
the boards and never prints secrets.
"""
from __future__ import annotations

import base64
import json
import os
import sqlite3
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
# Cron runs scripts under the active profile's HERMES_HOME; boards and .env
# live in the root home, so resolve it explicitly.
ROOT_HOME = Path.home() / ".hermes"
TEAM = {"lead", "engineer", "ops", "reviewer", "pm", "researcher", "analyst"}
HUMAN_CREATORS = {"user", "default", "dashboard", "desktop", None, ""}


def _board_dbs() -> list[tuple[str, Path]]:
    out = []
    if (ROOT_HOME / "kanban.db").exists():
        out.append(("default", ROOT_HOME / "kanban.db"))
    boards = ROOT_HOME / "kanban" / "boards"
    if boards.is_dir():
        for d in sorted(boards.iterdir()):
            if (d / "kanban.db").exists():
                out.append((d.name, d / "kanban.db"))
    return out


def _ro(db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def _payload(raw):
    try:
        return json.loads(raw or "{}")
    except Exception:
        return {}


def _short(text, n=220):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


ORCHESTRATORS = {"lead", "pm"}


def _is_decomposition(con, task_id: str, created_by: str) -> bool:
    """True when an orchestrator (lead/pm) split this card out of a card the
    human wrote: it reaches a human-created card through links (either
    direction) passing only through other orchestrator-created cards. Cards a
    worker created (follow-ups from an engineer's flags), and anything hung
    off them, count as created without the human."""
    if created_by not in ORCHESTRATORS:
        return False
    seen, frontier = {task_id}, [task_id]
    while frontier:
        cur = frontier.pop()
        for row in con.execute(
            "select t.id, t.created_by from task_links l join tasks t "
            "on t.id = case when l.child_id=? then l.parent_id else l.child_id end "
            "where l.child_id=? or l.parent_id=?",
            (cur, cur, cur),
        ):
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            if row["created_by"] in HUMAN_CREATORS:
                return True
            if row["created_by"] in ORCHESTRATORS:
                frontier.append(row["id"])
    return False


def collect(since_hours: float = 24.0) -> dict:
    now = int(time.time())
    since = now - int(since_hours * 3600)
    snap = {
        "generated_at": now,
        "since": since,
        "running": [],
        "blocked": [],
        "ready": [],
        "review": [],
        "triage": 0,
        "done_recent": [],
        "agent_created_recent": [],
        "counts": {},
        "boards_active": [],
    }
    for slug, db in _board_dbs():
        try:
            con = _ro(db)
            cols = {r[1] for r in con.execute("pragma table_info(tasks)")}
            goal_col = "goal_mode" if "goal_mode" in cols else "0 as goal_mode"
            rows = con.execute(
                f"select id,title,status,assignee,created_by,created_at,started_at,"
                f"completed_at,last_heartbeat_at,{goal_col} from tasks"
            ).fetchall()
        except Exception as e:  # board mid-migration etc.
            snap.setdefault("errors", []).append(f"{slug}: {e}")
            continue
        active = False
        for t in rows:
            st = t["status"]
            snap["counts"][st] = snap["counts"].get(st, 0) + 1
            card = {
                "board": slug,
                "id": t["id"],
                "title": t["title"],
                "assignee": t["assignee"],
                "goal": bool(t["goal_mode"]),
            }
            if st == "running":
                active = True
                card["since"] = t["started_at"]
                card["heartbeat"] = t["last_heartbeat_at"]
                snap["running"].append(card)
            elif st == "blocked":
                active = True
                ev = con.execute(
                    "select payload, created_at from task_events where task_id=? "
                    "and kind='blocked' order by id desc limit 1",
                    (t["id"],),
                ).fetchone()
                p = _payload(ev["payload"]) if ev else {}
                reason = p.get("reason") or ""
                card["parked"] = reason == "initial_status"
                card["kind"] = p.get("kind") or p.get("block_kind") or ""
                card["reason"] = _short(
                    "parked by " + (p.get("actor") or "?") + " (merge gate)"
                    if card["parked"]
                    else reason,
                    300,
                )
                card["at"] = ev["created_at"] if ev else None
                # A question to the product owner can also arrive as a comment.
                c = con.execute(
                    "select author, body, created_at from task_comments where task_id=? "
                    "order by id desc limit 1",
                    (t["id"],),
                ).fetchone()
                if c and c["author"] in TEAM:
                    card["last_comment"] = {
                        "author": c["author"],
                        "body": _short(c["body"], 300),
                        "at": c["created_at"],
                    }
                snap["blocked"].append(card)
            elif st == "ready":
                active = True
                snap["ready"].append(card)
            elif st == "review":
                active = True
                snap["review"].append(card)
            elif st == "triage":
                snap["triage"] += 1

            if t["created_at"] and t["created_at"] >= since and t["created_by"] not in HUMAN_CREATORS:
                expected = _is_decomposition(con, t["id"], t["created_by"])
                card2 = dict(card, created_by=t["created_by"], status=st, expected=expected)
                snap["agent_created_recent"].append(card2)

        for ev in con.execute(
            "select e.task_id, e.payload, e.created_at, t.title, t.status, t.assignee "
            "from task_events e join tasks t on t.id=e.task_id "
            "where e.kind='completed' and e.created_at>=? order by e.created_at",
            (since,),
        ):
            p = _payload(ev["payload"])
            run = con.execute(
                "select profile from task_runs where task_id=? and outcome='completed' "
                "order by id desc limit 1",
                (ev["task_id"],),
            ).fetchone()
            creator = con.execute(
                "select created_by from tasks where id=?", (ev["task_id"],)
            ).fetchone()["created_by"]
            snap["done_recent"].append(
                {
                    "board": slug,
                    "id": ev["task_id"],
                    "title": ev["title"],
                    "top_level": creator in HUMAN_CREATORS,
                    "by": run["profile"] if run else ev["assignee"],
                    "at": ev["created_at"],
                    "summary": _short(p.get("summary"), 260),
                }
            )
            active = True
        if active:
            snap["boards_active"].append(slug)
        con.close()
    snap["cost"] = langfuse_cost(since, now)
    return snap


def _env() -> dict:
    out = {}
    try:
        for line in (ROOT_HOME / ".env").read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def langfuse_cost(from_ts: int, to_ts: int) -> dict:
    """Sum of totalCost per hermes-* environment. {} when unavailable."""
    env = _env()
    pk, sk = env.get("HERMES_LANGFUSE_PUBLIC_KEY"), env.get("HERMES_LANGFUSE_SECRET_KEY")
    base = (env.get("HERMES_LANGFUSE_BASE_URL") or "https://cloud.langfuse.com").rstrip("/")
    if not (pk and sk):
        return {"error": "no Langfuse keys"}
    iso = lambda ts: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
    query = {
        "view": "observations",
        "metrics": [
            {"measure": "totalCost", "aggregation": "sum"},
            {"measure": "count", "aggregation": "count"},
        ],
        "dimensions": [{"field": "environment"}],
        "filters": [{"column": "type", "operator": "=", "value": "GENERATION", "type": "string"}],
        "fromTimestamp": iso(from_ts),
        "toTimestamp": iso(to_ts),
    }
    url = f"{base}/api/public/v2/metrics?query=" + urllib.parse.quote(json.dumps(query))
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{pk}:{sk}".encode()).decode())
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r).get("data", [])
    except Exception as e:
        return {"error": f"Langfuse: {type(e).__name__}"}
    roles = {}
    for row in data:
        envname = row.get("environment") or ""
        if not envname.startswith("hermes-"):
            continue
        cost = next((v for k, v in row.items() if k.lower().startswith("sum") and "cost" in k.lower()), 0) or 0
        calls = next((v for k, v in row.items() if k.lower().startswith("count")), 0) or 0
        roles[envname[len("hermes-"):]] = {"cost": float(cost), "calls": int(calls)}
    return {"roles": roles, "total": sum(r["cost"] for r in roles.values())}


def ago(ts: int | None, now: int | None = None) -> str:
    if not ts:
        return "?"
    s = (now or int(time.time())) - int(ts)
    if s < 90:
        return f"{s}s"
    if s < 5400:
        return f"{s // 60}m"
    if s < 172800:
        return f"{s // 3600}h"
    return f"{s // 86400}d"


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2, default=str))
