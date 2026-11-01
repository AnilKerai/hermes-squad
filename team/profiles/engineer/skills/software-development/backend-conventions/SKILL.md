---
name: backend-conventions
description: "Use when implementing backend work: .NET APIs, services, database schemas and migrations (EF Core, Postgres/Supabase), tests."
version: 0.2.0
metadata:
  hermes:
    tags: [dotnet, aspnetcore, backend, database, postgres, supabase, ef-core, testing]
---

# Backend conventions (.NET / ASP.NET Core, databases)

Defaults for this user's backend work. **The repo's AGENTS.md/CLAUDE.md and its existing code win over this file.** Match what's there before applying anything below. Grows from reviewer findings; keep it short.

## Build & quality gates
- Repos use `<Nullable>enable</Nullable>`, and often `TreatWarningsAsErrors`. Introduce zero new warnings; don't suppress with `#pragma`/`NoWarn` unless the card allows it.
- Central package management (`Directory.Packages.props`) where present: add versions there, never in a csproj.
- Run the repo's own build + test commands, and report pass counts per test project in the handoff.
- A csproj `Include` of a git-ignored file (`appsettings.local.json`) builds on a dev machine but fails a fresh clone/CI with MSB3030. Guard it with `Condition="Exists('…')"`, and prove a build fix in a fresh `git clone` (the working tree hides the problem). A test that parses the csproj with `System.Xml.Linq` (no MSBuild) catches it locally; red-check it by deleting the `Condition`.
- Linux CI check from a Mac: `git archive HEAD | tar -x -C <scratch>/tree`, then `docker run --rm -v <scratch>/tree:/src -w /src mcr.microsoft.com/dotnet/sdk:10.0-resolute bash -c 'unset LANG LC_ALL; dotnet build X.slnx -c Release && dotnet test X.slnx -c Release --no-build'`, log to a file. A non-git tree adds MINVER1001, `Microsoft.Build.Tasks.Git` and SourceLink warnings; those are not regressions, so count them by id.

## Tests
- Stack in use: **xUnit** (v2 and v3 both appear; match the project), **Shouldly** assertions, **NSubstitute** mocks, **AutoFixture** (`AutoFixture.Xunit3` / `AutoNSubstitute`) for test data. Don't introduce Moq, FluentAssertions or NUnit.
- Test behaviour through public seams; for APIs prefer `WebApplicationFactory` integration tests over mocking the framework.
- Driving a MAF `ChatClientAgent` runner in a test: pass a hand-written `IChatClient` that records `options.Tools` and the request messages on its first call, no model call. Return `FunctionCallContent` on that first call to run a real tool: `ChatClientAgent` wraps the client in `FunctionInvokingChatClient` itself, so the tool executes and its result lands in the trace.
- Offline test of a model-harness runner: a hand-written `IModelClient` returns one `ToolUse` `ModelResponse` per turn from a script, then `EndTurn` text for every later call (sensors and the critic call the same client). Inject it with `builder.WithModel(_ => model)` at the end of the runner's `configure` callback; `FakeModelClient` is hard-wired to a `calculator` call. Build `IConfiguration` in memory (`Agent:Provider=Anthropic`, no key) so a dev machine's `appsettings.local.json` can't reach a model. Red-check the OTel capture by flipping `enableSensitiveData` (arguments vanish) and by adding a second `OpenTelemetryTracer` via `WithTracer` (every call doubles).
- Unused `using` check (the compiler does not flag them): drop a temporary `.editorconfig` with `dotnet_diagnostic.IDE0005.severity = warning` at the repo root, build with `-p:EnforceCodeStyleInBuild=true -p:GenerateDocumentationFile=true -p:TreatWarningsAsErrors=false -p:NoWarn=CS1591 --no-incremental`, then delete it. Prove it fires by adding one unused using first. In a `Microsoft.NET.Sdk.Web` project, ImplicitUsings already supplies `Microsoft.Extensions.Configuration` and `DependencyInjection`, so the check flags explicit ones (it reports one per pass: rebuild until clean).
- A mutant that no test kills is dead code or an untested rule. Check whether an earlier condition already makes the branch unreachable (an agent-name exemption behind a `declared.Contains` gate was) and delete it rather than add a test.
- A test that captures `Console.SetOut` writes to process-global state: put it in a `[CollectionDefinition(Name, DisableParallelization = true)]` collection so no other test class prints into the capture. Prefer an internal helper that takes a `TextWriter` where the code under test allows it.
- A test that proves a counter or shared state is thread-safe: `Parallel.For` over ~10 calls never kills a `counter++` mutant. Repeat the scenario ~2000 times on fresh instances, with dedicated `Thread`s released together by a `Barrier` (not thread-pool tasks: a pool thread blocked on a barrier can starve). Check the mutant dies several runs in a row, and the real code never flakes.
- Mutation-check each rule of a selector or matcher and say which mutants survive. A comparer difference can be unobservable: `Uri.Host` is always lower-cased, so `Ordinal` vs `OrdinalIgnoreCase` on a host from a `Uri` survives every test. Keep it if the card specifies it, and note it in the handoff.
- A C# raw string `""""x""""` (four quotes) holds `x`, not `"x"`: the extra quotes are delimiters. For JSON text that must start with a quote, use a normal escaped string.
- Never delete, skip or weaken an existing test to get green. If one must change, say why in the handoff.
- A DI container disposes only singletons it has *created*: a factory-registered `TracerProvider` (or any disposable) that nothing resolved is never disposed. Resolve it once before returning the container, and test disposal without resolving it first; a test that calls `GetService` first lets the removed early resolve and an `AddSingleton(instance)` mutant survive.
- xUnit v3 with `TreatWarningsAsErrors`: xUnit1051 fails the build on any call that takes a `CancellationToken`, optional `ct:` included. Pass `TestContext.Current.CancellationToken`. A v2 test moved to v3 otherwise needs only its package set and the `<Using Include="Xunit" />` swap for `using Xunit;`.
- Red-checking a rule: with `TreatWarningsAsErrors`, mutating a condition to `if (false)` fails the build (CS0162), so no test runs. Use `&& i < 0` or similar to disable it. Re-check each mutant's own effect: a mutation on a set that is later copied into a new set with another comparer changes nothing.

