#!/bin/sh
# Re-run after adding a repo to ~/git: creates its project + scoped board, re-syncs projects to team profiles.
PY=$(ls -d "$HOME"/.hermes/tools/python-3.14*/bin/python3 | head -1)
cd "$HOME/.hermes/hermes-agent" && HERMES_HOME="$HOME/.hermes" "$PY" -c "import sys; sys.path.insert(0,'.'); exec(open('$HOME/.hermes/scripts/kanban_repo_boards.py').read())"
