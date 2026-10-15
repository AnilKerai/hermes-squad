# 03 Industry alignment

*Written 15 Oct 2026. Field moves fast; re-check sources before relying on a number. Ratings: **Aligned** = matches the practice; **Partial** = right idea, weak enforcement or coverage; **Gap** = missing.*

## Summary

**The process design is in line with where the field is going; delivery and enforcement lag behind it.** Role separation, independent verification, durable task state and a human gate all match current practice and recent research. The gaps are the same ones the research team found on 12 Oct: repo standards don't reach the workers' context, many "musts" are written rules rather than mechanisms, and nothing measures whether a context change helped.

## The trends

### 1. From instructions to goals
Agents can now work for hours, so you give them outcomes and checks, not step lists. METR's task-length horizon has doubled about every 7 months since 2019, faster in 2024–25 ([METR](https://metr.org/time-horizons/)). By March 2026 agents completed coding tasks taking humans 14+ hours half the time ([AI Digest](https://theaidigest.org/time-horizons)). A goal = intent + a verifier + limits.

| Here | Rating |
|---|---|
| Every card is a goal: Goal, Decisions, Acceptance criteria, Verify commands. The lead re-checks the root against the *original* criteria and files follow-ups. | **Aligned** at card level |
| Single attempt per run; Hermes goal-mode cards (`--goal`, judge plus turn budget) unused. No outcome goals above cards (e.g. an eval metric to hit). | **Gap** |

### 2. Verification is the bottleneck
Producing plausible work is now easy; checking it is hard, and every verifier is a stand-in for what you actually meant ([The Verification Horizon, 2026](https://arxiv.org/html/2606.26300v1)). On multi-hour tasks, frontier agents solved <30%, failing mostly through poor self-checking, wrongly claiming a task was impossible, and stopping early. They tried to game the verifier in 13.8% of runs ([SWE-Marathon, 2026](https://arxiv.org/pdf/2606.07682)).

| Here | Rating |
|---|---|
| A separate reviewer re-runs the checks; 19/19 approvals cite checks it ran; tests may not be deleted, skipped or weakened; red checks (break the code on purpose and confirm a test fails). | **Aligned** |
| Handoff completeness and "tests pass" aren't gated by a tool. No eval-based verifiers (rubrics, regression sets) beyond each repo's tests. | **Partial** |

### 3. Separate roles over durable shared state
Research systems converge on Manager / Planner / Engineer / Reviewer roles running bounded missions over persistent state, keeping **fixed user intent** apart from a plan that evidence may change, and adopting new memory and skills only after review ([Argus, 2026](https://arxiv.org/pdf/2608.05144.pdf)). Practitioners agree multi-agent works when **writes stay single-threaded** ([Cognition, 2026](https://cognition.com/blog/multi-agents-working); contrast [Cognition, 2025](https://cognition.com/blog/dont-build-multi-agents)).

| Here | Rating |
|---|---|
| lead / engineer / ops / reviewer, pm / researcher / analyst; the board is the durable state; one writer per card and branch; the human merges. Nearly the same structure as Argus. | **Aligned** |
| Self-improvement isn't gated by review: memory and skill write approval are off, and lessons are applied by hand when noticed. | **Gap** (planned weekly retro) |

### 4. Context engineering as a discipline
Keep the window small and high-signal; root standards pinned; detail loaded just in time; compaction is lossy (it keeps facts and drops conversational rules) ([Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents); research brief §1). Context files are followed but add ~20% cost without significant success gains when they hold derivable overviews ([Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988)).

| Here | Rating |
|---|---|
| Layered context (SOUL / skills / card / handoff), trimmed toolsets, per-role compression thresholds, research cards sized to keep context small. | **Aligned** |
| `AGENTS.md` is a pointer in 14/16 repos, so Hermes workers' system prompts carry no repo standards (verified in Hermes's `prompt_builder.py`). Repo files hold derivable structure lists and task state. | **Gap**, the biggest one |

### 5. Executable guardrails beat written rules
A trivial rule written in a file got 60–68% compliance across 1,650 Claude Code sessions; executable guardrails reached 88.3% vs 67.0% ([Instruction Adherence](https://arxiv.org/abs/2605.10039); [ContextCov](https://arxiv.org/abs/2603.00822); single-source each).

| Here | Rating |
|---|---|
| Tool-level `approvals.deny` per role (tested: 24 commands × 4 profiles plus a live probe); trimmed toolsets; instruction-file protection on for non-writers. | **Aligned** for infrastructure |
| "Never push" (engineer), "always request review", "handoff fields present" are SOUL text only; credentials are shared via `$HOME`. | **Partial** |

### 6. Memory: agents propose, humans promote
Self-written skills don't substitute for curated ones ([SkillsBench](https://arxiv.org/abs/2602.12670)); whole-context LLM rewrites degrade accuracy ([ACE](https://arxiv.org/abs/2510.04618)); cited, verified, itemised memories raised Copilot's merge rate from 83% to 90% ([GitHub](https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot), vendor, single source).

| Here | Rating |
|---|---|
| Lessons go into SOUL/skills by explicit human request, with backups; the review rule for instruction-file diffs. | **Partial** |
| Role memory mostly empty or stale; agent-made skill already drifted across profiles; no write approval. | **Gap** |

### 7. Measure outcomes, evaluate every context change
Teams evaluate agents with regression sets built from real failures ([Anthropic, Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)) and judge sessions by outcome (cost per merged change, review rework), not tokens.

| Here | Rating |
|---|---|
| Langfuse traces per role, with native prices; cost per role in one metrics query; board history gives review rounds and blocks. | **Partial** |
| No regression set; traces not tagged with card id or context version; no record of which SOUL version produced which result. This repo's snapshots are the first step. | **Gap** |

### 8. Multi-agent buys breadth with tokens
A lead plus subagents beat single-agent Opus 4 by 90.2% on research, at about **15× the tokens** ([Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)).

| Here | Rating |
|---|---|
| Research team's measured ~$53/brief vs ~$4 per dev feature matches that cost profile. Mitigations applied (compression, medium thinking, no quote-checking); not yet measured. | **Aligned, cost-managed** |

### 9. Humans back in the loop
As agents get capable, the bottleneck moves to capturing intent, making work checkable, and steering it ([Humans are Missing, 2026](https://arxiv.org/pdf/2608.12355v1)).

| Here | Rating |
|---|---|
| Chat-first card drafting; typed blocks for real decisions (2 genuine escalations in 65 cards); human merge and deploy gates. | **Aligned** |
| Steering mid-run is coarse: workers only read comments at start, so redirecting means a reclaim and requeue. | **Partial** |

## Where this setup deliberately differs

- **Human merge and deploy, always.** Many products auto-merge on green CI. Here the human is the final gate. A deliberate choice while learning, and cheap at this volume.
- **Opus for planning and review, Sonnet for doing.** Mainstream practice. The cheapest model tier (Haiku 5.5) is untested for researchers.
- **Same model family for writer and reviewer** (Anthropic only, by choice). Different model families have different blind spots, which would make the reviewer more independent; accepted trade-off.
