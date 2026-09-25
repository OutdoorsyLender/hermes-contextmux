# ContextMux — Phase 1B Result

**Status: PARTIAL — halted by operator decision, not by a failed probe.**

Date: 2026-09-24
Scope: `.unlazy/contextmux-phase1b`
Branch: `feature/contextmux-v0.1`
Decision record: [`decision.md`](decision.md)

> Every number below was remeasured immediately before this report was written
> (`GATES:G3`). Nothing here is carried forward from an earlier run on trust.

---

## REQUIRED KEY SET

```
CONTEXTMUX_PHASE_1B                       = PARTIAL
```

**PARTIAL, not PASS and not FAIL.** One of seventeen leaves was built and verified
end to end. The other sixteen were **abandoned by explicit operator decision**, not
attempted and failed. Per unlazy's rules an abandonment is terminal and is *never*
successful completion — this scope exits `HANDOFF REQUIRED`.

```
OUTBOUND_MUTATION_PROVEN                  = NOT TESTED
CHAT_COMPLETIONS_RUNTIME_TEST             = NOT TESTED
CODEX_RESPONSES_RUNTIME_TEST              = NOT TESTED
PERSISTED_HISTORY_UNCHANGED               = NOT TESTED
FAIL_OPEN_RUNTIME_PROVEN                  = NOT TESTED
```

These were the subject of leaves `1.2.x` and `1.4.x`. **The probe plugin was built
and its redaction path was proven, but no live Hermes turn was ever driven through
it.** The spec's own rule — *"Do not convert assumptions into PASS"* — is why these
read `NOT TESTED` rather than being inferred from the Phase 1A source trace.

```
MIDDLEWARE_CALLS_PER_TURN                 = NOT MEASURED
MIDDLEWARE_REPEATS_AFTER_TOOL_CALL        = NOT MEASURED
TURN_LEVEL_ROUTE_CACHE_REQUIRED           = UNDETERMINED
SKILL_INDEX_STRUCTURALLY_IDENTIFIABLE     = YES (source-verified)
FIRST_CALL_SUPPRESSION_PROVEN             = NO
TRANSFORMED_SYSTEM_PREFIX_BYTE_STABLE     = NOT TESTED
CATALOG_FREE_SAVINGS_TOKENS               = 2330   (measured, see below)
TURN_LOCAL_INJECTION_PROVEN               = NO
TOOL_SEARCH_REMAINS_FUNCTIONAL            = YES — BY DESIGN, and now moot
PLUGIN_ONLY_CONTEXTMUX_FEASIBLE           = CONDITIONAL (and not worth the conditions)
```

```
CRITICAL_FINDINGS
```

**1. The spec's core mechanism is cache-hostile, and Phase 1A proved it from source.**

`agent/prompt_builder.py:1243` `build_skills_system_prompt()` emits the skill catalog
into the **system prompt** — cache breakpoint 1, byte-stable for the life of a
conversation. Suppressing it per-turn mutates that breakpoint and re-bills the
protected prefix.

**2. Hermes already ships the tool half of the problem — enabled, and more capable
than the spec's design.**

```
tools.tool_search:
  enabled: 'on'
  threshold_pct: 5
  search_default_limit: 5
  max_search_limit: 25
  listing: auto
  listing_max_tokens: 4000
```

It is tiered: tier 0 (no deferrable tools) → everything eager; tier 1 → bridge plus a
name+description manifest when it fits the budget; tier 2 (over budget even
names-only, e.g. ~3,300-tool APIs) → bare bridge plus a one-line-per-server summary.
Anthropic's evals on this feature report **49% → 74% accuracy**. The spec's own
invariant #8 cedes this surface to Hermes, so ContextMux would inherit it, not build it.

**3. The savings are already negligible, measured.**

| Quantity | Tokens |
|---|---|
| RAG-MCP static tool injection (the problem *they* solved) | ~6,630 |
| RAG-MCP after retrieval (their fix) | ~1,670 |
| **Our entire skill catalog in the system prompt (remeasured)** | **2,330** |

