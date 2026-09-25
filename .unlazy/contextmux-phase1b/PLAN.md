# PLAN — ContextMux Phase 1B

**Scope:** `contextmux-phase1b` · **Contract revision:** 1
**Repository:** `~/dev/repos/hermes-contextmux` · **Branch:** `feature/contextmux-v0.1`
**Requested depth:** `tree 4` · **Actual depth:** 4

## Layer 1 — the requested task

Empirically prove the Hermes `llm_request` middleware contract before any production
ContextMux architecture is written. Phase 1A established this from source; Phase 1B must
**observe it at runtime** and convert nothing to PASS on assumption.

**Explicitly out of scope** (owner instruction): BM25, Jev, embeddings, telemetry,
project-context retrieval, and the production routing engine. No `resume-engine` work.

## Layer 2 — branches

| Branch | Contract | Verifying ledger | State |
|---|---|---|---|
| **1.1** Probe harness | A real Hermes plugin registering `llm_request`, writing sanitized structural records, plus the fresh-process vehicle to exercise it | `gates/node-1.1.md` | OPEN |
| **1.2** Invocation semantics | How often middleware fires, whether a per-turn route cache is required, fail-open at runtime, and that persisted history is untouched | `gates/node-1.2.md` | OPEN |
| **1.3** Prompt-shape semantics | Whether the skill index is structurally addressable, whether first-call suppression holds and stays byte-stable, and whether turn-local injection is possible | `gates/node-1.3.md` | OPEN |
| **1.4** API-mode coverage | Both `chat_completions` and `codex_responses` reach the seam with their respective payload shapes | `gates/node-1.4.md` | OPEN |
| **1.5** Tool Search coexistence | The probe does not perturb the `tools` array and Tool Search remains functional | `gates/node-1.5.md` | OPEN |

## Dispatch table

| Leaf | Owns | Needs | Tier | Planned wave | State |
|---|---|---|---|---|---|
| **1.1.1** | `plugins/contextmux-probe/**` (in `$HERMES_HOME`, mirrored under `probe/`) | — | judgment | ready-1 | WAITING |
| **1.1.2** | `harness/**` | 1.1.1 | judgment | ready-2 | WAITING |
| **1.1.2.1** | `harness/discovery/**` | 1.1.2 | mechanical | ready-3 | WAITING |
| **1.1.2.2** | `harness/dump/**` | 1.1.2 | mechanical | ready-3 | WAITING |
| **1.2.1.1** | `evidence/1.2.1.1/**` | 1.1.2.1, 1.1.2.2 | mechanical | ready-4 | WAITING |
| **1.2.1.2** | `evidence/1.2.1.2/**` | 1.1.2.1, 1.1.2.2 | mechanical | ready-4 | WAITING |
| **1.2.2** | `evidence/1.2.2/**` | 1.2.1.1, 1.2.1.2 | judgment | ready-5 | WAITING |
| **1.2.3** | `evidence/1.2.3/**` | 1.1.2.1 | mechanical | ready-4 | WAITING |
| **1.2.4** | `evidence/1.2.4/**` | 1.1.2.1 | mechanical | ready-4 | WAITING |
| **1.3.1** | `evidence/1.3.1/**` | 1.1.2.2 | judgment | ready-4 | WAITING |
| **1.3.2.1** | `evidence/1.3.2.1/**` | 1.3.1 | mechanical | ready-5 | WAITING |
| **1.3.2.2** | `evidence/1.3.2.2/**` | 1.3.2.1 | mechanical | ready-5 | WAITING |
| **1.3.3** | `evidence/1.3.3/**` | 1.3.1 | judgment | ready-4 | WAITING |
| **1.4.1** | `evidence/1.4.1/**` | 1.1.2.1, 1.1.2.2 | mechanical | ready-4 | WAITING |
| **1.4.2** | `evidence/1.4.2/**` | 1.1.2.1, 1.1.2.2 | mechanical | ready-4 | WAITING |
| **1.5.1** | `evidence/1.5.1/**` | 1.1.2.1, 1.1.2.2 | mechanical | ready-4 | WAITING |
| **1.5.2** | `evidence/1.5.2/**` | 1.1.2.2 | mechanical | ready-4 | WAITING |

