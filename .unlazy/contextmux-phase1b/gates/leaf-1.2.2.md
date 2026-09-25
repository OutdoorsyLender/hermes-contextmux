# Gates: leaf-1.2.2

OWNS: evidence/1.2.2/**

Scope: A decided answer, derived from the two measured counts, on whether routing must be cached once per session_id+turn_id.

- [ ] G1: the cache decision cites both measured counts
  CHECK: node scripts/verify-leaf.mjs --leaf 1.2.2 --mode decision
  EXPECT: leaf 1.2.2 decision verified
  EVIDENCE: pending

- [ ] G2: the driver reviews the decision against the raw counts rather than the summary
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
ABANDON: G2 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
