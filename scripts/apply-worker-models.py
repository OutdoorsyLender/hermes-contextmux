"""Apply the worker model migration.

For each worker profile:
  has nous credential      -> model.default=deepseek/deepseek-v4.1-flash, provider=nous,
                              base_url/api_mode set to match the working adversary template
  codex only               -> model.default=gpt-5.6-terra, provider=openai-codex
  no usable credential     -> skipped, reported

Uses the same invocation form repos.py uses: `hermes config -p <profile> set <key> <value>`.
Verifies each change by reading the value back.

Run: python scripts/apply-worker-models.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERMES = shutil.which("hermes") or "hermes"
PROFILES = Path("C:/Users/brand/AppData/Local/hermes/profiles")
BACKUP_DIR = Path("C:/Users/brand/dev/_notes/self-improvement/worker-model-backup")
ROLES = ("planner", "coder", "adversary", "reviewer")

NOUS_MODEL, NOUS_PROVIDER = "deepseek/deepseek-v4.1-flash", "nous"
NOUS_BASE_URL = "https://inference-api.nousresearch.com/v1"
NOUS_API_MODE = "chat_completions"
CODEX_MODEL, CODEX_PROVIDER = "gpt-5.6-terra", "openai-codex"


def creds(d: Path) -> set[str]:
    a = d / "auth.json"
    if not a.exists():
        return set()
    try:
        j = json.loads(a.read_text(encoding="utf-8"))
    except Exception:
        return set()
    out = set(j.get("providers") or {})
    for k, v in (j.get("credential_pool") or {}).items():
        if isinstance(v, list) and v:
            out.add(k)
    return out


def cfg_set(profile: str, key: str, value: str) -> bool:
    p = subprocess.run([HERMES, "config", "-p", profile, "set", key, value],
                       capture_output=True, text=True, timeout=120)
    return p.returncode == 0


def cfg_get(profile: str, key: str) -> str:
    p = subprocess.run([HERMES, "config", "-p", profile, "get", key],
                       capture_output=True, text=True, timeout=120)
    return (p.stdout or "").strip()


def main() -> int:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    targets = []
    for d in sorted(PROFILES.iterdir()):
        if not d.is_dir() or not any(d.name.startswith(r + "-") for r in ROLES):
            continue
        c = creds(d)
        if "nous" in c:
            targets.append((d.name, "nous"))
        elif "openai-codex" in c:
            targets.append((d.name, "codex"))
        else:
            print(f"   SKIP  {d.name:<38} no usable credential")

    print(f"\n   {len(targets)} profile(s) to change\n")
    changed, failed = [], []

    for profile, kind in targets:
        # Back up the live config before touching it.
        src = PROFILES / profile / "config.yaml"
        if src.exists():
            shutil.copyfile(src, BACKUP_DIR / f"{profile}.{stamp}.config.yaml")

        if kind == "nous":
            ok = all([
                cfg_set(profile, "model.default", NOUS_MODEL),
                cfg_set(profile, "model.provider", NOUS_PROVIDER),
                cfg_set(profile, "model.base_url", NOUS_BASE_URL),
                cfg_set(profile, "model.api_mode", NOUS_API_MODE),
            ])
            want_model, want_prov = NOUS_MODEL, NOUS_PROVIDER
        else:
            ok = all([
                cfg_set(profile, "model.default", CODEX_MODEL),
                cfg_set(profile, "model.provider", CODEX_PROVIDER),
            ])
            want_model, want_prov = CODEX_MODEL, CODEX_PROVIDER

        # Verify by reading back, never by trusting the write's exit code alone.
        got_model, got_prov = cfg_get(profile, "model.default"), cfg_get(profile, "model.provider")
        good = ok and got_model == want_model and got_prov == want_prov
        (changed if good else failed).append(profile)
        print(f"   {'OK   ' if good else 'FAIL '} {profile:<38} {got_model} / {got_prov}")

    print(f"\n   changed : {len(changed)}")
    print(f"   failed  : {len(failed)}")
    for f in failed:
        print(f"      {f}")
    print(f"   backups : {BACKUP_DIR}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())