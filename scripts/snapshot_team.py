#!/usr/bin/env python3
"""Snapshot the live Hermes squad into this repo as installable profile distributions.

For each role it writes team/profiles/<role>/, a Hermes profile distribution:
  distribution.yaml  manifest: name, version, description, optional env vars
  SOUL.md            the role prompt
  config.yaml        the profile's config (model, thinking level, toolsets, approvals.deny, ...)
  profile.yaml       the routing description the kanban dispatcher reads
  skills/            the agent-made (local) skills the profile holds, as they are live
It also writes team/kanban.yaml (dispatcher settings that install.sh applies) and
team/skill-drift.md (which roles hold which version of each agent-made skill), and copies the
helper scripts from ~/.hermes/scripts/ to scripts/hermes/.

It never reads .env, auth.json, memories, sessions or state databases. It rewrites the home
directory to ~, then scans the whole repo and exits 1 if anything looks like a secret, an email,
a phone number or an absolute home path. The repo is public, so fix every hit before committing.

Usage:  python3 scripts/snapshot_team.py      # then: git diff
Re-run after any SOUL/config/skill change so the change shows up as a reviewable diff.
For a release, bump VERSION first, then commit and tag v<version>.
"""
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEAM = REPO / "team"
HERMES = Path.home() / ".hermes"
PROFILES = ["lead", "engineer", "ops", "reviewer", "pm", "researcher", "analyst"]
AUTHOR = "Anil Kerai"
LICENSE = "MIT"
HERMES_REQUIRES = ">=0.22.0"
SKIP = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "*.bak*", ".usage.json*")
KANBAN_KEYS = [
    ("kanban.orchestrator_profile", "empty: each team's lead owns its own cards"),
    ("kanban.default_assignee", "unassigned cards go to the dev lead"),
    ("kanban.max_in_progress", "cards running at once across all boards"),
    ("kanban.auto_decompose", "the lead decomposes; no automatic decomposer"),
    ("kanban.review_dispatch", "finished cards move to the review lane"),
    ("kanban.failure_limit", "worker failures before a card blocks"),
    ("kanban.dispatch_interval_seconds", "dispatcher tick"),
    ("auxiliary.kanban_decomposer.provider", ""),
    ("auxiliary.kanban_decomposer.model", ""),
]

# Patterns that must never reach the (public) repo.
FORBIDDEN = {
    "absolute home path": re.compile(r"/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+"),
    "Anthropic key": re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}"),
    "Langfuse key": re.compile(r"\b[ps]k-lf-[A-Za-z0-9-]{8,}"),
    "GitHub token": re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "AWS key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "Slack token": re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"),
    "email address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}\b"),
    "phone number": re.compile(r"(?<![\w.])\+?44\d{9,10}\b"),
}
EMAIL_ALLOW = re.compile(r"@(example\.(com|org)|users\.noreply\.github\.com)$")


def run(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=False).stdout


def yaml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def portable(text: str) -> str:
    """Rewrite the home directory to ~ so paths work on any machine."""
    return text.replace(str(Path.home()), "~")


def description(profile: str) -> str:
    """The routing description from profile.yaml (a folded YAML string; no YAML lib needed)."""
    path = HERMES / "profiles" / profile / "profile.yaml"
    if not path.exists():
        return ""
    m = re.search(r"^description:\s*(['\"]?)(.*?)\1\s*$(?=\n\S|\Z)", path.read_text(), re.M | re.S)
    return re.sub(r"\s*\n\s*", " ", m.group(2)).replace("''", "'").strip() if m else ""


def local_skills(home: Path, profile: str) -> dict[str, Path]:
    """Agent-made skills: rows marked 'local' in `hermes skills list` (names may end in …)."""
    out = run("hermes", "-p", profile, "skills", "list", "--source", "local")
    prefixes = [cells[1].strip().rstrip("…") for line in out.splitlines()
                if "│ local" in line and len(cells := line.split("│")) > 2]
    found = {}
    for skill_md in sorted((home / "skills").glob("*/*/SKILL.md")):
        name = skill_md.parent.name
        if any(pre and name.startswith(pre) for pre in prefixes):
            found[name] = skill_md.parent
    return found


