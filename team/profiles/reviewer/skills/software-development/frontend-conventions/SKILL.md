---
name: frontend-conventions
description: "Use when implementing UI work: Blazor, MAUI, or React Native (Expo)."
version: 0.1.0
metadata:
  hermes:
    tags: [blazor, mudblazor, maui, react-native, expo, frontend, testing]
---

# Frontend conventions

Defaults for this user's UI work. **The repo's AGENTS.md/CLAUDE.md and existing components win over this file.** Find the nearest existing screen or component and copy its patterns. Grows from reviewer findings; keep it short.

## Blazor (ballistic, bh-app-thread-portal)
- Component library: **MudBlazor**. Use its components and theme; don't hand-roll equivalents or add a second UI library.
- Component tests with **bUnit** (plus the repo's xUnit/Shouldly stack). Test rendered behaviour (markup, events, state changes), not private methods.
- Keep logic out of `.razor` markup: put it in code-behind or services so it's testable (bh-app-thread-portal has a separate `Tests.Ui.Logic` project for this).
- Respect render mode and auth as the app sets them up. Call APIs through the existing typed clients/services.

## .NET MAUI (ballistic)
- Follow the existing MVVM structure. Platform-specific code goes behind an interface. Note in the handoff which platforms you actually built (Mac host: typically maccatalyst/iOS).

## React Native + Expo (plan-my-party)
- TypeScript strict; `npm run typecheck` (`tsc --noEmit`) must pass.
- Data via **TanStack Query** and the existing **Supabase** client; forms via **react-hook-form + zod**; navigation via React Navigation. Reuse these, don't add alternatives.
- Secrets never go in the bundle. Only the Supabase anon key and public config belong in the client; anything privileged belongs server-side (RLS policies or edge functions).
- Check the change runs with `expo start --web` where possible, and say in the handoff what you could and couldn't exercise (native modules, push, purchases).

## All UI
- Accessibility basics: labels on inputs and icon buttons, keyboard and screen-reader reachable, no colour-only meaning.
- Loading, empty and error states for anything that fetches data.
- Handoff: which screens changed, how you verified them (tests, run commands), and anything only a human can check visually.
