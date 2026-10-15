# 02 Context engineering

**Context engineering** is choosing which tokens sit in a model's window at each call, in what order, and keeping that set small, relevant and cheap to resend as the agent loop grows. Anthropic's framing, "the smallest possible set of high-signal tokens" ([Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)), matches what this setup found. The longer treatment is in [`research/context-engineering-coding-squads.md`](../research/context-engineering-coding-squads.md) §1–2.

## What a worker sees

Every Kanban worker is a new process with an empty window. It knows only what these layers put there:

| Layer | Source | Reaches | Holds | Status here |
|---|---|---|---|---|
| Role | `SOUL.md` | every run of that role | identity, standing rules, limits | ✅ Good: 1.7–4 KB per role |
| Routing | profile description | decomposer only | what work comes to this role and what it refuses | ✅ Tightened for two teams |
| Tools | toolsets + `approvals.deny` | every run | what the role can physically do | ✅ The strongest layer: removing a capability beats a written rule |
| Procedures | skills; per-card `--skill` pins | on demand | how-tos, conventions | ⚠️ New conventions skills untested; one skill has drifted between profiles |
| Repo rules | the worktree's `AGENTS.md` (or `CLAUDE.md`) | every role in that repo | commands, gotchas, done-means | ❌ **Broken in 14/16 repos**: `AGENTS.md` is a pointer, so workers get "read CLAUDE.md", not the rules (see [roadmap](06-roadmap.md) #1) |
| Lessons | profile memory | that role's later runs | what the role has learned | ❌ Barely used: only the lead has real lessons; three roles started with a stale copy of the default's memory (cleared 15 Oct) |
| Protocol | auto-injected kanban guidance | every worker | the board lifecycle | ✅ Built in |
| **Task** | **card body + attachments** | **that card only** | **goal, decisions, acceptance, verify** | ✅ **Strongest layer in practice** |
| Upstream | parents' handoff summary + metadata | child cards | what was decided and changed | ✅ Works; unchecked for completeness |
| History | prior runs + comments | retries of that card | what failed, reviewer findings | ✅ Works. Comments are read only at worker start. |

Inspect instead of guessing: `hermes kanban context <id>` shows what a worker received, `hermes kanban log <id>` what it did, and `hermes kanban runs <id>` the handoffs.

## Rules this setup runs on

1. **The card body is the prompt.** Workers can't see sibling cards or the chat that produced the card. Any decision two cards share is written into both, numbered so the reviewer can audit against it.
2. **Chat first, card second.** Ambiguity left in a card gets resolved by a guess, which copies into every child, or by a block. Product decisions are made with the human before the card exists.
3. **Separate the writer from the checker.** The reviewer re-runs the Verify commands; the engineer never marks its own homework.
4. **A handoff summary is a compression boundary.** The next role gets summary and metadata, not the transcript, so a thin summary starves it.
5. **Prefer a mechanism to a sentence.** A deny rule or a removed toolset beats "never do X" in a SOUL. Evidence: rules written in files get ~60–68% compliance vs ~88% for executable guardrails (research brief §0, single-source studies).
6. **Profile vs skill.** Create a new profile when a role needs different tools, credentials, model or risk rules. Use a skill when only the knowledge differs (hence `ops` is a profile; frontend/backend are skills).
7. **Standing rules go in SOUL.md, not repeated per card.** Per-card text is for this task only.
8. **Context size costs more than model tier.** The researchers' $72 was mostly re-read context (~230K tokens per call); compressing at a fixed token count and lowering the thinking level fix more than switching models does.
9. **Clones copy context.** `--clone` copies SOUL, memory, thinking level and toolsets. Set each per role and clear inherited memory.
10. **Agents propose, humans promote.** Self-written context is low-trust; lessons should become SOUL/skill/`AGENTS.md` changes through review. Not automated yet (see roadmap).

## Where to put a new piece of information

| It is... | Put it in | Not in |
|---|---|---|
| True for this one task | the card body | SOUL, memory |
| A standing behaviour for a role | that role's `SOUL.md` | every card |
| A procedure needed sometimes | a skill, pinned per card when needed | SOUL (it bloats every run) |
| A fact about one repo | that repo's `AGENTS.md` (canonical) | a role's memory |
| Something that must never happen | a deny rule, toolset removal or test | prose alone |
| A lesson a role keeps relearning | proposed as a SOUL/skill change, reviewed by the human | left in one role's memory |