## CLI commands (Spectre.Console.Cli)
- Reject bad flag combinations (both/neither of two exclusive options) in `Settings.Validate()` returning `ValidationResult.Error(...)`. Spectre prints `Error: <msg>` and exits 255, which satisfies "non-zero with a message".
- Take dependencies via the command's primary constructor. A type the container lacks (e.g. `IConfiguration`) is registered in `Program.cs` with `services.AddSingleton<IConfiguration>(configuration)`.
- **xUnit v3 on the .NET 10 SDK:** `dotnet test` refuses plain `xunit.v3` (MTP) projects unless `global.json` opts in. To share VSTest mode with the repo's xunit 2 projects use `xunit.v3.mtp-off` + `Microsoft.NET.Test.Sdk` + `xunit.runner.visualstudio` (`--filter "Category!=X"` then works as usual). A v3 project that must never run under `dotnet test <slnx>` (tests that fail on purpose) omits both Test.Sdk and the runner; it still builds as an exe, run it with `dotnet X.dll -xml out.xml` (the XML carries per-test result, failure message, output and traits).
- **xUnit v3 constructs assembly fixtures even when every test using them is filtered out.** Do nothing expensive or billable in a fixture constructor or `InitializeAsync`; run lazily on first use and cache the outcome.
- To prove behaviour of a test-framework extension, run a real test assembly out of process from a test: copy its build output to a temp dir per run, use `DOTNET_HOST_PATH` for the `dotnet` that is running the tests, and read results from the xUnit XML or trx. A revert-and-watch-it-fail check only discriminates if the scenario makes the reverted branch observable (for example a rule that depends on an unmet gate needs a scenario whose gate is actually red).

## Smoke-testing a host (console, web, eval runner)
- A foreground terminal call rejects `&`. Start a web host with `terminal(background=true)`, `sleep` then `curl` in a second call, and stop it with `kill -TERM <pid of the app binary>` (not the `dotnet run` wrapper; `pgrep -fl` lists both). Read the log with `process_manage log` for "Application is shutting down..." and no exception.
- Redirect a console or eval run to a file and print counts (`grep -c`) plus the non-JSON lines. A traced run emits one JSON line per event, which floods the context if printed.
- Run with the env vars the feature reads unset (`env -u X`), or set to fake values on a `.invalid` host to exercise the enabled path without any traffic leaving the machine.

