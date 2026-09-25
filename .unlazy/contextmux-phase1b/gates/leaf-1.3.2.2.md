# Gates: leaf-1.3.2.2

OWNS: evidence/1.3.2.2/**

Scope: Proof that the transformed system prompt is byte-stable across every call of the conversation.

- [ ] G1: the transformed system prefix is byte-identical on every call
  CHECK: node scripts/verify-leaf.mjs --leaf 1.3.2.2 --mode stability
  EXPECT: leaf 1.3.2.2 stability verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
