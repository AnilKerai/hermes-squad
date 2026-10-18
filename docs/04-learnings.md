# 04 Learnings

Each entry: what happened → why → what changed. Newest last. "Squad fix" = a change to SOUL/config/skills; "brief fix" = a change to how cards are written.

## Setup (11 Oct)

1. **Hermes already does "agent teams"; Bots are something else.** Kanban (durable board, dispatcher, review lane) runs the work; Bot Mode is chat with the same profiles. Both are built on profiles. → Built on Kanban.
2. **The Triage decomposer is a separate model call, not the lead.** It routes by profile *description*, ignoring the lead's SOUL. → Assign cards to the team's lead directly, so its own judgment frames the work; descriptions say what each role *refuses*.
3. **`hermes project create --board` doesn't link a board to its repo.** Cards defaulted to `scratch`, which is deleted at completion, so code would have been lost. → `kanban-repo-boards.sh` links boards the way the dashboard does; checked that new cards get `<repo>/.worktrees/<id>`.
4. **Projects are per-profile.** A lead creating `project=<repo>` cards resolves against its own projects database and silently falls back to scratch. → The script copies the project records to the team profiles.
5. **`default_assignee` does three jobs**: the desktop's default assignee, routing unassigned ready cards, and catching decomposer misroutes. → Set to `lead`, never an implementer. Archive probe cards before starting the gateway.

## First runs (11 Oct)