## Code
- Async all the way (`CancellationToken` through public async APIs); no `.Result`/`.Wait()`.
- Options pattern for configuration (`IOptions<T>` + validation), not raw `IConfiguration` lookups scattered in code. New setting names are a contract with `ops`: state them in the handoff.
- Azure access via `Azure.Identity` (`DefaultAzureCredential` / managed identity), never connection strings or keys in code or appsettings.
- Observability: repos use **OpenTelemetry** (hosting, AspNetCore, Http, OTLP exporter). Add spans/metrics via the existing setup; don't add a second logging or tracing framework.
- Keep the existing architecture (e.g. MediatR handlers where the repo uses them). Don't introduce new patterns in a feature card.

## Culture-invariant output (reports, console, generated text)
- Format user-facing numbers and dates with `CultureInfo.InvariantCulture`. A Linux CI runner with `LANG` unset has the invariant culture and a dev machine is en-GB/en-US, so a bare `:P0` prints `0 %` on CI and `0%` locally; `N0` and `dd MMM` dates differ on de-DE too. Invariant `P0` puts a space before `%`: clone `CultureInfo.InvariantCulture.NumberFormat` and set `PercentPositivePattern = 1` and `PercentNegativePattern = 1`.
- Make the whole string invariant: `sb.AppendLine(CultureInfo.InvariantCulture, $"…")` or `FormattableString.Invariant($"…")`. `$"a" + $"b"` is a plain string and does not fit the `IFormatProvider` handler overload; format the culture-sensitive piece on its own first.
- Test it by rendering one object (same `RunReport`, so timestamps match) under several `CultureInfo.CurrentCulture` values: de-DE, th-TH (Buddhist calendar moves the year in dates and folder names), invariant. Compare against the reference render and assert no `\d\s%` (de-DE puts a no-break space, which `\d %` misses). Setting `CurrentCulture` inside an async test flows through awaits; restore it in `finally`.
- Don't take month names from en-GB as the reference: Linux ICU spells September `Sept`, macOS `Sep`, invariant `Sep`. Normalise that one string in the expected output and assert the invariant date explicitly.
- A format with sections (`+0;-0;0`) copies `+`/`-` as literals, so it is already culture-independent; its invariant wrapper is an unobservable mutant. `F2` is not: sv-SE prints `−1,50`.

## System.Text.Json: strict config/data files and generated schemas
- Make a hand-authored JSON file strict with `UnmappedMemberHandling = Disallow` on one shared options instance, used by the loader and the schema generator alike, so the committed JSON Schema can't drift from what loads.
- `JsonSchemaExporter` locks the options before any (de)serialization has run, so set `TypeInfoResolver = new DefaultJsonTypeInfoResolver()` explicitly or it throws "must specify a TypeInfoResolver".
- A property with a custom converter, or typed `JsonElement`, exports as `true`. Rebuild its schema in `TransformSchemaNode`, and add `null` only where the property is nullable (`JsonPropertyInfo.IsSetNullable`).
- A nested `JsonSerializer.Deserialize(ref reader)` inside a converter restarts `Path` and `LineNumber`. Rethrow with the outer path prefixed, and drop the line rather than report a wrong one. Throwing from the converter itself keeps STJ's correct line.
- Pin the generated schema with a drift test that has an env-var regen switch, and validate the shipped files against it with an independent validator. Check the validator's licence: JsonSchema.Net 9.x moved to the OSMF EULA (8.0.5 is the last MIT).

