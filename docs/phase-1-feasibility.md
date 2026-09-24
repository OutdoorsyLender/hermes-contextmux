# ContextMux — Phase 1 Hermes feasibility spike

**Date:** 2026-09-24 · **Repo:** `~/dev/repos/hermes-contextmux` @ `2d89d930` (moved from `C:\Projects` per owner instruction)
**Hermes inspected:** `C:\Users\brand\AppData\Local\hermes\hermes-agent` @ `a51143f` (2026-09-18)
**Status:** read-only source investigation. **No ContextMux code written. No Hermes file modified.**

---

## Verdict

```
CONTEXTMUX_MIDDLEWARE_SPIKE = PARTIAL

LLM_REQUEST_MIDDLEWARE_ACTIVE = YES
REQUEST_MESSAGES_MUTABLE      = YES
REQUEST_TOOLS_MUTABLE         = YES (structurally; mutation untested)
SKILL_INDEX_IDENTIFIABLE      = YES
SKILL_INDEX_REMOVABLE         = YES — but ONLY at conversation start, NEVER per-turn
TOOL_SEARCH_COMPATIBLE        = UNVERIFIED
CONTEXT_ENGINE_REQUIRED       = NO
CONTEXT_ENGINE_COEXISTENCE    = YES
FAIL_OPEN_PROVEN              = YES

STOCK_PROMPT_SKILL_INDEX_TOKENS   = ~2,302   (9,209 chars, measured live)
CATALOG_FREE_SKILL_INDEX_TOKENS   = 0
NAIVE_TOKEN_REDUCTION             = ~2,302 / turn
NAIVE_COST_EFFECT                 = WORSE THAN ZERO — see the critical finding

PLUGIN_ONLY_CONTEXTMUX_FEASIBLE = CONDITIONAL
```

**The seam exists and is better than the spec assumed. But the spec's per-turn catalog
suppression design would make cost worse, not better, and violates a core Hermes invariant.
The project is viable; that specific mechanism is not.**

---

## 1A — The `llm_request` middleware seam is real

**`hermes_cli/middleware.py`**

```python
LLM_REQUEST_MIDDLEWARE = "llm_request"                                    # :21
VALID_MIDDLEWARE = {TOOL_REQUEST_MIDDLEWARE, TOOL_EXECUTION_MIDDLEWARE,
                    LLM_REQUEST_MIDDLEWARE, LLM_EXECUTION_MIDDLEWARE}     # :24

@dataclass
class RequestMiddlewareResult:                                            # :30
    payload: Any
    original_payload: Any
    changed: bool = False
    trace: List[Dict[str, Any]] = field(default_factory=list)

def apply_llm_request_middleware(request, **context) -> RequestMiddlewareResult:   # :88
    """Apply registered LLM request middleware; {"request": {...}} replaces the provider kwargs."""
    if not has_middleware(LLM_REQUEST_MIDDLEWARE):
        return RequestMiddlewareResult(payload=request, original_payload=request)
    original_request = _safe_copy(request)
    return _apply_request_chain(
        LLM_REQUEST_MIDDLEWARE, "request", [], original_request,
        request=_safe_copy(original_request), original_request=original_request, **context)
```

**Confirmed properties:**

| Property | Evidence |
|---|---|
| A plugin returns `{"request": {...}}` to replace the outbound kwargs | module docstring + `_apply_request_chain` :70-76 |
| Middleware **chain** — each sees the prior's output | `for result in invoke_middleware(...)` :70 |
| `payload` is a **deep copy**, tolerating non-copyable members | `_safe_copy` :50 |
| The pre-middleware request is preserved as `original_payload` | :95 |
| **Explainability is built in** — `trace` records `source`/`reason`/`name` | :77-82 — satisfies invariant 19 |
| `changed` is derived from whether any middleware actually changed anything | :84 |

**Call site — `agent/turn_api_request.py:139-152`**

```python
try:
    from hermes_cli.middleware import apply_llm_request_middleware
    _llm_request_mw = apply_llm_request_middleware(
        api_kwargs, task_id=..., turn_id=..., api_request_id=..., session_id=..., platform=...,
        model=..., provider=..., base_url=..., api_mode=..., api_call_count=...)
    api_kwargs = _llm_request_mw.payload          # ← REPLACES the outbound request
    _original_api_kwargs = _llm_request_mw.original_payload
    _llm_middleware_trace = _llm_request_mw.trace
except Exception:                                  # ← FAIL-OPEN IS BUILT IN
    _original_api_kwargs = dict(api_kwargs)
    _llm_middleware_trace = []
```

**Three things this settles:**

