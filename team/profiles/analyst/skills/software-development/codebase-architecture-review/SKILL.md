---
name: codebase-architecture-review
description: "Review a whole codebase honestly: bugs, gaps, verdict."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, architecture, audit, feedback, missing-features, technical-debt]
    related_skills: [requesting-code-review, codebase-inspection, systematic-debugging]
---

# Codebase Architecture Review

Someone hands you a project they built and asks how good it is, what's wrong with it,
or what it's missing. The deliverable is a severity-ranked verdict backed by commands
you actually ran — not an impression of the code.

**Core principle:** every claim cites a `path:line` or a command's output. A review that
cannot be checked is worth nothing to the author, and authors of good code will test you.

## When to Use

- "Review this / give me honest feedback / how good or bad is it"
- "What features am I missing?" / "What would you add?"
- Architectural audit, technical-debt assessment, pre-adoption evaluation of a library

**This skill vs others:** this reviews a WHOLE codebase as-is, usually the user's own.
`requesting-code-review` verifies YOUR uncommitted diff before it lands.
`github` reviews other people's PRs with inline comments.

## Step 1 — Establish a baseline before reading anything

Build it and run its tests first. Batch with the file inventory.

```bash
<build command>                 # dotnet build / cargo build / npm run build / make
<test command>                  # record the exact pass count
git ls-files | wc -l; git ls-files | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -30
git ls-files '*.<ext>' | xargs cat | wc -l
```

A review that cannot open with "builds clean, N tests pass" has no baseline, and a broken
build reprioritises every other finding. Record the numbers — you will quote them.

## Step 2 — Read the centre, not the breadth

In order: the entry point / main loop, then the **types every layer touches** (the
message, event, state, or payload records), then one adapter or plugin implementation.

Find the narrow central type before enumerating missing features. A text-only payload
record or a stringly-typed envelope is usually the single cause behind several apparently
separate gaps; reporting it once as "the ceiling" is far more useful than reporting each
symptom, and it tells the author the fix is one breaking change rather than five features.

## Step 3 — Hunt the high-yield defect patterns

Run these as greps, not as reading. Each has a characteristic shape:

- **Declared but never consumed.** Grep every status enum / flag / result field for a
  consumer outside logging and tracing. A value that adapters populate and only a tracer
  reads is a decision the code forgot to make — the highest-yield bug pattern in a layered
  codebase.
  ```bash
  grep -rn "<EnumName>" --include=<ext> src/ | grep -v -e tracing -e logging -e Tests
  ```
- **Stringly-typed internal protocol.** A struct flattened to a formatted string and
  re-parsed by hand in each adapter, where the project owns both sides. Flag the
  duplicated parsers together with the type that forced them.
  ```bash
  grep -rn "Parse\|Split(' ')\|IndexOf(']')" --include=<ext> src/ | head -30
  ```
- **Port with no adapter.** An interface shipped with only a `Null`/no-op implementation is
  an unexercised path, not a finished feature. Compare the interface list against the
  concrete implementations.
- **Asymmetric rigour.** A careful validate-and-repair loop on one side of a boundary and
  nothing on the other (output validated, input trusted). Name the asymmetry — the author
  already built the machinery, so the fix is cheap.
- **Untested by exclusion.** Grep for coverage-exclusion attributes and no-test markers on
  files containing real parsing or branching logic.
- **Hardcoded values behind a safety control.** A price table, limit, or threshold compiled
  in with a "update when stale" comment is a correctness issue when a safety mechanism
  depends on it, not a config convenience.

## Step 4 — Read the author's own docs LAST

Read the roadmap, design docs, and changelog only after your findings exist. Reading them
first anchors you to the author's framing and you will report documented gaps as
discoveries.

Then diff your findings against their stated plan and split into three buckets:

1. **Not built and not planned** — report as missing.
2. **Planned** — drop, or note the priority.
3. **Deliberately cut** — challenge only with a reason they have not already addressed.
   Reread their rationale first; pushing back on a documented decision without engaging
   the documented reason reads as not having read it.

A deliberate cut is still worth challenging when the stated reason has an unexamined
consequence — a scope decision that was right for internal use but wrong for a published
package, or a "we don't need it" that a different section of their own docs contradicts.

## Step 5 — Report

Shape, in order:

1. **Verdict first**, one short paragraph. Say plainly whether it's good.
2. **Strengths — specific and brief.** Name the one or two things that are genuinely
   better than comparable projects and why. Generic praise is noise; the value is below.
3. **Problems, worst first**, numbered, each with `path:line` and the concrete failure mode
   ("returns a complete status for a truncated answer" beats "status handling is weak").
4. **Missing features**, prioritised — a table works well.
5. **Pushback** on their own decisions, clearly separated from bugs.

Reference code as `path:line`; do not paste files back at the author. State what you
verified by running versus what you inferred by reading. Keep the register plain — no
hedging and no flattery.

## Step 6 — When the author disputes a finding

Settle it with a disposable probe, not argument. Write a temp test into their suite, run
it, paste the real output, delete the file, and confirm `git status` is clean.

A measured result ends the disagreement in one turn; restating your reasoning does not —
and when the probe proves you wrong, you have learned it the cheap way. Expect the dispute
to be a conflation of two mechanisms with similar symptoms: name both, show which one the
probe exercised.

Open by granting the part they have right, by name and without qualification — "your budget
path is correct and unchanged" — before restating the finding. Their defence of the adjacent
mechanism is usually accurate; conceding it first is what makes the rest read as precision
rather than stubbornness, and it narrows the dispute to the one path actually at issue.

## Step 7 — Fixing what you found

