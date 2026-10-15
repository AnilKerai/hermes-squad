# Context engineering for coding-agent squads: decision brief

Analyst card t_52f15274 · 12 October 2026 · Synthesises the five findings files in `context-engineering-coding-squads/` and builds on the earlier brief `coding-agent-squad-build-options.md` (10 Oct 2026), which covers harness choice, the guidance/enforcement split and AGENTS.md/CLAUDE.md portability and is not repeated here.[1]

**Labels.** `[vendor]` vendor docs, blogs or system cards; `[independent]` independent study, benchmark, regulator or standards body; `[practitioner]` practitioner report; `(single source)` a number resting on one source; `[Claude Code]` and `[Hermes]` tool-specific claims (unmarked claims are tool-neutral). "Synthesis" marks a researcher's or my own design, not a sourced fact. "Observed" marks something read in your local setup on 12 Oct 2026, read-only. Load-bearing claims were re-fetched today; the verification log is in section 7.

---

## 0. Recommendation

**Adopt a files-first, layered, gate-backed approach.** Keep each kind of memory in the store whose writer, reviewer and load mode fit it; load standards just in time from small, owned files; turn every "must" into a deterministic check; and pass work between sessions and agents through reviewed files and a small typed handoff block, not transcripts. The evidence for each piece is uneven, but it all points the same way, and none of it supports one big instruction file, an agent-curated memory service, or trusting the model to remember a rule.

1. **Standards and project knowledge live in reviewed repo files, loaded in layers.** One hand-written `AGENTS.md` per repo (about 100–200 lines: commands, non-default conventions, gotchas, done-means, a where-to-look index), imported by `CLAUDE.md`; detail in path-scoped rules, skills, ADRs and docs on demand. Anthropic targets under 200 lines `[vendor]`;[2] context files are followed but add about 20% to cost with no significant success gain `[independent]`.[3]
2. **Every "must" is executable.** A trivial rule written in the file got 60–68% compliance across 1,650 Claude Code sessions, while executable guardrails reached 88.3% against 67.0% for prompt-only `[independent]` (single source each).[4][5]
3. **Task state lives on the board plus a committed progress file; transcripts are disposable.** Resume from files and git, and keep must-survive rules in the root file or a gate: compactors kept 17% of session constraints on average `[independent]` (single source).[6][7]
4. **A handoff is short prose plus a typed block** (constraints verbatim, decisions with why, failed attempts, evidence at a SHA, unverified claims, open questions), checked by a hook. Ordinary compression deactivated binding constraints 100% of the time and led to forbidden actions 54.2% of the time, and four restored fields cut that to 0% `[independent]` (single source, synthetic).[8]
5. **Cross-repo work is contract-first, one writer per repo under a lead,** fed a curated contract-diff packet; raw upstream evidence lowered agent pass rates by 7–23 points and structured evidence raised them `[independent]` (single source).[9]
6. **Agents propose lessons; humans promote them by PR** into itemised, cited, dated entries. Self-written skills did not substitute for curated ones `[independent]`,[10] whole-context LLM rewrites collapsed accuracy `[independent]`,[11] and cited, verified memories raised Copilot's merge rate from 83% to 90% `[vendor]` (single source).[12]
7. **Every context change is evaluated, and sessions are measured by outcome:** a 20–50 task regression set from real failures `[vendor]`,[13] and Langfuse traces tagged with task id and context SHA for cost per merged change, first-pass CI, review rework and standards hits, not token counts `[independent]`.[14]

### First three changes at work (Claude Code, UK enterprise)

| # | Change | Why first |
|---|---|---|
| W1 | **Short, executable standards per repo.** A hand-written `AGENTS.md` imported by a thin `CLAUDE.md` (template 3.4), detail in `.claude/rules/` with `paths:`; a `Stop`/`SubagentStop` hook running `dotnet build -warnaserror`, `dotnet format --verify-no-changes`, architecture tests and the contract diff; the same commands as required CI checks | Moves compliance most: about two-thirds from context alone against close to 90% with executable checks (3.3, 3.4) |
| W2 | **One state and handoff protocol.** Task state on the tracker plus a committed `PROGRESS.md`; every handoff ends with the typed block (2.3), enforced by a `SubagentStop` key check; `/clear` between tasks, reset after two failed corrections | Long and multi-agent work fails at handoffs and compaction, and loses exactly constraints, dead ends and provenance (1.5, 2.2, 2.3) |
| W3 | **Ownership and measurement.** A named context owner; CODEOWNERS on `AGENTS.md`, `.claude/**` and `docs/`; lessons only by PR (auto memory off or inventoried on shared repos); a 20–50 task regression set; Langfuse tags `task`, `ctx`, `model`. Precondition: the managed-settings baseline (5.2, P0) | Without owners and an eval, context grows and goes stale, and nobody can tell whether a change helped (4.4, 4.5, 5.4) |

### First three changes in Hermes

| # | Change | Why first | Effort |
|---|---|---|---|
| H1 | **Fix the context-file inversion.** In 14 of your 16 code repos `AGENTS.md` is a 1–7 line pointer to `CLAUDE.md` (observed). Hermes loads only the first non-empty project file, `AGENTS.md` first, so engineer and reviewer workers start every card with the pointer in their system prompt and none of the 15–302 lines of real guidance (verified in the installed source). Make `AGENTS.md` canonical and `CLAUDE.md` an `@AGENTS.md` import; trim the over-budget files and move status and roadmap sections to the board | Standards reach a worker today only if it opens `CLAUDE.md` itself, and that copy is a tool result the compressor replaces with a placeholder once the context passes 50% | M, ~6–8 h |
| H2 | **Enforce the handoff and "never push" with `pre_tool_call` shell hooks** in the engineer and reviewer `config.yaml`: block `kanban_request_review`/`kanban_complete` unless the typed keys and a verification result are present, and block `git push`/`git merge` with `fail_closed`. Add **Constraints** and **Out of scope** to the lead's card fields | Both rules are advisory today; `pre_tool_call` is the only hook that can block here, and workers load it from `config.yaml`, not from `hooks/` | M, ~4–6 h with a throwaway-board test |
| H3 | **Gate and share skills.** Turn on `skills.write_approval` and `memory.write_approval` in all six profiles; move the squad's workflow skills into one git-tracked directory read through `skills.external_dirs` | Per-profile copies have already drifted: the dev profiles hold older `dotnet-prerelease-package-testing` and `sdlc-review` than the research profiles, and the agent-created .NET skill was patched 14–26 times in a day (observed) | S, ~2–3 h |

The full prioritised list of 12 Hermes changes is in 6.4.

### Confidence: medium

- **High on mechanics.** What loads, in what order, what survives compaction, what hooks can block and how caching is priced come from first-party docs and Hermes source, re-checked today. The finding behind H1 is high confidence: I read it in the installed v0.21.6+666 source.
- **Medium on the design.** Vendors, practitioners and independent studies converge: executable checks beat prose, summaries drop constraints, self-written context hurts, verified itemised memory helps. Most of the design itself is still experience, not controlled comparison.
- **Low on magnitudes for your stack.** No study covers C#/.NET, few cover Claude 5-series models, and the compliance and handoff numbers are mostly single-source 2026 preprints on Python or TypeScript.

What would change the recommendation is in section 7.

---

## 1. What context engineering is and how it works

**Context engineering is choosing which tokens sit in the window at each model call, in what order, and how that set stays small, relevant and cheap to resend as an agent loop keeps adding to it.** The mechanical parts are real and measurable: prefix caching, what compaction drops, tool-output bloat and isolation. Much of the surrounding vocabulary relabels existing practice.

### 1.1 Definition, contrast and hype

It differs from prompt engineering by working on the whole evolving window rather than one instruction, and from RAG by also covering removal, caching, ordering and isolation, not just retrieval. Anthropic calls it the "natural progression" of prompt engineering; an academic survey folds RAG, memory and multi-agent work into it `[vendor]` `[independent]`.[15][16]
The definitions disagree on one axis: Tobi Lütke asks for "all the context for the task to be plausibly solvable", Anthropic for "the smallest possible set of high-signal tokens".[17][15]
The degradation evidence below sides with Anthropic.

**Hype or relabelling:**
- "Context engineering replaced prompt engineering": it contains it.
- "Context rot" as a law: Chroma named it, tested models up to Claude Opus 4 on simple tasks, and sells a vector database `[independent]`.[18]
- Breunig's four failure modes as measured quantities: useful vocabulary, mostly anecdotal evidence `[practitioner]`.[19]
- Magic numbers such as "under 200 lines" or "compact at 150K": defaults, not optima.[2][20]
- "A bigger window solves it": Anthropic itself rejects this `[vendor]`.[15]

### 1.2 What goes into the window, and in what order

At the API the cached prefix is tools, then system, then messages; a change at any level invalidates that level and everything after it `[vendor]`.[21]
`[Claude Code]` sends system prompt and tools, then project context (`CLAUDE.md`, auto memory, unscoped rules), then the conversation. `CLAUDE.md` arrives as a user message, so the model treats it as context, not configuration `[vendor]`.[22][2]
In Anthropic's illustrative simulation the startup load is about 7,850 tokens; tool results ("file reads dominate context usage"), path-scoped rules, nested files, skill bodies and subagent results then accumulate mid-conversation.[23]
`[Hermes]` builds SOUL.md as the identity slot, one project context file, a frozen memory snapshot and the skills index; nested context files arrive inside tool results, which keeps the system prompt and its cache stable.[24][25]

Position effects are second-order: "lost in the middle" was measured on 2023 models `[independent]`, Anthropic says newer models are less end-biased `[vendor]`, and nothing controlled exists for Claude 5.x.[26][27]

### 1.3 How long context degrades

All six modes are gradients, not cliffs `[vendor]`.[15]

| Mode | Best evidence | Mitigation for coding agents |
|---|---|---|
| **Rot** (length alone) | Opus 4.8 GraphWalks F1 85.9 at 256K → 68.1 at 1M `[vendor]`;[28] 11 of 13 models below half their short-context score at 32K `[independent]`;[29] the Opus 5.5 card publishes no curve[30] | `/clear` between tasks; subagents for exploration; set `/autocompact` from your own traces |
| **Lost in the middle** | 2023 models `[independent]`[26] | Standing rules in the root file; plan in a file, re-read |
| **Poisoning** | 39% average drop from single-turn to multi-turn `[independent]`[31] | Tests as ground truth; clear after two failed corrections `[vendor]`[32] |
| **Distraction** | Premature termination rises with length (search tasks) `[independent]`;[33] Opus 4.5 removed Sonnet 4.5's "context anxiety" `[vendor]`[34] | Reset with a structured handoff |
| **Confusion** | Tool choice degrades past 30–50 tools `[vendor]`;[35] context files add 20–23% cost `[independent]`[3] | Defer tool schemas; gotchas-only files |
| **Clash** | Contradictions resolved "arbitrarily" `[vendor]`[2] | One statement per rule per layer; audits |

Successful bug-fix trajectories "typically remain under 20k-30k tokens" in one study on non-Claude models `[independent]`.[36] Claude Code on a 1M-window model auto-compacts at about 967K by default, deep into the range where GraphWalks falls `[Claude Code]`.[37]

### 1.4 Prompt caching

A cache read costs 0.1x base input by default and 0.05x on Opus 5.5 and Sonnet 5.5 (verified today); the default lifetime is 5 minutes and a 1-hour write costs 2x `[vendor]`.[21]
The match is an exact prefix, which gives four layout rules: stable content first; append-only history with no volatile values such as timestamps; a stable tool list (mask or defer, don't remove); and model, effort or tool changes only at natural breaks `[vendor]` `[practitioner]`.[21][38][22]

The primer researcher's worked example (synthesis, assumed token counts) puts a 40-turn Opus 5.5 task at $12.40 uncached, of which $11.20 is input, matching Anthropic's own pricing of the same scenario `[vendor]`, and $2.34 with a warm cache.[39] A cached 5K-token `CLAUDE.md` then costs about $0.06 per task: **short always-loaded files are about behaviour and cache invalidation, not dollars.** `[Claude Code]` reads `CLAUDE.md` once per session, so edits apply only after `/clear`, `/compact` or a restart.[22]

### 1.5 Compaction and context editing

**Compaction is lossy in a predictable direction: it keeps facts and drops rules stated only in conversation.** `[Claude Code]` clears old tool output first, then summarises.[37] What survives (verified today):[23]

| Survives | Lost, or reloaded only on demand |
|---|---|
| System prompt; project-root `CLAUDE.md` and unscoped rules (re-read from disk); auto memory; plan-mode plan; fresh git status; up to five recent files; invoked skills (5K tokens each, 25K total) | `paths:` rules and nested `CLAUDE.md` (until a matching file is touched); the skill list; hook-added context; anything said only in conversation |

At the API, server-side compaction (beta, default trigger 150K) is now "the primary strategy", and context editing clears old tool results by rule (default 100K, keep the last three) `[vendor]`.[40][20][41]
`[Hermes]` compresses at 50% of the window; its first phase replaces old tool results over 200 characters with a placeholder and always keeps the first exchange (verified today).[42]

What is lost:
- **Session constraints.** Compactors retained 17% of injected constraints on average; a constraint-aware extractor lifted that above 90% `[independent]` (single source).[6] Policy violations rose from 0% to 30% after compaction (59% for some models), and "constraint pinning" restored 0% `[independent]` (single source).[43]
- **The file trail.** It scored lowest of all dimensions in Factory's probe study `[vendor]` (a competitor's evaluation).[44]
- Clearing is the cheap option: on SWE-bench Verified, observation masking matched LLM summarisation and both roughly halved cost (Qwen3 and Gemini, not Claude) `[independent]`.[45][46]

