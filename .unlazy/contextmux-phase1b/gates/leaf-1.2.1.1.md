# Gates: leaf-1.2.1.1

OWNS: evidence/1.2.1.1/**

Scope: The measured llm_request invocation count for a turn that makes no tool call.

- [ ] G1: the no-tool invocation count is measured, not assumed
  CHECK: node scripts/verify-leaf.mjs --leaf 1.2.1.1 --mode count
  EXPECT: leaf 1.2.1.1 count verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
