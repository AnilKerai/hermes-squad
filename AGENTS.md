# AGENTS.md

This repo defines two Hermes Agent teams and installs them. `team/profiles/<role>/` holds seven Hermes profile distributions; `install.sh` installs them and wires up the kanban boards. The rest is documentation (`docs/`, `research/`). There is no application code and no build.

## Set the squad up on a machine

Run these in order. Steps marked **human** need a person (a browser sign-in, sudo, or access to private repos); stop and ask for them rather than working around them.

1. Hermes Agent v0.22 or later is installed (`hermes --version`). If not: `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`.
2. **human**: sign in to Anthropic once on the default profile: `hermes model`, or `hermes auth add anthropic --no-browser` on a headless server. The roles fall back to the default profile's credentials. Never ask for, type or store keys yourself.
3. **human** (or with their go-ahead): clone the repos the dev squad will work on into `~/git/<repo>` (folder name = board name). Override the root with `SQUAD_GIT_ROOT`.
4. Clone this repo and install: `git clone https://github.com/AnilKerai/hermes-squad ~/git/hermes-squad && cd ~/git/hermes-squad && ./install.sh --kanban`. The run ends with a wiring check. Fix every `FAIL` before going on.
5. **human** (it may need sudo on Linux): `hermes gateway install`. The gateway hosts the kanban dispatcher; without it no card is ever picked up.
6. `./install.sh --check` must end with `0 fail`. `WARN` lines name what is still missing. It spends no tokens and changes nothing.

`install.sh` skips any existing profile that wasn't installed from this repo. On a machine where these roles were built by hand (the author's), it changes nothing for them, which is intended. Don't delete or `--force` over those profiles.

Re-run after adding a repo to `~/git`: `scripts/hermes/kanban-repo-boards.sh`. To update after `git pull`: `./install.sh`.

## How cards reach the right role

Every card has an `assignee`: a profile name. The dispatcher (in the gateway) spawns that profile for it. Nothing routes by keywords or descriptions (`kanban.orchestrator_profile` is empty), so the assignee and the board are the whole routing decision:

| Work | Board | Assign to | What happens next |
|---|---|---|---|
| A change in one repo | that repo's board (slug = folder under `~/git`) | `lead`. Unassigned cards also go to `lead` (`kanban.default_assignee`) | `lead` writes `engineer` (application code) and `ops` (infrastructure) cards on the same board, each in its own worktree and branch. Finished cards go through the review lane to `reviewer`. When all children are done, `lead` checks the result against the original card |
| A change spanning repos | `cross-repo` | `lead` | Each child card sets `project=<repo>` and changes one repo |
| A product idea or research question | `research` | `pm`. Always set it explicitly, because the default assignee is `lead` | `pm` writes one `researcher` card per question plus an `analyst` card whose parents are those cards. All of them use workspace `dir:~/git/research` |

Creating a card (the [runbook](docs/runbook.md) has more):

```bash
hermes kanban --board <repo> create "<title>" --body-file card.md --assignee lead
hermes kanban --board research create "<title>" --body-file card.md --assignee pm --workspace dir:~/git/research
```

The card body is the only brief a worker gets: state the goal, constraints, and how to verify the result. Humans merge the agents' branches; no role pushes or merges.

## Changing a role

`team/` is generated from the live profiles in `~/.hermes/profiles/`. Don't edit it by hand:

1. Edit the live profile (`~/.hermes/profiles/<role>/SOUL.md`, `hermes -p <role> config set …`, its skills). Back up a SOUL before patching it (see the runbook).
2. `python3 scripts/snapshot_team.py`. It must end `scan: clean`.
3. Review `git diff`, commit, push. For a release, bump `VERSION` first, then tag `v<version>`.

## Rules

- **This repo is public.** Never commit keys, tokens, `.env`, `auth.json`, memories, sessions, emails, phone numbers or absolute home paths. The snapshot script refuses on these. Write paths as `~/…`.
- Keep `README.md`, this file and `docs/runbook.md` accurate when you change how the squad is installed or routed. Add dated lessons to `docs/04-learnings.md` and gaps to `docs/06-roadmap.md`.
- Test installer changes against a throwaway Hermes home, never the live one: `HERMES_HOME=$(mktemp -d) SQUAD_GIT_ROOT=<scratch dir with a test repo> ./install.sh --kanban --no-alias`. Don't start a gateway in that home.
