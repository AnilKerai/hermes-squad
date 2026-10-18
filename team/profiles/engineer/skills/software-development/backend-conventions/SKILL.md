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

## Tests
- Stack in use: **xUnit** (v2 and v3 both appear; match the project), **Shouldly** assertions, **NSubstitute** mocks, **AutoFixture** (`AutoFixture.Xunit3` / `AutoNSubstitute`) for test data. Don't introduce Moq, FluentAssertions or NUnit.
- Test behaviour through public seams; for APIs prefer `WebApplicationFactory` integration tests over mocking the framework.
- Never delete, skip or weaken an existing test to get green. If one must change, say why in the handoff.

## Code
- Async all the way (`CancellationToken` through public async APIs); no `.Result`/`.Wait()`.
- Options pattern for configuration (`IOptions<T>` + validation), not raw `IConfiguration` lookups scattered in code. New setting names are a contract with `ops`: state them in the handoff.
- Azure access via `Azure.Identity` (`DefaultAzureCredential` / managed identity), never connection strings or keys in code or appsettings.
- Observability: repos use **OpenTelemetry** (hosting, AspNetCore, Http, OTLP exporter). Add spans/metrics via the existing setup; don't add a second logging or tracing framework.
- Keep the existing architecture (e.g. MediatR handlers where the repo uses them). Don't introduce new patterns in a feature card.

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

## Handoff extras
- New/changed endpoints with their request/response shapes.
- New configuration keys and secrets the code expects, so ops can wire them.
- For a migration: what it changes, whether it's safe against the currently deployed code, and the exact deploy order (migration before or after which code or function deploy), plus rollback if it isn't purely additive.
