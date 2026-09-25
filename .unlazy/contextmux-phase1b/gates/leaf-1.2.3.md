# Gates: leaf-1.2.3

OWNS: evidence/1.2.3/**

Scope: Runtime proof that a raising middleware does not break the turn and the unmodified request proceeds.

- [ ] G1: a deliberately raising probe still completes the turn
  CHECK: node scripts/verify-leaf.mjs --leaf 1.2.3 --mode evidence
  EXPECT: leaf 1.2.3 evidence verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