- **Default to the minimal correct fix; name the richer alternative as an option and let
  them choose.** Authors reviewing their own code usually want the honest-status fix now
  and the feature later. Do not build the richer version unasked.
- **Follow the repo's own documented workflow.** Read `CLAUDE.md` / `AGENTS.md` /
  `CONTRIBUTING.md` for conventions — docs-updated-in-the-same-changeset, changelog entries
  with migration guides, commit-and-push without being asked, comment style. Deviating from
  a convention the repo states explicitly reads as not having read it.
- **Add a regression test per bug fixed**, including one that pins the *reason* (assert the
  failure message names the real cause) — that is what stops a future change from
  reattributing the failure to something else.
- **Fix the class, not the site you were pointed at.** Before changing what a status, enum
  or result field means, grep every producer and every consumer: adapters, tracers,
  serializers, wrappers that relay a sub-run's result, and the project's *own internal
  callers of the same port* (a summariser or critic that calls the model client directly).
  Internal callers are where the same bug survives the main-path fix, silently.
- **Decide "success" with an allowlist.** Name the normal values; everything else —
  unrecognised and future members included — is non-success. A denylist fails open on the
  next value nobody listed, which is how a first fix gets reopened. Mappers send unknown
  input to an explicit `Other`, never to the success value.
- **Check that every remedy you write removes the cause.** A remedy in an error message or
  changelog that only moves the failure (lowering an output cap to "fix" a full context
  window just truncates sooner) is a wrong instruction the user will follow.
- **Mutation-check before claiming the tests guard the fix.** Revert the fix several ways —
  the original bug, your own earlier incomplete fix, each adapter gap — and confirm each
  fails a test. Recipe, plus adapter wire tests and persistence pins, in
  `references/verifying-fixes.md`.
- **Do not choose the version number.** Write the changelog under `Unreleased` and hand the
  semver decision to the author; a published package version can never be reused.
- **Agent-instruction files are write-protected.** `CLAUDE.md`, `AGENTS.md` and similar need
  explicit user approval. A timed-out approval prompt is a refusal: never retry it and never
  route it through a shell or script. Sequence the work so additive, unprotected files land
  in their own commit and the protected edit is a separate approved step — then report
  exactly what is still pending.
- Mention it when pushing to a protected branch succeeds only by bypassing a rule; the
  author may not know their own protection is being skipped.

## Step 8 — When a second reviewer critiques your changes

The user may paste another model's or colleague's review of your commits. Treat every claim
as a hypothesis, including its citations — second reviews are usually mostly right and
partly overstated.

1. **Verify each point against primary source before editing anything**: the `path:line` it
   names, the upstream library's source at the pinned version (`gh api -H "Accept:
   application/vnd.github.raw" repos/O/R/contents/<path>?ref=<tag>`), the live docs page
   re-fetched and grepped. Record confirmed / partly right / wrong for each.
2. **Search outward from each confirmed point.** The constraint the reviewer missed is often
   one grep away (e.g. a proposed retry path that would not count toward an existing loop
   cap) and belongs in your answer.
3. **Fix defects and false claims now; record design suggestions as deferred** — in the ADR's
   alternatives (deferred, not rejected, with the constraint) and the roadmap — then ask
   whether to build them. Do not build an unrequested redesign on a review's say-so.
4. **When the critique cites a rule the repo does not contain**, say so neutrally (it may be
   the user's global rules) and still fix the substance behind it.
5. **Correct your own earlier text in place** — code comments, unreleased changelog entry,
   PR description, ADR — and sweep the repo for every copy of each corrected claim
   (`grep -rn` on the wrong phrase must come back empty).
6. **Reply as a table**: Point | What I found | Change. Then build/test counts, the commit,
   and — if the user tests from a preview package — the *new* version to switch to.

## Reviewing the project's documentation

Docs are in scope and usually unmeasured. Measure before asserting — "the docs are too
long" is an opinion, words-per-line and cross-file duplication counts are findings. See
`references/documentation-review.md` for the command set, the restructure shape, and how to
verify a backfilled changelog entry against git history before writing it.

## Pitfalls

- **Never assert a metric you did not run a command for.** No estimated line counts, no
  guessed test totals, no "looks like roughly".
- **Do not confuse a deliberate design with a bug.** Before calling something broken, grep
  for a comment or doc explaining it; good codebases encode the reason near the code.
- **A mature project's roadmap will pre-empt most easy findings.** The valuable findings are
  the ones absent from their docs entirely — that is where Step 4's ordering pays off.
- **Do not pad the strengths section to soften the review.** An author asking for honest
  feedback is paying for the problems list.
- **Check that the project's own central claim is tested.** A framework whose README states
  a thesis ("this makes X cheaper/faster/safer") and ships no benchmark for it has an
  unmeasured reason-for-existing — frequently the single highest-value gap, and it is never
  in the roadmap because the author believes the claim.
- **Quote sources verbatim or not at all.** Re-fetch the page and grep for the phrase before
  putting it in quotation marks; a paraphrase in quotes is a misquote, and the next reviewer
  will find it.
- **Take wire values from the serialization code, not from identifier names.** A constant
  named `ConnectionClosed` may serialize to `""` and be dropped by `omitempty`. Read the
  `String()`/JSON tags, and check the constant is ever assigned, before mapping, testing or
  documenting the value. Pin "added in version X" claims by bisecting tags, not by memory.
- **Re-measure after a cleanup you recommended and report the delta, even when it undercuts
  you.** State what you did not touch and what the remaining ceiling is. A restructure
  reported by files-touched rather than measured change lets a half-finished job read as
  complete, and the author cannot tell whether to continue.
