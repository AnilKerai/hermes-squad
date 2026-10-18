# Runbook

## Give the squad work
1. Draft in chat first (goal, why, constraints, out of scope, done-when as runnable checks). The card body is the only brief a worker gets.
2. Be on `main` in the repo (new branches start from its HEAD).
3. Create the card on the **repo's board**, assigned to the team lead:
   ```bash
   hermes kanban --board <repo> create "<title>" --body-file card.md --assignee lead --idempotency-key <key>
   hermes kanban --board research create "<title>" --body-file card.md --assignee pm \
     --workspace dir:~/git/research
   ```
   Cross-repo: `--board cross-repo`, assignee `lead`, not `--triage`.
4. Watch: desktop Kanban page (pick the board in the header), or `hermes kanban --board <repo> watch`.

## Goal-mode cards (keep going until X is true)
For open-ended work with a machine-checkable end state (coverage or warning targets, a flaky suite stable over N runs, every instruction file accurate). The worker loops in one session; after each turn a judge reads **only the title and body** and decides whether it's done. Out of budget → the card blocks for you. The review lane still runs after.
```bash
~/.hermes/scripts/kanban-goal-card.sh <board> "<title>" card.md [max-turns=20] [assignee=engineer]
# = hermes kanban --board <b> create "<title>" --body-file card.md --assignee engineer --goal --goal-max-turns 20 --idempotency-key goal-<hash>
hermes kanban --board <b> log <id> | grep "goal loop"    # one "turn N/M verdict=…" line per judged turn
```
- Write the body as the judge's checklist: Acceptance criteria with a Verify command each, and an exceptions clause on absolute ones.
- Assign the engineer directly for a single-repo loop; the lead can also create goal-mode children itself (lead SOUL step 5a).
- Skip it for ordinary feature cards: the judge adds a model call per turn, and the reviewer is already the check.
- The judge model is `auxiliary.goal_judge` (`auto` = the worker's own model).

## Morning digest and dashboard
- **Digest** (cron `Morning squad digest`, 07:30 daily, no model calls): `python3 ~/.hermes/scripts/squad_digest.py [hours]` shows what finished, what is waiting on you, cards agents created without you, what's in flight, and spend per role.
- **Dashboard** (cron `Squad dashboard refresh`, every 5 min, silent): writes `~/.hermes/dashboards/squad.html`. In the desktop chat, ask for "the squad dashboard" and it is shown with `::preview`; its buttons send prompts back to the chat.
- Both read the board DBs read-only and Langfuse cost via `squad_status.py`.
- On a new machine, `./install.sh --kanban --extras` creates both crons with `deliver: local`. Point them at a messaging channel with `hermes cron edit` once one is paired.

## Inspect
| Question | Command |
|---|---|
| What's live across all boards? | `for db in ~/.hermes/kanban.db ~/.hermes/kanban/boards/*/kanban.db; do sqlite3 -readonly "$db" "select id,status,assignee,title from tasks where status not in ('done','archived')"; done` |
| What did a worker receive? | `hermes kanban --board <b> context <id>` |
| What did it do? | `hermes kanban --board <b> log <id>` |
| Handoffs and review history | `hermes kanban --board <b> runs <id>` |
| Cost per role | Langfuse, filter environment `hermes-*`, or the metrics query in [05](05-metrics.md) |

## Answer a blocked card
Comment, **then** unblock (a comment alone doesn't resume it):
```bash
hermes kanban --board <b> comment <id> "<answer>"
hermes kanban --board <b> unblock <id>
```
For a capability block (missing access, protected file), fix the capability or do the step yourself on the card's branch, then comment "done, don't redo; re-verify" and unblock.

## Pause or stop
- **One card:** `hermes kanban --board <b> reclaim <id> && hermes kanban --board <b> schedule <id> "paused"`; resume with `unblock`. Never just block a running card: the worker keeps spending.
- **Everything:** `hermes gateway stop` (no new workers), then reclaim each running card; `hermes gateway start` to resume.
- **Redirect a running worker:** desktop "Note & requeue" (workers read comments only at start).

## Merge agent work
1. Card `done` (approved). Never merge a branch a worker may still write to.
2. `git fetch && git checkout main && git merge --ff-only <branch>`.
3. Build and test on `main` (`git clean -fdX` first if the layout changed).
4. `git push`, `git branch -d <branch>`, `git worktree prune`.

## Change the team
| Change | Steps |
|---|---|
| Edit a role | Back up (`cp SOUL.md backups/soul/SOUL.md.$(date +%Y%m%d-%H%M%S)`), patch in place, run `python3 scripts/snapshot_team.py` here (it must end `scan: clean`; the repo is public), commit. Applies from that role's next card; no restart. Write paths as `~/...`, never `/Users/<me>/...`, so the role works on another machine. |
| Add a repo | `~/.hermes/scripts/kanban-repo-boards.sh` |
| Add a profile | `hermes profile create <p> --clone-from <closest> --description "..."`; set model and thinking level; **clear inherited memory**; write SOUL; set toolsets and `approvals.deny`; `python3 ~/.hermes/scripts/sync_langfuse_env.py`; add to `TEAM` in `kanban_repo_boards.py` and re-run it; snapshot and commit. |
| Change `kanban.*` | `hermes config set kanban.<k> <v>`, then `hermes gateway restart` (running workers survive); confirm in `~/.hermes/logs/gateway.log`. |
| Rotate Langfuse keys | Edit `~/.hermes/.env` only, then `python3 ~/.hermes/scripts/sync_langfuse_env.py`. |

## Release a new version of the roles
Bump `VERSION`, run `python3 scripts/snapshot_team.py`, commit, then `git tag v$(cat VERSION) && git push --follow-tags`. Machines that installed the squad pick it up with `git pull && ./install.sh`.

## Move to another machine (e.g. a private server)
Two routes, depending on whether the agents' memories and history should come along:

| Route | Brings | Steps |
|---|---|---|
| **Fresh squad from this repo** | Roles, skills, kanban settings, boards, worktree cron. Not memories, sessions, crons with personal delivery targets, or keys | Install Hermes, `hermes model` (sign in), clone this repo and `./install.sh --kanban`, clone the repos into `~/git`, then `hermes gateway install` |
| **Exact copy** | Everything under `~/.hermes`: all profiles with memories and sessions, crons, kanban DBs, `.env` and `auth.json` | `hermes backup -o hermes-migrate.zip` here; on the server `hermes gateway stop`, `hermes import hermes-migrate.zip`, `hermes doctor`. Then fix what doesn't carry over: boards and projects point at the Mac's home-directory paths (re-run `scripts/hermes/kanban-repo-boards.sh` after cloning the repos), `hermes gateway install` for systemd, `gh auth login`. The zip holds credentials in plain text: copy it with `scp` and delete it afterwards |

Either way, stop the Mac's gateway or run `hermes pause` once the server is live, otherwise crons and the dispatcher run twice.
