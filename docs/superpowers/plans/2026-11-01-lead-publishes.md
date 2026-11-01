# Lead publishes feature branches — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `lead` pushes a feature's final branch, opens one PR and removes finished worktrees, through a script that can never touch the default branch; no other role can push.

**Architecture:** A stdlib Python helper `scripts/hermes/squad_publish.py` (installed to `~/.hermes/scripts/` by the existing `install.sh` loop) does the publishing and cleanup and enforces the rules in code. `lead` gets the `terminal` toolset plus deny globs that block raw `git push`/`gh pr merge`, so the helper is its only way to publish. Other roles get push/PR denies. SOULs, checks and docs follow.

**Tech Stack:** Python 3 stdlib (`subprocess`, `argparse`, `sqlite3`, `unittest`), git, gh, bash (`check_squad.sh`), Hermes profile config.

**Spec:** `docs/superpowers/specs/2026-11-01-lead-publishes-design.md`

## Global Constraints

- Never push to, merge into, or force-push the default branch, `main` or `master`. No `+` refspecs, no `--force*`.
- Push is `refs/heads/<b>:refs/heads/<b>`, same name both sides.
- `git worktree remove` without `--force`; branches are always kept.
- Only `lead` can publish. `engineer`, `ops` and `reviewer` deny `git push*` and `gh pr *`.
- Role changes are made to the live profiles in `~/.hermes/profiles/<role>/`, then `python3 scripts/snapshot_team.py` (must end `scan: clean`). Never edit `team/` by hand. Back up a SOUL before patching it.
- Public repo: no absolute home paths, tokens or emails; write `~/…`.
- Installer and deny tests run in a throwaway `HERMES_HOME` outside `~/.hermes`; never start a gateway there.
- Tests: stdlib `unittest`, run with `python3 -m unittest discover -s scripts/hermes/tests -v`. No real network: `gh` is a stub on `PATH`; the remote is a local bare repo.

## Review Focus

1. Branch given as `HEAD`, `origin/main`, `refs/heads/main` or `MAIN`: still refused as the default branch (resolve to the real branch name first, compare case-insensitively).
2. Branch name containing `:` or starting with `+`: refused (refspec smuggling).
3. Re-running publish after a successful run: no second PR, prints the existing URL, exit 0.
4. Remote branch moved ahead (someone pushed to it): refused as non-fast-forward, nothing pushed.
5. Cleanup given a card that isn't done, or whose worktree has uncommitted changes: worktree left in place, reported, other ids still processed.

---

### Task 1: `squad_publish.py publish` (squad card: engineer)

**Files:**
- Create: `scripts/hermes/squad_publish.py`
- Test: `scripts/hermes/tests/test_squad_publish.py`

**Interfaces:**
- Produces CLI: `squad_publish.py publish --repo <path> --branch <name> --title <text> --body-file <path>` → stdout: the PR URL only; exit 0. Refusal → stderr `refused: <reason>`, exit 2. A git/gh failure → stderr `error: <cmd>: <stderr>`, exit 1.
- Produces functions: `default_branch(repo: Path) -> str` (from `git symbolic-ref --short refs/remotes/origin/HEAD`, stripping `origin/`; fallback `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`), `publish(repo: Path, branch: str, title: str, body_file: Path) -> str`, `class Refused(Exception)`.

Test fixture (`setUp`): temp dir with a bare repo `remote.git` (default branch `main`), a clone `repo` with one commit on `main`, `origin/HEAD` set, a feature branch `feat/x` with one commit checked out in a worktree `repo/.worktrees/t1`. A stub `gh` script first on `PATH` that appends its argv to `gh.log` and, for `pr list`, prints the contents of `$GH_STUB_EXISTING` (empty by default); for `pr create`, prints `https://github.com/o/r/pull/7`.

- [ ] **Step 1: Write the failing tests**
  - `test_publishes_feature_branch`: `publish(repo, "feat/x", "T", body)` returns `https://github.com/o/r/pull/7`; `git -C remote.git rev-parse feat/x` equals the local `feat/x` sha; `gh.log` has `pr create --base main --head feat/x --title T --body-file <body>`; `remote.git`'s `main` sha unchanged.
  - `test_refuses_default_branch` (subTests for `main`, `MAIN`, `master`, `HEAD` while HEAD is `main`, `origin/main`, `refs/heads/main`): raises `Refused`; remote unchanged; `gh.log` has no `pr create`.
  - `test_refuses_refspec_like_names` (subTests `+feat/x`, `feat/x:main`): `Refused`.
  - `test_refuses_dirty_worktree`: an untracked file in `.worktrees/t1` → `Refused` mentioning the path; nothing pushed.
  - `test_refuses_non_fast_forward`: push `feat/x`, then push a different commit to `remote.git`'s `feat/x` from a second clone → `Refused` containing `non-fast-forward`; remote sha unchanged.
  - `test_idempotent_when_pr_exists`: `GH_STUB_EXISTING=https://github.com/o/r/pull/7` → returns that URL; no `pr create` in `gh.log`.
  - `test_cli_exit_codes`: subprocess run of the script: success → 0 and stdout is the URL; `--branch main` → 2 and stderr starts `refused:`.

