#!/usr/bin/env python3
"""Morning squad digest (no-agent cron job; stdout is delivered verbatim).

What finished in the last 24h, what is waiting on the human, cards agents
created without the human, what is running/queued, and spend per role.
Zero LLM tokens. Data comes from squad_status.collect().
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import squad_status as s  # noqa: E402

HOURS = float(sys.argv[1]) if len(sys.argv) > 1 else 24.0
MAX_ITEMS = 8


def main() -> None:
    d = s.collect(HOURS)
    now = d["generated_at"]
    out = []
    day = time.strftime("%a %d %b", time.localtime(now))

    # Dedupe completions: keep the latest event per card.
    done = {}
    for c in d["done_recent"]:
        done[(c["board"], c["id"])] = c
    done = sorted(done.values(), key=lambda c: c["at"])

    questions = [b for b in d["blocked"] if not b["parked"]]
    parked = [b for b in d["blocked"] if b["parked"]]
    cost = d["cost"]
    spend = f"${cost['total']:.2f}" if "total" in cost else "cost n/a"

    out.append(f"*Squad digest — {day}*")
    out.append(
        f"Last {HOURS:g}h: {len(done)} done · {len(questions)} need you · "
        f"{len(d['running'])} running · {len(d['ready'])} queued · {spend}"
    )

    if questions:
        out.append("")
        out.append(f"*⏸ Waiting on you ({len(questions)})*")
        for b in questions[:MAX_ITEMS]:
            why = b["reason"] or "(no reason recorded)"
            out.append(f"• [{b['board']}] {b['title']} ({b['id']}, {b['assignee']}, {s.ago(b['at'], now)} ago)")
            out.append(f"   ↳ {why}")
            if b.get("last_comment"):
                lc = b["last_comment"]
                out.append(f"   ↳ {lc['author']}: {lc['body']}")
    if parked:
        out.append("")
        names = ", ".join(f"{b['board']}/{b['id']}" for b in parked[:MAX_ITEMS])
        out.append(f"*🚧 Parked behind merge gates ({len(parked)})*: {names}")

    if done:
        top = [c for c in done if c.get("top_level")]
        out.append("")
        out.append(f"*✔ Finished: {len(top)} of your cards ({len(done) - len(top)} agent sub-cards)*")
        for c in list(reversed(top))[:MAX_ITEMS]:
            out.append(f"• [{c['board']}] {c['title']} ({c['id']}) — {c['by']}")
            if c["summary"]:
                out.append(f"   ↳ {s._short(c['summary'], 160)}")
        if len(top) > MAX_ITEMS:
            out.append(f"  …and {len(top) - MAX_ITEMS} more")

    agent_made = d["agent_created_recent"]
    unasked = [c for c in agent_made if not c["expected"]]
    if unasked:
        out.append("")
        out.append(f"*🤖 Agents created without you ({len(unasked)})*")
        for c in unasked[:MAX_ITEMS]:
            out.append(f"• {c['created_by']} → [{c['board']}] {c['title']} ({c['id']}, {c['status']})")
    if len(agent_made) > len(unasked):
        out.append(f"(+{len(agent_made) - len(unasked)} sub-cards split from your cards)")

    if d["running"] or d["review"] or d["ready"]:
        out.append("")
        out.append("*▶ In flight*")
        for c in d["running"][:MAX_ITEMS]:
            g = " 🎯goal" if c["goal"] else ""
            out.append(f"• running {s.ago(c['since'], now)}: [{c['board']}] {c['title']} — {c['assignee']}{g}")
        for c in d["review"][:MAX_ITEMS]:
            out.append(f"• in review: [{c['board']}] {c['title']}")
        if d["ready"]:
            out.append(f"• {len(d['ready'])} ready, waiting for a slot")
    if d["triage"]:
        out.append(f"📥 Triage holding pen: {d['triage']} idea(s)")

    if cost.get("roles"):
        out.append("")
        parts = [
            f"{('you' if r == 'default' else r)} ${v['cost']:.2f}"
            for r, v in sorted(cost["roles"].items(), key=lambda kv: -kv[1]["cost"])
            if v["cost"] >= 0.01
        ]
        out.append("*💷 Spend (Langfuse, USD)*: " + (", ".join(parts) or "nothing"))
    elif cost.get("error"):
        out.append(f"\n(cost unavailable: {cost['error']})")

    if not (done or questions or d["running"] or unasked):
        out.append("\nQuiet night: nothing finished, nothing waiting on you.")

    for e in d.get("errors", []):
        out.append(f"(board read error: {e})")
    print("\n".join(out))


if __name__ == "__main__":
    main()
