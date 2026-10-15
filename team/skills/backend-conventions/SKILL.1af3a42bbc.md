---
name: backend-conventions
description: "Use when implementing .NET backend work: APIs, services, data, tests."
version: 0.1.0
metadata:
  hermes:
    tags: [dotnet, aspnetcore, backend, testing]
---

# Backend conventions (.NET / ASP.NET Core)

Defaults for this user's backend work. **The repo's AGENTS.md/CLAUDE.md and its existing code win over this file.** Match what's there before applying anything below. Grows from reviewer findings; keep it short.

## Build & quality gates
- Repos use `<Nullable>enable</Nullable>`, and often `TreatWarningsAsErrors`. Introduce zero new warnings; don't suppress with `#pragma`/`NoWarn` unless the card allows it.
- Central package management (`Directory.Packages.props`) where present: add versions there, never in a csproj.
- Run the repo's own build + test commands, and report pass counts per test project in the handoff.

## Tests
- Stack in use: **xUnit** (v2 and v3 both appear; match the project), **Shouldly** assertions, **NSubstitute** mocks, **AutoFixture** (`AutoFixture.Xunit3` / `AutoNSubstitute`) for test data. Don't introduce Moq, FluentAssertions or NUnit.
- Test behaviour through public seams; for APIs prefer `WebApplicationFactory` integration tests over mocking the framework.
- Never delete, skip or weaken an existing test to get green. If one must change, say why in the handoff.

## Code
- Async all the way (`CancellationToken` through public async APIs); no `.Result`/`.Wait()`.
- Options pattern for configuration (`IOptions<T>` + validation), not raw `IConfiguration` lookups scattered in code. New setting names are a contract with `ops`: state them in the handoff.
- Azure access via `Azure.Identity` (`DefaultAzureCredential` / managed identity), never connection strings or keys in code or appsettings.
- Observability: repos use **OpenTelemetry** (hosting, AspNetCore, Http, OTLP exporter). Add spans/metrics via the existing setup; don't add a second logging or tracing framework.
- EF Core (Npgsql where used): migrations via the repo's existing process. Include the generated migration in the commit and mention it in the handoff.
- Keep the existing architecture (e.g. MediatR handlers where the repo uses them). Don't introduce new patterns in a feature card.

## Handoff extras
- New/changed endpoints with their request/response shapes.
- New configuration keys and secrets the code expects, so ops can wire them.