Our always-on catalog is **1.4× RAG-MCP's optimized state** and **0.35× their
unoptimized state.** The problem ContextMux solves is real at hundreds of skills; the
catalog here is 78.

**4. Prior art is mature — this does not need to be invented.**

- **RAG-MCP** — arXiv `2505.03275`, retrieval-augmented tool selection, >50% token cut,
  selection accuracy 13% → 43% on large toolsets. The accuracy gain, not the token
  gain, is the compelling result — and it appears at *catalog scale* we do not have.
- **Tool RAG** — Red Hat, production-grade through 2025.
- **arXiv `2602.12430`**, *Agent Skills for LLMs* — formalizes progressive disclosure as
  the architecture. Describes what Hermes already does.

```
IMPORTANT_FINDINGS
```

**5. The breakeven arithmetic is tighter than the first pass suggested, and that
tightens the conclusion rather than weakening it.**

```
skill index (remeasured 2026-09-24 18:05) : 9,320 chars  ≈ 2,330 tokens
system-prompt breakeven                   : ~2,600 tokens
ratio                                     : 0.90x breakeven
```

The index sits *just under* the breakeven line. That is the worst place for a
cache-mutating design to sit: the saving is small in absolute terms (2,330 tokens
against a context window of ~1M, i.e. ~0.2%), while the failure mode — re-billing a
protected prefix on every turn — is unbounded. A design whose upside is 0.2% and whose
downside is a per-turn prefix rebill is not a good trade at any catalog size we are
near.

**6. The genuinely uncovered problem is project-context routing, not skill routing.**

The spec's own split (Phase 15) is the valuable half:

> skill = procedure/how-to · **context = project state/facts**

Hermes loads context files from the CWD at startup, capped. **Nothing retrieves project
state per turn.** RAG-MCP does not cover it (tools). Tool Search does not cover it (MCP
tools). That gap is real — and it is reachable at rung 2 of Hermes' own Footprint
Ladder (CLI command + skill), one rung below the plugin the spec asked for.

```
MINOR_FINDINGS
```

**7. A negative result worth keeping.** The Phase 1A cache finding is the most valuable
artifact this project produced. It would have cost sixteen phases of building to
discover any other way.

**8. The probe plugin is sound and reusable.** Independent adversarial leak test
(driver-written, not the leaf's own): 4 sentinel secrets × 5 payload shapes × 2
`api_mode`s — **no sentinel content reached disk**; records still carried length and
digest; the caller's payload was not mutated in place. Registered middleware, handled
both `messages` and `input` shapes.

**9. `provides_middleware` is not in `_KNOWN_MANIFEST_FIELDS`** — a plugin declaring it
in `plugin.yaml` is not validated against it. Minor, but a real gap in plugin
manifest validation.

---

## What was actually verified

`met: 3` of 34 gates — and all three are honest:

| Gate | What it proves |
|---|---|
| `leaf-1.1.1:G1` | The probe plugin exists and registers `llm_request` (automatic, source oracle) |
| `leaf-1.1.1:G2` | A human/driver read the redaction path and ran an adversarial leak test (manual) |
| `GATES:G2` | No claim was reported as PASS without a runtime observation (automatic, honesty gate) |

**`GATES:G2` passing is the point.** The honesty gate is green precisely because
everything unproven is reported as unproven.

## Abandoned

`abandoned: 29` across 21 ledgers, plus `GATES:G1` (requires evidence for all 17 leaves;
impossible once the decision is to stop). Each carries an explicit
`ABANDON: <id> <reason>` line at column 1 naming the operator decision — **nothing was
silently deleted.**

Scope exits `HANDOFF REQUIRED` (exit 1). That is the correct terminal state for
abandonment.

## Files

- `scripts/verify-leaf.mjs` — the scope oracle, 17 leaf modes + 2 root modes
- `scripts/leaktest-probe.py` — adversarial leak test (driver-written)
- `scripts/close-phase1b.py` — records the manual gate and the abandonments
- `probe/contextmux-probe/{plugin.yaml,__init__.py}` — the probe plugin
- `docs/phase-1-feasibility.md` — the Phase 1A source trace (287 lines)