---
name: dotnet-prerelease-package-testing
description: "Use when testing or bumping a NuGet package in consumer apps."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [dotnet, nuget, prerelease, preview-package, downstream, dependency-bump, evals]
    related_skills: [github-pr-workflow, codebase-architecture-review]
---

# Testing and Bumping a Package in Downstream Consumers

The user changed a library they publish (PR preview, main-push alpha, or a release) and wants
to know whether an app that consumes it "still works", or wants the app's pin bumped. The
deliverable is a baseline-vs-new comparison backed by real build, test and eval output, then
(when asked) a pushed pin.

## When to Use

- "Test this preview in my <app>" / "see if everything still works" after a library change
- Bumping a consumer's pin to a PR preview, a main-push alpha, or a new stable release
- Checking a released library change against the apps that depend on it
- "Update <app A> and <app B> to vX" — several consumers, often on different old pins

Publishing the package (CI triggers, PR body, merging) is `github-pr-workflow`; this skill
starts once a version exists, or is about to.

## Step 1 — Know which feed holds the version

Read the library's CI workflow (`on:` triggers, `paths:` filters, each job's `if:`) before
promising anything. Typical split:

| Trigger | Feed | Version shape |
|---|---|---|
| PR push | GitHub Packages (`nuget.pkg.github.com/<owner>`) | `X.Y.Z-pr.<PR>.<run>.<height>` |
| push to main | nuget.org | `X.Y.Z-alpha.0.<height>` |
| `v*` tag | nuget.org | `X.Y.Z` |

"Wait for it to be on NuGet" usually means nuget.org. A PR preview never reaches nuget.org
until the PR merges — say so plainly and name the feed it *is* on. Confirm a version exists
rather than predicting it:

```bash
gh api "/users/<owner>/packages/nuget/<PackageId>/versions?per_page=5" --jq '.[].name'      # GitHub Packages
curl -s https://api.nuget.org/v3-flatcontainer/<packageid-lowercase>/index.json            # nuget.org
```

## Step 2 — Find and read the consumer

```bash
grep -rl --include=*.csproj --include=Directory.Packages.props "<PackageId>" ~/git | grep -v "/<library-repo>/"
```

- A repo that embeds the consumer as a **git submodule** has its own checkout; updating the
  consumer repo does not change it. Name it in the report as untouched.
- Read the consumer's `CLAUDE.md`/`README` for the build, test and eval commands, and for
  whether a run has **side effects** (real mailbox, real API writes). Fixture-driven runs are
  safe to execute; anything that acts on live systems needs the user's go-ahead first.
- Grep the consumer for every API the library change touched (enums it switches over,
  status checks, failure-reason handling) to predict compile breaks and behaviour changes
  before building.
- **When the bump skips releases, read every skipped release's changelog**, not only the
  newest, and map each behavioural entry to a consumer grep — the result becomes the commit
  body's "what reaches this app":
  ```bash
  awk '/^## \[<new>\]/{p=1} /^## \[<current>\]/{p=0} p' CHANGELOG.md | grep -E '^## |^### |^- \*\*'
  ```
- **Report adjacent consumer defects the change makes relevant, but do not fix them in the
  bump** — e.g. consumer code that calls the model directly and treats a null, unparseable or
  refused response as success. Offer the fix as a separate change.
- Never open `appsettings.local.json`, `.env` or user-secrets; only check they exist.

## Step 3 — Baseline on the current pin

Build and test **before** bumping, and note the most recent eval result already on disk
(`ls -t <evals>/bin/Debug/<tfm>/results | head`). Without a baseline "still works" is an
assertion.

- **If the newest on-disk eval predates the current pin, run a fresh baseline eval first**,
  so the comparison isolates this bump. Start it in the background while the feed indexes.
- **Do not restore or build a consumer while its eval runs** from `--no-build` binaries —
  assemblies load lazily from `bin/`, so a mid-run rebuild mixes versions. Work on another
  consumer meanwhile.
- With several consumers, finish first the one whose new source was already evaluated
  (build + tests only) and spend the waiting time on the other's baseline.
- Name the eval model's cost class (cheap Haiku vs Sonnet) before running and in the report.

## Step 4a — Consume a GitHub Packages preview (no credentials written anywhere)

Do not add an authenticated source with `--store-password-in-clear-text`; download the
packages instead, passing the token on stdin so it never lands in a file or `ps` output:

```bash
V=<version>; FEED=<abs scratch dir>/preview-feed; mkdir -p "$FEED"
for id in <every package id in the family>; do l=$(echo $id | tr A-Z a-z)
  printf 'header = "Authorization: Bearer %s"\n' "$(gh auth token)" | \
    curl -sSfL -K - -o "$FEED/$id.$V.nupkg" "https://nuget.pkg.github.com/<owner>/download/$l/$V/$l.$V.nupkg"
done
```

- Needs `read:packages` on the gh token (`gh auth status` lists scopes).
- Download **every** package in the family, not only the direct references — they depend
  on each other at the same version.
- Prove the package contains the change before testing it: .NET string literals are UTF-16,
  so search the DLL with Python (`s.encode('utf-16-le') in zipfile.ZipFile(p).read(dll)`),
  not `strings`.
- Restore once with the folder as an extra source, then run a **plain** `dotnet build` to
  prove day-to-day commands work from the global package cache with the repo's
  `nuget.config` untouched:
  ```bash
  dotnet restore <sln> --source "$FEED" --source https://api.nuget.org/v3/index.json
  dotnet build <sln>        # no --source: must succeed from ~/.nuget/packages
  ```
