#!/usr/bin/env python3
"""Release finished Kanban cards' git worktrees so their branches behave like normal branches.

Agents still work in isolated worktrees (<repo>/.worktrees/<task-id>) while a card is live.
Once the card is done/archived on any board, no unfinished card uses that path, and the
worktree is clean, this runs `git worktree remove` (no --force: git refuses dirty trees).
The branch is always kept, so you can `git checkout` it in your IDE.

Hermes' built-in cleanup only removes worktrees whose commits are pushed; our engineers
never push, so this fills the gap. Silent unless it released something (cron no-agent job).

The boards live under the Hermes root: HERMES_HOME, or its grandparent when HERMES_HOME is a
profile (<root>/profiles/<role>), or ~/.hermes when unset. It is resolved on every call.
"""
import os
import sqlite3
import subprocess
from pathlib import Path

GIT_ROOT = Path(os.environ.get("SQUAD_GIT_ROOT") or Path.home() / "git").expanduser()
TERMINAL = {"done", "archived"}


def hermes_root():
    """The Hermes root, which holds kanban.db and kanban/boards. A profile's HERMES_HOME
    (<root>/profiles/<role>) maps to <root>, as in Hermes' own _hermes_root_of. Unlike Hermes, a
    path that is merely under ~/.hermes (a worker's scratch dir) is not mapped to ~/.hermes, so
    a test's HERMES_HOME can't reach the live boards."""
    home = os.environ.get("HERMES_HOME")
    if not home:
        return Path.home() / ".hermes"
    home = Path(home)
    return home.parent.parent if home.parent.name == "profiles" else home


def kanban_dbs():
    root = hermes_root()
    return [root / "kanban.db", *sorted((root / "kanban" / "boards").glob("*/kanban.db"))]


def task_rows():
    rows = []
    for db in kanban_dbs():
        if not db.exists():
            continue
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
            rows += conn.execute("SELECT id, status, workspace_path, branch_name FROM tasks").fetchall()
            conn.close()
        except sqlite3.Error:
            continue
    return rows


def main():
    rows = task_rows()
    status = {r[0]: r[1] for r in rows}
    branch = {r[0]: r[3] for r in rows}
    live_paths = {str(Path(r[2])) for r in rows if r[2] and r[1] not in TERMINAL}

    for wt_root in sorted(GIT_ROOT.glob("*/.worktrees")):
        repo = wt_root.parent
        for wt in sorted(p for p in wt_root.iterdir() if p.is_dir()):
            tid = wt.name
            if status.get(tid) not in TERMINAL or str(wt) in live_paths:
                continue
            r = subprocess.run(["git", "-C", str(repo), "worktree", "remove", str(wt)],
                               capture_output=True, text=True)
            if r.returncode == 0:
                print(f"{repo.name}: card {tid} finished; branch ready to check out: {branch.get(tid) or '?'}")


if __name__ == "__main__":
    main()
