# Gates: ContextMux Phase 1B

OWNS: .unlazy/contextmux-phase1b/**, docs/phase-1b-*.md, evidence/**, harness/**, scripts/**, probe/**

Scope: empirically prove the Hermes llm_request middleware contract and report it without converting any assumption to PASS.

- [ ] G1: every required contract item has current runtime evidence
  CHECK: node scripts/verify-leaf.mjs --root --mode inventory
  EXPECT: Phase 1B contract inventory reconciled
  EVIDENCE: pending

- [x] G2: no claim is reported as PASS without a runtime observation
  CHECK: node scripts/verify-leaf.mjs --root --mode honesty
  EXPECT: no unobserved claim reported as pass
  EVIDENCE: automatic-evidence=v1; definition-sha256=19c051bfbe7f5122ec8dc8bfdf7ccfcff7a411fe984a60f1fef634368fe2f872; exit=0; EXPECT=matched; output-sha256=056df284633bb9a9670008bd63c5766624247a7de8dae5485a6ff4ce9297d65a; output-bytes=37; shell=C:\Users\brand\AppData\Local\hermes\git\usr\bin\bash.exe; cwd=C:\Users\brand\dev\repos\hermes-contextmux; path=50670ceedbed/51 entries

- [x] G3: the Phase 1B report remeasures every number immediately before reporting
  EVIDENCE: manual: driver remeasured at 2026-09-24 18:05:20 USMST — skill index chars=9320 / ~2330 tokens (agent.prompt_builder.build_skills_system_prompt via hermes venv); breakeven ratio 0.90x of ~2600; tools.tool_search enabled='on'; hermes-agent HEAD ac4181fdfa with 0 dirty files; RAG-MCP comparison 6630->1670. Values written into docs/phase-1b-result.md CATALOG_FREE_SAVINGS_TOKENS=2330

ABANDON: G1 phase 1B halted by operator decision 2026-09-24 (see docs/decision.md): this gate requires current evidence for all 17 leaves, but only 1 leaf was built before the stop decision, so it is impossible under the decision rather than unmet by failure

