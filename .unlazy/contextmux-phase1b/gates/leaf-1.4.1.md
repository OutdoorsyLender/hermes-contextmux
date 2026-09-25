# Gates: leaf-1.4.1

OWNS: evidence/1.4.1/**

Scope: The chat_completions path reaches the seam with its messages-shaped payload.

- [ ] G1: chat_completions reaches the middleware at runtime
  CHECK: node scripts/verify-leaf.mjs --leaf 1.4.1 --mode evidence
  EXPECT: leaf 1.4.1 evidence verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
