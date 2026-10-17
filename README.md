# hermes-squad

A record of how I built two AI agent teams on [Hermes Agent](https://hermes-agent.nousresearch.com/docs/) while learning AI/context engineering. It covers what the setup is, why it's shaped this way, what went wrong, and how it compares with where the industry is heading. The teams themselves are included as **installable Hermes profile distributions**, so you can run the same squad.

Started 11 Oct 2026. Hermes v0.22.x, Anthropic Claude 5.5 models.

![How a card flows through the two Hermes squads](docs/assets/squad-architecture.svg)

*Regenerate with `python3 scripts/render_architecture.py`.*

## The teams

| Role | Team | Model · thinking | Job | Guard rails |
|---|---|---|---|---|
| `lead` | dev | Opus 5.5 · xhigh | Turns a goal into cards with decisions, acceptance criteria and verify commands, routes each card to `engineer` or `ops`, and checks finished work against the original goal | No terminal or web; plans, never implements |
| `engineer` | dev | Sonnet 5.5 · xhigh | Implements one card in a git worktree (.NET / ASP.NET Core, Blazor, MAUI, React + TS), adds tests, keeps `AGENTS.md`/`CLAUDE.md` current, requests review | Never pushes or merges; cloud and cluster CLIs denied |
| `ops` | dev | Sonnet 5.5 · high | Bicep/ARM for Azure PaaS, GitHub Actions, Dockerfiles, k8s. Validates with build, lint and `what-if`, and lists the exact deploy steps for the human | Validates only: mutating `az`/`kubectl`/`helm`/`terraform`, pipeline runs, secrets and `git push` are denied at tool level |
| `reviewer` | dev | Opus 5.5 · xhigh | Re-runs tests and validation itself, checks the diff against the card, gives one verdict: approve, request changes, or escalate | Never edits code; same deny list as `ops` |
| `pm` | research | Opus 5.5 · xhigh | Works out the decision an idea should inform and frames 2–5 research questions as researcher cards, plus an analyst card that depends on them | No terminal or web; never does the research itself |
| `researcher` | research | Sonnet 5.5 · medium | Answers one question from primary sources, with every claim cited through the `grounded-citations` ledger | Never fabricates sources |
| `analyst` | research | Opus 5.5 · xhigh | Spot-checks the load-bearing claims and writes a skimmable decision brief | Verifies, doesn't redo the research |

Work starts as a card on a repo board for `lead`, or as an idea on the `research` board for `pm`. The lead or pm breaks it into child cards. Finished implementation cards go through the review lane to `reviewer`. When all its children are done, the lead or pm wakes up and judges the result against the original goal. A human merges every branch.

## Install the squad

```bash
# 1. Hermes Agent (v0.22 or later)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# 2. Sign in to Anthropic once on the default profile (the roles fall back to its credentials)
hermes model                     # choose Anthropic; or set ANTHROPIC_API_KEY

# 3. The squad
git clone https://github.com/AnilKerai/hermes-squad ~/git/hermes-squad
cd ~/git/hermes-squad
./install.sh --kanban            # seven roles + dispatcher settings, boards and worktree cron
hermes gateway install           # run the dispatcher as a background service (systemd or launchd)
```

| `./install.sh` option | What it does |
|---|---|
| *(roles…)* | Install only these roles, e.g. `./install.sh lead engineer reviewer` |
| `--kanban` | Applies [`team/kanban.yaml`](team/kanban.yaml) to the default profile (`default_assignee: lead`, 4 cards in flight, review lane on, no auto-decompose). It also creates the `research` board, one project-scoped board per git repo under `~/git` (override with `SQUAD_GIT_ROOT`) plus a `cross-repo` board, and a no-model cron that frees finished cards' worktrees every 5 minutes so their branches behave like normal branches |
| `--langfuse` | Installs and enables the official `langfuse` plugin per role. Fill in each profile's `.env` (the installer writes a `.env.EXAMPLE`); `HERMES_LANGFUSE_ENV=hermes-<role>` keeps cost grouped by role |
| `--no-alias` | Skips the `lead`, `engineer`, … shell wrappers |
| `--force-config` | On update, also resets each role's `config.yaml` to this repo's version |

`./install.sh` never overwrites a profile you built by hand. If a profile with the same name exists and wasn't installed from a distribution, it is skipped. To update later, run `git pull && ./install.sh`. That replaces each role's `SOUL.md`, skills and manifest and keeps your `config.yaml` (model tweaks survive). It never touches memories, sessions, `.env` or auth. Updating starts with `git pull` because `hermes profile install` needs `distribution.yaml` at a repo's root: each role is installed from its folder in your clone, and `hermes profile update` re-reads that folder.

**Before you run it:**

- **Approvals are off in every role** (`approvals.mode: off`) so that unattended kanban workers don't stall. The `approvals.deny` lists are the guard rail; Hermes enforces them even with approvals off. Run the squad on a machine or VM where that's acceptable. `hermes -p <role> config set approvals.mode smart` lets a cheap model approve low-risk commands instead.
- **These roles are tuned to my setup:** repos live in `~/git` and research output in `~/git/research`. The `*-conventions` and `azure-paas-iac` skills describe my stack (xUnit + Shouldly + NSubstitute, MudBlazor, TanStack Query + Supabase, Bicep modules). Each repo's `AGENTS.md` overrides them. Fork the repo and replace them with your own.
- **Models:** change a role's model with `hermes -p <role> config set model.default <model>`.

## Read in this order

| Doc | What it answers |
|---|---|
| [01 Architecture](docs/01-architecture.md) | What the squads are, how a card flows, what runs where |
| [02 Context engineering](docs/02-context-engineering.md) | What each agent sees, which layer each kind of information lives in, and the rules learned |
| [03 Industry alignment](docs/03-industry-alignment.md) | How this setup compares with current practice and research, with sources: where it aligns, where it lags |
| [04 Learnings](docs/04-learnings.md) | Dated lessons, each with the evidence and the change it led to |
| [05 Metrics](docs/05-metrics.md) | Scorecard snapshots and how to recompute them |
| [06 Roadmap](docs/06-roadmap.md) | Known gaps, ranked, with status |
| [Runbook](docs/runbook.md) | Day-to-day operation: new cards, blocks, pausing, merging, adding repos and roles, moving machines |

## What's in the repo

- `team/profiles/<role>/` holds one **Hermes profile distribution** per role: `distribution.yaml`, `SOUL.md`, the full `config.yaml` (model, thinking level, toolsets, deny list), `profile.yaml` (the routing description) and the role's own skills. Next to them, `team/kanban.yaml` has the dispatcher settings and `team/skill-drift.md` shows which role holds which version of each skill.
- `team/` is **generated** from the live profiles in `~/.hermes/profiles/` by `python3 scripts/snapshot_team.py`. Re-run it after any role change and commit, so every context change is a dated, reviewable diff. The script never reads `.env`, auth, memories or sessions. It rewrites the home directory to `~` and refuses to finish if the repo contains anything that looks like a key, an email, a phone number or an absolute home path.
- `install.sh` installs or updates the roles from this clone.
- `scripts/hermes/` holds the helper scripts the setup runs from `~/.hermes/scripts/` (board-per-repo setup, worktree release, digest, dashboard, Langfuse env sync).
- `research/` holds the research team's two briefs that this design draws on.

**Source of truth today:** the live files in `~/.hermes/profiles/`. This repo snapshots them and can install them elsewhere. Syncing changes *into* the live profiles from the repo is on the roadmap.

## License

[MIT](LICENSE)
