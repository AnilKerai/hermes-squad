#!/usr/bin/env python3
"""Compare two eval-harness result runs, case by case.

Usage:
  compare_eval_runs.py OLD_RUN_DIR NEW_RUN_DIR [--labels OLD NEW] [--log STDOUT_LOG ...]

A run dir is <evals>/bin/Debug/<tfm>/results/<timestamp>_<dataset>_<version>/ holding
report.md, benchmark.json and <case>/agent/run_NN/{grading,timing,trace}.json. trace.json
carries metadata.agent_status, metadata.failure_reason,
metadata.sensor_interventions[{sensor_name, hook_point, reason}], tool_calls[] and
cost.total_tokens.

Prints:
  1. the report.md diff with timing/token/cost lines and sections removed
     ("identical" = same verdicts, pass rates and readiness);
  2. per case and run: status, tool-call count, tokens, interventions, failure reason;
  3. token totals and any case whose final status changed.
--log summarises an eval console's stdout when its tracer prints one JSON event per line
(evt = trace_completed / model_call / sensor_result).
"""
import argparse
import collections
import difflib
import json
import os
import re

NOISE = re.compile(r"started|duration|tokens|cost|results:|\d{4}-\d\d-\d\d", re.I)
NOISY_SECTION = re.compile(r"cost|timing|duration", re.I)


def report_lines(run_dir):
    path = os.path.join(run_dir, "report.md")
    if not os.path.exists(path):
        return None
    kept, skipping = [], False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#"):
                skipping = bool(NOISY_SECTION.search(line))
            if skipping or NOISE.search(line):
                continue
            kept.append(line)
    return kept


def load_traces(run_dir):
    traces = {}
    for case in sorted(os.listdir(run_dir)):
        agent_dir = os.path.join(run_dir, case, "agent")
        if not os.path.isdir(agent_dir):
            continue
        for run in sorted(os.listdir(agent_dir)):
            path = os.path.join(agent_dir, run, "trace.json")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    traces[(case, run)] = json.load(f)
    return traces


def summarise(trace):
    meta = trace.get("metadata") or {}
    interventions = collections.Counter(
        f"{s.get('sensor_name', '?')}@{s.get('hook_point', '?')}"
        for s in meta.get("sensor_interventions") or []
        if isinstance(s, dict))
    return {
        "status": str(meta.get("agent_status")),
        "tools": len(trace.get("tool_calls") or []),
        "tokens": (trace.get("cost") or {}).get("total_tokens"),
        "interventions": dict(interventions),
        "failure": meta.get("failure_reason") or "",
    }


def summarise_log(path):
    events = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("{"):
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    by_evt = collections.defaultdict(list)
    for e in events:
        by_evt[e.get("evt")].append(e)
    count = collections.Counter
    print(f"== {path} ==")
    print("  statuses     :", dict(count((e.get("status"), e.get("failureReason")) for e in by_evt["trace_completed"])))
    print("  stop reasons :", dict(count(e.get("stopReason") for e in by_evt["model_call"])))
    print("  interventions:", dict(count(f"{e.get('sensor')}@{e.get('hookPoint')}"
                                       for e in by_evt["sensor_result"] if e.get("intervene"))))
    print("  sensor errors:", sum(1 for e in by_evt["sensor_result"] if e.get("error")))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("old")
    parser.add_argument("new")
    parser.add_argument("--labels", nargs=2, default=["old", "new"])
    parser.add_argument("--log", nargs="*", default=[], help="eval console stdout logs to summarise")
    args = parser.parse_args()
    old_label, new_label = args.labels

    old_report, new_report = report_lines(args.old), report_lines(args.new)
    print("== report.md (timing/token/cost removed) ==")
    if old_report is None or new_report is None:
        print("  report.md missing in one run")
    else:
        diff = list(difflib.unified_diff(old_report, new_report, old_label, new_label, lineterm="", n=0))
        print("\n".join(diff) if diff else "  identical")

    old_traces, new_traces = load_traces(args.old), load_traces(args.new)
    keys = sorted(old_traces.keys() | new_traces.keys())
    width = max([len(case) for case, _ in keys] + [4])
    print("\n== per case ==")
    print(f"{'case':{width}} {'run':6} {'ver':10} {'status':14} {'tools':>5} {'tokens':>8}  interventions / failure")
    totals = collections.Counter()
    for key in keys:
        for label, traces in ((old_label, old_traces), (new_label, new_traces)):
            if key not in traces:
                print(f"{key[0]:{width}} {key[1]:6} {label:10} (missing)")
                continue
            s = summarise(traces[key])
            totals[label] += s["tokens"] or 0
            tokens = "?" if s["tokens"] is None else s["tokens"]
            print(f"{key[0]:{width}} {key[1]:6} {label:10} {s['status']:14} {s['tools']:>5} {tokens:>8}  "
                  f"{s['interventions']} {s['failure']}")
    print("\ntotal tokens:", ", ".join(f"{label}={totals[label]}" for label in (old_label, new_label)))
    changed = [f"{c}/{r}" for c, r in keys
               if (c, r) in old_traces and (c, r) in new_traces
               and summarise(old_traces[(c, r)])["status"] != summarise(new_traces[(c, r)])["status"]]
    print("status changes:", ", ".join(changed) if changed else "none")

    for path in args.log:
        print()
        summarise_log(path)


if __name__ == "__main__":
    main()
