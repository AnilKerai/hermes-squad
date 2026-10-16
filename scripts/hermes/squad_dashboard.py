#!/usr/bin/env python3
"""Render the squad dashboard widget (HTML) for the Hermes desktop chat.

Run by a no-agent cron job every 5 minutes; prints nothing, so the job is
silent. The chat embeds the file with ::preview{file="..."} and re-renders
when it changes. Buttons use data-hermes-send to ask the chat agent to act.
"""
import html
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import squad_status as s  # noqa: E402

OUT = Path.home() / ".hermes" / "dashboards" / "squad.html"
e = html.escape


def card_row(c, now, extra="", buttons=()):
    goal = '<span class="pill goal">goal</span>' if c.get("goal") else ""
    btns = "".join(
        f'<button data-hermes-send="{e(prompt)}">{e(label)}</button>' for label, prompt in buttons
    )
    return (
        f'<li><div class="row"><span class="board">{e(c["board"])}</span>'
        f'<span class="title">{e(c["title"])}</span>{goal}</div>'
        f'<div class="meta">{e(c["id"])} · {e(str(c.get("assignee") or c.get("by") or ""))}{extra}</div>'
        f'{f"<div class=btns>{btns}</div>" if btns else ""}</li>'
    )


def section(title, items, empty):
    body = "".join(items) if items else f'<li class="empty">{e(empty)}</li>'
    return f'<section><h3>{e(title)}</h3><ul>{body}</ul></section>'


