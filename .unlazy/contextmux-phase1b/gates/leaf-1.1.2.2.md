# Gates: leaf-1.1.2.2

OWNS: harness/dump/**

Scope: Proof that HERMES_DUMP_REQUESTS produces a readable outbound-body dump from a fresh process.

- [ ] G1: request dump capture is wired and readable
  CHECK: node scripts/verify-leaf.mjs --leaf 1.1.2.2 --mode evidence
  EXPECT: leaf 1.1.2.2 evidence verified
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