1. **`REQUEST_MESSAGES_MUTABLE = YES`.** `api_kwargs = _llm_request_mw.payload` — the returned
   dict *is* what goes to the provider. `api_kwargs` is built from `_build_api_kwargs(api_messages)`
   at :118-120, so messages are inside it.
2. **`FAIL_OPEN_PROVEN = YES`.** Not by ContextMux's design — by Hermes' call site. A raising
   middleware is caught and the unmodified kwargs proceed. Invariant 12 is satisfied *upstream of
   us*, which is a stronger guarantee than anything ContextMux could implement itself. ContextMux
   should still log its own failures, but it cannot break the turn.
3. **Ordering:** `_build_api_kwargs` → `sanitize_outbound_kwargs` → transport preflight
   (`codex_responses`) → cache/initiator headers → **middleware** → `_fire_pre_api_request_hook`
   → `HERMES_DUMP_REQUESTS` dump → MoA injection. So middleware sees the **final assembled payload**
   and is the last mutation before the request is fired. That is the correct interception point.

**Context available to middleware** (useful for routing telemetry):
`task_id, turn_id, api_request_id, session_id, platform, model, provider, base_url, api_mode, api_call_count`.

**`api_call_count` matters:** it increments per tool-loop iteration, so middleware fires on
**every API call in a tool loop**, not once per turn. A naive per-turn router that recomputes
selection on each call would pay router cost N times per turn.

---

## 1C — The skill index: identified, and this is the critical finding

**`agent/prompt_builder.py:1`** — *"System prompt assembly -- identity, platform hints, **skills
index**, context files."*

**`prompt_builder.py:1243-1247`**

```python
def build_skills_system_prompt(...):
    """Compact skill index for the system prompt."""
```

**Measured live on this machine (calling the real function):**

```
skills index chars : 9,209
~tokens            : 2,302
```

### CRITICAL FINDING: the spec's design would make cost *worse*

`website/docs/developer-guide/context-compression-and-caching.md`, "Cache-Aware Design Patterns":

> **1. Stable system prompt**: The system prompt is **breakpoint 1 and cached across all turns.
> Avoid mutating it mid-conversation** (compression appends a note only on the first compaction).
>
> **2. Message ordering matters**: Cache hits require prefix matching. **Adding or removing
> messages in the middle invalidates the cache for everything after.**

And `agent/AGENTS.md`, "Message-flow invariants (every change is reviewed against these)":

> **Prompt caching must not break.** Never alter past context, change toolsets, reload memories,
> or rebuild the system prompt mid-conversation. **The system prompt is byte-stable for the life
> of a conversation; the ONLY context mutation is compression.** Anything that must inject content
> mid-conversation rides a **user message or tool result, never the system prompt.**

**The spec's architectural target is:**

```
ContextMux llm_request middleware
    +-- remove/suppress global skill catalog if safe     ← MUTATES BREAKPOINT 1, PER TURN
    +-- inject selected skill/context material           ← MUTATES THE PROMPT, PER TURN
```

**Suppressing the skill catalog per turn changes the system prompt per turn. That is exactly
the operation Hermes' most emphatic invariant forbids, and it is cache breakpoint 1.**

**The arithmetic:**

| | |
|---|---|
| Tokens saved per turn (removing the index) | **~2,302** |
| Consequence | Breakpoint-1 prefix no longer matches → **the entire protected prefix is re-billed uncached, every turn.** Not only the system prompt: "invalidates the cache for everything after" |
| Typical cache-read price vs full input | roughly an order of magnitude cheaper |
| Breakeven prefix size | ≈ **2,300 / 0.9 ≈ ~2,600 tokens** |
| Actual protected prefix | **far larger than 2,600 tokens** — system prompt alone is ~9k chars of skills index plus identity/platform/context/guidance, before any conversation history |

**Every real conversation is far past the breakeven. So the mechanism that is supposed to save
tokens would cost more on every turn of every conversation, and the penalty grows with
conversation length — precisely inverting the intended benefit.**

This is not a tuning problem. It is the stated design applied to the stated seam.

### The redesign that works

Both goals are achievable, but the split has to be different:

| Goal | Mechanism | Cache effect |
|---|---|---|
| **Shrink the stable prefix** | Omit the skill index from the system prompt **at conversation start** (config-driven, `skills.external_dirs`-style, decided once) | **Cache-safe** — system prompt stays byte-stable for the conversation's life |
| **Per-turn skill routing** | Inject the selected skills as a **user message or tool result**, which is the sanctioned mid-conversation injection path | **Cache-safe** — appends after the cached prefix; never rewrites it |
| **Never** | Mutate the system prompt, the tool list, or past context mid-conversation | Forbidden by invariant |

**This is a better product than the spec's version, not a compromise:**
- The 2,302-token saving applies to **every** turn when configured at start (the spec's design
  saved it too, but paid far more for it).