**Decision rule** (primer researcher's synthesis, untested): reset when the next task is unrelated; clear tool results first when context is mostly old output; write plan and decisions to a file, then `/compact` with a focus, while the cache is warm; reset with a structured handoff after two failed corrections or premature wrap-up; offload big reads to a subagent; and keep must-survive rules in the root file or a hook, never in conversation.

### 1.6 Pattern families

| Pattern | Coding-agent use | Fits | Fails by |
|---|---|---|---|
| **Write** state outside the window | Progress file, feature list, card summary[7] | Multi-session, multi-agent | Stale notes poison later sessions |
| **Select** just in time | grep/glob, skills on invocation, deferred schemas, path rules[15][47] | Large repos, many tools | Missed retrieval; mis-triggered skills |
| **Compress** | `/compact`, context editing, Hermes pruning | One long task near a limit | Drops constraints; breaks cache |
| **Isolate** in separate windows | Read-only explorer; fresh-context reviewer[48][49] | Search, review, big reads | ~15x tokens `[vendor]`;[48] parallel writers conflict |
| **Cache-friendly layout**, **recitation** | Stable prefix; plan rewritten at the end of context `[practitioner]`[38] | Any long loop | A wrong plan is re-read every turn |

### 1.7 Where practitioners disagree

| Question | Position A | Position B | What the evidence supports |
|---|---|---|---|
| Single or multi-agent? | Cognition 2025: don't; share full traces `[vendor]`[50] | Anthropic 2025: lead plus subagents beat single-agent Opus 4 by 90.2% on research, at ~15x tokens `[vendor]`[48] | Cognition 2026: works when writes stay single-threaded.[49] The dispute is about parallel writers; measured evidence is in the earlier brief[1] |
| Long context or retrieval? | Opus 5.5 cache reads 20x cheaper than input; 76% on 8-needle MRCR at 1M (Opus 4.6) `[vendor]`[21][51] | Reasoning still falls with length; agents using the file system beat long-context and RAG by 17.3% `[independent]`[28][52] | Offload to files and retrieve; grep vs index is open (4.3) |
| Compact or reset? | Anthropic 2026: Opus 4.5 needed no resets `[vendor]`[34] | Claude Code docs: clear after two failed corrections; summaries drop constraints[32][6] | Model-dependent; no 5-series data |
| Examples or judgement? | Anthropic 2025: diverse canonical examples `[vendor]`[15] | Anthropic 2026: for Claude 5, "giving examples actually constrains them" `[vendor]`[27] | Converging on short, specific, non-inferable; no published ablations |
| Keep errors in context? | Manus: yes, so the model updates `[practitioner]`[38] | Models don't recover from early wrong turns `[independent]`[31] | Keep a tool error inside one loop; reset after repeated corrections |

---

## 2. Memory and state across sessions and agents

**Put each kind of memory in the store whose writer, reviewer and load mode match it; resume long work from files and git; hand off with short prose plus a typed block; and treat anything an agent writes about itself as a low-trust inbox that a human promotes.** Neither Claude Code's nor Hermes's built-in memory is a squad-wide store, and nothing in the evidence beats plain reviewed files for standards or task state.

### 2.1 Kinds of memory and where each lives

Five properties decide the home: who writes and who reads it; how long it stays true; how it is versioned and reviewed; its scope; and whether it must load every time or on demand.

| Kind | Home at work (Claude Code) | Home in Hermes | Writer → reader; review | Load | Evidence |
|---|---|---|---|---|---|
| **Standards** | Repo `AGENTS.md` imported by `CLAUDE.md`; `.claude/rules/` with `paths:`; org layer in managed policy or a plugin; procedures as skills; "never" rules as hooks | Repo `AGENTS.md` (one project file loads); skills in a shared git directory; `SOUL.md` for role only | Humans → all agents; git and PR | Root always; rest on demand | Anthropic: "who writes it: you", under 200 lines `[vendor]`;[2] files are followed, so every line costs steps `[independent]`[3] |
| **Project knowledge** | `docs/`, ADRs, contracts; only non-derivable gotchas in `AGENTS.md` | Same; `MEMORY.md` for machine facts only | Humans and agents via PR; verify at use | Pointers always | Overviews did not help `[independent]`;[3] GitHub re-checks stored facts against the branch `[vendor]`[12] |
| **Task state** | Tracker issue plus committed `PROGRESS.md` and acceptance list on the branch | Kanban card (body, comments, summary, metadata, parents) plus a worktree progress file for multi-run cards | Working agent → next session, agent, reviewer; git and immutable runs | Read at start, never always-loaded | Anthropic's long-running harness `[vendor]`[7] |
| **Learned lessons** | Inbox: auto memory or `project`-scope subagent memory; promote by PR | Inbox: `MEMORY.md` and background review with write approval on; promote by card | Agent proposes → human approves; inbox entries expire | Inbox small | Self-authored skills underperformed curated ones;[10] verified, itemised memory helped[12][11] |

Two points behind the matrix. **Built-in memory is not a squad store:** `[Claude Code]` auto memory is machine-local, and the only built-in memory that travels through git is a subagent's `project`-scope memory `[vendor]`;[2][53]
`[Hermes]` memory is per profile, and the docs warn "Don't point two agent processes at the same Hermes home directory" (verified today).[25]
The squad channel in Hermes is the Kanban card.[54]
**Skills hold procedures, not incident logs:** Hermes's skill guidance asks for a generalisable rule with a clause of why `[Hermes]`.[55]

A vector or graph memory service should not be the primary home for anything in a repo-centred squad. On the one coding benchmark where later tasks need earlier evidence, a plain verbatim event log scored 82/180, hosted Mem0 97/180 and no memory 21/180, and the memory-versus-memory comparison was nonconfirmatory `[independent]` (single source).[56]

### 2.2 Long, multi-session work

**Resume from artefacts, not from the transcript.** Anthropic's harness has an initialiser write a feature list with every item "failing", a progress file and a first commit; each later session reads the progress file and `git log`, runs a smoke test, works on one feature and ends with a commit and a progress update (verified today) `[vendor]`.[7] The failure it targets "happens even with compaction".[7]

- **Resets depend on the model.** Sonnet 4.5 needed them; with Opus 4.5 Anthropic "was able to drop context resets from this harness entirely" `[vendor]`.[34] Nothing is published for the 5-series.
- **Anthropic's 2026 demo** packages a hook-enforced default-FAIL contract, a fresh-context evaluator with no write tools, and `PROGRESS.md` plus a `Stop` hook that commits stragglers; it calls the handoff "the layer most sensitive to model capability" `[vendor]`.[57]
- **Split state by tense:** a forward worklist that the next session must read, history that does not load, and a backlog `[practitioner]`.[58] A months-long N=1 report adds decision and dead-end stores; only 59 of 154 proposed decisions survived triage `[independent]` (single source).[59]
- **Don't rely on built-in task lists or transcripts.** Claude Code's Task tools are off by default on newer models, and transcripts are deleted after 30 days `[Claude Code]`.[60][53] `[Hermes]` starts a fresh worker per run; retries see prior attempts, and children receive parent summaries and metadata verbatim.[54]

**Resume protocol** (memory researcher's synthesis):
1. **Initialise once:** goal and done-when, an acceptance list all failing, an init script, the progress file; commit.[7]
2. **Read first, every session:** progress file, `git log -10`, `git status`, init script, smoke test. A Claude Code `SessionStart` hook can print the progress file; in Hermes `kanban_show()` is the read step.[61][54]
3. **Reconcile before trusting:** check recorded SHAs and "done" items; fix a red smoke test first.[59]
4. **One item under "Now"** per session.[7]
5. **Record as you go:** decisions with why, dead ends with why, open questions with an owner; commit at checkpoints.[57]
6. **Done means evidence:** flip an item only with a command and result at a SHA, checked by a hook or a fresh-context evaluator.[57]
7. **Close forward-only,** and emit the handoff block if another agent continues.[58]

| Situation | Choose |
|---|---|
| Same task and sitting, warm cache | Resume (`[Claude Code]` a session idle over an hour above 100K tokens has an expired cache)[62] |
| Mid-task, context filling, no failed-approach clutter | Compact with a focus[32] |
| Task boundary, second failed correction, long gap, different agent or model | Fresh session plus progress file[32][34] |
| Try an alternative | Fork or branch; use git, because rewind does not restore Bash or subagent edits[63] |
| Hermes retry or follow-up | Fresh worker by design[54] |

**Template: progress file** (refined from the memory findings).

```markdown
# PROGRESS: <task id> | owner: <agent/profile> | branch: <branch>
Updated: <ISO time> @ <sha> | tree: clean | uncommitted: <files>

## Goal and done-when (change only with human OK)
- <one line> | done when: `dotnet test` green and `oasdiff breaking` empty

## Binding constraints (verbatim, with source)
- "No schema change without a DBA ADR" (AGENTS.md#data)

## Acceptance list (all start failing; flip only with evidence)
| id | behaviour | status | evidence (cmd -> result @sha) |
| A1 | 429 past 100 req/min per user | failing | |

## Now (one item)
## Next (ordered, max 5)
## Decisions in force (one clause of why; ADR link if lasting)
## Dead ends (do not retry; why)
## Open questions (owner; what it blocks)

## Resume checklist
1. Read this file, `git log -10`, `git status`
2. Run `scripts/dev-up.sh` and the smoke test; if red, fix first
3. Take the single item under Now; commit at each checkpoint
Rule: no dates, session numbers or "done/fixed" verbs in Now/Next (that is history).
```

### 2.3 Handoffs between agents

**A handoff should be short prose for the reasoning plus a typed block for the few items summaries demonstrably drop, with pointers rather than copies and a mechanical check that the keys exist.**

**Contents:**
- goal and done-when as the sender understood it;
- decisions, including implicit ones, each with why (Cognition: actions carry implicit decisions `[vendor]`);[50]
- binding constraints verbatim, with authority;
- branch, head SHA and changed files, and verification as command, result and SHA;[7]
- failed attempts with why;[38][59]
- unverified claims, and open questions with an owner (failing to ask appeared in 11.65% of annotated multi-agent traces `[independent]`);[64]
- pointers, not copies, to avoid the "game of telephone" `[vendor]`.[48]

Hermes's suggested metadata keys are "a convention, not a schema requirement" (verified today) and omit decisions, constraints and unverified claims `[Hermes]`.[54]

**Structured or prose: the evidence side by side**

| Favours prose or flexibility | Favours structure for some items |
|---|---|
| Format restrictions degrade reasoning, more as they tighten (applies to producing an answer, not a record written afterwards) `[independent]`[65] | Summaries keep facts but weaken the rules governing them; compression deactivated constraints 100% of the time with 54.2% forbidden actions, and four restored state fields gave 0% (verified today) `[independent]` (single source each; synthetic)[66][8] |
| Graph-only delegation lost 14.6 points on AppWorld; a router choosing graph or prose per delegation gained 12.7 points `[independent]` (single source)[67] | Artifact-anchored claims beat prose notes in 7 of 7 repositories for a smaller model `[independent]` (single source)[68] |
| A strong relay was nearly lossless in every format; injected errors persisted 83–100% in every format: structure is "a faithful, error-localizing channel, not an error-correcting code" `[independent]` (single source)[69] | |

The evidence supports neither JSON-only handoffs nor free prose for constraints. Use prose for reasoning, typed fields for load-bearing items and pointers for bulk. `[Hermes]` `delegate_task` takes an `output_schema` with one correction turn; Kanban metadata is free-form.[70] `[Claude Code]` a `SubagentStop` hook can block a finish and say why.[71]

**How much to pass: Cognition and Anthropic side by side**

| Cognition `[vendor]` | Anthropic `[vendor]` |
|---|---|
| 2025: "Share context, and share full agent traces, not just individual messages".[50] 2026: writes single-threaded; a clean-context reviewer ("do not share any context beforehand") finds about 2 bugs per PR, 58% severe; a full-context fork only for a consulting model[49] | Subagents store work externally and "pass lightweight references back"; split by context boundary, not job title; verification needs only the artefact and criteria; orchestrators lose details that get "summarized away"[48][72][73] |

Both rest on production experience without a controlled comparison. **Working rule** (memory researcher's inference, which I adopt): references plus a condensed summary by default; a fork or full trace only to a receiver that will make decisions interacting with the sender's implicit choices; never the full trace to a verifier.

**What summarising loses, and the fix**

| Loss | Fix |
|---|---|
| Failed attempts[38][59] | Required `tried_and_failed`; `[Hermes]` retries see prior attempts[54] |
| Uncertainty[8] | Required `unverified` list |
| Implicit decisions[50] | `decisions` with why; lasting ones become ADRs |
| Binding constraints[66] | Verbatim field; hard ones also in a hook or test |
| Provenance[68] | Command, result and SHA; file and line for code facts |
| Working-tree state[7] | Commit at checkpoints; state SHA and dirty or clean |

MAST's frequencies across 200+ traces from seven frameworks (not Claude coding squads) also include task derailment 7.15% and reasoning-action mismatch 13.98% `[independent]`,[64] and architectures without a central verifier propagate errors more,[74] which argues for one accountable verifier at each handoff.

**Template: handoff block** (in `kanban_complete`/`kanban_request_review` metadata with a prose `summary`, or at the end of a Claude Code subagent's final message; checked by a hook; required keys may be empty but must be present).

```yaml
status: done | partial | blocked
goal: "<one line, as the sender understood it>"
branch: feat/PAY-1234-limiter
head_sha: 3f2a9c1
tree: clean
changed_files: [src/Limiter.cs, tests/LimiterTests.cs]
decisions:            # including implicit ones, each with why
  - "Token bucket keyed on user id, IP fallback: spec silent on anonymous traffic"
constraints_binding:  # verbatim, with authority and what to do if violated
  - {rule: "No schema change without a DBA ADR", authority: "AGENTS.md#data", if_violated: block}
verification:
  - {cmd: "dotnet build -warnaserror && dotnet test", result: "148 passed, 0 failed", at: 3f2a9c1}
contract_version: "Orders.Client 2.3.0-pre.4 | none"   # cross-repo producers only
tried_and_failed:
  - {attempt: "Sliding window in Redis", why_dropped: "no Redis in CI"}
unverified: ["Behaviour under clock skew not tested"]
open_questions: [{q: "Is the 429 body fixed by the gateway?", owner: human, blocks: merge}]
pointers: {progress: docs/progress/PAY-1234.md, log: artifacts/test.log, adr: docs/adr/0042.md}
next: "Reviewer: run scripts/loadtest.sh; do not re-derive the design"
```

### 2.4 Keeping memory correct

**Memory helps when it carries evidence the agent cannot derive from code, is itemised so edits stay local, and is verified at use. It does nothing or harm when it is a generic overview, a model-rewritten blob or unfiltered experience.**

| Finding | Label |
|---|---|
| Context files: no significant success change; developer files +2.4% (p=21%); +20–23% cost; instructions "well followed"; helped every agent but Claude Code (ETH v3, verified today)[3] | `[independent]` |
| Curated skills: 33.9% → 50.5% pass rate over 18 configurations; "Self-generated Skills do not substitute for curated ones" (verified today); self-authored skills 8.1–11.5 points below none on three configurations (SkillsBench)[10] | `[independent]` (single source for the last figure) |
| Itemised bullets merged by deterministic logic beat baselines by 10.6%; a full LLM rewrite collapsed 18,282 tokens to 122 and accuracy fell below baseline (ACE)[11] | `[independent]` |
| Copilot memories with code citations, verified against the branch before use: merge rate 90% vs 83%; seeded adversarial memories caught (verified today)[12] | `[vendor]` (single source) |
| Agents adopt conflicting memory at the first decision even when wrong, and stronger agents lose more; errors in stored experience propagate[75][76] | `[independent]` (single source for the first) |

| Failure | Detect | Curate | Tool support |
|---|---|---|---|
| Staleness | Re-check cited code at use; idle counters | Verify at read; derive rather than store; expire unused entries[12] | `[Claude Code]` `modified` timestamps on memory files;[2] `[Hermes]` curator archives idle agent-created skills; no TTL for `MEMORY.md`[77][25] |
| Conflicts | Two answers to one read | One writer per file; precedence: running code > this session > notes > training data[59] | `[Hermes]` rejects exact duplicates only[25] |
| Drift of self-written skills | Patch counts; size growth | Itemised deltas, never whole rewrites; pin what must not move[11] | `[Hermes]` curator ledger with hashes and rollback[77] |
| Bloat | Cap warnings; cost per session | Hard caps; prune lines whose removal causes no mistake | `[Hermes]` 2,200/1,375 chars;[25] `[Claude Code]` 200 lines or 25KB index[2] |
| Poisoning | Scan at write; review staged writes | Stage writes for approval | `[Hermes]` memory scanned for injection and invisible Unicode;[25] see 5.2 |

**Who curates, in three tiers:** deterministic hygiene, automated (caps, expiry, lint; the Hermes curator's prune pass makes no LLM call and never deletes);[77]
LLM-proposed, human-approved (`[Hermes]` `skills.write_approval` and `memory.write_approval` both default to false, verified today; set true, writes wait under `~/.hermes/pending/`;[55][25]
`[Claude Code]` documents no approval gate for auto memory, so the reviewable route is committed `project` memory);[2][53] and human-owned shared files via PR. Expect to reject most proposals: about 25–38% survived triage in the N=1 report, "the curation working" `[independent]` (single source).[59]

**Curator defaults are version-dependent (disputed today).** The installed v0.21.6+666 sets stale at 14 days and archive at 30, for agent-created skills only;[78][79] the live docs already say 30 and 90 with `prune_builtins: true`.[77] The researchers' figures are right for your machine today.

**Tests for memory** (no standard exists; designs to borrow):
- paired runs with and without a memory or skill;[10]
- hidden-oracle tasks that need earlier-session evidence;[56]
- a CI check that every cited path still exists;[12]
- later task outcomes as labels for stored experience.[76]

### 2.5 Concrete options

| | Use | Avoid or treat as experimental |
|---|---|---|
| `[Claude Code]` | `AGENTS.md` imported by `CLAUDE.md` (native read only without `CLAUDE.md`, v2.1.277+; verified today);[2] `paths:` rules; `project`-scope subagent memory;[53] `SessionStart` to load progress and re-inject after compaction; `Stop`/`SubagentStop` to gate and check handoff keys;[71][61] `/goal` with the acceptance list;[80] memory tool plus context editing for custom SDK squads[81][41] | Auto memory as a squad store (machine-local); Task tools on new models; agent teams (experimental)[82][60] |
| `[Hermes]` | One canonical `AGENTS.md`;[24] Kanban card plus metadata as the state channel;[54] `delegate_task` with `output_schema`;[70] write approval on; shared skills via `external_dirs`;[55] `session_search` for history;[83] `pre_tool_call` gates[84] | `MEMORY.md` beyond machine facts; external memory providers until files prove insufficient[85] |
| Tool-neutral | **Git plus Markdown** (progress file, acceptance list, ADRs): reviewable, portable, no service `[vendor]` `[practitioner]`;[7][58] **Copilot-style cited memory** (store with citations, verify at read, expire) as the idea to copy[12] | Mem0, Zep/Graphiti, Letta and the MCP memory server: conversational benchmarks only; no evidence they beat a verbatim log for code `[vendor]`[86][87][88] |

None beats files for task state or standards. For squad-wide claims with real concurrency, a dependency-aware queue (Kanban, or Beads with vendor docs only) does something Markdown cannot.[54][89]

---

## 3. Cross-repo and cross-domain changes that meet your standards

**Give each agent its own repo's short instruction file plus a curated packet about the other repos (affected-repo list, contract diff, call sites); run cross-repo changes contract-first with one writer per repo; deliver standards in thin layers from one canonical file; and enforce everything checkable with deterministic gates.** Context alone is followed only part of the time.

### 3.1 Context about other repos without flooding the agent

**Curated and structured beats complete.** On 95 cross-repo dependency updates, raw upstream evidence lowered agent pass rates by 7–23 points, while filtered changes, located usage sites and a hint per breaking-change type raised them `[independent]` (single source).[9] Spotify's background agent gets no search or documentation tools; context is condensed into a versioned prompt `[practitioner]`.[90]

| Mechanism | Verdict |
|---|---|
| **Contract diffs** (OpenAPI, protobuf, `PublicAPI.Shipped.txt`) | Primary channel. Small, machine-checkable, and cannot drift if `oasdiff`, `buf breaking` or `PublicApiAnalyzers` run in CI[91][92][93] |
| **Pre-computed blast radius** | Compute the consumer list from a catalogue or code search, as Spotify does `[practitioner]`[94] |
| **Code search over MCP** (Sourcegraph, GitHub) | For interactive work; small standing cost with tool search; index lag unmeasured `[vendor]`[95][96] |
| **ADRs** | Intent the code doesn't show; load on demand. Prose overviews in context files did not help `[independent]`[3] |
| **Repo maps, generated wikis** | No independent benchmark for cross-repo work[97][98] |
| **Multi-root (`--add-dir`)** | `[Claude Code]` the added repo's `CLAUDE.md` loads only with an env flag, and its `AGENTS.md` not at all[2] |

Monorepo or polyrepo: a monorepo shows one agent every consumer and allows atomic PRs; a polyrepo needs ordered PRs, published artefacts and backward compatibility.[99] Nx's "4x faster" is its own demo `[vendor]` (single source),[99] and there is no controlled comparison, so **don't restructure repos for agents**: standardise per-repo build, test and format, publish contracts, and let a catalogue or meta-repo stand in for the monorepo's read advantage `[practitioner]`.[100]

### 3.2 Orchestrating a change across several repos

1. **Classify it.** Strong evidence exists only for *homogeneous fan-out*, the same transform across many repos (Spotify, Google, Airbnb `[practitioner]`).[101][102][103]
   For *producer→consumer* changes the best configuration solved 51.2% of 203 hidden-breakage dependency upgrades `[independent]` (single source).[104]
   Add human checkpoints for the second kind.
2. **Decompose by context boundary, not job title** `[vendor]`.[72] Cognition's manager-and-children pattern needed "more context engineering than we expected" `[vendor]`.[49]
3. **Order expand → migrate → contract.**[105] A producer card adds the new contract beside the old and publishes a pre-release; one consumer card per repo pins that artefact and ends green; a final contract card removes the old shape after every consumer merges and `can-i-deploy` passes.[106] The producer's handoff carries the version string and changed symbols.
4. **Topology: one writer per repo under a coordinating lead** for independent repos, or one session across a few tightly coupled ones (Claude Code's docs suggest the latter for a shared type and its call sites `[vendor]`).[96] Parallel peer writers are not recommended.[1] Discoveries don't propagate between per-repo agents by default, which is why the contract and the handoff matter.[49]
5. **Make each repo self-verifying first.** Spotify's agent calls one verify tool and a `Stop` hook runs it before a PR opens; an LLM judge that sees only the diff and prompt vetoes about a quarter of sessions `[practitioner]` (single source).[107]
6. **Check consistency deterministically:** breaking-change diffs, consumer-driven contract tests (`pact-net`, `can-i-deploy`), and a CI job per consumer pinned to the pre-release.[108][109]
   A cross-repo reviewer gets a curated packet: the best review agent caught 71.9% of human-verified bugs in its top five comments `[independent]` (single source),[110] while on diff-only input eight models found 15–31% of human-flagged issues and more context made them worse `[independent]` (single source).[111]

### 3.3 Delivering standards in layers

| Layer | `[Claude Code]` | `[Hermes]` | Loads | Budget |
|---|---|---|---|---|
| **Global** | `~/.claude/CLAUDE.md`, rules, skills | Profile `SOUL.md`, profile skills | Every session | Tens of lines |
| **Org** | Managed-policy `CLAUDE.md` (cannot be excluded); managed settings; plugin marketplace[2][112] | Profile distributions; shared `skills.external_dirs`; managed scope `/etc/hermes`[113][55][114] | Every session | Shortest; procedures in skills, rules in CI |
| **Repo** | `CLAUDE.md`, or `AGENTS.md` without one | `.hermes.md` → `AGENTS.override.md` → `AGENTS.md` chain → `CLAUDE.md` → `.cursorrules`; one wins[24][115] | Session start | Under 200 lines; Hermes head/tail-truncates over a character cap[24] |
| **Path** | `.claude/rules/` with `paths:`; nested `CLAUDE.md` | Nested `AGENTS.md` injected into tool results; no glob-scoped rules found[24] | First matching file | A topic per file |
| **Task** | Skills, slash commands, `SessionStart` hooks, plan files[116] | Card body; per-card skills; `pre_llm_call` injection[117][84] | On dispatch | End state, preconditions, when not to act `[practitioner]`[90] |

Precedence differs by tool: the agents.md spec says the closest file wins, Claude Code concatenates root-down and resolves contradictions "arbitrarily", and Hermes merges the chain with deeper files later `[vendor]`.[118][2][24] Write layers that never contradict.

**Instruction budgets: the evidence side by side**

| Says length or volume hurts | Says no detectable effect |
|---|---|
| Anthropic: "Longer files consume more context and reduce adherence" (verified today) `[vendor]`[2] | 1,650 Claude Code sessions: 25 to 500 lines gave 60.0–67.7% compliance, no significant effect (p=0.16), and position or conflicts showed none either (verified today) `[independent]` (single source)[4] |
| IFScale: best model 68% at 500 simultaneous instructions; Claude Sonnet 4 42.9% (keyword task, 2025 models) `[independent]`[119] | Pass rates stable from 0 to 50 rules on SWE-bench Verified `[independent]` (single source)[120] |

My reading: treat 200 lines as a cost, conflict and maintenance budget, not an adherence cliff. **Long sessions matter more than long files:** compliance fell about 5.6% in odds per function generated within a session `[independent]` (single source).[4] And agents "almost never proactively retrieve the contribution rules", so a rule must be loaded or injected, not merely available `[independent]` (single source).[121]

**One canonical source across tools** (synthesis from verified mechanics). Keep `AGENTS.md` as the single hand-written file and make `CLAUDE.md` contain `@AGENTS.md` plus Claude-only lines. Claude Code never reads an imported `AGENTS.md` twice, and Hermes reads `AGENTS.md` and ignores `CLAUDE.md`, so shared content cannot diverge (verified today).[2][115]
Traps: a lone `CLAUDE.local.md` stops Claude Code reading `AGENTS.md`, and a Hermes `.hermes.md` or `AGENTS.override.md` silently replaces it.[2][24]

### 3.4 Compliance: what context achieves and what needs enforcement

Claude Code's docs call memory files "context, not enforced configuration" and point to a `PreToolUse` hook to block an action regardless of what Claude decides (verified today) `[vendor]`.[2]

| Study | Result | Flag |
|---|---|---|
| McMillan: Claude Code, Sonnet 4.6, trivial annotation rule, 1,650 sessions[4] | 0/524 without the file; 60.0–67.7% with it | `[independent]` (single source); real rules likely lower |
| ContextCov: SWE-bench Lite constraints from instruction files[5] | 88.3% with executable guardrails; 67.0% prompt-only; 50.3% LLM reflection | `[independent]` (single source, Python) |
| SWE-Gate: 303 Python repairs, constraint stated in the prompt[122] | 221 of 644 test-passing repairs violated it | `[independent]` (single source, no Claude) |
| Spotify LLM judge[107] | Vetoes ~25%; agent recovers about half the time | `[practitioner]` (single source) |

| Standard | Primary mechanism (.NET) |
|---|---|
| Formatting, naming | `.editorconfig` severities, `EnforceCodeStyleInBuild=true`, `dotnet format --verify-no-changes` in a hook and CI[123][124] |
| Quality, nullable, warnings | `AnalysisLevel`, `TreatWarningsAsErrors`[125] |
| Build and tests pass | `Stop`/`SubagentStop` hook `[Claude Code]`; `pre_tool_call` on the completion tool `[Hermes]`; required checks |
| Architecture and layering | NetArchTest or ArchUnitNET in CI[126][127] |
| Contract stability | `PublicApiAnalyzers`, `oasdiff`, `buf`, Pact `can-i-deploy` in CI |
| Forbidden commands ("never push") | `PreToolUse` deny `[Claude Code]`; `pre_tool_call` block with `fail_closed` `[Hermes]`; branch protection |
| Judgement (error semantics, idempotence) | Context plus examples, a clean-context reviewer, tests encoding the examples |

Three conclusions: convert every "must" to something executable; tests passing is not compliance (one in three test-passing repairs broke a stated constraint);[122] and never make a reviewer agent the primary gate, because recall runs from 72% down to 15–31%.[110][111]

**Hermes hooks, settled** (the earlier brief left this open).[1]
A `pre_tool_call` shell hook under `hooks:` in a profile's `config.yaml` can block (exit 2) or fail closed, and Kanban workers register these hooks because they are spawned with `--accept-hooks` (verified in docs and source).[84][128][117]
Gateway hooks in `hooks/` never run in a worker; `pre_verify` can send the agent back a bounded number of times; `subagent_stop` and the Kanban lifecycle hooks only observe.[84]
Gating a Kanban completion this way is inferred from source and untested on a live worker.[129]

**Template: AGENTS.md skeleton** (`CLAUDE.md` = `@AGENTS.md` plus Claude-only lines).

```markdown
# <repo>: <what it is, who consumes it> · owner @org/<team> · last verified <date>

## Commands the agent cannot guess (CI runs these nightly)
- Build: `dotnet build -warnaserror`   Test: `dotnet test --no-build`
- Format: `dotnet format --verify-no-changes`   Architecture: `dotnet test tests/Architecture.Tests`

## Rules that bite (negative constraints, each with a reason)
- Never edit a published contract in place: expand, migrate, then remove in a later card.
- No `DateTime.Now`; inject `TimeProvider` (tests freeze time).
- Don't touch `tests/Architecture.Tests` or `.editorconfig` without human sign-off.

## Contracts
- Owns `openapi/orders.v1.yaml`, `src/Orders.Client/PublicAPI.Shipped.txt`
- Consumes `Billing.Client` (NuGet), pinned in `Directory.Packages.props`

## Gotchas
- Integration tests need Docker: `--filter Category!=Integration` to skip.

## Where to look (read only when the task matches)
| Task involves | Read |
| Endpoints or events | docs/contracts/README.md |
| Why a design is so | docs/decisions/ (accepted ADRs bind; superseded don't) |

## Done means
- Commands above green; results pasted into the PR or card handoff.
- No roadmap, status or history here: that lives on the board. Keep under ~150 lines.
```

**Template: Claude Code `Stop`/`SubagentStop` gate** (from the cross-repo findings; exercised there only with a stubbed `dotnet`).

```bash
#!/usr/bin/env bash
# .claude/hooks/dotnet-gate.sh — register under Stop and SubagentStop in settings.json
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
out=$(dotnet build -warnaserror --nologo -v q 2>&1 \
   && dotnet format --verify-no-changes --no-restore -v q 2>&1 \
   && dotnet test tests/Architecture.Tests --no-build --nologo -v q 2>&1)
if [ $? -ne 0 ]; then
  { echo "Quality gate failed (build -warnaserror / format / architecture tests). Fix, then finish:"
    echo "$out" | tail -n 40; } >&2
  exit 2   # Stop/SubagentStop: exit 2 = keep working; stderr goes back to Claude
fi
exit 0
```

**Template: Hermes handoff gate** (engineer profile; matcher set to the engineer's actual terminal tool, `kanban_request_review`; untested on a live worker).

```bash
#!/usr/bin/env bash
# ~/.hermes/profiles/engineer/agent-hooks/handoff-gate.sh
# config.yaml:
#   hooks:
#     pre_tool_call:
#       - {matcher: "kanban_request_review", command: "<path>/handoff-gate.sh", timeout: 10, fail_closed: true}
#       - {matcher: "terminal", command: "<path>/no-push.sh", timeout: 5, fail_closed: true}
meta=$(jq -c '.tool_input.metadata // {}')
need='.changed_files and .tests_run and .head_sha and (.decisions|type=="array")
      and (.constraints_binding|type=="array") and (.unverified|type=="array")
      and (.open_questions|type=="array")'
if ! echo "$meta" | jq -e "$need" >/dev/null 2>&1; then
  echo "Handoff incomplete: metadata needs changed_files, tests_run (cmd + result), head_sha,
decisions, constraints_binding, unverified, open_questions (empty lists allowed)." >&2
  exit 2
fi
printf '{}\n'
```

---

## 4. How a business builds up its context at scale

**Build context as owned layers, not one file: a short hand-written index per repo pointing to service-owned docs, ADRs and skills; source systems left in place behind permission-aware MCP servers; learnings captured as itemised, cited candidates that an owner merges; and every change checked by owners, a review cadence, mechanical checks and a regression eval.** Split for cost, redundancy, staleness and ownership, and don't expect splitting alone to raise pass rates.

### 4.1 Why the single big file breaks

| Failure mode | Evidence |
|---|---|
| **Everything loads every time** | Context files raised inference cost by 20% and 23% on two benchmarks with no significant success gain; the cost comes from agents *obeying* them `[independent]`[130][3] |
| **Redundancy** | With other docs removed, LLM-generated files did help; overview sections did not help agents find files `[independent]`[130] |
| **Staleness and drift** | Files "evolve like configuration code through frequent, small additions" (2,303 files) `[independent]`;[131] OpenAI: a monolithic AGENTS.md "rots instantly" `[vendor]` (single source)[132] |
| **Conflicts, no owner** | Contradictions resolved "arbitrarily" `[vendor]`;[2] corrections never graduate to the shared file `[practitioner]` (single source; sells audits)[133] |
| **Instruction budget** | Contested; see the side-by-side table in 3.3[134][135] |

Context files can still pay where little is written down: LLM-generated files helped when other docs were absent,[130] and one 124-PR study found `AGENTS.md` associated with 28.64% lower median runtime at comparable completion `[independent]` (single source; efficiency, not correctness).[136]

### 4.2 Expose context where it already lives

**Leave each source in place and give agents a pointer plus a live, permission-aware way to fetch it;** a copy in a prompt is a second copy to go stale.

| Source | Expose by | Caveat |
|---|---|---|
| Code and tests | Agentic grep plus LSP, which Anthropic calls one of the highest-value investments for multi-language codebases `[vendor]`;[137] one `verify` command `[practitioner]`[90] | Fresh by construction |
| ADRs | `docs/decisions/` with status, listed from the index `[practitioner]`[138] | Agents defend obsolete accepted ADRs "tooth and nail" |
| Contracts and schemas | In repo; summaries generated into `docs/generated/` by CI `[vendor]`[132] | Never hand-copied |
| Jira, Confluence | Atlassian Rovo MCP, honouring user permissions `[vendor]`[139] | Stale pages look authoritative; external tickets are an injection path[140] |
| PR review threads | GitHub MCP, read-only toolsets `[vendor]`[141] | Mine into candidates (4.4) rather than query live |
| Slack, catalogue | Slack MCP; Backstage MCP Actions `[vendor]`[142][143] | Lowest signal; promote durable decisions to an ADR |

Five typical MCP servers can use about 55K tokens of definitions before work starts, so connect few and turn on tool search `[vendor]`.[35]

### 4.3 Structures that scale, and the evidence for each

| Structure | Evidence | Fits when |
|---|---|---|
| **Small index plus docs on demand** | Vercel: an index in `AGENTS.md` scored 100% against 53–79% for a skill left uninvoked in 56% of cases `[vendor]` (single source);[144] Anthropic and OpenAI design guidance;[145][132] lazily loaded rules kept about half the gain `[independent]` (single source)[146] | Content needed on a minority of tasks, with an owner per doc |
| **Org-owned skills and path rules** | Every substantive edit in five public skill repos went through a named human `[independent]`;[147] beneficial rules were all negative constraints `[independent]` (single source);[120] four plugins cost 7,778 tokens per request on one machine `[practitioner]` (single source)[148] | Repeatable procedures; a platform team curates |
| **Per-service context owned by its team** | `AGENTS.md` spec and CODEOWNERS `[vendor]`;[118][149] no controlled study | Many services with distinct owners |
| **Catalogue or knowledge graph** | Port: up to 80% fewer tokens on operational queries `[vendor]` (single source, headline unconfirmed);[150] a code graph traded 92% → 83% answer quality for 10x fewer tokens `[independent]` (single source)[151] | Navigation facts: owner, tier, dependencies |
| **Embeddings vs agentic search** | Cursor +12.5% `[vendor]` (single source);[152] a structural index lifted resolve 41.9% → 50.4%, not significantly above agentic grep, mainly on multi-file changes `[independent]` (single source)[153] | Very large estates, after your own eval shows a gain |

**Conflicts, side by side.**

| Question | One side | Other side | Reading |
|---|---|---|---|
| Skill or always-loaded index? | Vercel: skill unused in 56% of cases `[vendor]`[144] | Claude Code: skill fired 28/28; inline used fewer tokens `[practitioner]` (single source)[148] | Harness-specific; keep must-follow rules and the index always loaded |
| Index or agentic search? | Index vendors report gains[152][154] | Claude Code's team and Cline cite staleness and security `[vendor]`[155][156] | Live search plus LSP until your eval says otherwise |
| Expose live or bake in? | Anthropic: MCP for search and docs[137] | Spotify: condensed context in versioned prompts `[practitioner]`[90] | Bake in for repeatable migrations, expose for open-ended work |

### 4.4 Capturing knowledge as work happens

**Capture a candidate with evidence at the moment of work, gate it with a human or an outcome signal, and store it in the narrowest durable home.** The tools converge on this: Compound Engineering writes `docs/solutions/` entries only after a verified fix;[157]
CodeRabbit and Cursor Bugbot hold learned rules as candidates until approved or confirmed by signal `[vendor]`;[158][159]
Copilot Memory verifies cited facts before use and deletes unused ones after 28 days (verified today);[160]
Hermes's `skills.write_approval` gates every skill write `[Hermes]`.[55]

| Stage | What happens | Owner | Drift control |
|---|---|---|---|
| 1. Source | PR review comments and rejections, corrected sessions, incidents, eval failures | Whoever produced the signal | Linked, never "from memory" |
| 2. Candidate | One record: statement (ideally a negative constraint or exact command), why, evidence, file:line, date | Capturing agent or human | Itemised with ids, never a prose rewrite[161] |
| 3. Review | A PR into the owning repo | Service owner via CODEOWNERS | Human merge;[147] reject what code, tests or lint already cover |
| 4. Store | Standard → test, lint, hook or `AGENTS.md`; knowledge → docs or ADR; lesson → `docs/solutions/`; procedure → skill | Owning team | Narrowest home first;[157] `last_verified` |
| 5. Eval | Regression set with and without the change | Context owner | Held-out cases; read transcripts[162][13] |

Never let a model rewrite a whole context: ACE names brevity bias and context collapse as the failure modes and itemised delta updates as the fix `[independent]`.[161]

### 4.5 Keeping it true

- **Owners.** One context owner with authority over settings, permissions, marketplace and `CLAUDE.md` conventions `[vendor]`;[137] per-path owners through CODEOWNERS.[149]
- **Cadence.** Anthropic: a "meaningful configuration review every three to six months" and after major model releases `[vendor]`.[137] Suggested (synthesis): monthly candidate triage, quarterly prune, and a full regression run on each model upgrade that deletes rules written for the old model.
- **Freshness signals.** `last_verified` dates; file:line citations; `/doctor prompt-audit`, which flags old-model instructions, missing references and contradictions `[Claude Code]`;[2] reference-resolution linting `[practitioner]`;[163] a CI job that runs the commands `AGENTS.md` lists (synthesis, untested).
- **Evals.** "20-50 simple tasks drawn from real failures"; separate capability and regression suites; hold out cases; pass^k when reliability matters `[vendor]`.[13][162]
  A/B the context file with everything else fixed.[164]
  Langfuse documents CI experiments with a regression gate;[165] the wrapper that runs headless Claude Code and scores `dotnet test` is undocumented, so budget time for it.
- **Retirement.** Superseded ADRs are history only; archive skills rather than delete; remove rules written for older models.[138][137]

### 4.6 Starting path for a business with little written down

**Write by hand:** a ≤150-line `AGENTS.md` per repo (commands, non-default conventions, gotchas, done-means, where-to-look); CODEOWNERS over `AGENTS.md`, `docs/`, `.claude/` and skills; org "nevers" as negative constraints with reasons; the first 10–20 ADRs for decisions people argue about; a gotcha list from each team's last 10–20 merged PRs (untested elicitation); and a 20–50 task regression set.[32][149][138]
**Generate, after a no-context baseline eval:** module maps and API summaries into `docs/generated/` by CI, and draft ADR and gotcha candidates for humans to accept, but not prose overviews for repos that already have a README.[132][130]
**Leave in place:** Jira, Confluence, Slack, PRs, incidents, the catalogue, code and tests, referenced from the index; add an embedding index only when grep plus LSP demonstrably miss things.[153]

**Template: context index** (the where-to-look part of a service repo's `AGENTS.md`; commands, rules and done-means as in the 3.4 skeleton).

```markdown
## Where to look: read a file only when the task matches
| If the task involves | Read | Owner |
|---|---|---|
| An endpoint or event | docs/contracts/README.md (OpenAPI in /contracts) | payments-team |
| Persistence or migrations | docs/data/migrations.md | payments-team |
| Why a design is the way it is | docs/decisions/ (accepted ADRs bind) | architects |
| Owner, tier, dependencies, on-call | Backstage entity payments-api (MCP: backstage) | platform |
| Earlier tickets and rationale | Jira PAY-*, Confluence space PAY (MCP: atlassian) | payments-team |
| A problem that looks familiar | docs/solutions/ (search by symptom) | payments-team |
| Review standards | skill org-pr-review (marketplace org-standards) | dev-experience |
## Precedence
- Nearer AGENTS.md files add to this one; if they disagree, stop and ask the owner
```

---

## 5. Implementing it in a UK enterprise

**Treat the system as three zones (what agents may see, what they may do, what is kept) and make each zone's controls deterministic. Instruction files are advisory and prompt injection can only be bounded, so the real controls are managed settings, an OS sandbox, scoped credentials, required CI and a retention line for every store.** The stores that create UK GDPR risk are the ones nobody designs: transcripts, agent memory and traces.

### 5.1 Reference architecture

This is my design, assembled from sections 2–4 and the enterprise patterns in the UK findings: Claude Code's organisation setup and audit gateway, bounded write surfaces, and limited-tool background agents.[166][167][90]
Thoughtworks' split into feedforward guides and feedback sensors frames it.[168]
It has not been tested as a whole.

```
 READ PATH (what an agent sees)                      WRITE PATH (how context grows)
 ┌─────────────────────────────────────────┐   ┌──────────────────────────────────────┐
 │ Org: managed-policy CLAUDE.md, org      │   │ Signals: PR review comments, rejected │
 │ plugin (skills, hooks), managed settings│◄──│ reviews, corrected sessions, incidents│
 │ Repo: AGENTS.md index ≤150 lines        │PR │ eval failures                         │
 │       (CLAUDE.md = @AGENTS.md)          │   └──────────────────┬───────────────────┘
 │ On demand: path rules, nested AGENTS.md,│                      ▼
 │   skills, docs/, ADRs, docs/generated   │   ┌──────────────────────────────────────┐
 │ In place via scoped MCP: Jira, wiki,    │   │ Candidate inbox: itemised, cited,    │
 │   GitHub, Slack, catalogue, code search │   │ dated (write approval on)            │
 │ Task: ticket/card + PROGRESS.md +       │   └──────────────────┬───────────────────┘
 │   previous agent's handoff block        │                      ▼ PR, CODEOWNERS approve
 └───────────────────┬─────────────────────┘   ┌──────────────────────────────────────┐
                     ▼                         │ Narrowest home: test/lint > AGENTS.md │
 GATES: managed hooks → required CI (build     │ > skill > docs/ADR; eval before merge │
 -warnaserror, format, arch tests, contract    └──────────────────────────────────────┘
 diff, secret scan) → branch protection + human merge
                     ▼
 TELEMETRY: OTel metadata + Langfuse traces tagged task / ctx SHA / model → PR scores → evals
```

| Store | Work (Claude Code) | Personal (Hermes) | Owner | Versioned and reviewed | Load | Retention |
|---|---|---|---|---|---|---|
| **Org standards** | Managed-policy `CLAUDE.md`; org plugin from an allowlisted marketplace; managed settings | `SOUL.md` (role only); shared skills via `external_dirs`; `/etc/hermes` managed scope | Context owner with security | Plugin repo tags; PR by owner and security; quarterly and on model upgrade | Always (tiny) | Git |
| **Repo and path standards** | `AGENTS.md` + thin `CLAUDE.md`; `.claude/rules/` with `paths:` | `AGENTS.md`; nested `AGENTS.md` | Service team via CODEOWNERS | Git; every PR touching them; CI runs listed commands; quarterly prune | Root always; paths on touch | Git |
| **Procedures** | Skills in org or repo plugins | Skills in one shared git directory | DevEx (org), team (repo) | Git; paired eval before adoption | Description always, body on use | Git |
| **Project knowledge** | `docs/`, ADRs, contracts, `docs/generated`, `docs/solutions` | Same | Service team | Git; `last_verified`; regenerate-and-diff in CI | Via the index | Git |
| **Source systems** | Scoped, read-only MCP | Same, fewer | System owners; platform | Not copied; allowlist reviewed quarterly | On demand | Each system's policy |
| **Learned-lesson inbox** | Auto memory (inventoried, or off on shared repos); `project` subagent memory | `MEMORY.md` and background review, approval on | Proposing agent; approving human | Monthly triage; promote by PR; expire unused | Small, always | Short TTL |
| **Task state** | Issue + `PROGRESS.md` on branch + handoff block | Card + worktree progress file + completion metadata | Assignee agent; lead or human for the parent | Git; immutable runs; reviewer checks handoff | Read at start | Board policy |
| **Enforcement** | Managed hooks, permissions, sandbox; required CI; branch protection | `pre_tool_call` hooks in profile `config.yaml` | Platform and security | Settings and CI repos; quarterly allow-list review | n/a | n/a |
| **Telemetry and evals** | OTel metadata; Langfuse self-hosted in a UK region, or metadata-only to Cloud EU | Langfuse via an observer plugin | Platform; context owner owns the suite | Suite in git; run on every context change and model upgrade | n/a | Content 30–90 days; metadata longer |

Five rules hold it together: one writer per repo with a repo-scoped token; nothing becomes a standard without a human merge; every "must" has a gate; every store has an owner and a retention line; and every trace carries the task id and the context SHA.

### 5.2 Security

**What the sources say.** The NCSC says LLMs "do not enforce a security boundary between instructions and data", so rely on "deterministic (non-LLM) safeguards" `[independent]`.[169]
Adaptive attackers bypassed twelve published defences `[independent]` (single source).[170]
Never combine private data, untrusted content and an outbound channel in one session (Meta's Rule of Two allows two) `[practitioner]` `[vendor]`.[171][172]
Rules files, MCP results and repo-level hook config have all been working attack vectors `[vendor]` `[independent]`.[173][174][175]
Payloads planted in memory files attacked later sessions `[independent]` (preprint).[176]
Users accept 93% of permission prompts `[vendor]` (single source).[177]

| Threat | Claude Code (deterministic) | Hermes | Tool-neutral |
|---|---|---|---|
| Secrets or personal files read into context | Managed `permissions.deny` on `.env` and secrets, plus `sandbox.filesystem.denyRead`; deny rules alone don't stop a script[178][179] | Project `.env` read-denied for file tools; terminal deny patterns are "not a complete shell interpreter or an OS capability sandbox"[180][181] | No long-lived secrets on dev machines |
| Secrets or PII in traces, transcripts, memory | OTel content off by default; mask in the Langfuse hook; `cleanupPeriodDays`; auto memory off where unwanted[182][183][184] | `security.redact_secrets` on by default; `state.db` kept until pruned[83][181] | Mask client-side first |
| Poisoned instruction files, skills, memory | `strictPluginOnlyCustomization`, `allowManagedHooksOnly`, `allowManagedMcpServersOnly`, `strictKnownMarketplaces`[166][185] | Context files scanned for injection and invisible Unicode, "heuristics, not semantic intent detection"[180] | CODEOWNERS and required review; CI Unicode scan |
| Exfiltration | Sandbox proxy with an empty `allowedDomains`, no unsandboxed fallback, `failIfUnavailable`[179] | Docker egress isolation guide[186] | Egress allowlist at the network layer |
| Blast radius across repos | One short-lived repo-scoped credential per task; a Git tool that never pushes `[practitioner]`[90] | One board per repo; `HERMES_WRITE_SAFE_ROOT`[181] | Task-scoped tokens (OWASP ASI03)[187] |

A single agent holding tokens for many repos is a standing private-data leg of the trifecta, so keep "reads untrusted content" and "holds write credentials" in different sessions, and give coordinators read-only access to contracts (UK researcher's recommendation).[174][172]

**Audit trail.** Langfuse says its Claude Code hooks do not capture "session context files" and are "telemetry, not enforcement" (verified today) `[vendor]`.[188] The only documented way to evidence which standards loaded is the `InstructionsLoaded` hook: log path plus hash, not content `[Claude Code]`.[71] For proof of capture, Anthropic recommends a gateway with a per-request audit log.[166]

| How much to log? NCSC `[independent]` | ICO `[independent]` |
|---|---|
| Enough to spot attacks, "potentially including full input and output of the LLM, as well as tool use"[169] | Justify retention, review it, erase or anonymise; masking and observability are expected practice[189][190] |

Resolution (adopted from the UK findings): always log metadata; capture content only into a restricted, masked store with a short window, justified in the retention schedule.

**Correction to the UK findings,** which report no managed policy layer in Hermes: managed scope at `/etc/hermes` pins config keys a non-root user cannot override (verified today).[114] It is weaker than Claude Code's managed settings: pinning `hooks:` is unverified, and the pages read show no managed-only switch for hooks, plugins or MCP.

### 5.3 UK GDPR points (practical guidance, not legal advice)

| Store | Risk | Retention and erasure |
|---|---|---|
| Repo files, git history | Customer data in fixtures; names in history | Git is permanent, so prevent: PII and secret scans before merge; team aliases, not names, in instruction files |
| Agent memory, transcripts | Machine-local plaintext that may hold names and customer ids; the ICO flags inaccurate agent memory[190] | `cleanupPeriodDays`; auto memory off on shared repos; scheduled Hermes session pruning (compression "is not a privacy delete"); per-machine deletion needs an inventory[191][83] |
| Task board | Card text and pasted logs | Board policy; no documented expiry for the Hermes board |
| Vector index | Embeddings of personal data are derived personal data (OWASP 2026 #9)[192] | Source ids on chunks; delete and re-embed |
| Traces | Highest: full prompts, tool I/O, `user.email` in OTel[182][193] | Self-hosted Langfuse keeps data "indefinitely by default" unless an Enterprise retention policy is set (minimum 3 days; verified today); API deletion leaves dataset copies[194][195] |

**What the vendor processes** (as read on 12 Oct 2026, `[vendor]`). There is no training on commercial data unless you opt in. Standard retention is 30 days; zero data retention is only for qualified Claude for Enterprise accounts and does not cover MCP.[196][197]
The DPA uses SCCs plus the UK Addendum.[198]
Anthropic's own API offers only `us` or `global` inference,[199] while Bedrock London has in-region Opus 5.5 and Sonnet 5 since 30 Sep 2026 (verified today).[200]
Langfuse Cloud has no UK region, so self-host in a UK region if traces carry code.[201]
**Conflict:** the Privacy Center says API data is deleted within 30 days, and the API retention page says content "is not retained by default".[202][203]
Plan on 30 days and confirm in your contract. **Not covered:** the ICO's worker-monitoring and DPIA guidance, Anthropic's sub-processors and its UK-US transfer route.

### 5.4 Measuring whether it works, with Langfuse

**Measure outcome pairs, not tokens, by joining Langfuse sessions to git and PR data on a task id.** DORA finds AI amplifies an organisation's strengths and weaknesses, raising throughput but still raising instability, and warns that token counts invite gaming; it recommends "cost per accepted change and code rework rates" `[independent]`.[204][14]

| Metric | Definition | Source |
|---|---|---|
| Task success | Tasks (abandoned ones counted) whose PR merges, passes CI and is not reverted within 14 days; first-pass CI separately | Sessions tagged `task:`; merge, checks and reverts posted back as scores[205] |
| Standards violations caught | Review comments labelled `std:<rule-id>` per merged PR, plus gate failures at first push | Review API, check runs; cut by `ctx` |
| Review rework | Rounds requesting changes; commits after first review; fix or revert PRs within 14 days | PR timeline |
| Cost per merged change | All sessions linked to merged tasks, including abandoned ones; cache-read and cache-creation tokens shown apart | Langfuse cost tracking and Metrics API, reconciled with billing[206][207] |

Anthropic's figure of about $13 per developer per active day is a sanity baseline `[vendor]` (single source).[208] Telemetry studies disagree on size: Faros reports bugs per PR +28% and review time 5x `[vendor]` (single source); Microsoft found about 24% more merged PRs in its own rollout `[independent]` (single source).[209][210] Neither covered .NET.

**Template: trace tagging** (from the UK findings; the join was not run against a live instance).

```text
session_id = Claude Code session_id | Hermes session id      # groups turns
user_id    = hash(directory object id + salt)                # pseudonym and erasure key
tags (≤200 chars):  repo:payments-api  squad:payments  phase:p1-pilot
                    task:PAY-1234      # also branch agent/PAY-1234-…, PR title, card id
                    ctx:7f3a9c1        # git SHA of AGENTS.md + rules + skills (InstructionsLoaded log)
                    model:opus-5.5     harness:claude-code-2.1.296 | hermes-0.21.6
metadata: {"taskId":"PAY-1234","repo":"payments-api","ctxSha":"7f3a9c1","prNumber":"412"}
scores (CI posts after merge or review):
  merged BOOLEAN  ciFirstPass BOOLEAN  revertedIn14d BOOLEAN
  reviewRounds NUMERIC  standardsHits NUMERIC              # comments labelled std:<rule-id>
cost per merged change = Σ totalCost(sessions with task:X, merged) / count(merged)
retention: content 30 days; scores + metadata exported nightly without prompt text
erasure: find traces by user_id, delete via API, then delete dataset items copied from them
```

### 5.5 Phased rollout and failure modes

Phases are the UK researcher's synthesis from practitioner playbooks with commercial interests; the one independent data point is that adoption spread through peers.[211][210]

| Phase | Work | Exit |
|---|---|---|
| **P0 Groundwork** (1–2 weeks) | Managed settings (deny rules, sandbox with `failIfUnavailable`, empty network allowlist, MCP and plugin allowlists, `forceLoginOrgUUID`, no bypass mode, `cleanupPeriodDays`, pinned OTel collector); branch protection, required CI, blocking secret scan; CODEOWNERS and Unicode scan on instruction files; baselines[166][211] | Managed settings shown on every pilot machine; a seeded fake secret is masked in a test trace; agents cannot merge |
| **P1 Pilot** (2–6 weeks, 3–12 volunteers) | Real tickets on 1–3 repos; lessons land in the reviewed file the week they're learned; first 20–50 regression tasks; `ctx` tags | Instruction files stable; trace samples clean; cost per merged change measured |
| **P2 Expansion** (cohorts of 15–20) | A champion per cohort; written norms (same review gate, second person on significant changes, agent PRs labelled) | Violation and rework rates flat or better than baseline |
| **P3 Default-on, cross-repo** | Contract checks (3.2) | Change fail and rework flat or better over a quarter; injection and secret-leak drills done |
| **P4 Operate** | Quarterly allow-list and context review; evals on each model change[167] | Continuous |

**Failure modes to watch:**
- context sprawl and rule bloat (Thoughtworks Radar puts "agent instruction bloat" on Caution `[practitioner]`);[212]
- stale context steering runs (anecdotal) `[practitioner]`;[213]
- approval by reflex, and one person writing, reviewing and merging;[177]
- output outrunning review (Faros: PR size +71.8% `[vendor]`, single source);[214]
- shadow memories nobody reviewed, and tracing gaps when developers disable hooks;
- vanity metrics such as licence activity.[215]

Mitigations: named owners and eval-gated additions, `last_verified` checks, sandbox instead of prompts, PR size limits, managed hooks only, and outcome pairs instead of usage counts.

---

## 6. Applied to the Hermes squads: gap analysis

**The squad's process design already matches most of the findings: one writer per card, a fresh-context reviewer, decisions written into card bodies, producer-before-consumer ordering, human merge, and instruction-file hygiene in the SOULs. The gaps are in delivery and enforcement.** Repo standards do not reach Hermes workers' system prompts; the handoff and "never push" rules are advisory; skills drift between per-profile copies with no visible review gate; and nothing measures whether a context change helped.

Everything in 6.1 was observed read-only on 12 Oct 2026. Anything outside the read permission is a check for you in 6.5.

### 6.1 Current state

**SOULs** (`~/.hermes/profiles/<profile>/SOUL.md`)

| Profile | Lines | What it sets that matters for context |
|---|---|---|
| `lead` | 29 | Card fields **Goal, Decisions, Acceptance criteria** (with an exceptions clause) and **Verify**. Shared questions are decided before fan-out and written into every dependent card, because "a card body is all the context they get besides the repo". Cards are sized for one session. On `cross-repo`: `project` per card, one card per repo, parent links order producer before consumer. Uncheckable facts go to a fact-finding engineer card |
| `engineer` | 17 | Start from card, parent handoffs, prior attempts and comments; "Follow the repo's AGENTS.md / README conventions"; keep `AGENTS.md`/`CLAUDE.md` current in the same branch; never push, merge or force-push; hand off via `kanban_request_review` with `changed_files`, `tests_run`, `branch` and decisions |
| `reviewer` | 16 | Follow `sdlc-review`; never edit code; treat the handoff as a claim and run the tests; scrutinise instruction-file diffs and reject stale or unrequested agent-directed content |
| `pm`, `researcher`, `analyst` | 24, 24, 27 | Research flow; per-card citation ledgers |

**Kanban as the state channel.** Each run is a fresh worker; retries see prior attempts and children see parent summaries and metadata verbatim, as this run's own context showed `[Hermes]`.[54] The engineer's handoff keys cover neither binding constraints, failed attempts, unverified claims, open questions nor a head SHA, and nothing checks that any key is present.

**Repo instruction files** (`~/git/*`, top level)

| Repo | `AGENTS.md` | `CLAUDE.md` lines (size) | Hermes worker loads | Notes |
|---|---|---|---|---|
| ballistic | 6-line pointer | 104 (4.9 KB) | Pointer | No negative constraints |
| ballistic-landing | 6-line pointer | 35 (2.2 KB) | Pointer | |
| bh-app-thread-portal | 6-line pointer | 97 (5.6 KB) | Pointer | 2 commits since last update |
| claude-plugin-engineering | 3-line pointer | 15 (2.0 KB) | Pointer | Short invariants with reasons: the model to copy |
| debtor-verification-agent | 1-line pointer | 142 (9.8 KB) | Pointer | "Roadmap" section |
| email-triage-agent | none | 117 (14.9 KB) | `CLAUDE.md` | "Open decisions" section; 4 commits since |
| email-triage-jev | none | **261** (18.5 KB) | `CLAUDE.md` | "Status" and "Next steps" sections |
| eval-harness | 1-line pointer | **302** (21.8 KB) | Pointer | 12 commits since |
| innovation-lab-skills | 6-line pointer | 33 (1.9 KB) | Pointer | |
| istyar | 7-line pointer | 95 (6.4 KB) | Pointer | 4 commits since |
| katas | 6-line pointer | 123 (5.9 KB) | Pointer | Strong gotchas; long derivable structure list |
| model-harness | 1-line pointer | 173 (**44.9 KB**, ~11K tokens) | Pointer | "Roadmap status"; only repo with an ADR folder |
| plan-my-party | 5-line pointer | 90 (7.7 KB) | Pointer | 14 commits since |
| sandbox-cs | 6-line pointer | 58 (2.7 KB) | Pointer **to a file not in HEAD** | `CLAUDE.md` never committed, so worktrees lack it |
| vibes-asb-manager | 6-line pointer | 56 (2.2 KB) | Pointer | **51 commits** since last update |
| vibes-k8s-manager | 6-line pointer | 87 (4.6 KB) | Pointer | |

"Commits since" counts commits after the last one touching `CLAUDE.md`: a staleness signal, not proof. Against sections 3 and 4: 13 of 16 files list build, test or run commands and most carry real gotchas (good). All 16 have a structure or architecture section, the derivable overview the ETH study found unhelpful.[3] Four hold task state. None has a where-to-look index or a "done means" section, no repo has a nested `AGENTS.md`, and four files have no negative constraints. Three exceed the budget. Renamed unchanged, model-harness's file would be head/tail-truncated by Hermes's context-file character cap (dynamic, with a 20,000-character floor).[24]

**The inversion, verified.** Hermes loads "only ONE project context type", the first non-empty of `.hermes.md`, the `AGENTS.md` chain, `CLAUDE.md` and `.cursorrules`, so a pointer `AGENTS.md` wins (installed `agent/prompt_builder.py`).[115]
Kanban workers run with their working directory pinned to the card's workspace, so the worktree's `AGENTS.md` is the one that loads (`hermes_cli/kanban_db_dispatch.py`).[117]
Claude Code does the opposite: with both files present it reads `CLAUDE.md` and ignores `AGENTS.md` unless it is imported (verified today).[2]
Claude Code therefore gets the content and Hermes gets "please read CLAUDE.md". If a Hermes worker follows the pointer, the content arrives as a tool result: not pinned, and replaced by a placeholder once the compressor fires at 50% of the window (verified today).[42]
The engineer SOUL tells workers to follow `AGENTS.md`, so the only instruction to read the real file is the stub.

**Skills.** Each profile holds 89–90 skills, almost all bundled copies; `mlops/langfuse` exists only in the three research profiles. Identical usage timestamps across profiles, and skill-ledger paths pointing at `~/.hermes/skills/`, suggest each library was cloned from the default profile, the dev profiles first. The copies have since diverged:

| Skill | Origin | Dev profiles | Research profiles |
|---|---|---|---|
| `software-development/dotnet-prerelease-package-testing` | Agent-created on 11 Oct; not in the bundled manifest | 202 lines, 14 patches | 223 lines, 26 patches: adds throwaway-copy compile-break measurement and per-project pass counting |
| `devops/sdlc-review` | Bundled | 181 lines, unpatched | 182 lines: adds a step to scrutinise `AGENTS.md`/`CLAUDE.md`/`SOUL.md` diffs |

So the engineers who need the .NET skill hold the older copy, and the reviewer's own procedure lacks the step the research copies gained (its SOUL carries the rule instead). The .NET skill was patched 14–26 times in one day; whether through `skills.write_approval` cannot be told from the files I was allowed to read. The `logs/curator/` directories are outside the read permission; the docs defer the curator's first pass by 7 days after install.[77]

**Hooks.** Each profile's `hooks/` directory is where gateway hooks live, and those run "Gateway only", never in a Kanban worker (verified today).[84] Hooks that can gate a worker live under `hooks:` in `config.yaml`, which I could not read.

**Org standards reach Claude Code only.** `~/git/claude-plugin-engineering/CLAUDE.md` describes an `eng-standards` plugin. It injects your standards into every Claude Code session through a `SessionStart` hook, keeps the rule text only in `SKILL.md` bodies, preloads them into a reviewer subagent, gates `Stop` on a review, and adds a `-dotnet` skill only where a `.csproj` or `.sln` exists (observed). That is the org layer of 3.3 done well. Hermes workers don't run Claude Code, so unless a profile's `skills.external_dirs` or a hook points at those files, Hermes engineers never see them.

**Memory.** Capped at 2,200 and 1,375 characters per profile.[25] Memory files are outside the read permission, so whether they hold standards, task state or personal data is a check in 6.5.

### 6.2 The PM's observations, checked

| Observation | Verdict |
|---|---|
| Engineers update `AGENTS.md`/`CLAUDE.md` in the same branch; reviewers scrutinise those diffs | **Confirmed** (engineer step 3, reviewer rule 5). This matches PR-gated capture (4.4), but with no size budget or narrowest-home rule it invites "frequent, small additions"[131] |
| The lead defines Goal, Decisions, Acceptance criteria and Verify, one card per repo, producers before consumers | **Confirmed.** No Constraints or Out-of-scope field, no final contract-removal card, no rule that the producer hands over the published version |
| Many repos have both files; check divergence | **Both exist in 14 of 16; content cannot diverge because every `AGENTS.md` is a pointer, and that is the problem.** The earlier brief's "Hermes loads one file and prefers `AGENTS.md`" is confirmed in source[115][1] |
| The profiles have `hooks/` and `logs/curator`; can Hermes hooks enforce standards? | **Yes, but not from `hooks/`.** `pre_tool_call` hooks in `config.yaml` can block in workers; `hooks/` holds gateway hooks, which never run in workers (contents not read)[84][117] |

### 6.3 Where the setup falls short

| Gap | Finding it falls short of |
|---|---|
| G1. Workers' system prompts carry a pointer, not the repo's standards | Root-file pinning (1.5); one canonical file (3.3); agents rarely fetch rules themselves[121] |
| G2. Derivable overviews and task state in always-loaded files; three over budget | Overviews don't help and cost ~20% (4.1); task state belongs on the board (2.1) |
| G3. Handoffs lack constraints, dead ends, unverified claims, open questions, SHA; unchecked | Summaries drop "must"; typed fields restore it (2.3) |
| G4. "Never push or merge" and "tests pass" are advisory | Context ~60–68% vs executable 88% (3.4) |
| G5. Per-profile skill copies drift; heavy unreviewed self-patching | Self-written skills underperform; itemised, human-governed maintenance (2.4, 4.4) |
| G6. The org standards layer exists for Claude Code only | One canonical source across tools (3.3) |
| G7. Cross-repo ordering lacks the contract step and version handoff | Expand → migrate → contract (3.2) |
| G8. No regression set; traces not tagged by card or context version | Eval every context change; measure outcomes (4.5, 5.4) |
| G9. No progress-file convention for multi-run cards | Resume from files (2.2); mitigated by single-session sizing |
| G10. No retention routine for `state.db`, `kanban.db`, sessions | Every store needs a retention line (5.1) |

### 6.4 Prioritised changes

Effort is your time: S under 3 h, M 3–10 h, L over 10 h. Benefit is my estimate from the cited findings, not a measurement.

| # | Change | Label | Effort | Expected benefit | Rests on |
|---|---|---|---|---|---|
| 1 | **Invert the context files.** One `cross-repo` card per repo: move `CLAUDE.md` content into `AGENTS.md` (template 3.4) and make `CLAUDE.md` `@AGENTS.md` plus Claude-only lines; drop derivable structure lists; move roadmap, status, next-steps and open-decisions sections to cards or `docs/`; add where-to-look and done-means sections; cut eval-harness, email-triage-jev and model-harness to ≤150 lines (required for model-harness to avoid truncation); commit sandbox-cs's file; add `AGENTS.md` to the email repos; change the engineer SOUL to "`AGENTS.md` is canonical" | `[Hermes]` `[Claude Code]` | M, 6–8 h | **High.** Every Hermes card starts with the repo's commands, gotchas and done-means pinned in the system prompt; Claude Code sees the same content | G1, G2; 1.5, 3.3, 4.1 |
| 2 | **Typed handoff plus completion gate.** Lead card fields gain **Constraints** (verbatim, with source), **Out of scope / when not to act** and **Read first**; engineer metadata gains the 2.3 block; `pre_tool_call` gate on `kanban_request_review` (template 3.4), and a reviewer gate on `kanban_complete` requiring `reviewer_checks`; test on a throwaway board first | `[Hermes]` | M, 4–6 h | **High.** Constraints and dead ends survive handoffs; incomplete handoffs bounce back automatically | G3; 2.3, 3.4 |
| 3 | **Enforce "never push or merge"**: `pre_tool_call` on `terminal` in the engineer and reviewer profiles, matching `git push`, merges into main and `--force`, with `fail_closed: true` | `[Hermes]` | S, 1–2 h | **Medium-high.** A stated invariant becomes a guarantee | G4; 3.4 |
| 4 | **Gate and share skills**: `skills.write_approval` and `memory.write_approval` on in all six profiles; squad workflow skills (the fuller `sdlc-review` and `dotnet-prerelease-package-testing`, future house skills) in one git repo read through `skills.external_dirs`, read-only by file permission; remove the stale per-profile copies | `[Hermes]` | S, 2–3 h | **Medium-high.** One reviewed copy per skill; self-patching becomes proposals you approve | G5; 2.4, 4.4 |
| 5 | **Bring `eng-standards` to Hermes**: add the plugin's skill directory to the engineer and reviewer `skills.external_dirs`, or a `pre_llm_call` hook that injects the universal body on the first turn and the `-dotnet` body in .NET workspaces | `[Hermes]` | S, 2–3 h | **Medium.** One source of standards text for both tools | G6; 3.3 |
| 6 | **Instruction-file hygiene rules**: engineer SOUL caps `AGENTS.md` at ~150 lines, routes each learning to its narrowest home (test or analyser before an `AGENTS.md` line before `docs/`), bans task state and asks for negative constraints with reasons; the reviewer checks the budget and runs the listed commands | `[Hermes]`, tool-neutral | S, ~1 h | **Medium.** Stops the files regrowing after change 1 | G2; 4.1, 4.4 |
| 7 | **Contract-first cross-repo rules**: a final contract card after consumers merge; producer metadata carries `contract_version` and changed symbols; the lead's wake-up check reviews contract diff plus consumer call-site diffs; publishing repos add `PublicApiAnalyzers` or `oasdiff` to their verify commands | `[Hermes]`, tool-neutral | S for the SOUL; M per publishing repo | **Medium**, rising with cross-repo volume | G7; 3.2 |
| 8 | **.NET gates per repo**: `EnforceCodeStyleInBuild`, `TreatWarningsAsErrors`, `dotnet format --verify-no-changes`, and NetArchTest where layering matters, listed in `AGENTS.md` and run by the change-2 gate | Tool-neutral | L, 1–2 h per repo across ~10 repos | **Medium-high per repo.** Style and quality rules leave the prompt entirely | G4; 3.4 |
| 9 | **Trace with outcomes**: tag worker traces with card id, repo, `ctx` (git SHA of `AGENTS.md`) and model; post `merged`, `reviewRounds` and `ciFirstPass` after you merge (template 5.4) | `[Hermes]` | M, 6–10 h | **Medium.** Cost per merged card; whether a context change helped | G8; 5.4 |
| 10 | **Regression set**: 10–20 past cards from your busiest repos, replayed headless when `AGENTS.md`, a SOUL or a squad skill changes, comparing pass rate, review rounds and cost. Your `eval-harness` repo may be reusable; I did not assess it | Tool-neutral | L, 10–15 h | **Medium**, compounding: the only way to know whether changes 1–7 helped | G8; 4.5 |
| 11 | **Progress file for multi-run cards**: on a retry or requested changes, the engineer keeps `docs/progress/<card-id>.md` in the worktree (template 2.2) and reads it first | `[Hermes]` | S, ~1 h | **Low-medium.** Most cards fit one session | G9; 2.2 |
| 12 | **Version and retention hygiene**: pin the Hermes version (live docs already differ from the installed version); schedule session pruning and card archiving; confirm nothing in `hooks/` is meant to gate workers | `[Hermes]` | S, 1–2 h | **Low-medium.** No silent behaviour changes; bounded stores | G10; 5.3, 7 |

Changes 1–4 are the "first three" in section 0, with change 3 folded into H2. Land change 1 first: the gates, budgets and evals all assume the standards reach the worker.

### 6.5 What I could not check: checks for you

| Check | Why it matters | How |
|---|---|---|
| Profile `config.yaml`: `hooks:`, both `write_approval` flags, `skills.external_dirs`, `agent.verify_on_stop`, compression threshold, observer or Langfuse plugin | Changes 2–5 and 9 depend on current values | Read `~/.hermes/profiles/<profile>/config.yaml` |
| Whether Hermes engineers open `CLAUDE.md` after the pointer | Sizes the benefit of change 1 | Search a few recent worker sessions for an early `read_file` of `CLAUDE.md` |
| Profile `hooks/` contents | Anything meant as a worker gate there is inert | List them |
| Repo `.claude/` directories and whether `eng-standards` is installed | Path rules and Claude Code gates may already exist | `/memory` and `/hooks` in a Claude Code session |
| `eng-standards` skill bodies | Change 5 needs their size and fit for Hermes | Read `plugins/eng-standards/skills/*/SKILL.md` |
| Profile memory contents | Shadow facts or personal data | `hermes journey` per profile |
| A live `pre_tool_call` gate on `kanban_request_review` | Inferred from source only | A throwaway board with one dummy card |

---

## 7. Risks, open questions and what would change the recommendation

**The recommendation is robust to most unknowns, because files, gates and owners are cheap to keep even if a specific number turns out wrong. The main risks are tool churn, over-building and review capacity.**

**Risks.**
- **Tool churn.** On the day of this brief, Hermes's live docs already disagreed with the installed version on curator defaults and on the context-file order.[77][78][24]
  Claude Code's docs carry no dates.[2]
  Pin versions and re-run the regression set on upgrades.
- **Over-building.** Anthropic removed whole harness stages once a newer model no longer needed them `[vendor]`.[34] Keep gates that check code deterministically, and be readier to delete process gates.
- **Review capacity.** You are the final gate. The earlier brief's ceiling of one closely supervised stream plus two to four low-review-cost background streams still applies.[1]
- **Headless billing** for `claude -p` and the Agent SDK was unresolved in the earlier brief. Nothing here depends on it, but any design where Hermes drives Claude Code does.[1]

**Open questions.** Do Claude 5-series models still need resets for multi-day work? The evidence stops at Opus 4.6.[34] Does the typed handoff block reduce rework in a real squad, given that the supporting studies are synthetic?[8] Does grep plus LSP miss things on large C# solutions? No .NET study exists.[153] Does the Langfuse-to-PR join work in practice? What does the ICO's worker-monitoring and DPIA guidance require of per-developer tracing, and what do Anthropic's sub-processor list and UK-US transfer route say? None of these were read or tested.

| If this turned out true | Then |
|---|---|
| A paired eval on your repos shows the typed handoff block doesn't reduce rework | Drop to prose plus verification evidence; keep only the constraints field |
| A 5-series study shows compaction keeps session constraints | Relax in-session reset discipline; keep files across sessions |
| An index beats grep plus LSP on your C# solutions in your own eval | Add a structural index or code-search MCP there |
| Hermes adds a blocking completion hook, or managed-only hooks | Move the gates there; tighten 5.2 |
| Your traces show Hermes workers reliably read `CLAUDE.md` and keep it | Change 1 drops from top priority to hygiene (still worth one canonical file) |
| Controlled studies show long files cost nothing in adherence for realistic rule sets, and caching keeps cost negligible | Relax the 150–200-line budget; split for ownership alone |
| Claude Code gains a write-approval gate for auto memory | Use auto memory as the work inbox |

### Verification log

I re-fetched the sources behind the claims the recommendation and gap analysis rest on, and read the installed Hermes source where docs and behaviour could differ. **Verified today (25 checks):**
- Hermes: one project context file, first non-empty match, `AGENTS.md` before `CLAUDE.md`.[24][115]
  Workers run in the card workspace with `--accept-hooks`.[117]
  `pre_tool_call` blocks with exit 2 or `fail_closed`; gateway hooks are gateway-only.[84][128]
  The compressor fires at 50% and clears old tool results over 200 characters.[42]
  Memory caps, both write-approval flags defaulting to false, `external_dirs`, and "one agent per Hermes home".[25][55]
  Metadata keys are "a convention, not a schema requirement".[54]
  Managed scope pins config.[114]
- Claude Code: under-200-line target, "context, not enforced configuration", `AGENTS.md` only without `CLAUDE.md` (v2.1.277+), `@AGENTS.md` never read twice.[2]
  The compaction survival table.[23]
  Exit 2 blocks `Stop`, `SubagentStop`, `TaskCompleted` and `PreToolUse`.[71]
  Cache reads cost 0.05x on Opus 5.5 and Sonnet 5.5.[21]
- Studies: ETH v3 (no general gain, +20/23% cost, +2.4% at p=21%, all agents but Claude Code).[3]
  McMillan (60.0–67.7%, p=0.16, 0/524, OR 0.944).[4]
  ContextCov (88.3/67.0/50.3).[5]
  SWE-Gate (221/644).[122]
  Lost in Compaction (17%, >90%).[6]
  Governance Decay (0→30%, 59%, pinning 0%).[43]
  "Must Becomes Maybe" (100%, 54.2%, 0%).[8]
  SkillsBench (33.9→50.5; self-generated skills don't substitute).[10]
  Rules study (+13.8 pp; negative constraints).[120]
  Copilot memory (citations verified, 90 vs 83, 28-day expiry).[12][160]
  Anthropic's long-running harness.[7]
- UK: Bedrock London in-region Opus 5.5 and Sonnet 5.[200] Langfuse self-hosted retention is indefinite without Enterprise, minimum 3 days.[194] Langfuse hooks don't capture context files.[188]

**Disputed or corrected.**

| Claim | Where | Finding |
|---|---|---|
| Developer-written context files improve success "by about 4%" | Earlier brief[1] | **Stale.** That was ETH v1; v3 says +2.4%, p=21%, not significant. The three researchers who checked agree |
| Curator: stale at 14 days, archive at 30, agent-created skills only | Memory and org findings | **Version-dependent:** right for installed v0.21.6+666; the live docs now say 30/90 with `prune_builtins: true`[79][77] |
| Context-file order includes `AGENTS.override.md` | Memory and cross-repo findings | **Right for the installed version;** missing from the live docs page[115][24] |
| Hermes has no managed policy layer | UK findings | **Too strong:** managed scope exists, though weaker than Claude Code's[114] |
| ETH figures from v2 | Org findings | Use v3: cost figures agree, success figures moved |
| Copilot memory gave "a 7% increase" in merge rate | Memory and org findings | 7 percentage points (83% → 90%), about 8% relative |
| Profile `hooks/` directories can enforce standards | PM observation | They hold gateway hooks, which never run in Kanban workers |

**Conflicts between researchers** were limited to the three rows above about the ETH version, the Hermes managed layer and the curator defaults, and are resolved there. The substantive disagreements are between sources, shown side by side in 1.7, 2.3, 3.3, 4.3 and 5.2.

**Gaps, and why there is no follow-up research card.** No C#/.NET evidence; no 5-series data on compaction versus reset; synthetic, single-source handoff studies; the Hermes completion gate and the Langfuse join untested; ICO worker-monitoring guidance and Anthropic's sub-processors unread. None changes the recommendation; they change magnitudes and implementation details, as the table above shows. Experiments on your own repos (changes 2, 9 and 10) answer most of them better than desk research would, so I created no follow-up researcher card.

## Sources

[1] file:///Users/anilkerai/git/research/coding-agent-squad-build-options.md — Earlier brief: coding-agent-squad-build-options.md (10 Oct 2026)
[2] https://code.claude.com/docs/en/memory — Claude Code docs: Memory (CLAUDE.md, rules, AGENTS.md)
    > "Longer files consume more context and reduce adherence."
    > "Claude treats them as context, not enforced configuration."
[3] https://arxiv.org/abs/2602.11988 — Evaluating AGENTS.md (arXiv 2602.11988, v3 29 Sep 2026)
    > "providing context files does not generally improve task success rates, while increasing inference cost by over 20% on average"
    > "they improve performance for all agents but Claude Code"
[4] https://arxiv.org/abs/2605.10039 — Instruction Adherence in Coding Agent Configuration Files (arXiv 2605.10039)
    > "each additional function the agent generates is associated with approximately 5.6% lower odds of compliance per step"
[5] https://arxiv.org/abs/2603.00822 — ContextCov (arXiv 2603.00822)
    > "ContextCov achieves 88.3% constraint compliance (vs. 67.0% and 50.3%)"
[6] https://arxiv.org/abs/2608.11242 — Lost in Compaction (arXiv 2608.11242, 31 Jul 2026)
    > "Current compactors retain only 17% of injected SCs on average"
[7] https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents — Anthropic Engineering: Effective harnesses for long-running agents (26 Nov 2025)
    > "Read the git logs and progress files to get up to speed on what was recently worked on."
[8] https://arxiv.org/abs/2608.24569 — When 'Must' Becomes 'Maybe': Constraint Weakening in LLM Agent Workflows, arXiv 2608.24569 (Aug 2026)
    > "Normal handoff compression produces 100.0% deactivation and 54.2% forbidden action."
[9] https://arxiv.org/abs/2607.17957 — DepRepair / DepBench (arXiv 2607.17957)
[10] https://arxiv.org/abs/2602.12670 — SkillsBench, arXiv 2602.12670 (v1 13 Feb 2026, v4 14 Jun 2026)
    > "Curated Skills raise the average pass rate from 33.9% to 50.5%"
    > "Self-generated Skills do not substitute for curated ones."
[11] https://arxiv.org/abs/2510.04618 — Zhang et al., Agentic Context Engineering (ACE), arXiv 2510.04618 (Oct 2025, v3 29 Mar 2026, ICLR 2026)
[12] https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot — GitHub Blog: Building an agentic memory system for GitHub Copilot (15 Jan 2026)
    > "7% increase in pull request merge rates (90% with memories vs. 83% without)"
[13] https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents — Anthropic - Demystifying evals for AI agents (9 Jan 2026)
[14] https://dora.dev/insights/finding-balance-in-the-era-of-tokenmaxxing — DORA: Finding balance in the era of tokenmaxxing (2 Jun 2026)
[15] https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — Anthropic - Effective context engineering for AI agents
[16] https://arxiv.org/abs/2507.13334 — A Survey of Context Engineering for LLMs (arXiv 2507.13334)
[17] https://simonwillison.net/2025/Jun/27/context-engineering — Simon Willison - Context engineering (27 Jun 2025)
[18] https://www.trychroma.com/research/context-rot — Chroma - Context Rot
[19] https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html — Drew Breunig - How Long Contexts Fail (22 Jun 2025)
[20] https://platform.claude.com/docs/en/build-with-claude/compaction-threshold — Claude API docs - Compaction at a token threshold
[21] https://platform.claude.com/docs/en/build-with-claude/prompt-caching — Claude API docs - Prompt caching
    > "Cache hits and refreshes on Claude Opus 5.5 and Claude Sonnet 5.5 are priced at 0.05x the base input price."
[22] https://code.claude.com/docs/en/prompt-caching — Claude Code docs - How Claude Code uses prompt caching
[23] https://code.claude.com/docs/en/context-window — Claude Code docs - Explore the context window
    > "If a rule must persist across compaction, drop the"
[24] https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files — Hermes docs: Context Files
    > "project context type is loaded per session (first match wins)"
[25] https://hermes-agent.nousresearch.com/docs/user-guide/features/memory — Hermes docs: Persistent Memory (read 12 Oct 2026)
    > "Don't point two agent processes at the same Hermes home directory."
[26] https://arxiv.org/abs/2307.03172 — Liu et al. - Lost in the Middle (arXiv 2307.03172)
[27] https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models — Claude blog - The new rules of context engineering for Claude 5 generation models (24 Jul 2026)
[28] https://www-cdn.anthropic.com/0b4915911bb0d19eca5b5ee635c80fef830a37ea.pdf — Anthropic - Claude Opus 4.8 System Card (28 May 2026)
[29] https://arxiv.org/abs/2502.05167 — Modarressi et al. - NoLiMa (arXiv 2502.05167)
[30] https://www-cdn.anthropic.com/fc1b44717c85dc068bc6ba5024219938094694bd/Claude%20Opus%205.5%20System%20Card.pdf — Anthropic - Claude Opus 5.5 System Card
[31] https://arxiv.org/abs/2505.06120 — Laban et al. - LLMs Get Lost In Multi-Turn Conversation (arXiv 2505.06120)
[32] https://code.claude.com/docs/en/best-practices — Claude Code docs - Best practices
[33] https://arxiv.org/abs/2606.29718 — Diagnosing and Mitigating Context Rot in Long-horizon Search (arXiv 2606.29718)
[34] https://www.anthropic.com/engineering/harness-design-long-running-apps — Anthropic - Harness design for long-running application development (24 Mar 2026)
[35] https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool — Claude API docs - Tool search tool
[36] https://arxiv.org/abs/2602.16069 — The Limits of Long-Context Reasoning in Automated Bug Fixing (arXiv 2602.16069)
[37] https://code.claude.com/docs/en/model-config — Claude Code docs - Model configuration
[38] https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus — Manus - Context Engineering for AI Agents: Lessons from Building Manus (18 Jul 2025)
[39] https://claude.com/blog/what-a-task-costs-on-opus-5-5 — Claude blog - What a task costs on Opus 5.5 (25 Sep 2026)
[40] https://platform.claude.com/docs/en/build-with-claude/context-windows — Claude API docs - Context windows
[41] https://platform.claude.com/docs/en/build-with-claude/context-editing — Claude API docs - Context editing
[42] https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching — Hermes docs - Context Compression and Caching
    > "Old tool results (>200 chars) outside the protected tail are replaced with"
[43] https://arxiv.org/abs/2606.22528 — Governance Decay: Context Compaction Erases Safety Constraints (arXiv 2606.22528)
    > "violation rises from 0% with the policy in full context to 30% after compaction"
[44] https://factory.ai/news/evaluating-compression — Factory Research - Evaluating Context Compression for AI Agents (16 Dec 2025)
[45] https://arxiv.org/abs/2508.21433 — The Complexity Trap: Observation Masking vs LLM Summarization (arXiv 2508.21433)
[46] https://blog.jetbrains.com/research/2025/12/efficient-context-management — JetBrains Research - Cutting Through the Noise: Smarter Context Management (Dec 2025)
[47] https://code.claude.com/docs/en/features-overview — Claude Code docs - Extend Claude Code (features overview)
[48] https://www.anthropic.com/engineering/multi-agent-research-system — Anthropic - How we built our multi-agent research system (13 Jun 2025)
[49] https://cognition.com/blog/multi-agents-working — Cognition - Multi-Agents: What's Actually Working
[50] https://cognition.com/blog/dont-build-multi-agents — Cognition - Don't Build Multi-Agents (12 Jun 2025)
[51] https://www.anthropic.com/research/claude-opus-4-6 — Anthropic - Introducing Claude Opus 4.6 (5 Feb 2026)
[52] https://arxiv.org/abs/2603.20432 — Coding Agents are Effective Long-Context Processors (arXiv 2603.20432)
[53] https://code.claude.com/docs/en/sub-agents — Claude Code docs: Create custom subagents (read 12 Oct 2026)
[54] https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban — Hermes docs: Kanban (read 12 Oct 2026)
    > "These keys are a convention, not a schema requirement."
[55] https://hermes-agent.nousresearch.com/docs/user-guide/features/skills — Hermes docs: Skills System (read 12 Oct 2026)
    > "By default the agent writes skills freely"
[56] https://arxiv.org/abs/2608.20664 — DreamBench-SWE: A Multi-Session Memory-Hygiene Benchmark for Software Agents, arXiv 2608.20664 (21 Aug 2026)
[57] https://github.com/anthropics/cwc-long-running-agents/blob/main/README.md — Anthropic cwc-long-running-agents README, Code with Claude 2026 demo repo (May 2026)
[58] https://dontcodethisathome.com/steering-a-coding-agent-across-long-sessions-three-documents-and-one-rule — Practitioner: Steering a Coding Agent Across Long Sessions, Three Documents and One Rule (20 Jun 2026)
[59] https://arxiv.org/abs/2609.05510 — Memory as Infrastructure: Reliability Engineering for Persistent Agent Memory, arXiv 2609.05510 (31 Aug 2026)
[60] https://code.claude.com/docs/en/tools-reference — Claude Code docs: Tools reference, task tool availability (v2.1.268+; read 12 Oct 2026)
[61] https://code.claude.com/docs/en/hooks-guide — Claude Code docs: Automate actions with hooks (read 12 Oct 2026)
[62] https://code.claude.com/docs/en/sessions — Claude Code docs: Manage sessions (read 12 Oct 2026)
[63] https://code.claude.com/docs/en/checkpointing — Claude Code docs: Checkpointing (read 12 Oct 2026)
[64] https://arxiv.org/abs/2503.13657 — Cemri et al., Why Do Multi-Agent LLM Systems Fail? (MAST), arXiv 2503.13657 (Mar 2025; NeurIPS 2025 D&B)
[65] https://arxiv.org/abs/2408.02442 — Let Me Speak Freely? Impact of Format Restrictions on LLM Performance, arXiv 2408.02442 (Aug 2024; EMNLP Industry 2024)
[66] https://arxiv.org/abs/2608.29028 — Facts Without Rules: Boundary Metadata Collapse in Multi-Agent LLM Handoffs, arXiv 2608.29028 (29 Aug 2026)
[67] https://arxiv.org/abs/2608.25277 — Routed Graph Handoff: Adaptive Format Selection for Multi-Agent LLM Delegation, arXiv 2608.25277 (26 Aug 2026, EMNLP 2026)
[68] https://arxiv.org/abs/2608.04278 — EA-Graph: Artifact-Anchored Verification Memory for Coding Agents, arXiv 2608.04278 (4 Aug 2026)
[69] https://arxiv.org/abs/2607.09678 — Faithful, Not Corrective: Model Capability Governs Message-Format Effects in Multi-Hop Agent Relays, arXiv 2607.09678 (v2 17 Sep 2026)
[70] https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation — Hermes docs: Subagent Delegation (read 12 Oct 2026)
[71] https://code.claude.com/docs/en/hooks — Claude Code docs: Hooks reference (read 12 Oct 2026)
    > "SubagentStop Yes Prevents the subagent from stopping"
[72] https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them — Claude blog: Building multi-agent systems, when and how to use them (23 Jan 2026)
[73] https://claude.com/blog/multi-agent-coordination-patterns — Claude blog: Multi-agent coordination patterns (10 Apr 2026)
[74] https://arxiv.org/abs/2512.08296 — Towards a Science of Scaling Agent Systems, arXiv 2512.08296 (Dec 2025)
[75] https://arxiv.org/abs/2607.10608 — The Compliance Trap: Diagnosing How AI Agents Consume Conflicting Memory, arXiv 2607.10608 (12 Jul 2026)
[76] https://arxiv.org/abs/2505.16067 — Xiong et al., How Memory Management Impacts LLM Agents: Experience-Following Behavior, arXiv 2505.16067 (v2 10 Oct 2025; ACL 2026)
[77] https://hermes-agent.nousresearch.com/docs/user-guide/features/curator — Hermes docs: Curator (read 12 Oct 2026)
    > "default **7 days**"
[78] file:///Users/anilkerai/.hermes/hermes-agent/agent/curator.py — Hermes source (installed v0.21.6+666): agent/curator.py, DEFAULT_STALE_AFTER_DAYS, DEFAULT_ARCHIVE_AFTER_DAYS = 14, 30 (read 12 Oct 2026)
    > "DEFAULT_STALE_AFTER_DAYS, DEFAULT_ARCHIVE_AFTER_DAYS = 14, 30"
[79] file:///Users/anilkerai/.hermes/hermes-agent/website/docs/user-guide/features/curator.md — Hermes docs as shipped with installed v0.21.6+666: Curator (read 12 Oct 2026)
    > "By default the curator manages only agent-created skills."
[80] https://code.claude.com/docs/en/goal — Claude Code docs: Keep Claude working toward a goal (read 12 Oct 2026)
[81] https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool — Claude API docs: Memory tool, memory_20250818 (read 12 Oct 2026)
[82] https://code.claude.com/docs/en/agent-teams — Claude Code docs: Orchestrate teams of Claude Code sessions, experimental (read 12 Oct 2026)
[83] https://hermes-agent.nousresearch.com/docs/user-guide/sessions — Hermes docs: Sessions (read 12 Oct 2026)
[84] https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks — Hermes docs: Event Hooks (read 12 Oct 2026)
    > "hook can block or fail closed"
[85] https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers — Hermes docs: Memory Providers (read 12 Oct 2026)
[86] https://arxiv.org/abs/2504.19413 — Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory, arXiv 2504.19413 (28 Apr 2025)
[87] https://arxiv.org/abs/2501.13956 — Zep: A Temporal Knowledge Graph Architecture for Agent Memory, arXiv 2501.13956 (20 Jan 2025)
[88] https://www.letta.com/blog/context-repositories — Letta: Introducing Context Repositories, git-based memory for coding agents (12 Feb 2026)
[89] https://github.com/steveyegge/beads/blob/main/README.md — Beads README (steveyegge/gastownhall beads), read 12 Oct 2026
[90] https://engineering.atspotify.com/2025/11/context-engineering-background-coding-agents-part-2 — Spotify Honk Part 2: Context Engineering (24 Nov 2025)
[91] https://github.com/oasdiff/oasdiff — oasdiff (OpenAPI breaking changes)
[92] https://buf.build/docs/breaking — Buf docs: Detecting breaking changes
[93] https://github.com/dotnet/roslyn-analyzers/blob/main/src/PublicApiAnalyzers/PublicApiAnalyzers.Help.md — PublicApiAnalyzers help (dotnet/roslyn-analyzers)
[94] https://engineering.atspotify.com/2026/4/background-coding-agents-dataset-migrations-honk-part-4 — Spotify Honk Part 4: Dataset migrations (Apr 2026)
[95] https://sourcegraph.com/docs/api/mcp — Sourcegraph docs: MCP Server
[96] https://code.claude.com/docs/en/large-codebases — Claude Code docs: Monorepo and large codebase setup
[97] https://aider.chat/docs/repomap.html — Aider docs: Repository map
[98] https://docs.devin.ai/work-with-devin/deepwiki-mcp — Devin docs: DeepWiki MCP
[99] https://nx.dev/blog/the-effect-of-monorepos-on-the-effectiveness-of-ai-agents — Nx: The Monorepo Advantage for AI Agents (2026)
[100] https://seylox.github.io/2026/03/05/blog-agents-meta-repo-pattern.html — Anyline: agents meta-repository pattern (5 Mar 2026)
[101] https://engineering.atspotify.com/2025/11/spotifys-background-coding-agent-part-1 — Spotify Honk Part 1 (24 Nov 2025)
[102] https://arxiv.org/abs/2504.09691 — Migrating Code At Scale With LLMs At Google (arXiv 2504.09691)
[103] https://airbnb.tech/infrastructure/accelerating-large-scale-test-migration-with-llms — Airbnb: Accelerating large-scale test migration with LLMs (2025)
[104] https://arxiv.org/abs/2608.30300 — Update from Hell (arXiv 2608.30300)
[105] https://martinfowler.com/bliki/ParallelChange.html — Fowler bliki: Parallel Change (2014)
[106] https://docs.pact.io/pact_broker/can_i_deploy — Pact docs: Can I Deploy
[107] https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3 — Spotify Honk Part 3: Feedback Loops (Dec 2025)
[108] https://github.com/pact-foundation/pact-net — pact-net (Pact for .NET)
[109] https://docs.pact.io/pact_nirvana/step_6 — Pact docs: can-i-deploy with branch in PR pipelines (Pact Nirvana step 6)
[110] https://arxiv.org/abs/2610.13668 — CRBugBench: Benchmarking Code Review Agents (arXiv 2610.13668)
[111] https://arxiv.org/abs/2603.26130 — SWE-PRBench (arXiv 2603.26130)
[112] https://code.claude.com/docs/en/managed-settings — Claude Code docs: Deploy managed settings
[113] https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions — Hermes docs: Profile Distributions
[114] https://hermes-agent.nousresearch.com/docs/user-guide/managed-scope — Hermes docs: Managed Scope
    > "Managed scope lets an administrator push a baseline of configuration and secrets that a standard (non-root) user cannot override."
[115] https://github.com/NousResearch/hermes-agent/blob/main/agent/prompt_builder.py — Hermes source: prompt_builder.py (context file loading)
    > "Only ONE project context type loads, first found wins"
[116] https://code.claude.com/docs/en/skills — Claude Code docs: Skills
[117] https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/kanban_db_dispatch.py — Hermes source: kanban_db_dispatch.py (worker argv)
    > "pass --accept-hooks explicitly so"
[118] https://agents.md — AGENTS.md
[119] https://arxiv.org/abs/2507.11538 — IFScale: How Many Instructions Can LLMs Follow at Once? (arXiv 2507.11538)
[120] https://arxiv.org/abs/2604.11088 — Zhang et al. - Guardrails Beat Guidance: A Large-Scale Study of Rules, Skills, and Persistent Configuration for Coding Agents (arXiv 2604.11088; v1 13 Apr 2026, v2 28 May 2026)
    > "every individually beneficial rule is a negative constraint"
[121] https://arxiv.org/abs/2607.26819 — Coding Agents' Compliance with AI Contribution Rules (arXiv 2607.26819)
[122] https://arxiv.org/abs/2609.04167 — SWE-Gate (arXiv 2609.04167)
    > "among 644 repairs that pass the functional tests, 221 fail to satisfy the provided review constraints"
[123] https://learn.microsoft.com/en-us/dotnet/core/project-sdk/msbuild-props — Microsoft Learn: MSBuild properties for .NET SDK (EnforceCodeStyleInBuild)
[124] https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-format — Microsoft Learn: dotnet format
[125] https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/configuration-options — Microsoft Learn: code analysis configuration options
[126] https://github.com/BenMorris/NetArchTest — NetArchTest README
[127] https://archunitnet.readthedocs.io/en/latest — ArchUnitNET docs
[128] https://github.com/NousResearch/hermes-agent/blob/main/agent/shell_hooks.py — Hermes source: agent/shell_hooks.py
    > "BLOCK_EXIT_CODE = 2"
[129] https://github.com/NousResearch/hermes-agent/blob/main/agent/tool_executor.py — Hermes source: agent/tool_executor.py
[130] https://arxiv.org/html/2602.11988v2 — Evaluating AGENTS.md (full text, v2)
[131] https://arxiv.org/abs/2511.12884 — Chatlatanagulchai et al. - Agent READMEs: An Empirical Study of Context Files for Agentic Coding (arXiv 2511.12884; v1 Nov 2025, v2 Aug 2026)
[132] https://openai.com/index/harness-engineering — OpenAI - Harness engineering: leveraging Codex in an agent-first world (11 Feb 2026; read via Wayback copy)
[133] https://bestagent.dev/claude-md-problem-teams-2026 — bestagent.dev - The CLAUDE.md problem in teams of 5+ (24 May 2026)
[134] https://arxiv.org/html/2507.11538 — Jaroslawicz et al. - How Many Instructions Can LLMs Follow at Once? (IFScale, arXiv 2507.11538, Jul 2025)
[135] https://arxiv.org/pdf/2605.10039 — McMillan - Instruction Adherence in Coding Agent Configuration Files: A Factorial Study of Four File-Structure Variables (arXiv 2605.10039, 11 May 2026)
[136] https://arxiv.org/abs/2601.20404 — Lulla et al. - On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents (arXiv 2601.20404, Jan 2026)
[137] https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start — Anthropic - How Claude Code works in large codebases: best practices and where to start (14 May 2026)
[138] https://oreilly.com/radar/coding-agents-love-decision-records — Davidson - Coding Agents Love Decision Records (O'Reilly Radar)
[139] https://github.com/atlassian/atlassian-mcp-server/tree/main — Atlassian - atlassian-mcp-server README (GitHub)
[140] https://simonwillison.net/2025/Jun/19/atlassian-prompt-injection-mcp — Simon Willison - Cato CTRL PoC attack targeting Atlassian's MCP (19 Jun 2025)
[141] https://raw.githubusercontent.com/github/github-mcp-server/main/README.md — GitHub - github-mcp-server README (toolsets, read-only, lockdown mode)
[142] https://docs.slack.dev/ai/slack-mcp-server — Slack Developer Docs - Slack MCP server overview
[143] https://backstage.io/docs/ai/mcp-actions — Backstage docs - MCP Actions Backend (accessed 12 Oct 2026)
[144] https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals — Vercel - AGENTS.md outperforms skills in our agent evals (27 Jan 2026)
[145] https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills — Anthropic - Equipping agents for the real world with Agent Skills (16 Oct 2025; updated 18 Dec 2025)
[146] https://arxiv.org/abs/2610.04832 — Wang et al. - Agent Skill Evolution: How Revisions Affect Coding Agents (arXiv 2610.04832, 4 Oct 2026)
[147] https://arxiv.org/abs/2609.05677 — Shen et al. - Who Maintains Agent Skills? A Longitudinal Study of Human-Governed, AI-Assisted Skill Maintenance (arXiv 2609.05677, 4 Sep 2026)
[148] https://maryanmats.com/blog/what-claude-code-skills-actually-cost — Mats - I Recommended Skills. Then I Measured Them (3 Aug 2026)
[149] https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners — GitHub Docs - About code owners (accessed 12 Oct 2026)
[150] https://port.io/guide/how-to-save-up-to-80-in-ai-costs-with-a-context-lake — Port - How to save up to 80% in AI costs with a Context Lake (vendor experiment)
[151] https://arxiv.org/abs/2603.27277 — Vogel et al. - Codebase-Memory: Tree-Sitter-Based Knowledge Graphs for LLM Code Exploration via MCP (arXiv 2603.27277, 28 Mar 2026)
[152] https://cursor.com/blog/semsearch — Cursor - Improving agent with semantic search (6 Nov 2025)
[153] https://arxiv.org/abs/2606.22417 — Bhola et al. - Code Isn't Memory: A Structural Codebase Index Inside a Coding Agent (arXiv 2606.22417, 21 Jun 2026)
[154] https://augmentcode.com/blog/context-engine-mcp-now-live — Augment - Context Engine is now available for any AI coding agent (6 Feb 2026; updated 18 Jun 2026)
[155] https://news.ycombinator.com/item?id=43164253 — Boris Cherny (Anthropic) on Hacker News - 'Claude Code doesn't use RAG currently' (24 Feb 2025)
[156] https://cline.bot/blog/why-cline-doesnt-index-your-codebase-and-why-thats-a-good-thing — Cline - Why Cline Doesn't Index Your Codebase (May 2025)
[157] https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/guides/ce-compound.md — Every - compound-engineering-plugin: ce-compound guide (accessed 12 Oct 2026)
[158] https://docs.coderabbit.ai/knowledge-base/learnings.md — CodeRabbit docs - Learnings (accessed 12 Oct 2026)
[159] https://cursor.com/blog/bugbot-learning — Cursor - Bugbot now self-improves with learned rules (8 Apr 2026)
[160] https://docs.github.com/en/copilot/concepts/agents/copilot-memory — GitHub Docs - About GitHub Copilot Memory (accessed 12 Oct 2026)
    > "any stored fact or preference that goes unused is automatically deleted after 28 days"
[161] https://arxiv.org/html/2510.04618v1 — Zhang et al. - Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models (ACE; arXiv 2510.04618, Oct 2025)
[162] https://claude.dev/blog/automating-eval-design-and-hillclimbing — Lance Martin / Anthropic - Automating eval design and hillclimbing with Claude (28 Sep 2026)
[163] https://docs.agentlint.app/checks — AgentLint - Check Reference (community CI linter for agent config files; accessed 12 Oct 2026)
[164] https://promptfoo.dev/docs/guides/test-agent-skills — Promptfoo docs - Test Agent Skills (accessed 12 Oct 2026)
[165] https://langfuse.com/docs/evaluation/experiments/experiments-ci-cd — Langfuse docs - Experiments in CI/CD (accessed 12 Oct 2026)
[166] https://code.claude.com/docs/en/admin-setup — Claude Code docs: Set up Claude Code for your organization (retrieved 12 Oct 2026)
[167] https://claude.com/blog/ciso-guide-to-agentic-ai — Anthropic (Jason Clinton): Zero risk isn't the job, a CISO's guide to agentic AI (17 Jul 2026)
[168] https://www.martinfowler.com/articles/harness-engineering.html — Böckeler (Thoughtworks): Harness engineering for coding agent users (2 Apr 2026)
[169] https://www.ncsc.gov.uk/blog-post/prompt-injection-is-not-sql-injection — NCSC: Prompt injection is not SQL injection (it may be worse), 8 Dec 2025
[170] https://arxiv.org/abs/2510.09023 — Nasr, Carlini et al.: The Attacker Moves Second (arXiv, 10 Oct 2025)
[171] https://simonwillison.net/2025/Jun/16/the-lethal-trifecta — Simon Willison: The lethal trifecta for AI agents, 16 Jun 2025
[172] https://ai.meta.com/blog/practical-ai-agent-security — Meta AI: Agents Rule of Two, 31 Oct 2025
[173] https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents — Pillar Security: Rules File Backdoor, 18 Mar 2025
[174] https://invariantlabs.ai/blog/mcp-github-vulnerability — Invariant Labs: GitHub MCP Exploited, 26 May 2025
[175] https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536 — Check Point Research: Caught in the Hook, RCE and API token exfiltration via Claude Code project files (25 Feb 2026)
[176] https://arxiv.org/abs/2607.14611 — Gadgil et al.: Bad Memory, prompt injection risks from memory in agentic systems (arXiv, 16 Jul 2026)
[177] https://www.anthropic.com/engineering/claude-code-auto-mode — Anthropic Engineering: How we built Claude Code auto mode (25 Mar 2026)
[178] https://code.claude.com/docs/en/permissions — Claude Code docs: Configure permissions (retrieved 12 Oct 2026)
[179] https://code.claude.com/docs/en/sandboxing — Claude Code docs: Sandboxed Bash tool (retrieved 12 Oct 2026)
[180] https://hermes-agent.nousresearch.com/docs/user-guide/security — Hermes docs: Security (retrieved 12 Oct 2026)
[181] https://hermes-agent.nousresearch.com/docs/guides/secure-hermes-on-a-work-machine — Hermes docs: Running Hermes on a Personal or Work Machine (retrieved 12 Oct 2026)
[182] https://code.claude.com/docs/en/monitoring-usage — Claude Code docs: Monitoring (OpenTelemetry) (retrieved 12 Oct 2026)
[183] https://langfuse.com/docs/observability/features/masking — Langfuse docs: Masking (retrieved 12 Oct 2026)
[184] https://code.claude.com/docs/en/settings-reference — Claude Code docs: Settings reference (retrieved 12 Oct 2026)
[185] https://code.claude.com/docs/en/plugins/org — Claude Code docs: Manage plugins for your organization (retrieved 12 Oct 2026)
[186] https://hermes-agent.nousresearch.com/docs/user-guide/egress/network-isolation — Hermes docs: Network Egress Isolation (Docker) (retrieved 12 Oct 2026)
[187] https://genai.owasp.org/download/52117 — OWASP Top 10 for Agentic Applications 2026 (9 Dec 2025)
[188] https://langfuse.com/resources/engineering/coding-agent-tracing — Langfuse: Tracing coding agents with Langfuse (as of Jul 2026)
    > "telemetry, not enforcement"
[189] https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation — ICO: Principle (e) Storage limitation
[190] https://ico.org.uk/about-the-ico/research-reports-impact-and-evaluation/research-and-reports/technology-and-innovation/tech-horizons-and-ico-tech-futures/ico-tech-futures-agentic-ai/data-protection-and-privacy-risks — ICO Tech Futures: Agentic AI, data protection and privacy risks
[191] https://code.claude.com/docs/en/claude-directory — Claude Code docs: Explore the .claude directory, application data (retrieved 12 Oct 2026)
[192] https://genai.owasp.org/download/56857/?tmstv=1785822482 — OWASP Top 10 for LLM Applications 2026 (published 3 Aug 2026)
[193] https://langfuse.com/integrations/developer-tools/claude-code — Langfuse docs: Trace Claude Code with Langfuse (retrieved 12 Oct 2026)
[194] https://langfuse.com/docs/administration/data-retention — Langfuse docs: Data Retention (retrieved 12 Oct 2026)
    > "data is stored indefinitely by default"
[195] https://langfuse.com/docs/administration/data-deletion — Langfuse docs: Data Deletion (retrieved 12 Oct 2026)
[196] https://code.claude.com/docs/en/data-usage — Claude Code docs: Data usage (retrieved 12 Oct 2026)
[197] https://code.claude.com/docs/en/zero-data-retention — Claude Code docs: Zero data retention (retrieved 12 Oct 2026)
[198] https://anthropic.com/legal/data-processing-addendum — Anthropic Data Processing Addendum (retrieved 12 Oct 2026)
[199] https://platform.claude.com/docs/en/manage-claude/data-residency — Claude Platform docs: Data residency (retrieved 12 Oct 2026)
[200] https://aws.amazon.com/about-aws/whats-new/2026/09/claude-region-expansion-lhr — AWS What's New: Bedrock expands Claude in-region support in the UK (London), 30 Sep 2026
    > "the processing never leaves that Region"
[201] https://langfuse.com/security/data-regions — Langfuse: Data Regions and Availability (retrieved 12 Oct 2026)
[202] https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data — Anthropic Privacy Center: How long do you store my organization's data? (1 Jul 2026)
[203] https://platform.claude.com/docs/en/manage-claude/api-and-data-retention — Claude Platform docs: API and data retention (retrieved 12 Oct 2026)
[204] https://services.google.com/fh/files/misc/2025_state_of_ai_assisted_software_development.pdf — DORA: State of AI-assisted Software Development 2025 (PDF v2025.2)
[205] https://langfuse.com/docs/evaluation/scores/data-model — Langfuse docs: Scores Data Model (retrieved 12 Oct 2026)
[206] https://langfuse.com/docs/observability/features/token-and-cost-tracking — Langfuse docs: Model Usage and Cost Tracking (retrieved 12 Oct 2026)
[207] https://langfuse.com/docs/metrics/features/metrics-api — Langfuse docs: Metrics API v2 (retrieved 12 Oct 2026)
[208] https://code.claude.com/docs/en/costs — Claude Code docs: Manage costs effectively (retrieved 12 Oct 2026)
[209] https://www.faros.ai/research/ai-acceleration-whiplash — Faros AI: AI Engineering Report Q2 2026, The Acceleration Whiplash
[210] https://arxiv.org/abs/2607.01418 — Murphy-Hill et al.: Adoption and Impact of CLI AI Coding Agents, Microsoft early-2026 rollout (arXiv, 1 Jul 2026)
[211] https://aq.dev/guides/rolling-out-coding-agents-to-your-team — AQ: Rolling out AI coding agents to your team, a staged plan (12 Sep 2026)
[212] https://www.thoughtworks.com/en-cl/radar/techniques/agent-instruction-bloat — Thoughtworks Technology Radar: Agent instruction bloat (Apr 2026)
[213] https://www.ai-primer.com/engineer/stories/stale-agent-docs-context-drift-coding-workflow — AI Primer: Developers report stale agents.md files derailing coding-agent runs (aggregates X posts, 2026)
[214] https://www.faros.ai/blog/ai-speed-trap-takeaways — Faros AI: The Speed Trap, 8 takeaways (18 Sep 2026)
[215] https://www.digitalapplied.com/blog/claude-code-anti-patterns-team-adoption-failure-modes-2026 — Digital Applied: Claude Code anti-patterns, team adoption failure modes (6 May 2026)
