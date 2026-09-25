# Gates: leaf-1.3.2.1

OWNS: evidence/1.3.2.1/**

Scope: Proof that catalog suppression applied on the first call of a fresh conversation persists, plus the measured token saving.

- [ ] G1: suppression applied at first call survives the conversation
  CHECK: node scripts/verify-leaf.mjs --leaf 1.3.2.1 --mode evidence
  EXPECT: leaf 1.3.2.1 evidence verified
  EVIDENCE: pending

- [ ] G2: the catalog-free saving is measured in tokens
  CHECK: node scripts/verify-leaf.mjs --leaf 1.3.2.1 --mode saving
  EXPECT: leaf 1.3.2.1 saving verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
ABANDON: G2 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
