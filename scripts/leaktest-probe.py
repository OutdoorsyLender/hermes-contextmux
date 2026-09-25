"""Independent leak test for the contextmux-probe plugin.

Written by the DRIVER (not the leaf) to refute or confirm the leaf's privacy claim.
Feeds the handler a payload containing unmistakable sentinel secrets and asserts that
none of them can appear in the line the plugin actually writes.

This is an adversarial check: it looks for the secrets in the RAW BYTES on disk, so a
whitelist that leaked would be caught even if the JSON looked well-formed.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "probe" / "contextmux-probe" / "__init__.py"

# Sentinels: strings that must NEVER appear anywhere on disk.
SECRET_PROMPT = "SENTINEL-PROMPT-CONTENT-8f3a1c"
SECRET_TOOL_ARG = "SENTINEL-TOOL-ARG-9b2e7d"
SECRET_API_KEY = "SENTINEL-KEY-4c8f0a"
SECRET_INSTRUCTIONS = "SENTINEL-INSTRUCTIONS-5d1b6e"

failures: list[str] = []


def check(condition: bool, label: str) -> None:
    print(f"   {'PASS' if condition else 'FAIL'}  {label}")
    if not condition:
        failures.append(label)


def load_plugin(home: Path):
    os.environ["HERMES_HOME"] = str(home)
    spec = importlib.util.spec_from_file_location("contextmux_probe_leaktest", PLUGIN)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def chat_payload() -> dict:
    return {
        "model": "test-model",
        "api_key": SECRET_API_KEY,
        "messages": [
            {"role": "system", "content": f"system text {SECRET_PROMPT}"},
            {"role": "user", "content": SECRET_PROMPT},
            {"role": "assistant", "content": "ok"},
            {"role": "tool", "content": SECRET_TOOL_ARG},
        ],
        "tools": [
            {"type": "function", "function": {"name": "read_file", "description": SECRET_TOOL_ARG}},
        ],
    }


def responses_payload() -> dict:
    return {
        "model": "test-model",
        "instructions": f"instructions {SECRET_INSTRUCTIONS}",
        "input": [
            {"role": "system", "content": [{"type": "text", "text": SECRET_INSTRUCTIONS}]},
            {"role": "user", "content": [{"type": "text", "text": SECRET_PROMPT}]},
        ],
        "tools": [{"type": "function", "name": "terminal", "description": SECRET_TOOL_ARG}],
    }


def run_case(mod, home: Path, payload: dict, mode: str, label: str) -> None:
    os.environ["CONTEXTMUX_PROBE_MODE"] = mode
    os.environ["CONTEXTMUX_MUTATE_MARKER"] = "PROBE-MARKER-OK"
    log = home / "logs" / "contextmux-probe.jsonl"
    before = log.stat().st_size if log.exists() else 0

    try:
        mod._on_llm_request(payload, session_id="sess-1", turn_id="turn-1",
                            api_mode="chat_completions", model="m", provider="p",
                            api_call_count=1)
    except Exception as exc:  # a raising handler is legitimate in `raise` mode
        if mode != "raise":
            check(False, f"{label}: handler raised in {mode} mode ({type(exc).__name__})")

    if not log.exists():
        check(False, f"{label}: no log file was written")
        return
    raw = log.read_bytes()
    new = raw[before:]

    for name, secret in (
        ("prompt content", SECRET_PROMPT),
        ("tool argument", SECRET_TOOL_ARG),
        ("api key", SECRET_API_KEY),
        ("instructions", SECRET_INSTRUCTIONS),
    ):
        check(secret.encode() not in new, f"{label}: {name} absent from written bytes")

    # The record must still be useful: parse the last line and demand real structure.
    last = new.decode("utf-8", "replace").strip().splitlines()
    check(bool(last), f"{label}: a record was written")
    if last:
        rec = json.loads(last[-1])
        check(rec.get("system_len", 0) > 0 or not rec.get("system_present"),
              f"{label}: a length was recorded (not the text)")
        check(bool(rec.get("system_sha256_16")) or not rec.get("system_present"),
              f"{label}: a digest was recorded (not the text)")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        mod = load_plugin(home)
        print("   --- chat_completions shapes")
        for mode in ("observe", "mutate", "raise"):
            run_case(mod, home, chat_payload(), mode, f"chat/{mode}")
        print("   --- Responses-API shapes")
        for mode in ("observe", "mutate"):
            run_case(mod, home, responses_payload(), mode, f"responses/{mode}")

        # In-place mutation of the caller's object would be a correctness bug.
        print("   --- caller's payload is not mutated in place")
        os.environ["CONTEXTMUX_PROBE_MODE"] = "mutate"
        p = chat_payload()
        before_msg = json.dumps(p["messages"])
        mod._on_llm_request(p, session_id="s", turn_id="t", api_mode="chat_completions",
                            model="m", provider="p", api_call_count=1)
        check(json.dumps(p["messages"]) == before_msg,
              "mutate does not alter the caller's request object in place")

    print()
    if failures:
        print(f"LEAK TEST FAILED: {len(failures)} problem(s)")
        for f in failures:
            print(f"   - {f}")
        return 1
    print("LEAK TEST PASSED: no sentinel content reached disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())