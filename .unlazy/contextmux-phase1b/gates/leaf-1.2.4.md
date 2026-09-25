# Gates: leaf-1.2.4

OWNS: evidence/1.2.4/**

Scope: Proof that a mutating middleware does not rewrite persisted conversation history.

- [ ] G1: persisted history is byte-identical across a mutating turn
  CHECK: node scripts/verify-leaf.mjs --leaf 1.2.4 --mode evidence
  EXPECT: leaf 1.2.4 evidence verified
  EVIDENCE: pending

- [ ] G2: a human confirms the comparison is against the persisted session store, not memory
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
ABANDON: G2 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
