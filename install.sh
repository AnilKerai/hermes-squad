#!/usr/bin/env bash
# Install or update the squad's Hermes profiles from this clone.
#
#   ./install.sh                  install every role; roles already installed from here are updated
#   ./install.sh lead engineer    only these roles
#   ./install.sh --kanban         also set up the dispatcher: kanban.yaml settings on the default
#                                 profile, a research board, one board per repo in ~/git (override
#                                 with SQUAD_GIT_ROOT), and a 5-minute cron that frees finished
#                                 cards' worktrees
#   ./install.sh --langfuse       also install and enable the official langfuse plugin per role
#   ./install.sh --no-alias       don't create `lead`, `engineer`, ... shell wrappers
#   ./install.sh --force-config   on update, also reset each role's config.yaml to this repo's
#   ./install.sh --check          only check the wiring (roles, skills, settings, boards, gateway);
#                                 changes nothing. Also runs at the end of every install.
#
# Update later with: git pull && ./install.sh
# A profile that already exists but was not installed from a distribution is never touched.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
all=(lead engineer ops reviewer pm researcher analyst)
alias_flag=(--alias); update_flags=(-y); kanban=0; langfuse=0; check=0; roles=()
for a in "$@"; do
  case "$a" in
    --kanban) kanban=1 ;;
    --check) check=1 ;;
    --langfuse) langfuse=1 ;;
    --no-alias) alias_flag=() ;;
    --force-config) update_flags+=(--force-config) ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    -*) echo "unknown option: $a" >&2; exit 2 ;;
    *) roles+=("$a") ;;
  esac
done
[ ${#roles[@]} -eq 0 ] && roles=("${all[@]}")
command -v hermes >/dev/null || { echo "hermes not found: install Hermes Agent first" >&2; exit 1; }
root="${HERMES_HOME:-$HOME/.hermes}"
if [ "$check" = 1 ]; then exec bash "$here/scripts/check_squad.sh" "${roles[@]}"; fi

for p in "${roles[@]}"; do
  src="$here/team/profiles/$p"
  [ -f "$src/distribution.yaml" ] || { echo "no such role: $p" >&2; exit 2; }
  if [ -d "$root/profiles/$p" ]; then
    if [ -f "$root/profiles/$p/distribution.yaml" ]; then
      echo "== updating $p"
      hermes profile update "$p" "${update_flags[@]}"
    else
      echo "== skipping $p: a hand-built profile with this name already exists"
      continue
    fi
  else
    echo "== installing $p"
    hermes profile install "$src" -y ${alias_flag[@]+"${alias_flag[@]}"}
  fi
  # Seed Hermes's bundled skills now (the roles use sdlc-review and grounded-citations) rather than
  # waiting for the role's first run. Same sync `hermes profile create` runs.
  HERMES_HOME="$root/profiles/$p" hermes --run-module tools.skills_sync >/dev/null \
    || echo "   bundled skill sync failed for $p (it will run on the role's first start)" >&2
  if [ "$langfuse" = 1 ]; then
    hermes -p "$p" plugins install langfuse --enable --yes-deps || echo "   langfuse plugin install failed for $p" >&2
  fi
done

if [ "$kanban" = 1 ]; then
  echo "== kanban settings on the default profile"
  grep -E '^[a-z_.]+:' "$here/team/kanban.yaml" | while IFS= read -r line; do
    key="${line%%:*}"; value="${line#*: }"; value="${value%%  #*}"; value="${value#\"}"; value="${value%\"}"
    hermes config set "$key" "$value" >/dev/null && echo "   $key = ${value:-(empty)}"
  done
  echo "== research board (~/git/research)"
  mkdir -p "$HOME/git/research"
  # Count matches instead of `cmd | grep -q`: with pipefail, grep -q exiting early fails the pipeline.
  boards="$(hermes kanban boards list 2>/dev/null || true)"
  if [ "$(awk '{print ($1 == "●" ? $2 : $1)}' <<<"$boards" | grep -cx research)" -gt 0 ]; then
    echo "   exists"
  else
    hermes kanban boards create research --name Research --default-workdir "$HOME/git/research" \
      --description "Product & research team (pm, researcher, analyst). Assign new ideas to pm. Output lives in ~/git/research."
  fi
  echo "== one board per repo"
  mkdir -p "$root/scripts"
  cp "$here/scripts/hermes/kanban_release_worktrees.py" "$root/scripts/"
  sh "$here/scripts/hermes/kanban-repo-boards.sh"
  echo "== worktree release cron"
  jobs="$(hermes cron list 2>/dev/null || true)"
  if [ "$(grep -c "Release finished kanban worktrees" <<<"$jobs")" -gt 0 ]; then
    echo "   exists"
  else
    hermes cron create "every 5m" --name "Release finished kanban worktrees" \
      --script kanban_release_worktrees.py --no-agent --deliver local
  fi
  echo "Restart the gateway so the dispatcher picks this up: hermes gateway restart (or: hermes gateway install)"
fi

echo
echo "== checking the wiring"
bash "$here/scripts/check_squad.sh" "${roles[@]}" || { echo "Fix the FAIL lines above, then: ./install.sh --check" >&2; exit 1; }
echo "Clear any WARN lines (sign-in, gateway, repos), then re-check with: ./install.sh --check"