6. **"I can't see the output"**: the work is on a branch in a hidden worktree; `main` looks unchanged until merge.
7. **Hermes only removes a worktree whose commits are pushed**, and engineers never push, so worktrees lingered and held their branch (the IDE couldn't check it out). → A no-model cron releases finished cards' worktrees and keeps the branches.
8. **New worktrees branch from whatever the main checkout has checked out.** → Be on `main` when creating cards.
9. **CLAUDE.md/AGENTS.md are write-protected for headless workers**, and nobody can approve, so the card blocks. → Off for engineer (and later ops) only; reviewer scrutinises those diffs; standing rule to keep them current.
10. **A comment alone doesn't resume a blocked card**: comment then unblock. Capability blocks (protected files, missing credentials) don't clear with more input.
11. **Stale ignored build output broke the build after a layout change** (duplicate assembly attributes). → `git clean -fdX` before building a merged layout change.

## Two teams (11 Oct)

12. **Kanban routing config is global; boards isolate work, not teams.** A set `orchestrator_profile` *overrides* the root card's owner, so the dev lead would own research Triage cards. → Cleared; each team's lead owns its cards by assignment.
13. **Cards agents create default to scratch even when the board has a default folder** (only `dir`/`worktree` cards inherit it). → pm SOUL passes `workspace_kind="dir"` on every card.
14. **Parallel researchers share one citation ledger by default** and would overwrite each other's. → A ledger per card.
14b. **Triage works better as a human holding pen than as an auto-decompose queue.** The generic decomposer bypasses the lead's framing. → `kanban.auto_decompose: false`; rough ideas wait in Triage until promoted; executable work goes straight to the lead.

## Observability (11 Oct)

15. **Langfuse keys in `.env` do nothing on their own**: tracing needs the plugin enabled per profile plus the SDK. Clones copy keys only at creation. → `sync_langfuse_env.py`; `HERMES_LANGFUSE_ENV=hermes-<profile>` keeps Hermes traces apart from app traces in the shared project.
16. **Langfuse now prices Claude 5.5 natively** (15 Oct), and the v2 metrics API returns cost per role in one request; paging raw observations hits the rate limit. Use Langfuse's `totalCost`, not hand estimates from token counts: mine assumed a fixed cache read/write split and came out at ~$180 against Langfuse's $228.

## Cost and control (11–15 Oct)

17. **Research cost came from context size, not the model.** The researchers spent ~$72 over 1,730 calls averaging ~230K tokens each, mostly re-reading context. Compression never fired (50% of a 1M window). Every role had inherited `xhigh` thinking from the clone, and researchers attached a verbatim quote to every source. → Researcher on `medium`, compressing at 120K via Haiku; analyst compresses at 150K; quote checking left to the analyst. *Not yet measured.*
18. **Blocking a running card doesn't stop its worker**: the process keeps spending. → Stop it with `reclaim`, then park with `schedule`; a requeued worker starts fresh from the card, comments and files on disk.
19. **Hermes's "not a recognized config key" warning for `agent.reasoning_effort` is wrong.** Every surface reads it, including kanban workers (checked in the source).
20. **I wrongly ruled out Haiku** without checking the current release. Haiku 5.5 (Oct 2026) costs about 1/20 of Sonnet 5.5. → Check current releases and prices before ruling a tier out; A/B test it for researchers.

## Roles and guardrails (15 Oct)

21. **Split a profile for different tools, credentials, model or risk; use a skill when only the knowledge differs.** → `ops` became a profile; frontend/backend became skills, not profiles (FE+BE features would add handoffs that lose context).
22. **Every agent shares the real `$HOME`, so your `az` login was reachable by every role**, the researcher included. → `approvals.deny` per role: ops and reviewer read and validate only; the other roles have no cloud CLIs. These rules are matched per shell segment and apply even with approvals off; a raw `subprocess` gets around them.
23. **Pinned skills must exist on every profile the card visits**: review runs on the same card, so the reviewer needs them too.

## Review of the squad (15 Oct)

24. **The card loop works; the improvement loop is manual.** 53/65 cards done, no crashes; 19/19 approvals cite checks the reviewer ran; one real defect caught; 2 genuine escalations.
25. **One review skip**: an engineer used `kanban_complete` because a parent card was waiting on it. The lesson lived only in the lead's memory. → Rule added to engineer and ops SOULs.
26. **Cloning copied stale memory into three roles**, injecting wrong facts into every run. → Cleared (backups kept). Clones copy memory: audit it after creating a profile.
27. **My review missed the biggest gap, which the research team had already found**: `AGENTS.md` pointer files mean workers never get repo standards. Lesson: read the existing research before reviewing.
28. **Agent-made skills drift between per-profile copies** (`dotnet-prerelease-package-testing`: dev profiles hold the older version). The snapshot script now reports drift.

## Loops, digest and briefings (16 Oct)

29. **Kanban links run both ways, so "created without me" needs a graph walk.** A lead's own card is the *child* of the implementation card it waits on, so "has a human parent" misses most decomposition. → The digest counts a card as decomposition only when it reaches a human-created card through lead/pm-created cards; engineer follow-ups, and anything hung off them, count as created without you. Last 24 h: 6 of those vs 10 decomposition cards.
30. **Measure before writing a goal card.** A mutation-score goal for katas looked ideal, but Stryker.NET 5.0 doesn't support Microsoft Testing Platform (stryker-net#3094) and, with code and tests in one assembly, it mutates `Katas.Testing` instead. → Coverage of production files was used instead (baseline: ABCGame 81% lines, FizzBuzz `Program.cs` 31%, MagicSquare 74% branches; the rest 100%).
31. **Cron `deliver: origin` from the desktop app resolves to `local`**: there is no live delivery channel without a messaging platform. → WhatsApp for the digest and briefings.

## Portability and publishing (17 Oct)

32. **Absolute home paths tie a role to one machine.** The pm, researcher and analyst SOULs hard-coded `/Users/<me>/git/research` in four places, which doesn't exist on a Linux server. → Changed to `~/git/research`. Kanban expands `~` for `dir` workspaces (`resolve_workspace` returns the absolute path; checked in the source). The snapshot now rewrites the home directory and refuses to finish on any absolute home path left in the repo.
33. **A profile distribution installs only from a repo whose root holds `distribution.yaml`.** Hermes v0.22.2 has no subdirectory sources, so `hermes profile install github.com/...` can't reach one role in a seven-role repo. → Install each role from its folder in a local clone. `hermes profile update` re-reads the recorded folder, so updating is `git pull && ./install.sh`.
34. **A freshly installed distribution has no bundled skills until the role first starts.** Right after install the reviewer had no `sdlc-review` and the researchers had no `grounded-citations`, both of which their SOULs name. → `install.sh` seeds them with the same sync `hermes profile create` runs (`HERMES_HOME=<profile> hermes --run-module tools.skills_sync`).
35. **`kanban-repo-boards.sh` had silently broken.** It ran Hermes's managed Python without `hermes_bootstrap`, so `hermes_cli` stopped importing once a dependency moved (`No module named 'ruamel'`). → It now asks `hermes --print-runtime-command` for the interpreter and imports `hermes_bootstrap` first. Testing the install in a throwaway `HERMES_HOME` caught this, along with two installer bugs: a pipefail + `grep -q` check that created duplicate crons, and the board script assuming every dev role was installed.
36. **Check git history, not just HEAD, before making a repo public.** All 56 blobs ever committed were scanned for keys, emails, phone numbers, GUIDs, IPs and absolute paths. They were clean apart from home paths, so no history rewrite was needed.
37. **Routing is decided by the assignee and the board alone, so install can be verified without spending tokens.** In a throwaway Hermes home, `hermes kanban --board <b> dispatch --dry-run` sent an unassigned repo card to `lead` (via `default_assignee`), an `engineer` card to `engineer` with a worktree and branch in that repo, a research card to `pm` with workspace `~/git/research`, and a cross-repo card to `lead`. → `./install.sh --check` checks the static half: roles, kanban toolset, pinned skills, dispatcher settings, a board per repo, cron, sign-in and gateway. Against the live squad it found `hermes-squad` itself had no board. `gateway.multiplex_profiles` was missing from the published settings and is now included.
38. **An agent given only the repo URL got the roles installed but not the boards. The test also showed a sandbox in the wrong place points at the live home.** A fresh subagent followed `AGENTS.md`. Two things stopped or misled it: a `HERMES_HOME` inside `~/.hermes`, which Hermes resolves to `~/.hermes` itself (`get_default_hermes_root`), so the installer and Hermes disagreed about the home; and Hermes refuses kanban writes from `delegate_task` children. Only the existence of the hand-built profiles kept the live home safe. → `install.sh`, `check_squad.sh` and `kanban-repo-boards.sh` resolve the root the way Hermes does, refuse a `HERMES_HOME` inside `~/.hermes`, and point every `hermes` call at the root. The gateway check reads the `hermes_home` in `gateway.pid` instead of `hermes gateway status`, which reported the machine's live service. `AGENTS.md` says to install from a top-level session.
39. **A subagent's `export`s leaked into the parent's terminal session.** After the delegated test, my own shell had the child's `HOME`, `HERMES_HOME` and `SQUAD_GIT_ROOT`, so `~` pointed at the sandbox. → Before trusting the shell after a delegated task that exports variables, check `env`. Better, tell the child to set variables per command instead of exporting them.

