"""Hermes probe plugin: structural observation of outbound LLM requests.

ContextMux Phase 1B needs to see what Hermes actually assembles before it hands a request
to a provider.  This plugin registers ``llm_request`` middleware and appends one sanitized
structural record per call to ``$HERMES_HOME/logs/contextmux-probe.jsonl``.

**Redaction rule (hard requirement):** lengths and digests only.  Message content, prompt
text, tool argument content, and credentials are never written -- not even truncated.

**Fail-open rule:** the handler swallows every internal error and returns ``None`` so the
outbound request stays exactly as Hermes assembled it.  Only the deliberate ``raise`` probe
mode raises, and that is the behaviour under test.

Modes, selected by ``CONTEXTMUX_PROBE_MODE``:

* ``observe`` (default) -- record, return ``None`` (request untouched).
* ``mutate``            -- record, then return the request with ``CONTEXTMUX_MUTATE_MARKER``
                           appended to the system message.
* ``raise``             -- record, then raise ``RuntimeError`` (proves fail-open at runtime).

Record fields: ``ts, mode, session_id, turn_id, api_request_id, api_mode, model, provider,
api_call_count, request_keys, message_count, roles, system_present, system_len,
system_sha256_16, tools_count, tool_names, responses_shape``.

Field semantics worth knowing when reading the log:

* ``system_len`` counts characters of the *extracted* system text; block-list content
  (multimodal, Anthropic blocks, Responses input parts) is joined on its ``text`` members
  before it is measured and hashed, and ``system_sha256_16`` is the digest of that same
  joined text -- so the length and the digest always describe one string.
* ``message_count`` counts ``messages`` for Chat Completions and ``input`` items for the
  Responses API.  ``roles`` and ``tool_names`` are structure only: no content, no tool
  descriptions or parameter schemas are read.
* ``mode`` is the effective mode, so a typo in ``CONTEXTMUX_PROBE_MODE`` shows up here as
  ``observe`` rather than as a mode Hermes never ran.

The record write is synchronous and inline on the request path: one small ``append`` per
call.  That cost is deliberate -- a probe that batches would misreport call ordering -- and
it is the only side effect this plugin has on a turn.

Standard library only (``hermes_constants`` is imported lazily, with a platform-default
fallback, so the module also imports cleanly outside Hermes).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MIDDLEWARE_KIND = "llm_request"

MODE_ENV_VAR = "CONTEXTMUX_PROBE_MODE"
MARKER_ENV_VAR = "CONTEXTMUX_MUTATE_MARKER"

MODE_OBSERVE = "observe"
MODE_MUTATE = "mutate"
MODE_RAISE = "raise"
_PROBE_MODES = (MODE_OBSERVE, MODE_MUTATE, MODE_RAISE)

HOME_ENV_VAR = "HERMES_HOME"
LOG_DIRNAME = "logs"
LOG_FILENAME = "contextmux-probe.jsonl"

DELIBERATE_FAILURE_MESSAGE = "contextmux probe: deliberate failure"

# The marker is appended after a newline so it reads as a distinct line in a captured
# request dump.  Nothing else is ever added to a request.
MARKER_SEPARATOR = "\n"

# Roles that carry the system prompt.  ``developer`` is the OpenAI-native variant of
# ``system`` and appears in both payload shapes.
_SYSTEM_ROLES = frozenset({"system", "developer"})

# The fixed ContextMux Phase 1B record schema, in its published order.  Serialization is a
# whitelist over this tuple, so a field added to the record dict later can never smuggle
# request text into the log by accident.
RECORD_FIELDS: Tuple[str, ...] = (
    "ts",
    "mode",
    "session_id",
    "turn_id",
    "api_request_id",
    "api_mode",
    "model",
    "provider",
    "api_call_count",
    "request_keys",
    "message_count",
    "roles",
    "system_present",
    "system_len",
    "system_sha256_16",
    "tools_count",
    "tool_names",
    "responses_shape",
)

_write_failure_reported = False


def register(ctx: Any) -> None:
    """Register the ``llm_request`` middleware.  Called once at plugin load."""
    ctx.register_middleware(MIDDLEWARE_KIND, _on_llm_request)


# ── middleware entry point ────────────────────────────────────────────────────────


def _on_llm_request(request: Any = None, **context: Any) -> Optional[Dict[str, Any]]:
    """Observe (and optionally rewrite) one outbound LLM request.

    ``request`` is the assembled provider kwargs.  Hermes dispatches middleware callbacks as
    keywords -- ``invoke_middleware`` calls ``callback(**kwargs)`` -- so the payload arrives as
    ``request=``; a positional first argument is accepted too, because the published contract
    describes it that way.  ``context`` carries ``task_id, turn_id, api_request_id,
    session_id, platform, model, provider, base_url, api_mode, api_call_count`` (plus
    ``original_request``), and is read defensively: unknown and missing keys are fine.

    Returns ``None`` when the request must be left alone (the default), a
    ``{"request": {...}}`` replacement in ``mutate`` mode, and raises in ``raise`` mode.
    """
    mode = _probe_mode()

    try:
        _write_record(_build_record(request, context, mode))
    except Exception:
        # Observation is never allowed to affect the request path.
        pass

    if mode == MODE_RAISE:
        raise RuntimeError(DELIBERATE_FAILURE_MESSAGE)

    if mode == MODE_MUTATE:
        try:
            mutated = _mutate(request, _mutate_marker())
        except Exception:
            return None
        if mutated is not None:
            return {"request": mutated}

    return None


def _probe_mode() -> str:
    """Effective mode; anything unset or unrecognised is ``observe``."""
    try:
        raw = os.environ.get(MODE_ENV_VAR) or ""
    except Exception:
        return MODE_OBSERVE
    mode = raw.strip().lower()
    return mode if mode in _PROBE_MODES else MODE_OBSERVE


def _mutate_marker() -> str:
    """Sentinel appended in ``mutate`` mode; empty means "no marker configured"."""
    try:
        return os.environ.get(MARKER_ENV_VAR) or ""
    except Exception:
        return ""


# ── record construction ───────────────────────────────────────────────────────────


def _build_record(request: Any, context: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """Build one record from *request* and the middleware context.  Reads only structure."""
    payload = request if isinstance(request, dict) else {}
    api_mode = _context_str(context, "api_mode")
    system_text = _system_text(payload)
    tool_names = _tool_names(payload)

    return {
        "ts": _utc_now_iso(),
        "mode": mode,
        "session_id": _context_str(context, "session_id"),
        "turn_id": _context_str(context, "turn_id"),
        "api_request_id": _context_str(context, "api_request_id"),
        "api_mode": api_mode,
        "model": _context_str(context, "model"),
        "provider": _context_str(context, "provider"),
        "api_call_count": _int_or_none(context.get("api_call_count")),
        "request_keys": sorted(str(key) for key in payload),
        "message_count": _message_count(payload),
        "roles": _roles(payload),
        "system_present": system_text is not None,
        "system_len": len(system_text) if system_text is not None else 0,
        "system_sha256_16": _digest(system_text) if system_text is not None else None,
        "tools_count": len(tool_names),
        "tool_names": tool_names,
        "responses_shape": _is_responses_shape(payload, api_mode),
    }


def _utc_now_iso() -> str:
    """UTC timestamp, millisecond precision, ``Z`` suffixed."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _digest(text: str) -> str:
    """First 16 hex chars of the SHA-256 of *text* -- a digest, never the text."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _context_str(context: Dict[str, Any], key: str) -> Optional[str]:
    """String form of a context value; ``None`` when the key is absent."""
    value = context.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return str(value)
    except Exception:
        return None


def _int_or_none(value: Any) -> Optional[int]:
    """``int(value)`` when that is meaningful; ``None`` otherwise (bools are refused)."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _role_of(item: Dict[str, Any]) -> str:
    role = item.get("role")
    return role if isinstance(role, str) else ""


