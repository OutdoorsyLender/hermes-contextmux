# Gates: node-1.5

Children: 1.5.1, 1.5.2

Scope: the probe coexists with Tool Search and does not perturb tools

- [ ] G1: every child ledger is reverified, not merely status-read
  CHECK: node scripts/verify-leaf.mjs --branch 1.5 --mode reverify
  EXPECT: branch 1.5 children reverified
  EVIDENCE: pending

- [ ] G2: the branch interface claim holds end to end
  EVIDENCE: pending


ABANDON: G1 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
ABANDON: G2 phase 1B halted by operator decision 2026-09-24: Phase 1A proved the spec's core mechanism re-bills the cached system-prompt prefix, and Hermes already ships the tool half (tools.tool_search, enabled) with the skill half already on 3-stage progressive disclosure at ~1,343 tokens/turn. Superseded by a project-context retrieval skill (decision record: docs/decision.md)
