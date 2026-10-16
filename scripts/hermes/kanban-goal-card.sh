#!/usr/bin/env bash
# Create a goal-mode kanban card: the worker loops (same session) until an
# auxiliary judge agrees the card's acceptance criteria are met, or the turn
# budget runs out (then the card blocks for a human).
#
# Usage:
#   kanban-goal-card.sh <board> "<title>" <body-file> [max-turns=20] [assignee=engineer] [extra hermes kanban create args...]
#
# Example:
#   kanban-goal-card.sh katas "Katas: production code fully covered" card.md 15
#
# The judge reads ONLY the title and body, so write the body as explicit
# acceptance criteria, each with a Verify command and an exceptions clause.
# Use goal mode for "keep going until X is true" work with a machine-checkable
# end state; skip it for normal feature cards (the review lane is the check).
set -euo pipefail

if [[ $# -lt 3 ]]; then
  sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
fi

board=$1 title=$2 body=$3
turns=${4:-20}
assignee=${5:-engineer}
shift $(( $# < 5 ? $# : 5 ))

[[ -f "$body" ]] || { echo "body file not found: $body" >&2; exit 1; }
key="goal-$(printf '%s|%s' "$board" "$title" | shasum | cut -c1-12)"

hermes kanban --board "$board" create "$title" \
  --body-file "$body" \
  --assignee "$assignee" \
  --goal --goal-max-turns "$turns" \
  --idempotency-key "$key" \
  --json "$@"
