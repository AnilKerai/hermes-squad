#!/usr/bin/env python3
"""Sync Langfuse settings from the default profile to every Hermes profile.

Edit HERMES_LANGFUSE_* only in ~/.hermes/.env, then run this. For every profile
(default included) it:
  - copies HERMES_LANGFUSE_* (keys, base URL, and any other options) from the default .env,
  - sets HERMES_LANGFUSE_ENV=hermes-<profile>, so Langfuse can filter traces by role
    and keep them apart from app environments (development, evals) in a shared project,
  - backs up the old file to .env.bak-langfuse-<timestamp> (mode 600).
Values are never printed.
"""
import os
import re
import shutil
import stat
import time
from pathlib import Path

HOME = Path.home() / ".hermes"
KEY_RE = re.compile(r"\s*(?:export\s+)?(HERMES_LANGFUSE_[A-Z0-9_]+)\s*=")


def langfuse_lines(env_path: Path) -> dict:
    out = {}
    for line in env_path.read_text().splitlines():
        m = KEY_RE.match(line)
        if m and m.group(1) != "HERMES_LANGFUSE_ENV":
            out[m.group(1)] = line.strip()  # last occurrence wins, like dotenv
    return out


def main():
    source = langfuse_lines(HOME / ".env")
    missing = {"HERMES_LANGFUSE_PUBLIC_KEY", "HERMES_LANGFUSE_SECRET_KEY"} - source.keys()
    if missing:
        raise SystemExit(f"default .env is missing {sorted(missing)}; nothing synced")

    profiles = {"default": HOME}
    profiles.update({p.name: p for p in sorted((HOME / "profiles").iterdir())
                     if p.is_dir() and not p.name.startswith(".")})
    ts = time.strftime("%Y%m%d-%H%M%S")
    for name, home in profiles.items():
        env = home / ".env"
        old = env.read_text().splitlines() if env.exists() else []
        kept = [line for line in old if not KEY_RE.match(line)]
        while kept and not kept[-1].strip():
            kept.pop()
        new = kept + ["", "# Langfuse (synced from default by sync_langfuse_env.py)",
                      *source.values(), f"HERMES_LANGFUSE_ENV=hermes-{name}"]
        if env.exists():
            backup = env.with_name(f".env.bak-langfuse-{ts}")
            shutil.copy2(env, backup)
            os.chmod(backup, stat.S_IRUSR | stat.S_IWUSR)
        env.write_text("\n".join(new) + "\n")
        os.chmod(env, stat.S_IRUSR | stat.S_IWUSR)
        print(f"{name:12s} synced {len(source)} keys, HERMES_LANGFUSE_ENV=hermes-{name}")


if __name__ == "__main__":
    main()