- **Do not commit a PR-preview pin.** It restores on no machine without the private feed.
  Leave it uncommitted and say so.

## Step 4b — Consume a nuget.org alpha or release

- New pushes take minutes to appear (validation + indexing). Poll the flat container for
  every package id until all list the version, bounded, rather than guessing:
  `for i in $(seq 1 28); do …grep -q '"<V>"'…; sleep 20; done`.
  The nuget.org web page lists a version before restore can see it, so the user saying "it's
  on NuGet now" still means poll.
- **Restore with `--no-http-cache`** when these package ids were restored in the last ~30
  minutes (e.g. the alpha just before the release): NuGet caches each id's version list, and
  the stale list fails with NU1102 "nearest version: <previous>".
- Check the version was **not** already in `~/.nuget/packages/<id>/<V>` beforehand, restore
  with only the repo's `nuget.config`, and confirm the source in
  `~/.nuget/packages/<id>/<V>/.nupkg.metadata` (a dotfile — a `*.nupkg.metadata` glob misses
  it). That proves the pin restores anywhere.

## Step 5 — Bump, build, test, eval, compare

- Bump every package of the family to the **same** version. `replace_all` on the exact old
  version string is safe only after checking no unrelated package shares it.
- Confirm resolution per project from `obj/project.assets.json` (Python: keys of
  `libraries` starting with the package prefix), not from the csproj.
- Run build (warnings count), unit tests (pass count), then the model-in-the-loop evals —
  the consumer's real check. Prefer the configured cheap model; one run per case is enough
  for a regression check.
- When restore fails, `dotnet test --no-build` still "passes" on the old binaries — check the
  restore and build exit codes before trusting any test output.
- Compare runs with `scripts/compare_eval_runs.py <old-run-dir> <new-run-dir> --labels <old>
  <new> [--log <eval-stdout>]`: it diffs `report.md` with timing/token/cost removed and prints
  per case status, tool-call count, tokens, interventions and failure reason; `--log`
  summarises JSON trace events (statuses, stop reasons, sensor errors). A readiness flag
  present in both runs is pre-existing — say so instead of chasing it.
- **Explain a token delta before calling it noise.** When per-case tokens move both ways and
  the rises track tool-call count with unchanged statuses, it is the model's research depth,
  not the library — name the cases that moved.
- State when the changed code path was **not exercised** by the run (e.g. no cut-short
  responses), so a green result is not oversold.
- **Do not re-run paid evals when the code is identical.** After a merge compare trees
  (`[ "$(git rev-parse origin/main^{tree})" = "$(git rev-parse <tested-sha>^{tree})" ]`); for a
  release tag, `git diff --stat <tested-sha> v<X>` showing only `CHANGELOG.md` is the same
  proof. Build + tests then suffice — but only for a consumer that already ran that source; a
  consumer coming from an older pin needs baseline and new evals.

## Step 6 — Pin and push (when asked)

- **Match each repo's own bump-commit style — the user's repos differ.** Find prior bumps by
  file, not keyword (`git log --format='%h %s' -6 -- '*.csproj' Directory.Packages.props`),
  then read two with `git show -s --format=%B <sha>`. Shapes in use:
  - `Pin <lib> to the <V> preview` for a test pin, later `Upgrade to <lib> <V> (stable)`,
    which names the test-pin commit it replaces and says whether the release adds behaviour.
  - `chore(deps): bump <lib> <old> -> <new>`, whose body lists which of the releases' changes
    reach this consumer and which do not, and why.
  Every body ends with verification evidence (restore source, warnings, test count, eval
  verdict and token spread) and what was not exercised.
- **Sweep the consumer for the old version string** (`grep -rn "<old>" --include=*.md
  --include=*.csproj --include=*.cs .`) and update current-state mentions (a status line, a
  csproj comment). Reword comments to name no version so they cannot go stale; leave
  historical notes ("from 2.0.0 the enforcer…") alone.
- **Push consumer pin bumps directly to main — no PR.** The user wants PRs for library
  changes, not for downstream version bumps.
- **Check the consumer has CI before waiting on it** (`ls .github/workflows`); a `CLAUDE.md`
  "CI pipeline" line may sit under *Planned*. Without CI, say the push was not re-verified on
  a clean machine.
- Stage only the files the bump touched (version pins and swept mentions); leave eval
  results and unrelated changes out.
- Delete the local preview feed folder afterwards.

## Report shape

A table: Check | old version | new version (build, tests, evals, run outcomes, report diff);
for several consumers, one column per consumer (bump, commit, restore source, build, tests,
evals). Then how the package was obtained, exactly what changed in each consumer, what was
not covered (unexercised paths, missing CI, eval spend), adjacent defects found, and the next
pin to make (e.g. move to the stable when it is tagged).

## Pitfalls

- **`Conflict` on a `.snupkg` push step after the `.nupkg` step is benign** — `dotnet nuget
  push *.nupkg` also uploads the sibling `.snupkg`, so a second explicit symbols push finds
  them present and `--skip-duplicate` skips. Verify by counting "Your package was pushed".
- **Bound every wait with a counted `for` loop** around the check (CI status, feed
  indexing) so the tool call ends before its timeout.
- **Never compute the published version** (merge commits and `paths:` filters change the
  height) — read it from the publish job log or the feed.