- [ ] **Step 2: Run tests, confirm they fail**
  Run: `python3 -m unittest discover -s scripts/hermes/tests -v`
  Expected: errors importing `squad_publish`.

- [ ] **Step 3: Implement `publish`**
  Order: validate name (no leading `+`, no `:`, no whitespace) → resolve `branch` with `git rev-parse --abbrev-ref <branch>` (so `HEAD` resolves) and strip a leading `origin/`/`refs/heads/` → refuse if it equals `default_branch()`, `main` or `master` (case-insensitive) → find the worktree holding the branch via `git worktree list --porcelain`; if any, refuse when `git -C <wt> status --porcelain` is non-empty → `git fetch origin` then if `refs/remotes/origin/<b>` exists, refuse unless `git merge-base --is-ancestor origin/<b> <b>` → `git push origin refs/heads/<b>:refs/heads/<b>` (shell-free `subprocess.run` list, never `--force`) → `gh pr list --head <b> --state open --json url -q '.[0].url'`; return it if non-empty, else `gh pr create --base <default> --head <b> --title … --body-file …` and return its last stdout line. Run `gh` with `cwd=repo`.

- [ ] **Step 4: Run tests, confirm they pass** (same command; expected `OK`).

- [ ] **Step 5: Commit** `feat(scripts): squad_publish publish refuses default branch and force`.

### Task 2: `squad_publish.py cleanup` (same squad card)

**Files:**
- Modify: `scripts/hermes/squad_publish.py`
- Test: `scripts/hermes/tests/test_squad_publish.py`

