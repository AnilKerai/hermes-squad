#!/usr/bin/env python3
"""Publish a feature branch as one PR, and remove finished cards' worktrees.

Used by `lead`, the only role allowed to publish; raw `git push` and `gh pr` are denied to
every role, so this script is the one way out and its rules are enforced here, in code:

  publish  push <branch> to origin under the same name and open (or reuse) one PR against the
           repo's default branch. Refuses the default branch, `main` and `master` however they
           are spelled (HEAD, origin/main, refs/heads/main, MAIN), refspec-like names (`+b`,
           `a:b`), a dirty worktree, and a remote branch that is not an ancestor of the local
           one. Pushes are plain `refs/heads/<b>:refs/heads/<b>` and nothing lands on the
           default branch.
  cleanup  `git worktree remove` (git refuses dirty trees) the worktrees of finished cards.
           Branches are always kept.

Exit codes: 0 ok, 2 refused (stderr `refused: <reason>`), 1 git/gh failure (stderr `error: ...`).

Usage:
  squad_publish.py publish --repo <path> --branch <name> --title <text> --body-file <path>
  squad_publish.py cleanup --repo <path> <task-id>...
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Sibling helper, installed next to this file in ~/.hermes/scripts/. Used as a module (not
# from-imported) so `task_rows` and `TERMINAL` are looked up at call time.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kanban_release_worktrees as krw  # noqa: E402

TASK_ID = re.compile(r"[A-Za-z0-9_-]+")
BRANCH_PREFIXES = ("refs/heads/", "refs/remotes/origin/", "origin/")


class Refused(Exception):
    """A rule of the publish flow forbids this request."""


class CommandError(Exception):
    """A git or gh command failed: `<cmd>: <stderr>`."""


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except OSError as e:  # e.g. gh not installed
        r = subprocess.CompletedProcess(cmd, 127, "", str(e))
    if check and r.returncode != 0:
        raise CommandError(f"{' '.join(cmd)}: {r.stderr.strip()}")
    return r


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return run(["git", "-C", str(repo), *args], check=check)


def strip_prefix(name: str) -> str:
    for prefix in BRANCH_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def worktrees(repo: Path) -> list[tuple[str, str | None]]:
    """(path, branch ref or None) for every worktree of the repo."""
    out = git(repo, "worktree", "list", "--porcelain", check=False).stdout
    found = []
    for block in out.split("\n\n"):
        path, ref = None, None
        for line in block.splitlines():
            if line.startswith("worktree "):
                path = line[len("worktree "):]
            elif line.startswith("branch "):
                ref = line[len("branch "):]
        if path:
            found.append((path, ref))
    return found


def default_branch(repo: Path) -> str:
    r = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False)
    name = r.stdout.strip() if r.returncode == 0 else ""
    if name.startswith("origin/"):
        name = name[len("origin/"):]
    if not name:
        r = run(["gh", "repo", "view", "--json", "defaultBranchRef", "-q", ".defaultBranchRef.name"],
                cwd=repo, check=False)
        name = r.stdout.strip() if r.returncode == 0 else ""
    if not name or name == "null":
        raise Refused("can't determine the default branch")
    return name


def publish(repo: Path, branch: str, title: str, body_file: Path) -> str:
    repo = Path(repo)
    # 1. Validate the name: nothing that git could read as a refspec or an option.
    if (not branch or branch.startswith(("+", "-")) or ":" in branch
            or any(c.isspace() for c in branch)):
        raise Refused(f"bad branch name {branch!r}")
    # 2. Resolve the name, so HEAD, origin/b and refs/heads/b all become the real branch.
    typed = strip_prefix(branch)
    r = git(repo, "rev-parse", "--abbrev-ref", branch, check=False)
    resolved = strip_prefix(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else typed
    # 3. Never the default branch, whatever it is spelled as.
    default = default_branch(repo)
    protected = {default.lower(), "main", "master"}
    if typed.lower() in protected or resolved.lower() in protected:
        raise Refused(f"{branch} is the default branch ({default}); nothing is published to it")
    # 4. A real local branch.
    if resolved == "HEAD" or git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{resolved}",
                                 check=False).returncode != 0:
        raise Refused(f"no local branch {resolved}")
    b = resolved
    # 5. A clean worktree: uncommitted work would not be in the PR.
    for path, ref in worktrees(repo):
        if ref == f"refs/heads/{b}" and git(Path(path), "status", "--porcelain").stdout.strip():
            raise Refused(f"worktree {path} has uncommitted changes")
    # 6. Fast-forward only.
    git(repo, "fetch", "origin")
    if git(repo, "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{b}", check=False).returncode == 0:
        r = git(repo, "merge-base", "--is-ancestor", f"refs/remotes/origin/{b}", f"refs/heads/{b}", check=False)
        if r.returncode == 1:
            raise Refused(f"non-fast-forward: origin/{b} has commits {b} lacks")
        if r.returncode != 0:
            raise CommandError(f"git merge-base --is-ancestor origin/{b} {b}: {r.stderr.strip()}")
    if not Path(body_file).is_file():  # before the push: a missing body must not leave a branch without a PR
        raise Refused(f"body file not found: {body_file}")
    # 7. Push: same name both sides, no force, no upstream tracking.
    git(repo, "push", "origin", f"refs/heads/{b}:refs/heads/{b}")
    # 8. Reuse the open PR if there is one, so a retry is safe.
    r = run(["gh", "pr", "list", "--head", b, "--state", "open", "--json", "url", "-q", ".[0].url"], cwd=repo)
    existing = r.stdout.strip()
    if existing and existing != "null":
        return existing.splitlines()[-1]
    r = run(["gh", "pr", "create", "--base", default, "--head", b, "--title", title,
             "--body-file", str(Path(body_file).absolute())], cwd=repo)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    if not lines:
        raise CommandError("gh pr create: printed no PR URL")
    return lines[-1].strip()


def cleanup(repo: Path, task_ids: list[str]) -> list[str]:
    # Validate every id first, so a bad one changes nothing.
    for tid in task_ids:
        if not TASK_ID.fullmatch(tid):
            raise Refused(f"bad task id {tid}")
    repo = Path(repo).resolve()
    rows = krw.task_rows()  # (id, status, workspace_path, branch_name)
    by_id = {row[0]: row for row in rows}
    lines = []
    for tid in task_ids:
        row = by_id.get(tid)
        wt = repo / ".worktrees" / tid
        if row is None:
            lines.append(f"kept {tid}: no such card")
        elif row[1] not in krw.TERMINAL:
            lines.append(f"kept {tid}: card is {row[1]}")
        elif not wt.exists():
            lines.append(f"kept {tid}: no worktree at {wt}")
        else:
            other = next((o[0] for o in rows if o[0] != tid and o[2] and o[1] not in krw.TERMINAL
                          and Path(o[2]).resolve() == wt.resolve()), None)
            if other:
                lines.append(f"kept {tid}: in use by card {other}")
                continue
            ref = next((ref for path, ref in worktrees(repo) if ref and Path(path).resolve() == wt.resolve()), None)
            branch = (ref[len("refs/heads/"):] if ref else None) or row[3] or "?"
            r = git(repo, "worktree", "remove", str(wt), check=False)
            if r.returncode == 0:
                lines.append(f"released {tid} (branch {branch})")
            else:
                reason = " ".join(r.stderr.split()) or "git worktree remove failed"
                lines.append(f"kept {tid}: {reason}")
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Publish a feature branch as one PR; remove finished worktrees.")
    sub = ap.add_subparsers(dest="command", required=True)
    pub = sub.add_parser("publish", help="push a branch and open (or reuse) one PR")
    pub.add_argument("--repo", required=True, type=Path)
    pub.add_argument("--branch", required=True)
    pub.add_argument("--title", required=True)
    pub.add_argument("--body-file", required=True, type=Path)
    cln = sub.add_parser("cleanup", help="remove the worktrees of finished cards")
    cln.add_argument("--repo", required=True, type=Path)
    cln.add_argument("task_ids", nargs="+", metavar="task-id")
    args = ap.parse_args(argv)
    try:
        if args.command == "publish":
            print(publish(args.repo, args.branch, args.title, args.body_file))
        else:
            for line in cleanup(args.repo, args.task_ids):
                print(line)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    except CommandError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