def render() -> str:
    day = s.collect(24)
    week = s.collect(24 * 7)
    now = day["generated_at"]

    questions = [b for b in day["blocked"] if not b["parked"]]
    parked = [b for b in day["blocked"] if b["parked"]]
    done_day = {(c["board"], c["id"]) for c in day["done_recent"]}
    done_week = {}
    for c in week["done_recent"]:
        if c["top_level"]:
            done_week[(c["board"], c["id"])] = c
    done_week = sorted(done_week.values(), key=lambda c: -c["at"])
    unasked = [c for c in week["agent_created_recent"] if not c["expected"]]

    cost_d = day["cost"].get("total")
    cost_w = week["cost"].get("total")
    tiles = [
        ("Need you", len(questions), "warn" if questions else ""),
        ("Running", len(day["running"]), "live" if day["running"] else ""),
        ("Review / ready", f'{len(day["review"])} / {len(day["ready"])}', ""),
        ("Done 24h", len(done_day), ""),
        ("Spend 24h", f"${cost_d:.2f}" if cost_d is not None else "n/a", ""),
        ("Spend 7d", f"${cost_w:.2f}" if cost_w is not None else "n/a", ""),
    ]
    tiles_html = "".join(
        f'<div class="tile {cls}"><div class="v">{e(str(v))}</div><div class="k">{e(k)}</div></div>'
        for k, v, cls in tiles
    )

    q_items = []
    for b in questions:
        extra = f' · blocked {s.ago(b["at"], now)} ago<div class="reason">{e(b["reason"] or "(no reason)")}</div>'
        if b.get("last_comment"):
            lc = b["last_comment"]
            extra += f'<div class="reason">{e(lc["author"])}: {e(lc["body"])}</div>'
        q_items.append(
            card_row(
                b, now, extra,
                [
                    ("Help me answer", f'Kanban card {b["id"]} on board {b["board"]} is blocked waiting on me. Read the whole thread, audit the options against the original brief, and recommend an answer.'),
                    ("Show card", f'Show me kanban card {b["id"]} on board {b["board"]}: body, latest handoff and comments.'),
                ],
            )
        )
    if parked:
        q_items.append(
            f'<li class="empty">{len(parked)} parked behind merge gates: '
            + ", ".join(e(f'{b["board"]}/{b["id"]}') for b in parked[:6])
            + "</li>"
        )

    r_items = [
        card_row(
            c, now,
            f' · running {s.ago(c["since"], now)} · heartbeat {s.ago(c["heartbeat"], now)} ago',
            [("Is it stuck?", f'Is kanban card {c["id"]} on board {c["board"]} stuck? Check its log, output files and elapsed time against siblings.')],
        )
        for c in day["running"]
    ] + [card_row(c, now, " · in review") for c in day["review"]] + [
        card_row(c, now, " · ready, waiting for a slot") for c in day["ready"]
    ]

    d_items = [
        card_row(
            c, now,
            f' · {s.ago(c["at"], now)} ago<div class="reason">{e(s._short(c["summary"], 200))}</div>',
            [("Verify & ship", f'Card {c["id"]} on board {c["board"]} is done. Verify it independently and tell me what you would ship.')],
        )
        for c in done_week[:6]
    ]

    u_items = [
        card_row(dict(c, assignee=f'created by {c["created_by"]}'), now, f' · {c["status"]}')
        for c in unasked[:8]
    ]

    roles = week["cost"].get("roles", {})
    mx = max([v["cost"] for v in roles.values()] or [1]) or 1
    bars = "".join(
        f'<div class="bar"><span class="lbl">{e("you (chat)" if r == "default" else r)}</span>'
        f'<span class="track"><span class="fill" style="width:{100 * v["cost"] / mx:.1f}%"></span></span>'
        f'<span class="num">${v["cost"]:.2f}</span></div>'
        for r, v in sorted(roles.items(), key=lambda kv: -kv[1]["cost"])
        if v["cost"] >= 0.01
    ) or '<div class="empty">No cost data</div>'

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
:root {{ --gap: 10px; }}
.wrap {{ display:flex; flex-direction:column; gap:14px; max-width:760px; color:var(--foreground); }}
header {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
header h2 {{ margin:0; font-size:16px; }}
.dot {{ width:8px; height:8px; border-radius:50%; background:var(--accent); animation:p 2s infinite; }}
@keyframes p {{ 50% {{ opacity:.3 }} }}
.muted, .meta, .k {{ color:var(--muted-foreground); }}
.tiles {{ display:grid; grid-template-columns:repeat(6, minmax(0,1fr)); gap:8px; }}
.tile {{ border:1px solid var(--border); background:var(--card); border-radius:10px; padding:8px 10px; }}
.tile .v {{ font-size:18px; font-weight:600; }}
.tile .k {{ font-size:11px; }}
.tile.warn {{ border-color:#f59e0b; }} .tile.warn .v {{ color:#f59e0b; }}
.tile.live .v {{ color:var(--accent); }}
section {{ border:1px solid var(--border); background:var(--card); border-radius:10px; padding:10px 12px; }}
h3 {{ margin:0 0 6px; font-size:13px; }}
ul {{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:8px; }}
li {{ font-size:12.5px; }}
.row {{ display:flex; gap:6px; align-items:baseline; }}
.board {{ font-size:10.5px; padding:1px 6px; border-radius:6px; border:1px solid var(--border); color:var(--muted-foreground); white-space:nowrap; }}
.title {{ font-weight:500; }}
.meta {{ font-size:11px; margin-top:2px; }}
.reason {{ margin-top:3px; font-size:11.5px; color:var(--foreground); opacity:.85; }}
.pill.goal {{ font-size:10px; padding:0 5px; border-radius:6px; background:var(--accent); color:var(--card); }}
.empty {{ color:var(--muted-foreground); font-size:12px; }}
.btns {{ display:flex; gap:6px; margin-top:4px; }}
button {{ font:inherit; font-size:11px; padding:3px 9px; border-radius:7px; border:1px solid var(--border); background:transparent; color:var(--foreground); cursor:pointer; }}
button:hover {{ border-color:var(--accent); color:var(--accent); }}
.bar {{ display:grid; grid-template-columns:90px 1fr 70px; gap:8px; align-items:center; font-size:12px; margin:3px 0; }}
.track {{ height:8px; background:var(--border); border-radius:4px; overflow:hidden; }}
.fill {{ display:block; height:100%; background:var(--accent); }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
@media (max-width:640px) {{ .tiles {{ grid-template-columns:repeat(3,1fr); }} .grid2 {{ grid-template-columns:1fr; }} }}
</style></head><body><div class="wrap">
<header><span class="dot"></span><h2>Squad dashboard</h2>
<span class="muted" id="age" data-ts="{now}">updated {time.strftime('%H:%M', time.localtime(now))}</span>
<span style="flex:1"></span>
<button data-hermes-send="Refresh the squad dashboard now (run ~/.hermes/scripts/squad_dashboard.py) and re-show it.">Refresh</button>
<button data-hermes-send="Give me the squad digest for the last 24 hours (run ~/.hermes/scripts/squad_digest.py).">Digest</button>
</header>
<div class="tiles">{tiles_html}</div>
{section("Waiting on you", q_items, "Nothing is waiting on you.")}
{section("In flight", r_items, "Nothing running. Triage holding pen: " + str(day["triage"]) + " idea(s).")}
<div class="grid2">
{section("Your cards finished (7d)", d_items, "None in the last 7 days.")}
{section("Agents created without you (7d)", u_items, "None.")}
</div>
<section><h3>Spend per role, last 7 days (Langfuse, USD)</h3>{bars}</section>
</div>
<script>
const a=document.getElementById('age'); const ts=+a.dataset.ts;
function tick(){{const m=Math.round((Date.now()/1000-ts)/60); a.textContent='updated '+(m<1?'just now':m+'m ago')+(m>12?' (stale: is the gateway running?)':'');}}
tick(); setInterval(tick,30000);
</script></body></html>"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(render())
    tmp.replace(OUT)
    if "-v" in sys.argv:
        print(OUT)


if __name__ == "__main__":
    main()