## OpenTelemetry capture (System.Diagnostics `ActivityListener`)
- Scope a listener to one run by trace id in **both** `Sample`/`SampleUsingParentId` (`options.TraceId`) and `ActivityStopped` (`activity.TraceId`): an activity is created when any listener samples it, and then every listener gets its stop. Start the run activity with `parentContext: new ActivityContext(traceId, default, Recorded)` to get a fresh trace under an ambient `Activity.Current`.
- `Activity.Stop()` puts `Activity.Current` back to the activity that was current at `Start()`, even for an explicit-context parent (`run.Parent` is that activity). A manual restore is a mutant no test kills; leave it out.
- Read tags with `GetTagItem`/`TagObjects`; `Activity.Tags` returns string values only and drops token counts.
- `Activity.Duration` is `TimeSpan.Zero` until the activity stops, so read it after `Stop()`. Pin it with a lower bound: start a `Stopwatch` after `Start()`, `Thread.Sleep(30)`, then `Assert.InRange(durationMs, elapsedMs - 1, long.MaxValue)`. Comparing the value with itself or checking only an upper bound lets `= 0` and `TotalSeconds` survive.
- Probe what an emitter really produces before asserting: dump spans from a listener (`TagObjects`, `Events`). MEAI 10.9.0 emits `execute_tool` only for `UseFunctionInvocation().UseOpenTelemetry(...)` in that order, JSON-encodes `gen_ai.tool.call.result` (a string keeps its quotes), and names the cache tag `gen_ai.usage.cache_read.input_tokens`.
- model-harness `AddStandardModelHarness`/`AddStandardChatHarness`/`AddStandardAgent` already register an `OpenTelemetryTracer`. Use `builder.WithOtelTracer(enableSensitiveData: true)`; `WithTracer(_ => new OpenTelemetryTracer(...))` on top doubles every span. Prove such claims end to end in a scratch project outside the repo, using the packages in `~/.nuget/packages` and `FakeModelClient` (no model call).
- Collect a TracerProvider's spans in a test with a `BaseProcessor<Activity>` (`OpenTelemetry` namespace) overriding `OnEnd`, added through `AddProcessor` (`OpenTelemetry.Trace`), and filter to the run's trace id: the provider samples every parallel test's spans too. Point `BaseUrl` at `http://127.0.0.1:9` for any provider built with keys.
- xUnit v2 projects have no `TestContext.Current`; pass `CancellationToken.None`. macOS `sed -i` needs `-i ''`; prefer a small Python edit.

## Database (schemas, migrations, Postgres/Supabase, EF Core)
- **Design:** the smallest schema that meets the card. Enforce invariants in the database (NOT NULL, FK, CHECK, UNIQUE) rather than only in app code. Index every foreign key and the columns that real queries filter or sort on, and no more.
- **Migrations are append-only.** Never change a migration that may already be applied anywhere. To change behaviour, add a new migration. A fix that only makes an old migration replay cleanly must be a no-op where it's already applied.
- **Safe to deploy before and after the code.** Prefer additive changes: add the column or table, deploy code that uses it, then remove the old one in a later card. Keep backfills separate from schema changes. Avoid operations that rewrite or lock a large table.
- **EF Core:** generate migrations with the repo's existing process and commit them. Read the generated `Up`/`Down` before committing. EF writes a rename as drop + add, which loses data, so fix it by hand.
- **Access control (Postgres/Supabase):**
  - Row-level security is on for every table.
  - Every INSERT/UPDATE policy has `WITH CHECK`. A policy with only `USING` doesn't check inserted rows.
  - `WITH CHECK` sees only the new row, so it can't make a column immutable (owner, billing, entitlement columns). Guard those with a trigger.
  - Take the user id from the verified JWT or `auth.uid()`, never from the request body.
- **Server-only objects:** Supabase's default privileges grant every new table and view to `anon`/`authenticated`. A server-only table or view needs RLS on with no policies, plus `REVOKE ALL ... FROM anon, authenticated`. Repeat the revoke whenever the object is dropped and recreated.
- **Functions:** a `SECURITY DEFINER` function sets `search_path`, revokes `EXECUTE` from `PUBLIC, anon, authenticated` and grants only the role that calls it.
- **Triggers on the same event fire in name order.** When order matters, encode it in the names and note it in the repo's agent file.
- **Tests:** every migration that changes behaviour or access gets a database test (pgTAP where the repo uses it). Include the negative case: another user, `anon`, or a client writing a guarded column gets refused.
- **Agents never apply migrations to shared or prod databases.** Run them locally only (`supabase db reset` / `dotnet ef database update` against local). The human applies them using the handoff.

