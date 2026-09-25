# Gates: leaf-1.3.3

OWNS: evidence/1.3.3/**

Scope: Proof that turn-local selection can be injected at the volatile boundary without disturbing the stable prefix.

- [ ] G1: turn-local injection is possible and leaves the stable prefix intact
  CHECK: node scripts/verify-leaf.mjs --leaf 1.3.3 --mode evidence
  EXPECT: leaf 1.3.3 evidence verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
