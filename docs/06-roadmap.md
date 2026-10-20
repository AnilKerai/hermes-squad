# 06 Roadmap

Ranked by expected payoff. "Research §6.4 #n" = the matching change in [`research/context-engineering-coding-squads.md`](../research/context-engineering-coding-squads.md), which has the evidence and effort estimates.

| # | Change | Why | Status |
|---|---|---|---|
| 1 | **Make `AGENTS.md` canonical in every repo**: move `CLAUDE.md` content into it, make `CLAUDE.md` import it, drop derivable structure lists and task state, add "done means" and "where to look", keep files ≤150 lines (research §6.4 #1) | Workers currently get a pointer instead of repo standards; everything else assumes standards reach the worker | Open |
| 2 | **Weekly retro**: a scheduled job reads the week's runs, review findings, blocks and cost per role; writes a scorecard and *proposes* SOUL/skill changes for human approval | Closes the improvement loop without agents rewriting their own instructions | Agreed, not started |
| 3 | **Team as code**: this repo becomes the source; SOULs and shared skills sync into profiles (shared skills via `skills.external_dirs`); `skills.write_approval` and `memory.write_approval` on (research §6.4 #4) | One reviewed copy of each skill; every context change is a diff; fixes skill drift | Snapshot done; `team/profiles/` are installable profile distributions with `install.sh` (17 Oct); sync into the live profiles not started |
| 4 | **Typed handoff + completion gate**: Constraints / Out of scope fields in lead cards; handoff block (constraints, dead ends, unverified claims, head SHA); `pre_tool_call` hook rejects incomplete `kanban_request_review` (research §6.4 #2) | Summaries drop binding constraints; a mechanism beats a written rule | Open |
| 5 | **Enforce "never push/merge" for the engineer** with a `pre_tool_call` hook (research §6.4 #3) | Only ops and reviewer have it at tool level | Open |
| 6 | **Outcome-tagged traces + regression set**: tag traces with card id, repo and `AGENTS.md`/SOUL version; replay 10–20 past cards when context changes (research §6.4 #9–10) | The only way to know whether changes 1–5 helped | Open |
| 7 | **Goal-mode experiment**: one eval-driven card on istyar (target metric, `--goal`, turn budget, reviewer checks the eval) | Moves from task goals to outcome goals | Lead SOUL step 6a (was 5a) + `kanban-goal-card.sh` done (16 Oct); calibration card on katas (coverage) drafted; istyar eval card next |
| 8 | **Haiku 5.5 A/B for researchers** on the next research card | Potentially ~20× cheaper research at equal quality | Proposed |
| 9 | **Bring `eng-standards` (Claude Code plugin) into Hermes** via `skills.external_dirs` (research §6.4 #5) | One source of standards across tools | Open |
| 10 | **Contract-first cross-repo rules** (research §6.4 #7) | Producer/consumer changes need a contract step and version handoff | Open |
| 11 | **Credential isolation**: per-profile home or scoped service principal for ops; no CLI logins for other roles | Deny lists cover verbs, not credentials | Deferred (proportionate for private dev) |
| 12 | **Housekeeping**: fix the snapshot-reported skill drift; reviewer description mentions ops; `az bicep upgrade` (0.36 → 0.48); fix ballistic's secret-bearing Bicep output | Small fixes found along the way | Open |
| 13 | **Bug-hunt replay**: run the `bug-hunt` process on model-harness @ a8d0267 and score its findings against the ~25 known bugs (`~/.hermes/evals/model-harness-bughunt-a8d0267`); then a blind replay of the original, uncorrected fix cards to see whether the reviewer catches a narrow fix | First outcome-scored regression set (feeds #6); measures learning #43 | Planned (after 1.4.0) |
