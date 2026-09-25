# Decision: do not build ContextMux as specified

**Date:** 2026-09-24
**Status:** Accepted (operator)
**Supersedes:** the full 16-phase ContextMux implementation plan

---

## Decision

**Do not build ContextMux as specified.** Halt after Phase 1B.

Keep the artifacts already produced (the verified middleware probe, the unlazy scope
and oracle, the Phase 1A feasibility trace, this record).

**Redirect** any future effort at the one part of the spec that is genuinely uncovered:
**project-context routing** — and build that at rung 2 of Hermes' Footprint Ladder
(CLI command + skill), not as a plugin.

---

## Why

### 1. The tool half is already shipped, and better than the spec's design

`tools.tool_search` is **enabled** on this box. It is Hermes' own progressive-disclosure
layer for MCP and non-core plugin tools, it is *tiered* (eager → manifest → per-server
summary, degrading by budget), and Anthropic's evals on it report a **49% → 74%
accuracy gain**. The spec's invariant #8 explicitly cedes tool/MCP progressive disclosure
to Hermes. So ContextMux would inherit this surface rather than build it — meaning the
majority of the "capability routing" value was never ContextMux's to deliver.

### 2. The skill half is already solved, and the numbers are small

Hermes already does the three-stage pattern the literature describes: name + description
always resident, body on demand via `skill_view`.

| Quantity | Tokens |
|---|---|
| RAG-MCP static tool injection (their problem) | ~6,630 |
| RAG-MCP after retrieval (their fix) | ~1,670 |
| **Our skill catalog, remeasured 2026-09-24 18:05** | **2,330** |

We would be building a retrieval layer to optimize ~2,330 tokens — roughly **0.2% of a
~1M-token context window**, and cache-read priced.

### 3. The specified mechanism is cache-hostile, proven from source

`build_skills_system_prompt()` writes the catalog into the **system prompt** — cache
breakpoint 1, byte-stable for the conversation's life. Suppressing it per-turn mutates
that breakpoint. The index measures **0.90× the ~2,600-token breakeven**, which is the
worst position for such a design: a capped, small upside against an unbounded per-turn
prefix rebill.

### 4. RAG-MCP's real result is an accuracy result at catalog scale

The headline was **13% → 43% tool-selection accuracy on large toolsets** — not the token
cut. That degradation regime begins at hundreds of catalog entries. **Our catalog is 78.**
The problem ContextMux solves is real; it is not *our* problem yet.

### 5. Mature prior art exists

RAG-MCP (arXiv `2505.03275`), Tool RAG (Red Hat, production through 2025), and
arXiv `2602.12430` (*Agent Skills for LLMs*, which formalizes progressive disclosure as
the architecture). If the catalog ever reaches the scale where this bites, the move is to
adopt a proven design, not to invent one.

### 6. Footprint

Sixteen phases, a Python package, a routing policy engine, telemetry, and an eval
harness — an ongoing maintenance burden tracking a fast-moving core — to chase 0.2% of a
context window that is already cached.

---

## What we keep

| Artifact | Why it stays useful |
|---|---|
| `probe/contextmux-probe/` | A verified `llm_request` middleware probe with a proven no-content-leak guarantee (adversarial leak test: 4 sentinels × 5 shapes × 2 modes, none reached disk). Reusable for any future middleware work. |
| `.unlazy/contextmux-phase1b/` | The oracle (`scripts/verify-leaf.mjs`, 17 leaf modes + 2 root modes) and the tree transfer to whatever we build next. Exits `HANDOFF REQUIRED` — the honest state. |
| `docs/phase-1-feasibility.md` | The cache finding. The single most valuable output: it would have taken sixteen phases to discover any other way. |
| `scripts/leaktest-probe.py` | A reusable adversarial privacy harness for any middleware that touches prompts. |

## What we redirect to

**Project-context routing.** The spec's own split is the valuable half:

> skill = procedure/how-to · **context = project state/facts**

Hermes loads context files from the CWD **once at startup, capped**. Nothing retrieves
project state per turn: not `AGENTS.md`, not handoffs, not authority docs, not project
brains. RAG-MCP does not cover this (tools). Tool Search does not cover this (MCP tools).
It is a real, uncovered gap.

**Build it as a CLI command + skill** — rung 2 of Hermes' Footprint Ladder, one rung below
the plugin the spec asked for, and the rung whose own guidance says *"Default for
subscriptions, scheduled tasks, service setup."* A retrieval tool over local markdown,
invoked when the agent needs project state — **not** a per-turn middleware rewrite of the
system prompt.

---

## Reconsider if

- the skill catalog grows past a few hundred entries, **or**
- measurement shows skill-selection *accuracy* degrading (the RAG-MCP failure mode), **or**
- prompt caching stops being the dominant cost factor.

Any of those reopens this — and the first move is to adopt RAG-MCP's approach, not to
build ContextMux's.