- Per-turn routing still works — the parent model still sees only the useful skills for this turn.
- Nothing violates an invariant, so ContextMux stays installable on stock Hermes.

**It also changes a sizing assumption:** in the working design ContextMux mostly *adds* selected
skill bodies to the turn. The saving is the avoided static index; the cost is the injected bodies.
Whether that is net-negative depends on how many skills are selected and how large they are —
which is a **measurement in Phase 12**, not an assumption. `selected_k: 5` against an 11,532-char
average body (measured today in `skill-context-cost.md`) would inject far more than 2,302 tokens.
**That is the real trade to measure, and it may argue for a small `selected_k` and/or index-only
injection rather than full bodies.**

---

## 1F — Fail-open, verified by reading the call site

Not tested by making a probe fail, but the call site makes it structural:

```python
except Exception:
    _original_api_kwargs = dict(api_kwargs)
    _llm_middleware_trace = []
```

`api_kwargs` is unchanged in the handler, so the provider receives the pre-middleware request.
**A ContextMux crash cannot break a turn.** Worth an explicit probe test later (Phase 1B), but the
mechanism is not in doubt.

---

## 1G — Runtime coverage: NOT established

**This is the weakest area and I am not going to infer it.** What the source shows:

- The call site is in `agent/turn_api_request.py`, which serves the **interactive CLI and gateway
  alike** (the gateway drives the same `conversation_loop`). That suggests CLI + gateway + desktop
  are covered by one path.
- **`api_mode` is passed to middleware** and is one of
  `"chat_completions" | "codex_responses" | ...` (`agent/AGENTS.md`), and the preflight branch at
  `:124` only runs for `codex_responses`. So both API modes reach the middleware, but the payload
  *shape differs per mode* — `messages` for chat completions, `input` for Responses.
  **ContextMux must handle both shapes or detect and skip.** This is a real implementation
  requirement, not a formality.
- Auxiliary calls (curator, vision, compression, titles) go through `agent/auxiliary_client.py`,
  **a different path** — whether they hit this middleware is **unverified**.
- Delegated subagents run the same agent loop (`tools/delegate_tool.py`), so they likely do — **unverified**.
- Kanban/background workers run the agent loop — **unverified**.
- Cron passes `skip_memory=True` but its call path is **unverified**.

| Surface | Classification |
|---|---|
| Interactive CLI | `COVERED_BY_SOURCE_TRACE` |
| One-shot / headless | `COVERED_BY_SOURCE_TRACE` |
| Desktop / gateway | `COVERED_BY_SOURCE_TRACE` |
| Delegated subagents | `UNKNOWN` |
| Kanban / background workers | `UNKNOWN` |
| Auxiliary model calls | `UNKNOWN` — likely NOT_COVERED (separate client path) |
| Chat Completions | `COVERED_BY_SOURCE_TRACE` |
| Responses API (`codex_responses`) | `COVERED_BY_SOURCE_TRACE`, **different payload shape** |

**No surface is `COVERED_AND_TESTED`.** Phase 1B must close this before any production work.

---

## STOP RULE assessment

The spec's stop rule triggers on `PLUGIN_ONLY_CONTEXTMUX_FEASIBLE = NO`.

**It is `CONDITIONAL`, so the stop rule does not fire** — no Hermes upstream change is required.
The middleware seam is present, documented, chainable, trace-carrying and fail-open.

**But the condition is substantive:** plugin-only is feasible **only with the cache-safe design
above**. The spec's per-turn system-prompt mutation is not a smaller version of the same thing —
it is a different, self-defeating design.

---

## What I did not do

- **No ContextMux code written.** No scaffold, no branch, no commit in the new repo.
- **No Hermes file modified.** The `hermes-agent` checkout is untouched and remains
  updater-clean — verified read-only.
- **No runtime test run**, so nothing here is `COVERED_AND_TESTED`.
- **Tool Search interaction not investigated** — Phase 1D is unstarted.
- **ContextEngine coexistence not investigated** — Phase 1E is unstarted.
- **No token measurement from a real provider call.** 9,209 chars is the *assembled* index text;
  the provider's tokenizer would give a slightly different number, and the cached prefix's true
  size depends on the conversation.

## Recommended next step

**Do not start Phase 2 architecture yet.** Phase 1B's probe is still the gate, and it now has a
sharpened purpose: prove (a) mutation of messages and tools actually reaches the provider, (b)
addressing **both API modes**, and (c) that a cache-safe injection path — user message or tool
result — behaves as the invariants describe.

The single measurement that decides the product is: **for a realistic conversation, is
`avoided static index` + `injected selected bodies` net-negative against the cached baseline,
without ever invalidating breakpoint 1?** Everything else follows from that number.