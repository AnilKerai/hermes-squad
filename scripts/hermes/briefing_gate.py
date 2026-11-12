#!/usr/bin/env python3
"""wakeAgent gate for the AI brief cron jobs.

Jobs: 8809de896614 "AI brief (daily, short)"   - weekdays
      c03f50ee5050 "AI week (Saturday synthesis)" - Sat/Sun

Why: the MacBook clamshell-sleeps overnight. Power Nap DarkWakes give processes a
few seconds every ~15 min, so a run fired at a fixed 07:45 crawls one step per
DarkWake, its model stream goes stale, the session turn lease expires, and Hermes
hard-interrupts it on the next real wake ("Operation interrupted: waiting for model
response" / "agent reported failure"). 7 of 10 weekday runs died that way.

So the jobs poll every 30 min and this gate wakes the agent only when:
  1. the target file is missing (Mon-Fri: daily/YYYY-MM-DD.md, Sat/Sun: weekly/YYYY-Www.md),
  2. the machine is fully awake (Graphics capability present; DarkWake has none),
  3. fewer than MAX_ATTEMPTS agent runs were started for that target today
     (stops a persistent failure from re-running the agent all day).

Test overrides: BRIEF_GATE_DATE=YYYY-MM-DD, BRIEF_GATE_STATE=/path/state.json.
"""
import datetime
import json
import os
import subprocess

BASE = os.path.expanduser("~/git/research/briefings")
STATE = os.environ.get(
    "BRIEF_GATE_STATE", os.path.expanduser("~/.hermes/scripts/.briefing_gate_state.json")
)
MAX_ATTEMPTS = 4


def emit(wake, **extra):
    print(json.dumps({"wakeAgent": wake, **extra}))


def fully_awake():
    try:
        out = subprocess.run(
            ["pmset", "-g", "systemstate"], capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:
        return True  # cannot tell: do not block the run
    caps = next((l for l in out.splitlines() if "Capabilities" in l), "")
    return "Graphics" in caps if caps else True


def main():
    override = os.environ.get("BRIEF_GATE_DATE")
    today = datetime.date.fromisoformat(override) if override else datetime.date.today()
    if today.weekday() < 5:
        target = os.path.join(BASE, "daily", f"{today:%Y-%m-%d}.md")
    else:
        year, week, _ = today.isocalendar()
        target = os.path.join(BASE, "weekly", f"{year}-W{week:02d}.md")

    if os.path.exists(target):
        return emit(False, reason=f"already written: {target}")
    if not fully_awake():
        return emit(False, reason="system in DarkWake; retry on a later tick")

    try:
        state = json.load(open(STATE))
    except Exception:
        state = {}
    key = f"{today.isoformat()}:{os.path.basename(target)}"
    attempts = state.get(key, 0)
    if attempts >= MAX_ATTEMPTS:
        return emit(False, reason=f"{attempts} attempts today for {target}; giving up until tomorrow")
    # keep only today's keys so the file stays tiny
    state = {k: v for k, v in state.items() if k.startswith(today.isoformat())}
    state[key] = attempts + 1
    with open(STATE, "w") as fh:
        json.dump(state, fh)
    emit(True, context={"target_file": target, "attempt": attempts + 1})


if __name__ == "__main__":
    main()
