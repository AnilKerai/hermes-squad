# Solution-wide upgrades (TFM + third-party packages)

Load when moving a whole .NET solution to a new target framework and bringing every
package to its latest stable version, or when writing acceptance criteria for an agent
or teammate to do it. The baseline and test-counting rules in SKILL.md Step 3/5 apply.

## Inventory before touching anything

```bash
grep -H -E '<TargetFramework' $(git ls-files '*.csproj')   # mixed TFMs?
dotnet --list-sdks; dotnet --list-runtimes                 # can every TFM actually run here?
dotnet list package --outdated                             # same package id only (see below)
```

Read `Directory.Build.props` / `Directory.Packages.props` too: with central package
management, versions live only in `Directory.Packages.props`, and props files often inject
the test stack and global usings that an upgrade will break.

Latest **stable** version of one id (the flat container also lists prereleases):

```bash
curl -s https://api.nuget.org/v3-flatcontainer/<id-lowercase>/index.json \
  | python3 -c 'import sys,json; v=[x for x in json.load(sys.stdin)["versions"] if "-" not in x]; print(v[-1] if v else None)'
```

## Successor packages are invisible to `--outdated`

`dotnet list package --outdated` only reports newer versions of the *same* package id. A
successor published under a new id never appears, so audit the test stack by hand:

- `xunit` (v2) → `xunit.v3`: v3 is a new package id, not a 3.x of `xunit`, so a v2
  solution looks "up to date".
- `AutoFixture.Xunit2` → `AutoFixture.Xunit3` follows the xunit move, and so do custom
  xunit data attributes and global usings of the `AutoFixture.Xunit2` namespace.

A "Done when: `dotnet list package --outdated` reports nothing" criterion therefore does
not prove the job is complete; pair it with an explicit successor rule, and with an
exceptions clause for packages held back by dependency ranges (next section).

## Dependency ranges cap "latest stable"

A package's latest stable can lie outside the range another package declares, e.g.
`AutoFixture.AutoNSubstitute` 4.18.1 declares NSubstitute `[2.0.3, 6.0.0)`. Forcing the
newer version gives NU1608 on restore, which is a build error in any project with
`TreatWarningsAsErrors`. Read the ranges before demanding "latest" for every id:

```bash
curl -s https://api.nuget.org/v3-flatcontainer/<id>/<ver>/<id>.nuspec | grep -E '<dependency|<group'
```

- Write the rule as "latest stable that every dependent's declared range allows; list each
  held-back package and the range that holds it". Never lift it with a blanket `NoWarn`.
- To unblock a capped package, weigh these in order and let the owner choose:
  1. The capping family's newest prerelease, when it widens the range (every AutoFixture
     `5.0.0-rc.1` package allows NSubstitute `[5.0.0, 7.0.0)`): no suppression, no custom
     code, and a plain bump once the stable ships. Needs explicit approval for that one
     prerelease; record the "move to the stable" follow-up in CLAUDE.md.
  2. Stay stable and suppress NU1608 for that one package only (per-`PackageReference`
     `NoWarn` metadata with a comment; confirm it really silences it), justified by a test
     that exercises the seam.
  3. Replace the glue package with a few lines of your own (e.g. a specimen builder that
     hands interfaces and abstract classes to `Substitute.For`), losing its extras.
- Package families drift: one member can ship a stable version the rest don't have
  (AutoFixture.Xunit3 4.19.0 vs the others at 4.18.1). Check each id before requiring
  "one version across the family".
- "Tests still pass with the forced version" is evidence only if a test exercises the seam.
  A mocking glue package is untested when the repo has no interfaces to substitute. Add a
  test that requests an interface and asserts substitute behaviour (`.Returns` read-back,
  `Received(1)`), not just non-null; commit it on the old stack first, then red-check it
  (remove the customization, see it fail, restore) on both stacks.

## xunit v3 is a test-platform migration, not a package bump

- On the .NET 10 SDK, `xunit.v3` projects are Microsoft Testing Platform (MTP) apps. A VSTest
  `dotnet test` fails before running anything with "Testing with VSTest target is no longer
  supported by Microsoft.Testing.Platform on .NET 10 SDK and later". Opt in with a repo-root
  `global.json` of `{ "test": { "runner": "Microsoft.Testing.Platform" } }` (no `sdk` section
  needed). A rule such as "stay on VSTest / no global.json" therefore makes v3 impossible, so
  scope v3 as its own change, and check the IDE's test runner supports MTP.
- Under MTP, `Microsoft.NET.Test.Sdk`, `xunit.runner.visualstudio` and `coverlet.collector`
  are not needed; remove them. `dotnet test <p>.csproj` and `dotnet test --project <p>.csproj`
  both work (without the opt-in, `--project` is rejected).
- xunit.v3 4.x requires executables but does not set `OutputType` itself (its build
  validation errors "xUnit.net v3 test projects must be executable"): set
  `<OutputType>Exe</OutputType>` once in the test-project section of `Directory.Build.props`.
- A project that is both a console app and its own test project can stay one project: set
  `XunitAutoGeneratedEntryPoint=false`, and in `Program.cs` hand a first argument that starts
  with `-` and isn't an integer to a copy of the generated entry point. Copy it from another
  test project's `obj/<cfg>/<tfm>/XunitAutoGeneratedEntryPoint.cs` and rename its
  `<RootNamespace>.SelfRegisteredExtensions` reference; it routes `--server` /
  `--internal-msbuild-node` to the MTP framework and anything else to the in-process console
  runner. MTP launches the exe as `--server dotnettestcli --dotnet-test-pipe <pipe>` (coverage
  prepends `--results-directory … --coverage …`), so the dash rule fits; VSTest launched it as
  `@@ <tempfile>`, which it does not. Capture the real argv (temporarily log `args`) before
  designing a dispatch, and document that `--help` now reaches the test runner.
- Coverage: `Microsoft.Testing.Extensions.CodeCoverage` excludes the test assembly by
  default, so projects that keep code and tests in one assembly get empty reports. Pass a
  settings file containing `<IncludeTestAssembly>True</IncludeTestAssembly>`:
  `dotnet test --coverage --coverage-output-format cobertura --coverage-settings CodeCoverage.config --results-directory TestResults`.
  Keep `--` out of its XML comments (invalid XML aborts the run) and don't name it so it
  matches a `coverage*.xml` ignore pattern.
- After `dotnet sln add`, check the `.sln` diff: it can rewrite the whole file with extra
  platform configurations; keep only the new project's entries.
- `dotnet list package --deprecated` flags `xunit` and `xunit.extensibility.core` as Legacy →
  their `xunit.v3*` successors; a criterion of "no deprecations" conflicts with staying on v2.

## Stale transitive chains hide behind a TFM bump

On newer TFMs NuGet prunes framework-provided packages from the graph, so warnings such as
NU1603 can disappear while a shared helper project still resolves ancient transitive
versions (a test-helper library pulling NSubstitute 2.x / Castle.Core 4.x through
AutoFixture's minimum ranges). Check the real graph, not the warning count:

```bash
dotnet list <shared>.csproj package --include-transitive
```

Fix by having the shared project reference directly every package whose namespaces it
imports (versions stay central), not with transitive pinning or `NoWarn`.

## Target framework in one place

Setting `<TargetFramework>` in `Directory.Build.props` makes the next upgrade a one-line
change, but only once the per-project `<TargetFramework>` elements are removed (a project's
own value overrides the props file). Verify with `git grep <old-tfm>` returning nothing.
