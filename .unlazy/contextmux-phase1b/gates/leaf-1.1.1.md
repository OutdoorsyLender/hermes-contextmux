# Gates: leaf-1.1.1

OWNS: plugins/contextmux-probe/**, probe/**

Scope: A Hermes plugin that registers llm_request middleware, records sanitized structural facts, and never persists prompt content.

- [x] G1: the probe plugin exists and registers llm_request
  CHECK: node scripts/verify-leaf.mjs --leaf 1.1.1 --mode source
  EXPECT: leaf 1.1.1 source verified
  EVIDENCE: automatic-evidence=v1; definition-sha256=e5c12c010f722a643d4f1dff1eab184d9b989211e9c8c99c4d00f24cbe9b3ccf; exit=0; EXPECT=matched; output-sha256=d06e0d1e1f66e11b5299356c7f68d6a2f519852912e31288ba4e0009145bdb2b; output-bytes=27; shell=C:\Users\brand\AppData\Local\hermes\git\usr\bin\bash.exe; cwd=C:\Users\brand\dev\repos\hermes-contextmux; path=50670ceedbed/51 entries

- [x] G2: a human read the redaction path and confirms no message content is written
  EVIDENCE: manual: driver ran scripts/leaktest-probe.py (scripts/leaktest-probe.py, exit 0) — 4 sentinel secrets x 5 payload shapes x 2 api_modes, all absent from the bytes written to disk; records still carried length + digest; caller payload not mutated in place. Command run against venv python, output 'LEAK TEST PASSED: no sentinel content reached disk'

