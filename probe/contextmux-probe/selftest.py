"""Self-test for the contextmux-probe plugin.

Run with the Hermes venv python:

    C:/Users/brand/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe \
        C:/Users/brand/dev/repos/hermes-contextmux/probe/contextmux-probe/selftest.py

Exercises the handler directly (no live Hermes turn): both payload shapes, all three
modes, degenerate payloads, the record schema, path handling, and -- the point of the
whole thing -- that no message content, prompt text, or tool argument text reaches the
log.  Records are written to a scratch HERMES_HOME under the OS temp dir.

Exit code 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
from pathlib import Path

PLUGIN = Path(__file__).with_name("__init__.py")
SENTINEL = "SENTINEL_CONTENT_9f3a_do_not_persist"

# Importing the plugin by path would otherwise drop a __pycache__ into the plugin directory.
sys.dont_write_bytecode = True


def temp_root() -> Path:
    """Scratch root for test homes: LOCALAPPDATA on Windows, the temp dir elsewhere."""
    local = (os.environ.get("LOCALAPPDATA") or "").strip()
    if local:
        return Path(local)
    import tempfile

    return Path(tempfile.gettempdir())


HOME = temp_root() / "Temp" / "cmp-selftest"


_failures: list[str] = []
_mod_counter = 0


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS {label}")
    else:
        print(f"FAIL {label} {extra}")
        _failures.append(label)


def load():
    """Import the plugin under a fresh module name (module globals are state)."""
    global _mod_counter
    _mod_counter += 1
    name = f"contextmux_probe_selftest_{_mod_counter}"
    spec = importlib.util.spec_from_file_location(name, PLUGIN)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fresh(mode=None, marker=None, home=None):
    """Reload the plugin with the given env; returns the module."""
    for var in ("CONTEXTMUX_PROBE_MODE", "CONTEXTMUX_MUTATE_MARKER"):
        os.environ.pop(var, None)
    if mode is not None:
        os.environ["CONTEXTMUX_PROBE_MODE"] = mode
    if marker is not None:
        os.environ["CONTEXTMUX_MUTATE_MARKER"] = marker
    os.environ["HERMES_HOME"] = str(home or HOME)
    return load()


def log_path(home=None):
    return (home or HOME) / "logs" / "contextmux-probe.jsonl"


def clear(home=None):
    path = log_path(home)
    if path.exists():
        path.unlink()


def read_lines(home=None):
    path = log_path(home)
    if not path.exists():
        return [], ""
    raw = path.read_text(encoding="utf-8")
    return [json.loads(line) for line in raw.splitlines() if line.strip()], raw


class Ctx:
    """Minimal ctx stand-in recording middleware registrations."""

    def __init__(self):
        self.registered = []

    def register_middleware(self, kind, callback):
        self.registered.append((kind, callback))


def main() -> int:
    shutil.rmtree(HOME, ignore_errors=True)

    # ── register() ────────────────────────────────────────────────────────────────
    module = fresh()
    ctx = Ctx()
    module.register(ctx)
    check(
        "register() registers llm_request middleware",
        ctx.registered == [("llm_request", module._on_llm_request)],
        repr(ctx.registered),
    )

    ctx_kwargs = dict(
        task_id="t1", turn_id="turn-1", api_request_id="req-1", session_id="sess-1",
        platform="cli", model="m", provider="nous", base_url="https://x/v1",
        api_mode="chat_completions", api_call_count=1, original_request={"x": 1},
    )
    system_text = "You are Hermes. " + SENTINEL
    chat = {
        "model": "m",
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": SENTINEL},
            {"role": "assistant", "content": "ok"},
        ],
        "tools": [
            {"type": "function", "function": {"name": "terminal", "description": SENTINEL,
                                              "parameters": {"a": SENTINEL}}},
            {"type": "function", "function": {"name": "read_file"}},
        ],
        "temperature": 0.7,
        "stream": True,
        "api_key": "sk-SECRET-SENTINEL",
    }
    chat_snapshot = json.dumps(chat, sort_keys=True)

    # ── chat shape, observe ───────────────────────────────────────────────────────
    clear()
    module = fresh()
    check("observe returns None", module._on_llm_request(chat, **ctx_kwargs) is None)
    check("observe leaves the request unchanged", json.dumps(chat, sort_keys=True) == chat_snapshot)

    records, raw = read_lines()
    check("exactly one record written", len(records) == 1, str(len(records)))
    record = records[0]
    check("record keys match the schema exactly", set(record) == set(module.RECORD_FIELDS),
          str(sorted(set(record) ^ set(module.RECORD_FIELDS))))
    check("record keys are in schema order", list(record) == list(module.RECORD_FIELDS))
    check("mode recorded", record["mode"] == "observe", repr(record["mode"]))
    check(
        "context fields recorded",
        (record["session_id"], record["turn_id"], record["api_request_id"], record["api_mode"],
         record["model"], record["provider"], record["api_call_count"])
        == ("sess-1", "turn-1", "req-1", "chat_completions", "m", "nous", 1),
        json.dumps(record),
    )
    check("request_keys", record["request_keys"] == sorted(chat), json.dumps(record["request_keys"]))
    check("message_count", record["message_count"] == 3, str(record["message_count"]))
    check("roles", record["roles"] == ["system", "user", "assistant"], json.dumps(record["roles"]))
    check("system_present", record["system_present"] is True)
    check("system_len", record["system_len"] == len(system_text), str(record["system_len"]))
    check("system_sha256_16",
          record["system_sha256_16"] == hashlib.sha256(system_text.encode()).hexdigest()[:16],
          repr(record["system_sha256_16"]))
    check("tools_count", record["tools_count"] == 2, str(record["tools_count"]))
    check("tool_names", record["tool_names"] == ["terminal", "read_file"], json.dumps(record["tool_names"]))
    check("responses_shape is false for chat", record["responses_shape"] is False)
    check("ts is ISO-8601 UTC", record["ts"].endswith("Z") and "T" in record["ts"], record["ts"])
    check("REDACTION: no content in the log",
          SENTINEL not in raw and "SECRET" not in raw and "sk-" not in raw)
    check("REDACTION: no tool description or params in the log",
          "parameters" not in raw and "description" not in raw)

    # ── responses shape, observe ──────────────────────────────────────────────────
    clear()
    module = fresh()
    responses = {
        "model": "gpt-5",
        "instructions": "Sys " + SENTINEL,
        "input": [
            {"type": "message", "role": "developer", "content": [{"type": "input_text", "text": SENTINEL}]},
            {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "hi"}]},
            {"type": "function_call", "name": "terminal", "arguments": SENTINEL},
        ],
        "tools": [{"type": "function", "name": "terminal", "description": SENTINEL, "parameters": {"a": SENTINEL}}],
        "store": False,
        "reasoning": {"effort": "low"},
    }
    check("responses observe returns None",
          module._on_llm_request(request=responses, api_mode="codex_responses", session_id="s",
                                 turn_id="t", api_request_id="a", model="gpt-5",
                                 provider="openai-codex", api_call_count=2) is None)
    records, raw = read_lines()
    record = records[0]
    check("responses_shape is true", record["responses_shape"] is True, json.dumps(record))
    check("responses message_count counts input items", record["message_count"] == 3, str(record["message_count"]))
    check("responses roles exclude non-message items", record["roles"] == ["developer", "user"],
          json.dumps(record["roles"]))
    check("responses system comes from instructions",
          record["system_present"] and record["system_len"] == len("Sys " + SENTINEL), json.dumps(record))
    check("responses system digest",
          record["system_sha256_16"] == hashlib.sha256(("Sys " + SENTINEL).encode()).hexdigest()[:16])
    check("responses tool_names use the flat schema", record["tool_names"] == ["terminal"],
          json.dumps(record["tool_names"]))
    check("REDACTION: no content in the responses log", SENTINEL not in raw)

    # ── system reached through a top-level system key ─────────────────────────────
    clear()
    module = fresh()
    module._on_llm_request(
        {"model": "claude", "system": [{"type": "text", "text": "Sys " + SENTINEL}],
         "messages": [{"role": "user", "content": SENTINEL}]},
        api_mode="anthropic_messages",
    )
    record = read_lines()[0][0]
    check("top-level system block list is found",
          record["system_present"] and record["system_len"] == len("Sys " + SENTINEL), json.dumps(record))
    check("top-level system payload is not responses-shaped", record["responses_shape"] is False)

    # ── a payload with no system carrier records that honestly ────────────────────
    clear()
    module = fresh()
    module._on_llm_request(
        {"model": "m", "messages": [{"role": "user", "content": "x"}],
         "tools": [{"type": "function", "function": {"name": "t"}}]},
        **ctx_kwargs)
    record = read_lines()[0][0]
    check("no system carrier: system_present false", record["system_present"] is False)
    check("no system carrier: system_len 0", record["system_len"] == 0)
    check("no system carrier: digest null", record["system_sha256_16"] is None)

    # ── mutate, chat ──────────────────────────────────────────────────────────────
    clear()
    module = fresh(mode="mutate", marker="<<MARK>>")
    chat_copy = json.loads(chat_snapshot)
    snapshot = json.dumps(chat_copy, sort_keys=True)
    out = module._on_llm_request(chat_copy, **ctx_kwargs)
    check("mutate returns {'request': ...}", isinstance(out, dict) and set(out) == {"request"}, repr(out))
    mutated = out["request"] if isinstance(out, dict) else {}
    check("mutate appends the marker to the system message",
          mutated.get("messages", [{}])[0].get("content") == system_text + "\n<<MARK>>",
          repr(mutated.get("messages", [{}])[0].get("content")))
    check("mutate preserves every other key",
          mutated.get("temperature") == 0.7 and mutated.get("stream") is True and len(mutated.get("messages", [])) == 3)
    check("mutate does not modify the caller's request object",
          json.dumps(chat_copy, sort_keys=True) == snapshot)
    records, raw = read_lines()
    check("mutate records the call", len(records) == 1 and records[0]["mode"] == "mutate")
    check("REDACTION: mutate log has no content", SENTINEL not in raw)

    module = fresh(mode="mutate")
    check("mutate without a marker returns None", module._on_llm_request(json.loads(chat_snapshot), **ctx_kwargs) is None)

    # ── mutate, other shapes ──────────────────────────────────────────────────────
    clear()
    module = fresh(mode="mutate", marker="<<MARK>>")
    out = module._on_llm_request(dict(responses), api_mode="codex_responses")
    check("responses mutate appends to instructions",
          bool(out) and out["request"]["instructions"] == "Sys " + SENTINEL + "\n<<MARK>>", repr(out))

    module = fresh(mode="mutate", marker="<<MARK>>")
    out = module._on_llm_request(
        {"model": "gpt-5", "input": [{"role": "user", "content": [{"type": "input_text", "text": "hi"}]}]},
        api_mode="codex_responses")
    check("responses mutate with no system slot sets instructions",
          bool(out) and out["request"]["instructions"] == "<<MARK>>", repr(out))

    module = fresh(mode="mutate", marker="<<MARK>>")
    out = module._on_llm_request({"model": "claude", "system": "Sys", "messages": [{"role": "user", "content": "x"}]},
                                 api_mode="anthropic_messages")
    check("top-level system is appended to", bool(out) and out["request"]["system"] == "Sys\n<<MARK>>", repr(out))

    module = fresh(mode="mutate", marker="<<MARK>>")
    out = module._on_llm_request({"model": "m", "messages": [{"role": "user", "content": "x"}]}, **ctx_kwargs)
    check("chat mutate inserts a system message when absent",
          bool(out) and out["request"]["messages"][0] == {"role": "system", "content": "<<MARK>>"}, repr(out))

    module = fresh(mode="mutate", marker="<<MARK>>")
    out = module._on_llm_request(
        {"model": "m", "messages": [{"role": "system", "content": [{"type": "text", "text": "a"}]}]}, **ctx_kwargs)
    check("chat mutate handles block-list content",
          bool(out) and out["request"]["messages"][0]["content"]
          == [{"type": "text", "text": "a"}, {"type": "text", "text": "<<MARK>>"}], repr(out))

    # a system carrier the inspector skipped must not be rewritten into
    module = fresh(mode="mutate", marker="<<MARK>>")
    out = module._on_llm_request({"model": "gpt-5", "instructions": 42,
                                  "input": [{"role": "user", "content": "x"}]}, api_mode="codex_responses")
    check("mutate leaves an unappendable carrier alone", out is None, repr(out))

    # instructions outranks a system-role input item in both the record and the rewrite
    module = fresh(mode="mutate", marker="<<MARK>>")
    out = module._on_llm_request(
        {"model": "gpt-5", "instructions": "Sys",
         "input": [{"type": "message", "role": "system", "content": [{"type": "input_text", "text": "a"}]}]},
        api_mode="codex_responses")
    check("responses mutate prefers instructions over a system input item",
          bool(out) and out["request"]["instructions"] == "Sys\n<<MARK>>"
          and out["request"]["input"][0]["content"] == [{"type": "input_text", "text": "a"}], repr(out))

    # with no instructions, a system-role input item is the carrier
    module = fresh(mode="mutate", marker="<<MARK>>")
    out = module._on_llm_request(
        {"model": "gpt-5",
         "input": [{"type": "message", "role": "system", "content": [{"type": "input_text", "text": "a"}]},
                   {"role": "user", "content": "x"}]},
        api_mode="codex_responses")
    check("responses mutate targets a system input item",
          bool(out) and out["request"]["input"][0]["content"][-1] == {"type": "text", "text": "<<MARK>>"}
          and "instructions" not in out["request"], repr(out))

    # the recorded carrier and the rewritten carrier are the same message
    clear()
    module = fresh(mode="mutate", marker="<<MARK>>")
    mixed = {"model": "m", "instructions": "IGNORED",
             "messages": [{"role": "user", "content": "x"}, {"role": "system", "content": "Real"}]}
    out = module._on_llm_request(mixed, **ctx_kwargs)
    record = read_lines()[0][0]
    check("mutate rewrites the carrier that was recorded",
          bool(out) and out["request"]["messages"][1]["content"] == "Real\n<<MARK>>"
          and mixed["messages"][1]["content"] == "Real"
          and record["system_sha256_16"] == hashlib.sha256(b"Real").hexdigest()[:16], repr(out))

    # ── raise mode ────────────────────────────────────────────────────────────────
    clear()
    module = fresh(mode="raise")
    try:
        module._on_llm_request(json.loads(chat_snapshot), **ctx_kwargs)
        check("raise mode raises RuntimeError", False, "no exception raised")
    except RuntimeError as exc:
        check("raise mode raises RuntimeError", str(exc) == "contextmux probe: deliberate failure", str(exc))
    except Exception as exc:  # noqa: BLE001 - the point is that it must be a RuntimeError
        check("raise mode raises RuntimeError", False, repr(exc))
    records, _ = read_lines()
    check("raise mode records before raising", len(records) == 1 and records[0]["mode"] == "raise")

    # ── unknown mode falls back to observe ────────────────────────────────────────
    clear()
    module = fresh(mode="banana")
    check("an unknown mode behaves as observe",
          module._on_llm_request(json.loads(chat_snapshot), **ctx_kwargs) is None
          and read_lines()[0][0]["mode"] == "observe")

    # ── degenerate payloads must not raise ────────────────────────────────────────
    clear()
    module = fresh()
    degenerate = (
        None, {}, [], "raw-string", 42, {"messages": "not-a-list"}, {"input": "hi"},
        {"messages": [], "tools": "nope"},
        {"messages": [None, 1, {"role": 5}], "tools": [None, {}, {"function": {"name": 7}}]},
        {"instructions": None, "input": [{"role": "system"}]},
        {"system": {"weird": 1}},
        {"messages": [{"role": "system", "content": {"not": "text"}}], "tools": 5},
    )
    for payload in degenerate:
        try:
            survived = module._on_llm_request(payload, **ctx_kwargs) is None
        except Exception as exc:  # noqa: BLE001 - a raise here is the defect under test
            survived = False
            print(f"     raised on {payload!r:.60}: {exc!r}")
        check(f"degenerate payload tolerated: {payload!r:.44}", survived)
    records, _ = read_lines()
    check("every degenerate call was still recorded", len(records) == len(degenerate), str(len(records)))

    # ── a second call appends rather than truncating ──────────────────────────────
    before_count = len(read_lines()[0])
    module._on_llm_request(json.loads(chat_snapshot), **ctx_kwargs)
    check("records append, one JSON object per line", len(read_lines()[0]) == before_count + 1)

    # ── log directory is created on demand ────────────────────────────────────────
    fresh_home = temp_root() / "Temp" / "cmp-selftest-fresh"
    shutil.rmtree(fresh_home, ignore_errors=True)
    module = fresh(home=fresh_home)
    check("scratch home has no logs dir yet", not (fresh_home / "logs").exists())
    module._on_llm_request(json.loads(chat_snapshot), **ctx_kwargs)
    check("logs dir created on demand", log_path(fresh_home).exists())

    # ── an unwritable log path fails open, and warns without content ─────────────
    blocked = temp_root() / "Temp" / "cmp-selftest-blocked"
    shutil.rmtree(blocked, ignore_errors=True)
    blocked.mkdir(parents=True)
    (blocked / "logs").write_text("a file where the directory should be", encoding="utf-8")
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        module = fresh(home=blocked)
        first = module._on_llm_request(json.loads(chat_snapshot), **ctx_kwargs)
        second = module._on_llm_request(json.loads(chat_snapshot), **ctx_kwargs)
    check("unwritable log path: the handler still returns None", first is None and second is None)
    check("unwritable log path: warned exactly once", stderr.getvalue().count("probe log write failed") == 1,
          repr(stderr.getvalue()))
    check("unwritable log path: the warning carries no content", SENTINEL not in stderr.getvalue())

    # ── request that is not a dict, in mutate mode ────────────────────────────────
    module = fresh(mode="mutate", marker="<<MARK>>")
    check("mutate on a non-dict payload returns None", module._on_llm_request(None, **ctx_kwargs) is None)

    print()
    if _failures:
        print(f"FAILED {len(_failures)} check(s): {_failures}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())