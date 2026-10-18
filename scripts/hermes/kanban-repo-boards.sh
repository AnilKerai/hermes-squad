#!/usr/bin/env bash
# Create one project-scoped kanban board per git repo under $SQUAD_GIT_ROOT (default ~/git),
# plus a cross-repo board, and share the project records with the dev roles.
# Re-run after adding a repo. Runs kanban_repo_boards.py inside Hermes's own runtime.
set -eu
here="$(cd "$(dirname "$0")" && pwd)"
# Resolve the Hermes root exactly as Hermes does (hermes_constants.get_default_hermes_root):
# HERMES_HOME inside ~/.hermes means ~/.hermes itself; <root>/profiles/<name> means <root>.
# A HERMES_HOME elsewhere inside ~/.hermes is refused: Hermes would silently use the live home.
resolve_root() {
  local native="$HOME/.hermes" h hp np rel
  h="${HERMES_HOME:-$native}"
  hp="$(cd "$h" 2>/dev/null && pwd -P || echo "$h")"
  np="$(cd "$native" 2>/dev/null && pwd -P || echo "$native")"
  case "$hp/" in
    "$np/"*)
      rel="${hp#"$np"}"
      case "$rel" in
        ""|/profiles/*) echo "$np" ;;
        *) echo "refusing: HERMES_HOME=$h is inside $native, and Hermes treats any path there as $native itself (the live home). Use a directory outside $native." >&2; return 1 ;;
      esac ;;
    *) if [ "$(basename "$(dirname "$hp")")" = profiles ]; then dirname "$(dirname "$hp")"; else echo "$hp"; fi ;;
  esac
}
root="$(resolve_root)" || exit 2
command -v hermes >/dev/null || { echo "hermes not found" >&2; exit 1; }
# Ask the launcher for its interpreter and source tree; hermes_bootstrap then puts its deps on sys.path.
cmd="$(hermes --print-runtime-command)"
py="$(printf '%s' "$cmd" | sed -E 's/^\["([^"]+)".*/\1/')"
src="$(printf '%s' "$cmd" | sed -n "s/.*sys\.path\.insert(0, '\([^']*\)').*/\1/p")"
[ -x "$py" ] && [ -d "$src" ] || { echo "could not resolve Hermes's Python or source tree" >&2; exit 1; }
cd "$src"
HERMES_HOME="$root" "$py" -I -c "
import os, sys
os.environ.pop('PYTHONHOME', None)
script, src = sys.argv[1], sys.argv[2]
sys.path.insert(0, src)
import hermes_bootstrap  # noqa: F401  (puts Hermes's dependencies on sys.path)
sys.argv = [script]
exec(compile(open(script).read(), script, 'exec'))
" "$here/kanban_repo_boards.py" "$src"
