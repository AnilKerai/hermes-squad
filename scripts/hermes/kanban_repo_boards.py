"""Create one project-scoped kanban board per repo in ~/git, plus a cross-repo board.

Run via kanban-repo-boards.sh (Hermes's own Python, HERMES_HOME = the Hermes root).
Repos root: $SQUAD_GIT_ROOT, default ~/git. Idempotent: existing projects/boards are reused.
"""
import os
import sqlite3
import subprocess
from pathlib import Path

from hermes_cli import projects_db as pdb
from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_boards as kbb

HERMES = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")
GIT = Path(os.environ.get("SQUAD_GIT_ROOT") or Path.home() / "git").expanduser()
TEAM = ["lead", "engineer", "reviewer", "ops"]

repos = sorted(p for p in GIT.iterdir() if (p / ".git").exists())
print(f"{len(repos)} repos")

with pdb.connect_closing() as conn:
    for repo in repos:
        slug = repo.name
        proj = pdb.find_by_primary_path(conn, str(repo)) or pdb.get_project(conn, slug)
        if proj is None:
            pid = pdb.create_project(conn, name=slug, slug=slug, folders=[str(repo)],
                                     primary_path=str(repo), board_slug=slug)
            proj = pdb.get_project(conn, pid)
            made = "created"
        else:
            pdb.update_project(conn, proj.id, board_slug=slug)
            made = "reused"
        # Board scoped to the project: new cards default to <repo>/.worktrees/<id> + branch.
        kbb.create_board(slug, name=slug, description=f"Work in {repo}",
                         default_workdir=str(repo), project_id=proj.id)
        # Keep agent worktrees out of the main checkout's `git status` (local-only, not committed).
        ignored = subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", ".worktrees/x"]).returncode == 0
        if not ignored:
            excl = Path(subprocess.check_output(["git", "-C", str(repo), "rev-parse", "--git-path", "info/exclude"], text=True).strip())
            if not excl.is_absolute():
                excl = repo / excl
            excl.parent.mkdir(parents=True, exist_ok=True)
            with excl.open("a") as f:
                f.write("\n# Hermes kanban agent worktrees\n.worktrees/\n")
        print(f"  {slug:28s} project {made:7s} {proj.id}  board scoped  exclude={'already' if ignored else 'added'}")

kbb.create_board("cross-repo", name="Cross-repo",
                 description="Changes spanning several repos. Assign cards to `lead`; every child card must set project=<repo>.")
print("  cross-repo board created (unscoped)")

# Give the team profiles identical project records (same ids) so cards they create
# resolve to the same repos. Projects are per-profile state in $HERMES_HOME/projects.db.
src = sqlite3.connect(str(pdb.projects_db_path()))
for p in TEAM:
    if not (HERMES / "profiles" / p).is_dir():
        print(f"  projects skipped -> {p} (profile not installed)")
        continue
    dst_path = HERMES / "profiles" / p / "projects.db"
    dst = sqlite3.connect(str(dst_path))
    src.backup(dst)
    dst.close()
    print(f"  projects copied -> {p}")
src.close()
