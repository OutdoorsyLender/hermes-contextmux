# Gates: leaf-1.4.2

OWNS: evidence/1.4.2/**

Scope: The codex_responses path reaches the seam with its input-shaped payload.

- [ ] G1: codex_responses reaches the middleware at runtime
  CHECK: node scripts/verify-leaf.mjs --leaf 1.4.2 --mode evidence
  EXPECT: leaf 1.4.2 evidence verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
