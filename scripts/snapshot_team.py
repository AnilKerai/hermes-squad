#!/usr/bin/env python3
"""Snapshot the live Hermes squad definition into this repo's team/ folder.

Reads each profile's role-shaping settings through `hermes config get` (Hermes's own
resolution), copies SOUL.md and agent-made (local) skills, and writes kanban settings.
Never reads .env, auth.json or memories, so no secrets or personal data land in git.

Usage:  python3 scripts/snapshot_team.py      # then: git diff team/
Re-run after any SOUL/config/skill change so the change shows up as a reviewable diff.
"""
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEAM = REPO / "team"
HOME = Path.home() / ".hermes"
PROFILES = ["lead", "engineer", "ops", "reviewer", "pm", "researcher", "analyst"]
KEYS = [
    "model.default", "model.provider", "agent.reasoning_effort",
    "compression.threshold_tokens", "auxiliary.compression.model",
    "security.protected_instruction_files", "approvals.deny", "platform_toolsets.cli",
    "skills.write_approval", "memory.write_approval",
]
KANBAN_KEYS = ["orchestrator_profile", "default_assignee", "max_in_progress", "auto_decompose",
               "review_dispatch", "failure_limit", "dispatch_interval_seconds"]


def get(profile: str, key: str) -> str:
    out = subprocess.run(["hermes", "-p", profile, "config", "get", key],
                         capture_output=True, text=True).stdout
    lines = [l for l in out.splitlines() if not l.startswith(("⚠", "  Did you mean", "  (Use"))]
    return "\n".join(lines).rstrip()


def description(profile: str) -> str:
    """Routing description from the profile's profile.yaml (folded YAML string, read without a YAML lib)."""
    path = HOME / "profiles" / profile / "profile.yaml"
    if not path.exists():
        return ""
    m = re.search(r"^description:\s*(['\"]?)(.*?)\1\s*$(?=\n\S|\Z)", path.read_text(), re.M | re.S)
    return re.sub(r"\s*\n\s*", " ", m.group(2)).replace("''", "'").replace('"', "'") if m else ""


def block(key: str, value: str) -> str:
    if "\n" in value or value.startswith("- "):
        body = "\n".join("  " + l for l in value.splitlines())
        return f"{key}:\n{body}"
    return f"{key}: {value or 'null'}"


def local_skills(home: Path, profile: str) -> dict:
    """Agent-made skills: rows marked 'local' in `hermes skills list` (names may be truncated with …)."""
    out = subprocess.run(["hermes", "-p", profile, "skills", "list"], capture_output=True, text=True).stdout
    prefixes = [cells[1].strip().rstrip("…") for l in out.splitlines()
                if "│ local" in l and len(cells := l.split("│")) > 2]
    found = {}
    for skill_md in (home / "skills").glob("*/*/SKILL.md"):
        name = skill_md.parent.name
        if any(pre and name.startswith(pre) for pre in prefixes):
            found[name] = skill_md
    return found


def main():
    if TEAM.exists():
        shutil.rmtree(TEAM)
    (TEAM / "skills").mkdir(parents=True)
    skill_hashes: dict[str, dict[str, str]] = {}
    for p in PROFILES:
        home = HOME / "profiles" / p
        d = TEAM / "profiles" / p
        d.mkdir(parents=True)
        shutil.copy2(home / "SOUL.md", d / "SOUL.md")
        lines = [f"# Snapshot of profile '{p}' role-shaping settings (generated; do not edit)",
                 f"description: \"{description(p)}\""]
        lines += [block(k, get(p, k)) for k in KEYS]
        (d / "profile.yaml").write_text("\n".join(lines) + "\n")
        for name, path in local_skills(home, p).items():
            h = hashlib.sha256(path.read_bytes()).hexdigest()[:10]
            skill_hashes.setdefault(name, {})[p] = h
            dest = TEAM / "skills" / name / f"SKILL.{h}.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
        print(f"{p:11s} SOUL + settings captured")
    kanban = ["# kanban settings on the default profile (the dispatcher's home)"]
    kanban += [block(k, get("default", f"kanban.{k}")) for k in KANBAN_KEYS]
    kanban += [block("auxiliary.kanban_decomposer.model", get("default", "auxiliary.kanban_decomposer.model"))]
    (TEAM / "kanban.yaml").write_text("\n".join(kanban) + "\n")
    report = ["# Agent-made skills: which profile holds which version", "",
              "| Skill | Versions (hash: profiles) | Drift |", "|---|---|---|"]
    for name, per in sorted(skill_hashes.items()):
        by_hash: dict[str, list[str]] = {}
        for prof, h in per.items():
            by_hash.setdefault(h, []).append(prof)
        versions = "; ".join(f"`{h}`: {', '.join(sorted(ps))}" for h, ps in by_hash.items())
        report.append(f"| `{name}` | {versions} | {'**yes**' if len(by_hash) > 1 else 'no'} |")
    (TEAM / "skills" / "README.md").write_text("\n".join(report) + "\n")
    shutil.copytree(HOME / "scripts", REPO / "scripts" / "hermes", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.bak*"))
    print("kanban settings, skills report and helper scripts captured")


if __name__ == "__main__":
    main()