**No two concurrent leaves own the same path.** Ownership is by repository-relative glob and
enforced by `gate-check --claim`.

## Contract items (independently omittable outcomes)

| id | Outcome | Owner | Observing gate | Disposition |
|---|---|---|---|---|
| C1 | Middleware mutation reaches the real outbound provider request | 1.2 | `1.2:G1` | required |
| C2 | `chat_completions` reaches the seam | 1.4.1 | `1.4.1:G1` | required |
| C3 | `codex_responses` reaches the seam | 1.4.2 | `1.4.2:G1` | required |
| C4 | Persisted conversation history unchanged by mutation | 1.2.4 | `1.2.4:G1` | required |
| C5 | Fail-open works at runtime, not only by source trace | 1.2.3 | `1.2.3:G1` | required |
| C6 | Middleware invocation count per turn is measured | 1.2.1.1 | `1.2.1.1:G1` | required |
| C7 | Behaviour across a tool-loop turn is measured | 1.2.1.2 | `1.2.1.2:G1` | required |
| C8 | Turn-level route cache requirement is decided from C6+C7 | 1.2.2 | `1.2.2:G1` | required |
| C9 | Skill index is structurally identifiable at runtime | 1.3.1 | `1.3.1:G1` | required |
| C10 | Suppression applies from the first call of a fresh conversation | 1.3.2.1 | `1.3.2.1:G1` | required |
| C11 | Transformed system prefix is byte-stable across the conversation | 1.3.2.2 | `1.3.2.2:G1` | required |
| C12 | Turn-local injection at the volatile boundary is possible | 1.3.3 | `1.3.3:G1` | required |
| C13 | Tool Search remains functional with the probe present | 1.5.1 | `1.5.1:G1` | required |
| C14 | The probe does not perturb the `tools` array | 1.5.2 | `1.5.2:G1` | required |
| C15 | Catalog-free saving is measured in tokens | 1.3.2.1 | `1.3.2.1:G2` | required |
| C16 | Plugin discovery works in a fresh process | 1.1.2.1 | `1.1.2.1:G1` | required |
| C17 | Request dump capture is wired | 1.1.2.2 | `1.1.2.2:G1` | required |

## Fixed interfaces (decided before fan-out)

- **Probe record** — one JSON object per line, `contextmux-probe.jsonl` under `$HERMES_HOME/logs/`.
  Fields: `ts, session_id, turn_id, api_request_id, api_mode, model, provider, api_call_count,
  request_keys, message_count, roles[], system_present, system_len, system_sha256_16,
  tools_count, tool_names[], responses_shape`.
  **Never persisted:** message content, prompt text, tool argument content, credentials.
- **Probe modes** — `CONTEXTMUX_PROBE_MODE` ∈ {`observe`, `mutate`, `raise`}. Default `observe`.
- **Mutate sentinel** — `CONTEXTMUX_MUTATE_MARKER`, appended to the system message only in `mutate`.
- **Redaction rule** — the probe hashes lengths and digests, never raw text.
- **Fail-open rule** — the probe's own handler is wrapped in `try/except`; it must return `None`
  on any internal failure.

## Toolchain

- shell: `C:\Users\brand\AppData\Local\hermes\git\usr\bin\bash.exe` (`UNLAZY_SHELL`)
- node `v22.23.2`; **native `C:/...` paths only for node** (MSYS form fails)
- python: `C:/Users/brand/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe` (Hermes venv)
- Fresh-process vehicle: `hermes chat -q "<prompt>"` — loads plugins at startup

## Error and compatibility conventions

- A surface that cannot be exercised is recorded `UNKNOWN` or `NOT_COVERED`, never inferred.
- A runtime result that contradicts the Phase 1A source trace is a **CRITICAL** finding.
- No `PASS` without a runtime observation.

## Integration gates (branch level)

Every branch must reverify its children, then check interfaces, end-to-end behaviour, and
regressions per `gates/node-<id>.md`.

## Notes

- This plan is a **dispatch** plan, not a difficulty claim. Per `references/method.md`, depth
  tracks real integration boundaries only. `tree 4` was honored and every L4 leaf is an
  independently verifiable outcome; a 5th level would be empty hierarchy.
- Phase 1A output that this phase tests: `docs/phase-1-feasibility.md`.