**Interfaces:**
- Consumes: `task_rows()` and `TERMINAL` from `scripts/hermes/kanban_release_worktrees.py` (import by putting the script's own directory on `sys.path`; both live side by side in `~/.hermes/scripts/`).
- Produces CLI: `squad_publish.py cleanup --repo <path> <task-id>...` → one stdout line per id: `released <id> (branch <b>)`, `kept <id>: <reason>`; exit 0 unless an id was malformed (exit 2).

- [ ] **Step 1: Write the failing tests** (patch `kanban_release_worktrees.task_rows` to return fixture rows `(id, status, workspace_path, branch_name)`):
  - `test_cleanup_releases_done_card`: `t1` done, clean → `.worktrees/t1` gone, `feat/x` still in `git branch --list`, output `released t1 (branch feat/x)`.
  - `test_cleanup_keeps_unfinished_card`: `t1` running → still present, output `kept t1: card is running`.
  - `test_cleanup_keeps_dirty_worktree`: done but with an untracked file → present, output starts `kept t1:`.
  - `test_cleanup_continues_after_keep`: ids `t1` (running) and `t2` (done, clean) → `t2` released.
  - `test_cleanup_rejects_path_like_id`: id `../x` → exit 2, nothing removed.

- [ ] **Step 2: Run, confirm failures.**
- [ ] **Step 3: Implement `cleanup(repo: Path, task_ids: list[str]) -> list[str]`**: ids must match `^[A-Za-z0-9_-]+$`; path `repo/.worktrees/<id>`; release only when status ∈ `TERMINAL` and the path exists; `git worktree remove <path>` (no `--force`), report git's stderr as the keep reason.
- [ ] **Step 4: Run, confirm `OK`.**
- [ ] **Step 5: Commit** `feat(scripts): squad_publish cleanup releases finished worktrees`.

### Task 3: Wiring check (same squad card)

**Files:**
- Modify: `scripts/check_squad.sh` (Roles section, after the kanban/model/skills checks)

**Interfaces:**
- Consumes: `hermes -p <role> config get platform_toolsets.cli` and `config get approvals.deny` (same style as the existing `tools=` line).

- [ ] **Step 1:** Add checks:
  - `lead`: FAIL `lead: no terminal toolset, so it can't publish` unless `- terminal` is present; FAIL `lead: raw git push not denied` unless deny contains `git push*`; FAIL `squad_publish.py not installed (./install.sh --kanban)` unless `$root/scripts/squad_publish.py` exists.
  - `engineer`, `ops`, `reviewer`: FAIL `<role>: can push (only lead publishes)` unless deny contains `git push*` and `gh pr *`.
- [ ] **Step 2: Verify in a throwaway home**: `HERMES_HOME=$(mktemp -d /tmp/hsq-test.XXXXXX) SQUAD_GIT_ROOT=<scratch dir with a test repo> ./install.sh --kanban --no-alias` → the new lines report FAIL (profiles are still the old ones) and the script is copied to `$HERMES_HOME/scripts/`. Paste the output in the handoff.
- [ ] **Step 3: Commit** `feat(check): verify only lead can publish`.

### Task 4: Live profile changes (default agent, top level, after the squad card is merged)

**Files:**
- Modify (live): `~/.hermes/profiles/lead/config.yaml`, `…/lead/SOUL.md`, `…/engineer/config.yaml`, `…/engineer/SOUL.md`, `…/ops/config.yaml`, `…/ops/SOUL.md`, `…/reviewer/config.yaml`
- Generated: `team/profiles/*` via snapshot

- [ ] **Step 1: Back up** each SOUL and config being changed (`cp X X.bak-$(date +%Y%m%d-%H%M%S)`).
- [ ] **Step 2: lead config**: add `terminal` to `platform_toolsets.cli`; append to `approvals.deny`: `git push*`, `git -c * push*`, `git -C * push*`, `gh pr merge*`, `gh api * -X *`, `gh api * --method *`, `git branch -D*`, `git reset --hard*`.
- [ ] **Step 3: engineer config**: add `git push*`, `git -C * push*`, `gh pr *` to `approvals.deny`. **ops, reviewer**: add `git -C * push*`, `gh pr *`.
- [ ] **Step 4: Probe the deny matcher** with Hermes's interpreter against each profile (`HERMES_HOME=~/.hermes/profiles/<role>` and `tools.approval_floors._match_user_deny_rule`), for:
  - lead: blocked: `git push origin feat/x`, `git -C /r push origin HEAD:main`, `gh pr merge 7`, `gh api repos/o/r/merges -X POST`. Allowed: `python3 ~/.hermes/scripts/squad_publish.py publish --repo . --branch feat/x --title t --body-file b`, `git log --oneline`, `gh pr view 7`.
  - engineer: blocked: `git push`, `gh pr create`. Allowed: `git commit -m "fix push retry"`.
  Expected: every case as listed. If a glob over-blocks a commit message, narrow it and re-probe.
- [ ] **Step 5: lead SOUL**:
  - Replace "You have no terminal or web." with: "Your terminal is for publishing and quick read-only checks (`git log`/`diff`/`status`, `gh pr view`). You still never implement, build or run tests; get anything more than a quick read from a fact-finding card."
  - Step 8 becomes: after the criteria check passes, publish the final branch (the integration branch, else the single implementation branch; on `cross-repo`, each repo's final branch) with `python3 ~/.hermes/scripts/squad_publish.py publish --repo <repo> --branch <b> --title <feature title> --body-file <file>`. The body summarises the original card's goal, acceptance criteria and the reviewer's verdict. Then `… cleanup --repo <repo> <child ids>`. Complete with the PR URL in the summary and `metadata.pr_url`. If publish prints `refused:` or fails, block with the output; never work around it.
- [ ] **Step 6: engineer and ops SOUL**: keep "Never push"; change "The human merges." to "`lead` publishes your branch as part of the feature PR; the human merges."
- [ ] **Step 7: Verify**: `./install.sh --check` ends `0 fail`; `python3 scripts/snapshot_team.py` ends `scan: clean`; `git diff team/` shows only the intended changes.

### Task 5: Docs and release (default agent)

**Files:**
- Modify: `README.md`, `AGENTS.md` (the "Humans merge the agents' branches; no role pushes or merges" line), `docs/runbook.md` (the human's flow: review and merge the PR; the worktree cron is a backstop), `docs/01-architecture.md:59` (push row: tool-level for all; only lead via `squad_publish`), `docs/04-learnings.md` (dated entry: squad trusted to publish; why the script, not globs), `docs/06-roadmap.md:11` (item 5 done), `docs/assets/squad-architecture.*` via `scripts/render_architecture.py` (labels "never pushes" / "you merge (ff-only) and push"), `scripts/hermes/kanban_release_worktrees.py` docstring (backstop now), `VERSION` → `1.5.0`.

- [ ] **Step 1:** Make the edits; `grep -rn "never push\|no role pushes\|ff-only" README.md AGENTS.md docs scripts` shows nothing stale.
- [ ] **Step 2:** `python3 scripts/snapshot_team.py` → `scan: clean`.
- [ ] **Step 3:** Show the user `git diff --stat`; commit, tag `v1.5.0` and push only when they say so.
- [ ] **Step 4:** Update the user-profile memory: the "card is done" routine becomes "verify, merge the PR, deploy server side to prod".

### Task 6: First real run (watch, don't build)

- [ ] On the next feature card: confirm `lead`'s summary has a PR URL, `git -C <repo> log origin/main` gained nothing from the squad, the child worktrees are gone, and `lead`'s Opus spend in Langfuse (env `hermes-lead`) hasn't jumped against its recent average. Note the result in `docs/04-learnings.md`.