def _sequence_items(payload: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    """Dict items of ``payload[key]`` when it is a list; empty list for any other type."""
    value = payload.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _message_count(payload: Dict[str, Any]) -> int:
    """Message count of the payload's conversation list, whichever shape carries it.

    Chat Completions counts ``messages``; the Responses API counts its ``input`` items (a
    bare ``input`` string counts as one).
    """
    messages = payload.get("messages")
    if isinstance(messages, list):
        return len(messages)
    items = payload.get("input")
    if isinstance(items, list):
        return len(items)
    if isinstance(items, str):
        return 1 if items else 0
    return 0


def _roles(payload: Dict[str, Any]) -> List[str]:
    """Role strings in payload order -- never content, never non-role metadata."""
    roles: List[str] = []
    for key in ("messages", "input"):
        for item in _sequence_items(payload, key):
            role = _role_of(item)
            if role:
                roles.append(role)
    return roles


def _tool_names(payload: Dict[str, Any]) -> List[str]:
    """Tool names in payload order, for both tool schemas.

    Chat Completions nests the name under ``function``; the Responses API puts it flat.
    Descriptions and parameter schemas are deliberately not read.
    """
    tools = payload.get("tools")
    if not isinstance(tools, list):
        return []
    names: List[str] = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = tool.get("name")
        if not isinstance(name, str):
            function = tool.get("function")
            if isinstance(function, dict):
                name = function.get("name")
        if isinstance(name, str) and name:
            names.append(name)
    return names


def _is_responses_shape(payload: Dict[str, Any], api_mode: Optional[str]) -> bool:
    """True when the payload is Responses-API shaped rather than Chat Completions.

    A ``messages`` list settles it as Chat Completions.  Otherwise the presence of ``input``
    or ``instructions`` is decisive, and ``api_mode`` is the last resort for a payload that
    somehow carries neither.
    """
    if isinstance(payload.get("messages"), list):
        return False
    if "input" in payload or "instructions" in payload:
        return True
    return (api_mode or "").strip().lower() == "codex_responses"


# ── system-message inspection ─────────────────────────────────────────────────────


def _text_of(value: Any) -> Optional[str]:
    """Extract text from a message ``content`` value, or ``None`` when there is none.

    Strings come back verbatim.  Block lists (multimodal content, Anthropic blocks, Responses
    input parts) are joined on their ``text`` members.  ``None`` means "not a text carrier",
    which is different from ``""`` -- a carrier that exists but holds no text.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for block in value:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts) if parts else None
    if isinstance(value, dict) and isinstance(value.get("text"), str):
        return value["text"]
    return None


def _system_text(payload: Dict[str, Any]) -> Optional[str]:
    """System-prompt text of either payload shape, or ``None`` when there is no carrier.

    Precedence mirrors :func:`_mutate` so that what is recorded is what a mutation would
    touch: a ``messages`` item with a system role, then top-level ``instructions``
    (Responses) or ``system`` (Anthropic-shaped), then an ``input`` item with a system role.
    Every probe is type-guarded; a key of the wrong type is skipped rather than raised on.
    """
    for item in _sequence_items(payload, "messages"):
        if _role_of(item) in _SYSTEM_ROLES:
            return _text_of(item.get("content")) or ""

    for key in ("instructions", "system"):
        if key in payload:
            text = _text_of(payload.get(key))
            if text is not None:
                return text

    for item in _sequence_items(payload, "input"):
        if _role_of(item) in _SYSTEM_ROLES:
            return _text_of(item.get("content")) or ""

    return None


# ── mutate mode ───────────────────────────────────────────────────────────────────


def _mutate(request: Any, marker: str) -> Optional[Dict[str, Any]]:
    """Copy of *request* with *marker* appended to its system message, or ``None``.

    ``None`` means "leave the request alone": no marker configured, not a dict, an
    unappendable carrier, or a shape with no system slot to write to.  Callers must not
    treat it as a change.  The original dict and its nested messages are never modified --
    a new dict is returned -- so nothing the caller still holds is aliased into the rewrite.

    The carrier search is the one :func:`_system_text` performs, in the same order, so the
    rewrite always lands on the message that was recorded.  Only when *no* carrier exists is
    one created, and then in the shape's own system slot (a Chat Completions system message,
    or Responses' top-level ``instructions``) so the request stays valid for the API in use.
    """
    if not marker or not isinstance(request, dict):
        return None

    messages = request.get("messages")
    if isinstance(messages, list):
        for index, item in enumerate(messages):
            if isinstance(item, dict) and _role_of(item) in _SYSTEM_ROLES:
                content = _append_to_content(item.get("content"), marker)
                if content is None:
                    return None
                updated = list(messages)
                updated[index] = {**item, "content": content}
                return {**request, "messages": updated}

    for key in ("instructions", "system"):
        if key not in request or _text_of(request.get(key)) is None:
            continue
        content = _append_to_content(request.get(key), marker)
        if content is None:
            return None
        return {**request, key: content}

    items = request.get("input")
    if isinstance(items, list):
        for index, item in enumerate(items):
            if isinstance(item, dict) and _role_of(item) in _SYSTEM_ROLES:
                content = _append_to_content(item.get("content"), marker)
                if content is None:
                    return None
                updated = list(items)
                updated[index] = {**item, "content": content}
                return {**request, "input": updated}

    if isinstance(messages, list):
        return {**request, "messages": [{"role": "system", "content": marker}, *messages]}
    if isinstance(items, list) and "instructions" not in request:
        return {**request, "instructions": marker}

    return None


def _append_to_content(content: Any, marker: str) -> Any:
    """*content* with *marker* appended, or ``None`` when the value cannot take one."""
    if isinstance(content, str):
        return marker if not content else content + MARKER_SEPARATOR + marker
    if isinstance(content, list):
        return [*content, {"type": "text", "text": marker}]
    if content is None:
        return marker
    return None


# ── the log ───────────────────────────────────────────────────────────────────────


def _hermes_home() -> Optional[Path]:
    """Active Hermes home: the context-local/profile-aware resolver, else the platform default.

    Resolved per call, never cached, because one process can serve several profiles.
    """
    try:
        from hermes_constants import get_hermes_home

        return Path(get_hermes_home())
    except Exception:
        pass

    try:
        raw = (os.environ.get(HOME_ENV_VAR) or "").strip()
        if raw:
            return Path(os.path.expandvars(os.path.expanduser(raw)))
        if os.name == "nt":
            base = (os.environ.get("LOCALAPPDATA") or "").strip()
            root = Path(base) if base else Path.home() / "AppData" / "Local"
            return root / "hermes"
        return Path.home() / ".hermes"
    except Exception:
        return None


def _log_path() -> Optional[Path]:
    home = _hermes_home()
    return None if home is None else home / LOG_DIRNAME / LOG_FILENAME


def _write_record(record: Dict[str, Any]) -> bool:
    """Append one sanitized record.  Returns success and never raises.

    The line is a whitelist projection over :data:`RECORD_FIELDS`, so only schema fields can
    reach the file.  Failures are reported once per process, by stage and exception *class*
    only -- an exception message could quote payload text, and this is the one place that
    could leak it.
    """
    path = None
    try:
        path = _log_path()
        if path is None:
            _report_write_failure("resolve-home")
            return False
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _report_write_failure("mkdir", exc)
            return False
        line = json.dumps(
            {key: record.get(key) for key in RECORD_FIELDS},
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
        return True
    except Exception as exc:
        _report_write_failure("write", exc)
        return False


def _report_write_failure(stage: str, exc: Optional[BaseException] = None) -> None:
    """Warn once per process that probe records are not being persisted."""
    global _write_failure_reported
    if _write_failure_reported:
        return
    _write_failure_reported = True
    detail = f" ({type(exc).__name__})" if exc is not None else ""
    try:
        sys.stderr.write(
            f"contextmux-probe: probe log write failed at {stage}{detail}; "
            "continuing without structural logging\n"
        )
        sys.stderr.flush()
    except Exception:
        pass