## Vendor SDK adapters (Anthropic and similar)
- A struct options type (`Anthropic.Core.ClientOptions`) makes an `Action<Options>` hook a silent no-op: the action edits a copy. Expose `Func<Options, Options>` and use the result. Assert on the built SDK client through an `internal` seam (`SdkClient`), never on a standalone options value; red-check by discarding the hook's result in the constructor.
- Prove a timeout reaches the transport with a stub `HttpMessageHandler` (`await Task.Delay(Timeout.Infinite, ct)`) injected via the SDK's `HttpClient` option, a 4 s backstop `CancellationTokenSource`, and an assertion that the backstop did not fire. Red-check it by dropping only the timeout (`with { Timeout = null }`), not the HTTP client, so the red run never leaves the machine.
- Pin what an adapter sends with a golden request test: a capturing stub handler returns a canned response, the body is compared as sorted-key JSON (`Assert.Equal` on the canonical text gives a readable diff), and goldens are `EmbeddedResource`s. Generate the golden from one real run, then review it by hand against the API. Mutation-check it: default `max_tokens`, cache on/off, dropped system/tools, `is_error`, lone-text-as-block, first-vs-last system message.
- A body golden does not see headers. Across an SDK major, send one request through a stub handler in a throwaway file-based app per version and diff the headers: Anthropic 12 -> 13 changed `anthropic-version` (2023-06-01 -> 2026-10-21) and the key header (`X-Api-Key` -> `Authorization: Bearer`) with the body byte-identical. Report that as unverified-live and hand the user a smoke script.
- File-based probes that serialise SDK types need `#:property JsonSerializerIsReflectionEnabledByDefault=true` and `#:property PublishAot=false`, or the first `JsonSerializer` call throws "Reflection-based serialization has been disabled".
- Verify changelog snippets by extracting the fenced blocks from the release section with a script, wrapping each `// After` in a method in a scratch project that restores a `5.0.0-local.<n>` pack from a scratch feed with `NUGET_PACKAGES` pointed at scratch (so `~/.nuget/packages` never holds the version), and compiling each `// Before` that should break. For NU1605 claims, restore a csproj with the old and new `PackageReference` line.
- A scratch app outside the repo that `ProjectReference`s a repo project fails with MSB3202 on macOS when its directory sits behind the `/var` -> `/private/var` symlink: create it with `cd "$(mktemp -d)" && pwd -P`.
- The terminal tool masks text shaped like a credential in its OUTPUT (`Authorization: Bearer <x>` shows as `***`); check such a line with `grep -c`, not by reading it back.

## NuGet dependency bumps
- `dotnet list <slnx> package --outdated` is the red/green check. Its Latest column is the newest stable overall, so a held-back major stays listed; `--outdated --highest-minor` is empty once every package sits on the newest minor of its major. Also run `--vulnerable --include-transitive` and `--deprecated` (xunit 2.x reports Legacy). The output has a line per project: filter out `has no ... given the current sources` before reading it.
- Edit versions with a small Python regex over `Include="<id>" Version="<old>"` (the ids `Microsoft.Extensions.DependencyInjection` and `.Abstractions` share a prefix, so match the closing quote) and compare per-id counts with the `grep` counts from before.
- Cost of a held-back major: `rsync -a --exclude bin --exclude obj --exclude .git` the tree to scratch, bump that one version, build the tests project with `-p:TreatWarningsAsErrors=false`. The compile errors are the migration cost for the handoff.
- Read an SDK's retry/timeout change in its source at both tags (`git clone --depth 1 --branch <tag>`), not from the changelog wording. A shallow clone of someone else's repo creates no tag in yours.
- A release-notes read misses the two breaks a consumer feels most. Probe both for each runtime SDK you bump. (1) New abstract members on its public client interface (`IAnthropicClient`, `IOllamaApiClient`): a throwaway file-based app per version (`#:package X@<ver>` plus `dotnet run f.cs`) printing `typeof(I).GetProperties()` and the abstract non-accessor methods; an added member stops a consumer's own fake compiling. Count properties, not `get_`/`set_` accessors, when you quote it. (2) Every functional commit in the GitHub compare (`/compare/<old>...<new>`), not only the changelog line: for a serializer-option change like `AllowOutOfOrderMetadataProperties`, grep the library for the types it can touch (`JsonPolymorphic`, `$type`) before saying the adapter is unaffected.
- Microsoft.Extensions.* and System.Text.Json patch releases re-version every package in lockstep and the release notes list no per-package change. Use the GitHub compare API on dotnet/runtime (`/compare/v10.0.11...v10.0.14`) and filter `files` by `src/libraries/<Package>/src`.
- MinVer major bump: pack the committed tree with the new and the old MinVer (revert the one line uncommitted, then `git checkout` it) in the untagged form and with `-p:MinVerDefaultPreReleaseIdentifiers=pr.1.1`, and compare the file names. At the release tag the version is the tag; one commit later it is `<next patch>-alpha.0.1`, so a pack before committing proves nothing about MinVer.

## Handoff extras
- New/changed endpoints with their request/response shapes.
- New configuration keys and secrets the code expects, so ops can wire them.
- For a migration: what it changes, whether it's safe against the currently deployed code, and the exact deploy order (migration before or after which code or function deploy), plus rollback if it isn't purely additive.
