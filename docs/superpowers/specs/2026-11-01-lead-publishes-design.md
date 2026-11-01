# Lead publishes feature branches as PRs

## Intent

The squad has earned enough trust to publish its own work. Today every branch stays local and the human merges, pushes and cleans up worktrees. From now on `lead` pushes the finished feature branch, opens one PR per feature and cleans up the worktrees. The human still reviews and merges the PR.

## Goals

- When a feature's final branch is approved by the reviewer, `lead` pushes it and opens a PR against the repo's default branch.
- `lead` removes the worktrees of its finished child cards.
- Only `lead` publishes. `engineer`, `ops` and `reviewer` never push.

## Non-goals

- No change to how work is planned, implemented or reviewed. Merging stays with the human.
- No server-side branch protection (the human may add it later; this design must not depend on it).
- No Hermes `completion_contract` PR gate: it needs required checks, which private repos on GitHub Free can't have.
- Superpowers: parked, separate decision.

## Anti-goals

- Anything reaching `main`/the default branch: a push, a force-push, or a merge.
- `lead` drifting into implementing or testing now that it has a shell.

## Approaches

| | Approach | Verdict |
|---|---|---|
| A | Give `lead` the terminal toolset; publishing only through `squad-publish`, a script that enforces the rules in code; raw `git push`/`gh pr merge` denied to `lead` | **Chosen** by the human: the rule is tested code, and it's `lead` doing it. Cost: "never implement" goes back to being a SOUL rule only |
| B | `lead` gets a terminal; deny-list patterns only | Rejected: refspecs (`HEAD:main`) slip past globs |
| C | `lead` stays shell-less; a cron publishes from `lead`'s handoff | Rejected: not the lead, delayed, failures not seen by `lead` |

## Decided

- **One PR per feature.** The branch published is the integration branch (`lead`'s own card branch) when there's an integration card, otherwise the single implementation card's branch. Cross-repo: one PR per repo, each from that repo's final branch.
- **When:** in `lead`'s wake-up step (SOUL step 8), after the criteria check passes and before `kanban_complete`. The PR URL goes in `lead`'s completion summary and metadata (`pr_url`).
- **`squad-publish <repo-path> <branch> --title … --body-file …`** (in `scripts/hermes/`, installed to `~/.hermes/scripts/` like the other helpers). It refuses, with a non-zero exit, when:
  - the branch is the repo's default branch (read from `origin/HEAD`/`gh repo view`) or `main`/`master`;
  - the push would not be a plain fast-forward of the remote branch (no force, no `+refspec`);
  - the working tree of that branch's worktree is dirty.
  Otherwise it runs `git push -u origin <branch>:<branch>` (same name both sides), then `gh pr create --base <default> --head <branch>` (or prints the existing PR's URL if one is open, so a retry is safe). It never merges.
- **Worktree cleanup:** `squad-publish --cleanup <card-id>…` (or a step in the same run) removes the worktrees of the named finished child cards with `git worktree remove` (no `--force`), keeping the branches. `lead`'s own worktree is released after completion by the existing cron, which stays as a backstop.
- **Enforcement:**
  - `lead` config: add `terminal` to its CLI toolsets; deny `git push*`, `gh pr merge*`, `gh api * -X *`/`--method *` (writes via the API), `git branch -D*`, `git reset --hard*` on top of the current deny list.
  - `engineer` config: deny `git push*` and `gh pr *` (roadmap item 5 closed at tool level: only `lead` publishes now).
  - `ops`/`reviewer`: unchanged (already deny `git push*`); add `gh pr *`.
- **SOUL changes (lead):** replace "You have no terminal or web" with: you have a terminal for publishing and read-only fact checks (git log/diff/status, gh pr view); you still never implement, build, or run tests, which stays the engineer's and reviewer's job. Fact-finding cards remain the default for anything beyond a quick read.
- **SOUL changes (engineer/ops):** "Never push" stays; reword "The human merges" to "`lead` publishes; the human merges".
- **Docs:** README, AGENTS.md, runbook (the human's flow becomes "merge the PR"), 01-architecture (push row), 04-learnings (dated entry), 06-roadmap (item 5 done), architecture diagram labels.

## Left to the builder

- Exact deny patterns, verified against Hermes's matcher in a throwaway `HERMES_HOME`, including whether a denied command inside `squad-publish` is still allowed (it must be: the deny applies to the agent's command string).
- Tests for `squad-publish` against a scratch repo with a local bare remote: refuses main/default, refuses a non-fast-forward, refuses a dirty tree, is idempotent on retry. `gh pr create` stubbed.
- `check_squad.sh`: PASS when `lead` has terminal plus the push deny and the script is installed.

## Verify

- Script tests pass; `./install.sh --check` ends `0 fail`; `python3 scripts/snapshot_team.py` ends `scan: clean`.
- In a throwaway home: `lead` running raw `git push` is denied; `squad-publish … main` refuses.
- First real feature after rollout: PR opened by `lead`, no push to the default branch, child worktrees gone.
