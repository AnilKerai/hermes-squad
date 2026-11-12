---
name: research-topic-fanout
description: Use when a PM card asks for research. Fan out cards.
version: 1.0.0
author: pm
license: MIT
metadata:
  hermes:
    tags: [kanban, research, orchestration]
    related_skills: [grounded-citations, llm-wiki, sdlc-review]
---

# Research topic fan-out (pm on the `research` board)

Turns one user research card into N researcher cards + 1 analyst card, then parks the PM card
until the brief lands so the PM can judge it.

## When to Use

- The `pm` profile owns a `research`-board card that asks for research to inform a decision.
- The PM card is woken again after its analyst card completes (see the last section).

## Orient (read before framing)

1. `kanban_show()` for the user's card: decisions, constraints, "Done when", builds-on files.
2. Read `~/git/research/wiki/index.md` (may be stale: list `wiki/concepts/`, `wiki/entities/` too),
   then grep earlier briefs/findings for the topic's terms. Quote what is known, with wikilinks,
   into every card so researchers re-check only what they rely on.
3. If the user points at his repos, read their `CLAUDE.md`/docs yourself to frame questions, but
   restrict workers to `.md` docs (no code, config, git history) unless told otherwise.
4. Look at a previous topic's cards (`kanban_show` on an old researcher + analyst id) to keep the
   format consistent.

## Card format that works

- Per card: Decision context / Question (parts A, B, C in priority order with "if budget runs
  short, finish X first") / Scope (in; out with which sibling covers it) / Preferred sources /
  Output file / Acceptance criteria (named tables, verdicts, sketches with line caps).
- Append one **Shared context block, identical on every card**: date and paths (brief, findings dir,
  `.ledger/<card-id>.json`, `.work/`), a **topic map** of all sibling files (workers can't see
  siblings), reader profile, decisions, hypotheses under test, shared vocabulary and labels,
  builds-on facts, evidence labels, recency, model constraint, privacy, conflicts rule, findings
  structure, step budget (150 steps, skeleton first), topic-wide out-of-scope, "leads are not facts".
- Settle naming, labels, baselines and file names yourself and write them into every body; never
  let two cards decide the same thing.
- Comparable size: give the heaviest cards explicit priority order and caps (e.g. ≤8 rows).
- Every card: `workspace_kind="dir"`, `workspace_path="~/git/research"`, and an
  `idempotency_key` like `<topic>/<letter>-<slug>` so a retry doesn't duplicate.
- Analyst body: map each findings file to a brief section, the brief structure with the
  recommendation first, access rules, length, wiki ingest per `wiki/SCHEMA.md`, and what to do
  about material gaps.

## Wiring (the pitfall)

- **Never put the PM card in `parents` of researcher cards.** That gates them on the PM card, and
  with no unlink tool you can't then hang the PM card under the analyst (cycle).
- Correct order: create researchers (no parents) → create analyst with `parents=[all researchers]`
  → `kanban_link(parent_id=<analyst>, child_id=<own PM card>)` → `kanban_comment` the plan on the
  PM card → `kanban_block(kind="dependency")`. The PM card reopens when the analyst completes.

## Privacy

- If a repo's docs name the user's employer, tell every worker not to search for it or write it,
  and keep it out of your own card bodies and comments.
- On every review pass (brief and addendum), grep the whole vault for the employer name **and**
  the repo's sample names/refs (they live in the repo's skill/eval docs, e.g. a triage skill's
  worked examples), not just the new file. Zero hits is the bar.

## When woken after the analyst

- Judge the brief against the user's "Done when": findings files present, ledgers, dated citations,
  required sections. Spot-check one or two load-bearing figures against the findings and ledgers.
- Accept: complete with recommendation, confidence, caveats, brief path; "build X" goes in as
  a recommended next step only (no code cards).
- Gaps: targeted researcher follow-ups naming each gap + analyst revision card; link own card
  under the revision card and block on the dependency again.
- Read the brief's own "what would flip it" / open-question lists and check each flip condition
  rests on a verified fact. An unchecked flip condition, or one the brief treats differently in
  two sections, is a material gap even when the analyst says "no follow-up needed".
- Also test the example spec's acceptance criteria and pre-stated readings for passability and
  coverage (e.g. a test that cannot pass on the chosen edition; an undefined margin band).
- The brief is immutable once the analyst card completes, so the revision is an addendum file
  `~/git/research/<topic>-addendum.md` (frontmatter `type: brief-addendum`, `amends: <topic>`),
  with the follow-up findings in `<topic>/<slug>.md`. One researcher card (parts in priority
  order) + one analyst addendum card is enough for a handful of checkable facts.
- Before blocking again, comment the interim answer on the PM card so the user has the
  recommendation while the follow-up runs.
- When woken after the addendum: check each gap you named is closed (fact settled, conflict
  resolved, criterion passable, rule has no hole), spot-check 2-3 addendum figures against the
  follow-up findings, then complete. Tell the user the build spec is "brief §6 as amended by
  addendum §3", and list what is the user's call (policy, provider) separately from research gaps.
