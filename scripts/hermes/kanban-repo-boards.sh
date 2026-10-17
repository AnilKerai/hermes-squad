#!/bin/sh
# Create one project-scoped kanban board per git repo under $SQUAD_GIT_ROOT (default ~/git),
# plus a cross-repo board, and share the project records with the dev roles.
# Re-run after adding a repo. Runs kanban_repo_boards.py inside Hermes's own runtime.
set -eu
here="$(cd "$(dirname "$0")" && pwd)"
root="${HERMES_HOME:-$HOME/.hermes}"
case "$root" in */profiles/*) root="${root%/profiles/*}" ;; esac  # run from inside a role: use the Hermes root
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
