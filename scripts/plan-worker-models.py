"""Plan the worker model migration: report only, change nothing.

Target:
  profiles WITH a nous credential      -> deepseek/deepseek-v4.1-flash  (provider nous)
  profiles WITHOUT nous, with codex    -> gpt-5.6-terra                 (provider openai-codex)
  profiles with neither                -> reported as UNCHANGEABLE

Run: python scripts/plan-worker-models.py
"""

from __future__ import annotations

import json
from pathlib import Path

PROFILES = Path("C:/Users/brand/AppData/Local/hermes/profiles")
ROLES = ("planner", "coder", "adversary", "reviewer")

NOUS_MODEL = "deepseek/deepseek-v4.1-flash"
NOUS_PROVIDER = "nous"
CODEX_MODEL = "gpt-5.6-terra"
CODEX_PROVIDER = "openai-codex"

# Matches the working adversary profile's nous block exactly.
NOUS_BASE_URL = "https://inference-api.nousresearch.com/v1"
NOUS_API_MODE = "chat_completions"


def read_config_model(profile_dir: Path) -> tuple[str, str]:
    """Return (model.default, model.provider) from the profile's config.yaml, text-scanned."""
    cfg = profile_dir / "config.yaml"
    if not cfg.exists():
        return "", ""
    model = provider = ""
    in_model = False
    for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("model:"):
            in_model = True
            continue
        if in_model:
            if line and not line[0].isspace():
                break
            s = line.strip()
            if s.startswith("default:"):
                model = s.split(":", 1)[1].strip()
            elif s.startswith("provider:"):
                provider = s.split(":", 1)[1].strip().strip("'\"")
            elif s.startswith("api_mode:") or s.startswith("base_url:"):
                continue
    return model, provider


def credential_providers(profile_dir: Path) -> set[str]:
    a = profile_dir / "auth.json"
    if not a.exists():
        return set()
    try:
        j = json.loads(a.read_text(encoding="utf-8"))
    except Exception:
        return set()
    pool = j.get("credential_pool") or {}
    provs = set(j.get("providers") or {})
    for k, v in pool.items():
        if isinstance(v, list) and v:
            provs.add(k)
    return provs


def main() -> int:
    rows = []
    for d in sorted(PROFILES.iterdir()):
        if not d.is_dir() or not any(d.name.startswith(r + "-") for r in ROLES):
            continue
        role = next(r for r in ROLES if d.name.startswith(r + "-"))
        repo = d.name[len(role) + 1 :]
        creds = credential_providers(d)
        cur_model, cur_provider = read_config_model(d)
        has_nous = "nous" in creds
        has_codex = "openai-codex" in creds

        if has_nous:
            target_model, target_provider, why = NOUS_MODEL, NOUS_PROVIDER, "has nous credential"
        elif has_codex:
            target_model, target_provider, why = CODEX_MODEL, CODEX_PROVIDER, "codex only; terra is the mini tier"
        else:
            target_model, target_provider, why = "", "", "NO usable credential"

        rows.append({
            "profile": d.name, "role": role, "repo": repo,
            "cur_model": cur_model, "cur_provider": cur_provider,
            "target_model": target_model, "target_provider": target_provider,
            "why": why, "change": (cur_model != target_model) if target_model else False,
        })

    print(f"{'profile':<38} {'current':<26} {'target':<30} {'note'}")
    print("-" * 118)
    for r in rows:
        cur = f"{r['cur_model']} ({r['cur_provider']})" if r["cur_model"] else "<none>"
        tgt = f"{r['target_model']} ({r['target_provider']})" if r["target_model"] else "<LEAVE ALONE>"
        mark = "  " if r["change"] else "= "
        print(f"{mark}{r['profile']:<36} {cur:<26} {tgt:<30} {r['why']}")

    changing = [r for r in rows if r["change"]]
    nous_bound = [r for r in rows if r["target_provider"] == NOUS_PROVIDER]
    codex_bound = [r for r in rows if r["target_provider"] == CODEX_PROVIDER]
    stuck = [r for r in rows if not r["target_model"]]

    print()
    print(f"total worker profiles : {len(rows)}")
    print(f"to change             : {len(changing)}")
    print(f"  -> {NOUS_MODEL:<34} {len(nous_bound)}")
    print(f"  -> {CODEX_MODEL:<34} {len(codex_bound)}")
    print(f"left alone (no cred)  : {len(stuck)}")
    for r in stuck:
        print(f"     {r['profile']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())