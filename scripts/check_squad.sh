#!/usr/bin/env bash
# Check that the squad is wired so the right role picks up the right card. Spends no tokens and
# changes nothing. Run via `./install.sh --check` (install.sh also runs it at the end).
#
#   FAIL  routing is broken: a card would sit unclaimed, go to the wrong role, or lack its skills
#   WARN  routing is wired but something the human must do is missing (sign-in, gateway, repos)
#
# Usage: scripts/check_squad.sh [role ...]     exit 1 if any FAIL
set -uo pipefail
roles=("$@"); [ ${#roles[@]} -eq 0 ] && roles=(lead engineer ops reviewer pm researcher analyst)
root="${HERMES_HOME:-$HOME/.hermes}"
case "$root" in */profiles/*) root="${root%/profiles/*}" ;; esac
git_root="${SQUAD_GIT_ROOT:-$HOME/git}"
fails=0; warns=0
pass() { echo "  PASS  $*"; }
fail() { echo "  FAIL  $*"; fails=$((fails + 1)); }
warn() { echo "  WARN  $*"; warns=$((warns + 1)); }
has() { [ "$(grep -c -- "$2" <<<"$1")" -gt 0 ]; }   # has <text> <pattern>, pipefail-safe

echo "Roles (each card's assignee must be an installed profile with the kanban toolset)"
for p in "${roles[@]}"; do
  if [ ! -d "$root/profiles/$p" ]; then fail "$p: profile not installed (cards assigned to $p would never be claimed)"; continue; fi
  [ -f "$root/profiles/$p/distribution.yaml" ] || warn "$p: hand-built profile, not installed from this repo"
  tools="$(HERMES_HOME="$root" hermes -p "$p" config get platform_toolsets.cli 2>/dev/null)"
  model="$(HERMES_HOME="$root" hermes -p "$p" config get model.default 2>/dev/null | tail -1)"
  need=()
  case "$p" in
    engineer) need=(backend-conventions frontend-conventions) ;;
    ops) need=(azure-paas-iac) ;;
    reviewer) need=(sdlc-review backend-conventions frontend-conventions azure-paas-iac) ;;
    researcher|analyst) need=(grounded-citations) ;;
  esac
  # Check the files: `hermes skills list` truncates long names.
  missing=(); for s in ${need[@]+"${need[@]}"}; do
    ls "$root/profiles/$p/skills/"*/"$s/SKILL.md" >/dev/null 2>&1 || missing+=("$s"); done
  if ! has "$tools" "- kanban"; then fail "$p: no kanban toolset, so it can't read or finish cards"
  elif [ -z "$model" ] || [ "$model" = "null" ]; then fail "$p: no model set"
  elif [ ${#missing[@]} -gt 0 ]; then fail "$p: missing skills its cards pin or its SOUL names: ${missing[*]}"
  else pass "$p ($model)"; fi
done

echo "Dispatcher settings (default profile)"
get() { HERMES_HOME="$root" hermes config get "$1" 2>/dev/null | tail -1; }
[ "$(get kanban.default_assignee)" = "lead" ] && pass "unassigned cards go to lead" || fail "kanban.default_assignee is not lead"
case "$(get kanban.orchestrator_profile)" in ""|null|"''") pass "no global orchestrator (each lead owns its cards)" ;;
  *) fail "kanban.orchestrator_profile is set; lead and pm would not own their own cards" ;; esac
[ "$(get kanban.review_dispatch)" = "true" ] && pass "review lane on (finished work goes to reviewer)" || fail "kanban.review_dispatch is off: finished cards skip review"
[ "$(get gateway.multiplex_profiles)" = "true" ] && pass "one gateway serves every role" || warn "gateway.multiplex_profiles is off: run a gateway per role, or apply team/kanban.yaml"

echo "Boards (one per repo so cards get that repo's worktree)"
boards="$(HERMES_HOME="$root" hermes kanban boards list 2>/dev/null | awk '{print ($1 == "●" ? $2 : $1)}')"
for b in research cross-repo; do has "$boards" "^$b\$" && pass "board $b" || fail "board $b missing (./install.sh --kanban)"; done
repos=0
for repo in "$git_root"/*/; do
  [ -d "$repo/.git" ] || continue; repos=$((repos + 1)); slug="$(basename "$repo")"
  has "$boards" "^$slug\$" || warn "repo $slug has no board, so it can't take cards yet (scripts/hermes/kanban-repo-boards.sh)"
done
[ "$repos" -gt 0 ] && pass "$repos repo(s) under $git_root checked" || warn "no git repos under $git_root yet: clone them, then run scripts/hermes/kanban-repo-boards.sh"
[ -d "$HOME/git/research" ] && pass "research output dir ~/git/research" || warn "~/git/research missing"
has "$(HERMES_HOME="$root" hermes cron list 2>/dev/null)" "Release finished kanban worktrees" && pass "worktree release cron" || warn "worktree release cron missing (./install.sh --kanban)"

echo "Things only the human can do"
if has "$(HERMES_HOME="$root" hermes auth list 2>/dev/null)" "anthropic" || [ -n "${ANTHROPIC_API_KEY:-}" ]; then pass "Anthropic credentials"
else warn "no Anthropic credentials: hermes model (or hermes auth add anthropic --no-browser on a server)"; fi
if has "$(HERMES_HOME="$root" hermes gateway status 2>&1)" "PID"; then pass "gateway running (it hosts the dispatcher)"
else warn "gateway not running, so nothing gets dispatched: hermes gateway install"; fi

echo
echo "$fails fail, $warns warn"
[ "$fails" -eq 0 ]