def manifest(profile: str, version: str, desc: str) -> str:
    env = [
        ("ANTHROPIC_API_KEY", "", "Anthropic API key. Not needed if you sign in once on the default "
                                  "profile (`hermes model`); profiles fall back to its credentials."),
        ("HERMES_LANGFUSE_PUBLIC_KEY", "", "Langfuse public key (optional tracing; needs the langfuse plugin)"),
        ("HERMES_LANGFUSE_SECRET_KEY", "", "Langfuse secret key (optional tracing)"),
        ("HERMES_LANGFUSE_BASE_URL", "https://cloud.langfuse.com", "Langfuse host (optional tracing)"),
        ("HERMES_LANGFUSE_ENV", f"hermes-{profile}", "Langfuse environment, one per role so cost groups by role"),
    ]
    lines = [f"name: {profile}", f"version: {version}", f"description: {yaml_str(desc)}",
             f"hermes_requires: {yaml_str(HERMES_REQUIRES)}", f"author: {yaml_str(AUTHOR)}",
             f"license: {LICENSE}", "env_requires:"]
    for name, default, text in env:
        lines += [f"  - name: {name}", f"    description: {yaml_str(text)}", "    required: false"]
        if default:
            lines.append(f"    default: {yaml_str(default)}")
    return "\n".join(lines) + "\n"


def kanban_settings() -> str:
    lines = ["# Kanban settings for the dispatcher's home (the default profile).",
             "# `./install.sh --kanban` applies them with `hermes config set`. Generated; do not edit."]
    for key, why in KANBAN_KEYS:
        value = run("hermes", "config", "get", key).strip().splitlines()
        value = value[-1].strip() if value else ""
        value = "" if value in ("null", "None") else value
        lines.append(f"{key}: {yaml_str(value)}" + (f"  # {why}" if why else ""))
    return "\n".join(lines) + "\n"


def tree_hash(d: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in d.rglob("*") if p.is_file()):
        h.update(str(f.relative_to(d)).encode() + b"\0" + f.read_bytes())
    return h.hexdigest()[:10]


def drift_report(hashes: dict[str, dict[str, str]]) -> str:
    out = ["# Agent-made skills: which role holds which version", "",
           "Generated by `scripts/snapshot_team.py`. Each role carries its own copy under",
           "`team/profiles/<role>/skills/`; more than one hash means the copies have drifted.", "",
           "| Skill | Versions (hash: roles) | Drift |", "|---|---|---|"]
    for name, per in sorted(hashes.items()):
        by_hash: dict[str, list[str]] = {}
        for prof, h in per.items():
            by_hash.setdefault(h, []).append(prof)
        versions = "; ".join(f"`{h}`: {', '.join(sorted(ps))}" for h, ps in by_hash.items())
        out.append(f"| `{name}` | {versions} | {'**yes**' if len(by_hash) > 1 else 'no'} |")
    return "\n".join(out) + "\n"


def scan(root: Path) -> list[str]:
    """Every text file under root (skipping .git, caches and backups) checked against FORBIDDEN."""
    problems = []
    for f in sorted(root.rglob("*")):
        rel = f.relative_to(root).parts
        if not f.is_file() or {".git", "__pycache__", ".idea"} & set(rel) or f.name == ".DS_Store" \
                or ".bak" in f.name:
            continue
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue  # images
        for label, rx in FORBIDDEN.items():
            for m in rx.finditer(text):
                if label == "email address" and EMAIL_ALLOW.search(m.group(0)):
                    continue
                line = text.count("\n", 0, m.start()) + 1
                problems.append(f"{f.relative_to(REPO)}:{line}: {label}: {m.group(0)[:40]}")
    return problems


def main() -> int:
    version = (REPO / "VERSION").read_text().strip()
    if TEAM.exists():
        shutil.rmtree(TEAM)
    hashes: dict[str, dict[str, str]] = {}
    for p in PROFILES:
        home = HERMES / "profiles" / p
        d = TEAM / "profiles" / p
        d.mkdir(parents=True)
        desc = description(p)
        (d / "distribution.yaml").write_text(manifest(p, version, desc))
        (d / "SOUL.md").write_text(portable((home / "SOUL.md").read_text()))
        (d / "config.yaml").write_text(portable((home / "config.yaml").read_text()))
        (d / "profile.yaml").write_text(f"description: {yaml_str(desc)}\ndescription_auto: false\n")
        skills = local_skills(home, p)
        for name, src in skills.items():
            dest = d / "skills" / src.parent.name / name
            shutil.copytree(src, dest, ignore=SKIP)
            for f in dest.rglob("*"):
                if f.is_file() and f.suffix in {".md", ".py", ".sh", ".yaml", ".yml", ".json", ".txt"}:
                    f.write_text(portable(f.read_text()))
            hashes.setdefault(name, {})[p] = tree_hash(dest)
        print(f"{p:11s} {version}  skills: {', '.join(skills) or '-'}")
    (TEAM / "kanban.yaml").write_text(kanban_settings())
    (TEAM / "skill-drift.md").write_text(drift_report(hashes))
    shutil.copytree(HERMES / "scripts", REPO / "scripts" / "hermes", dirs_exist_ok=True, ignore=SKIP)
    print("kanban settings, skill drift report and helper scripts captured")
    problems = scan(REPO)
    if problems:
        print("\nREFUSING: possible secrets or personal data in the repo:", *problems, sep="\n  ")
        return 1
    print("scan: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
