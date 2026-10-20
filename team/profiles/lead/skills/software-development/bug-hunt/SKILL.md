---
name: bug-hunt
description: "Use when a card asks for a bug hunt, audit or findings review. Lead plans it, engineer proves each finding with a probe, reviewer re-verifies."
version: 1.0.0
metadata:
  hermes:
    tags: [bug-hunt, audit, fact-finding, probes, verification, kanban]
---

# Bug hunt

A bug hunt is **fact-finding that needs execution**. Its output becomes fix cards, and the review lane checks fixes only against those cards. So a finding that is wrong, or a fix scope that is narrower than the bug, passes review untouched. Everything here is aimed at getting the findings and their fix scope right *before* they become cards.

Learned from a model-harness hunt done by one read-only agent. It covered 76 of 141 source files and 1 of 15 docs. It filed one false claim from memory, called a documented security bug "a product decision", and wrote 7 of 16 fixes narrower than the bug. Parallel verifiers with probes found every one of those gaps.

## Lead: plan the hunt, don't do it

You have no terminal, so you can't prove a finding. Don't hunt yourself.

1. Read CLAUDE.md/AGENTS.md and list `src/` (and `docs/`) to see the areas.
2. Split the repo into **3–6 areas** by domain (e.g. loop/state, adapters, tracing/dashboard, stores/persistence, sensors/security). Aim for about 20–40 source files each. Every source file belongs to exactly one area. Docs go to the area they describe.
3. Create one `engineer` card per area with `skills=["bug-hunt"]` and the repo's worktree. Each body says:
   - **Goal:** hunt bugs in <area>, following the `bug-hunt` skill's Engineer section. This is fact-finding: no commits.
   - **Scope:** the exact paths, plus the docs for that area.
   - Whether **live calls** are allowed, which credentials (e.g. "the key in samples/X/appsettings.local.json, read in place"), and a spend cap. Without this line, there are no live calls.
4. Make your own hunt card the **child** of all the area cards, and block it as a dependency. You resume when every area has passed review.
5. When the area cards are done, read each handoff's `findings[]`. Then:
   - **One fix card per root cause.** Merge findings from different areas that share a root cause.
   - **Evidence** = the finding's probe and its result. Never put an `unverified[]` item into a fix card. List those in your summary for the human, or create a further fact-finding card.
   - **Decisions must cover the finding's `fix_scope` in full:** sibling sites, `breaks_if_fixed` (tests and fakes to update), docs and CHANGELOG. If you narrow it, say why in Decisions.
   - **INTENDED findings are not filed.** Report them, with their citation, in your summary.
   - **Hotspots:** cards that edit the same file are serialised with parent links and a "Stacking" section (merge the parent's branch first). End with one integration card.
   - If the hunt card asked for findings "in triage", create the fix cards with `triage=true`.
6. **Your summary:** cards by priority, the INTENDED list with citations, the unverified list, each area's `not_checked`, and the hotspots.

## Engineer: hunt one area, prove every finding

**No commits on the card branch.** Probes live outside the repo.

1. **Read the decisions first.** CLAUDE.md/AGENTS.md, then every doc, ADR and README section for your area. Write down the documented behaviour you'll check against. A contradiction between the docs and the code is a finding.
2. **Make a scratch copy:** `git archive HEAD | tar -x -C $TMPDIR/hunt-<card>/src`. Build it and run the existing tests once, so you have a baseline.
3. **Read every file in your scope.** Hunt with these lenses, one after another:
   - failure and error paths
   - defaults and configuration values (a default that doesn't exist, a default that's off)
   - boundaries and limits (budgets, caps, sizes, encodings, culture)
   - concurrency and ordering
   - trust and security boundaries (untrusted input, secrets, sensitive data in logs and telemetry, path traversal)
   - persistence and serialisation (round-trips, legacy data, growth)
   - docs versus behaviour
   - code that other code relies on but no test covers
4. **For every candidate finding:**
   - **Probe it.** Write a throwaway test in the scratch copy (reuse the repo's test project and fakes) that **asserts the buggy behaviour** and passes on unmodified code. Or run a live check if the card allows it. Read credentials in place from the file the card names; never print or copy them. Use the cheapest model and a small max-tokens. A finding with no probe goes in `unverified[]`, not `findings[]`.
   - **INTENDED** needs a citation: a CLAUDE.md line, a doc, an ADR or a CHANGELOG entry that records the behaviour as a decision. Tests that pin a behaviour are not a decision. If the docs say the opposite, it is a bug.
   - **Root cause and sibling sites.** Name the root cause, then search the whole repo for the same pattern. List every site, inside your area or outside it.
   - **Fix scope.** Apply the minimal fix in the scratch copy and run the **full** suite. List what breaks (tests, test fakes, callers), the docs and CHANGELOG entries needed, and whether it changes a public API or behaviour. Then revert it. You are proving the scope, not fixing the bug.
   - **Severity** comes from the probe (who can reach it, what it costs), not from how the code looks.
5. **Attach the probe files** to the card with `kanban_attach`, so the reviewer and the lead can re-run them after $TMPDIR is pruned.
6. **Handoff:** finish with `kanban_request_review`, `reviewer="reviewer"`, so your findings get verified. Metadata:
   - `findings[]`: id, severity (P1–P3), where (file:line), what_happens, probe (attachment name + test name + result on unmodified code), root_cause, sibling_sites[], fix_scope, breaks_if_fixed[], docs_to_update[].
   - `intended[]`: what, citation.
   - `unverified[]`: what, and why it couldn't be proved.
   - `not_checked[]`: the files or lenses you didn't cover, and why.
   - `baseline`: the build and test counts from the scratch copy.

## Reviewer: verify the findings, not the prose

The deliverable is `findings[]`. There is no diff, and the branch should have no commits; any commit is a finding. Use a fresh `git archive` of the same base.

- **Re-run every probe** from the attachments on unmodified code. A probe that doesn't reproduce means request changes for that finding.
- **Check each INTENDED citation** really records a decision (not just a test), and that no doc contradicts it.
- **Check fix scope** on every P1/P2: apply the stated minimal fix in your copy and run the full suite. Anything that breaks and isn't in `breaks_if_fixed` is a finding. Search for sibling sites yourself.
- **Check severity** against the probe.
- **Spot-check coverage:** pick 2–3 files that `not_checked` doesn't mention, read them with a lens the handoff didn't stress, and request changes if you find a real bug there.
- Approve only when every finding is reproduced or explicitly moved to `unverified[]`. Name the probes you re-ran in your summary.
