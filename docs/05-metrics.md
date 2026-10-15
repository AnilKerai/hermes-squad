# 05 Metrics

## Snapshot: 11–15 Oct 2026

| Measure | Value |
|---|---|
| Cards | 65 (53 done, 9 parked in Triage, 1 running, 2 archived) |
| Failures | 0 crashed, 0 given up, 0 missing handoffs; 1 research card timed out and succeeded on retry |
| Implementation cards reviewed | 20; 19 approved first time, 1 sent back for a real defect (fixed in round 2) |
| Approvals citing checks the reviewer ran | 19/19 |
| Review skipped | 1 (engineer `kanban_complete` while a parent waited; SOUL fixed 15 Oct) |
| Escalations needing the human | 4: 2 instruction-file protection (fixed by config), 2 genuine version-conflict decisions |
| Implementation card duration | 2–46 min |
| Research card duration | 14–70 min |
| Cost, API-equivalent, by Langfuse day (11–15 Oct) | $62.81, $81.38, $46.75, $7.87, $25.99 = **$227.79** (all Hermes profiles, including the human's own chats) |
| Cost per role, 11–15 Oct (Langfuse `totalCost`) | researcher $72.18 · default (chat) $53.71 · analyst $28.07 · lead $27.30 · engineer $23.76 · reviewer $16.07 · pm $6.62 · ops $0.08 |
| Unit cost | ~$4 per shipped dev feature (lead + engineer + reviewer + ops $67 / ~17 features); ~$53 per research brief (researcher + analyst + pm $107 / 2) |
| Average context per call | researcher 233K · analyst 278K · engineer 170K · reviewer 115K · lead 105K |

## How to recompute

**Board outcomes**: read every board DB, read-only:
```bash
for db in ~/.hermes/kanban.db ~/.hermes/kanban/boards/*/kanban.db; do
  sqlite3 -readonly "$db" "select profile, outcome, count(*) from task_runs group by 1,2"; done
```
- Review rounds = number of `changes_requested` + 1 per card.
- Review skipped = an engineer or ops `completed` run on a card with no `review_requested`.
- Real escalations = `blocked` events of kind `needs_input` or `capability`. Untyped blocks from `initial_status` are cards the human parked.

**Cost per role**: Langfuse v2 metrics API, one request:
```
GET /api/public/v2/metrics?query={"view":"observations",
  "metrics":[{"measure":"totalCost","aggregation":"sum"},{"measure":"count","aggregation":"count"}],
  "dimensions":[{"field":"environment"}],
  "filters":[{"column":"type","operator":"=","value":"GENERATION","type":"string"},
             {"column":"environment","operator":"starts with","value":"hermes","type":"string"}],
  "fromTimestamp":"…","toTimestamp":"…"}
```

## Not yet measured (see roadmap)

- Cost per *merged* card: traces aren't tagged with card id.
- Whether a SOUL/skill change helped: no regression set; context versions not recorded against runs.
- The research cost fixes, and Haiku vs Sonnet for researchers.
