# Gates: leaf-1.1.2.1

OWNS: harness/discovery/**

Scope: Proof that a fresh hermes process discovers and loads the probe plugin.

- [ ] G1: plugin discovery is confirmed in a fresh process
  CHECK: node scripts/verify-leaf.mjs --leaf 1.1.2.1 --mode evidence
  EXPECT: leaf 1.1.2.1 evidence verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
