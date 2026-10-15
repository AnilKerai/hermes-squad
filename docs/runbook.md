# Runbook

## Give the squad work
1. Draft in chat first (goal, why, constraints, out of scope, done-when as runnable checks). The card body is the only brief a worker gets.
2. Be on `main` in the repo (new branches start from its HEAD).
3. Create the card on the **repo's board**, assigned to the team lead:
   ```bash
   hermes kanban --board <repo> create "<title>" --body-file card.md --assignee lead --idempotency-key <key>
   hermes kanban --board research create "<title>" --body-file card.md --assignee pm \
     --workspace dir:/Users/anilkerai/git/research
   ```
   Cross-repo: `--board cross-repo`, assignee `lead`, not `--triage`.
4. Watch: desktop Kanban page (pick the board in the header), or `hermes kanban --board <repo> watch`.

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
| Edit a role | Back up (`cp SOUL.md backups/soul/SOUL.md.$(date +%Y%m%d-%H%M%S)`), patch in place, run `python3 scripts/snapshot_team.py` here, commit. Applies from that role's next card; no restart. |
| Add a repo | `~/.hermes/scripts/kanban-repo-boards.sh` |
| Add a profile | `hermes profile create <p> --clone-from <closest> --description "..."`; set model and thinking level; **clear inherited memory**; write SOUL; set toolsets and `approvals.deny`; `python3 ~/.hermes/scripts/sync_langfuse_env.py`; add to `TEAM` in `kanban_repo_boards.py` and re-run it; snapshot and commit. |
| Change `kanban.*` | `hermes config set kanban.<k> <v>`, then `hermes gateway restart` (running workers survive); confirm in `~/.hermes/logs/gateway.log`. |
| Rotate Langfuse keys | Edit `~/.hermes/.env` only, then `python3 ~/.hermes/scripts/sync_langfuse_env.py`. |
