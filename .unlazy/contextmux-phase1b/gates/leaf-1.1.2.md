# Gates: leaf-1.1.2

OWNS: harness/**

Scope: A fresh-process vehicle that loads the probe plugin and captures a request dump without touching the running desktop app.

- [ ] G1: the harness runs a fresh hermes process and captures output
  CHECK: node scripts/verify-leaf.mjs --leaf 1.1.2 --mode harness
  EXPECT: leaf 1.1.2 harness verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
