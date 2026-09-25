# Gates: leaf-1.5.2

OWNS: evidence/1.5.2/**

Scope: Proof that the probe does not perturb the outbound tools array.

- [ ] G1: the tools array is unchanged by the probe
  CHECK: node scripts/verify-leaf.mjs --leaf 1.5.2 --mode equivalence
  EXPECT: leaf 1.5.2 equivalence verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
