"""Generate unlazy ledgers for the ContextMux Phase 1B scope.

Each runnable gate verifies the LEAF's OWN evidence artifact through one shared
validator (scripts/verify-leaf.mjs), parametrised by leaf id and mode. That keeps
one verified code path instead of fifteen bespoke oracles.

Run from the repository root:  python scripts/gen-ledgers.py
"""

from pathlib import Path

ROOT = Path(".unlazy/contextmux-phase1b")
G = ROOT / "gates"
G.mkdir(parents=True, exist_ok=True)

# leaf id -> (owns, scope sentence, runnable gates, manual gate titles)
LEAVES: dict[str, tuple[str, str, list[tuple[str, str, str, str]], list[str]]] = {
    "1.1.1": (
        "plugins/contextmux-probe/**, probe/**",
        "A Hermes plugin that registers llm_request middleware, records sanitized structural facts, and never persists prompt content.",
        [("G1", "the probe plugin exists and registers llm_request",
          "node scripts/verify-leaf.mjs --leaf 1.1.1 --mode source",
          "leaf 1.1.1 source verified")],
        ["a human read the redaction path and confirms no message content is written"],
    ),
    "1.1.2": (
        "harness/**",
        "A fresh-process vehicle that loads the probe plugin and captures a request dump without touching the running desktop app.",
        [("G1", "the harness runs a fresh hermes process and captures output",
          "node scripts/verify-leaf.mjs --leaf 1.1.2 --mode harness",
          "leaf 1.1.2 harness verified")],
        [],
    ),
    "1.1.2.1": (
        "harness/discovery/**",
        "Proof that a fresh hermes process discovers and loads the probe plugin.",
        [("G1", "plugin discovery is confirmed in a fresh process",
          "node scripts/verify-leaf.mjs --leaf 1.1.2.1 --mode evidence",
          "leaf 1.1.2.1 evidence verified")],
        [],
    ),
    "1.1.2.2": (
        "harness/dump/**",
        "Proof that HERMES_DUMP_REQUESTS produces a readable outbound-body dump from a fresh process.",
        [("G1", "request dump capture is wired and readable",
          "node scripts/verify-leaf.mjs --leaf 1.1.2.2 --mode evidence",
          "leaf 1.1.2.2 evidence verified")],
        [],
    ),
    "1.2.1.1": (
        "evidence/1.2.1.1/**",
        "The measured llm_request invocation count for a turn that makes no tool call.",
        [("G1", "the no-tool invocation count is measured, not assumed",
          "node scripts/verify-leaf.mjs --leaf 1.2.1.1 --mode count",
          "leaf 1.2.1.1 count verified")],
        [],
    ),
    "1.2.1.2": (
        "evidence/1.2.1.2/**",
        "The measured llm_request invocation count for a turn that makes at least one tool call.",
        [("G1", "the tool-loop invocation count is measured, not assumed",
          "node scripts/verify-leaf.mjs --leaf 1.2.1.2 --mode count",
          "leaf 1.2.1.2 count verified")],
        [],
    ),
    "1.2.2": (
        "evidence/1.2.2/**",
        "A decided answer, derived from the two measured counts, on whether routing must be cached once per session_id+turn_id.",
        [("G1", "the cache decision cites both measured counts",
          "node scripts/verify-leaf.mjs --leaf 1.2.2 --mode decision",
          "leaf 1.2.2 decision verified")],
        ["the driver reviews the decision against the raw counts rather than the summary"],
    ),
    "1.2.3": (
        "evidence/1.2.3/**",
        "Runtime proof that a raising middleware does not break the turn and the unmodified request proceeds.",
        [("G1", "a deliberately raising probe still completes the turn",
          "node scripts/verify-leaf.mjs --leaf 1.2.3 --mode evidence",
          "leaf 1.2.3 evidence verified")],
        [],
    ),
    "1.2.4": (
        "evidence/1.2.4/**",
        "Proof that a mutating middleware does not rewrite persisted conversation history.",
        [("G1", "persisted history is byte-identical across a mutating turn",
          "node scripts/verify-leaf.mjs --leaf 1.2.4 --mode evidence",
          "leaf 1.2.4 evidence verified")],
        ["a human confirms the comparison is against the persisted session store, not memory"],
    ),
    "1.3.1": (
        "evidence/1.3.1/**",
        "Runtime proof that the skill index is structurally identifiable inside the outbound request.",
        [("G1", "the skill index boundary is located at runtime",
          "node scripts/verify-leaf.mjs --leaf 1.3.1 --mode evidence",
          "leaf 1.3.1 evidence verified")],
        [],
    ),
    "1.3.2.1": (
        "evidence/1.3.2.1/**",
        "Proof that catalog suppression applied on the first call of a fresh conversation persists, plus the measured token saving.",
        [("G1", "suppression applied at first call survives the conversation",
          "node scripts/verify-leaf.mjs --leaf 1.3.2.1 --mode evidence",
          "leaf 1.3.2.1 evidence verified"),
         ("G2", "the catalog-free saving is measured in tokens",
          "node scripts/verify-leaf.mjs --leaf 1.3.2.1 --mode saving",
          "leaf 1.3.2.1 saving verified")],
        [],
    ),
    "1.3.2.2": (
        "evidence/1.3.2.2/**",
        "Proof that the transformed system prompt is byte-stable across every call of the conversation.",
        [("G1", "the transformed system prefix is byte-identical on every call",
          "node scripts/verify-leaf.mjs --leaf 1.3.2.2 --mode stability",
          "leaf 1.3.2.2 stability verified")],
        [],
    ),
    "1.3.3": (
        "evidence/1.3.3/**",
        "Proof that turn-local selection can be injected at the volatile boundary without disturbing the stable prefix.",
        [("G1", "turn-local injection is possible and leaves the stable prefix intact",
          "node scripts/verify-leaf.mjs --leaf 1.3.3 --mode evidence",
          "leaf 1.3.3 evidence verified")],
        [],
    ),
    "1.4.1": (
        "evidence/1.4.1/**",
        "The chat_completions path reaches the seam with its messages-shaped payload.",
        [("G1", "chat_completions reaches the middleware at runtime",
          "node scripts/verify-leaf.mjs --leaf 1.4.1 --mode evidence",
          "leaf 1.4.1 evidence verified")],
        [],
    ),
    "1.4.2": (
        "evidence/1.4.2/**",
        "The codex_responses path reaches the seam with its input-shaped payload.",
        [("G1", "codex_responses reaches the middleware at runtime",
          "node scripts/verify-leaf.mjs --leaf 1.4.2 --mode evidence",
          "leaf 1.4.2 evidence verified")],
        [],
    ),
    "1.5.1": (
        "evidence/1.5.1/**",
        "Proof that Hermes Tool Search still functions normally with the probe installed.",
        [("G1", "Tool Search remains functional with the probe present",
          "node scripts/verify-leaf.mjs --leaf 1.5.1 --mode evidence",
          "leaf 1.5.1 evidence verified")],
        [],
    ),
    "1.5.2": (
        "evidence/1.5.2/**",
        "Proof that the probe does not perturb the outbound tools array.",
        [("G1", "the tools array is unchanged by the probe",
          "node scripts/verify-leaf.mjs --leaf 1.5.2 --mode equivalence",
          "leaf 1.5.2 equivalence verified")],
        [],
    ),
}

BRANCHES: dict[str, tuple[str, str]] = {
    "1.1": ("1.1.1, 1.1.2, 1.1.2.1, 1.1.2.2",
            "the probe harness loads in a fresh process and records structurally"),
    "1.2": ("1.2.1.1, 1.2.1.2, 1.2.2, 1.2.3, 1.2.4",
            "invocation semantics are measured and the cache decision follows from them"),
    "1.3": ("1.3.1, 1.3.2.1, 1.3.2.2, 1.3.3",
            "prompt-shape claims hold at runtime without disturbing the stable prefix"),
    "1.4": ("1.4.1, 1.4.2",
            "both API modes reach the seam with their respective shapes"),
    "1.5": ("1.5.1, 1.5.2",
            "the probe coexists with Tool Search and does not perturb tools"),
}


def write(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


for leaf, (owns, scope, runnable, manual) in LEAVES.items():
    lines = [f"# Gates: leaf-{leaf}", "", f"OWNS: {owns}", "", f"Scope: {scope}", ""]
    for gid, title, check, expect in runnable:
        lines += [f"- [ ] {gid}: {title}", f"  CHECK: {check}", f"  EXPECT: {expect}",
                  "  EVIDENCE: pending", ""]
    for i, title in enumerate(manual, start=len(runnable) + 1):
        lines += [f"- [ ] G{i}: {title}", "  EVIDENCE: pending", ""]
    write(G / f"leaf-{leaf}.md", lines)

for branch, (kids, scope) in BRANCHES.items():
    write(G / f"node-{branch}.md", [
        f"# Gates: node-{branch}", "", f"Children: {kids}", "", f"Scope: {scope}", "",
        "- [ ] G1: every child ledger is reverified, not merely status-read",
        f"  CHECK: node scripts/verify-leaf.mjs --branch {branch} --mode reverify",
        f"  EXPECT: branch {branch} children reverified",
        "  EVIDENCE: pending", "",
        "- [ ] G2: the branch interface claim holds end to end",
        "  EVIDENCE: pending", "",
    ])

write(ROOT / "GATES.md", [
    "# Gates: ContextMux Phase 1B", "",
    "OWNS: .unlazy/contextmux-phase1b/**, docs/phase-1b-*.md, evidence/**, harness/**, scripts/**, probe/**", "",
    "Scope: empirically prove the Hermes llm_request middleware contract and report it without converting any assumption to PASS.", "",
    "- [ ] G1: every required contract item has current runtime evidence",
    "  CHECK: node scripts/verify-leaf.mjs --root --mode inventory",
    "  EXPECT: Phase 1B contract inventory reconciled",
    "  EVIDENCE: pending", "",
    "- [ ] G2: no claim is reported as PASS without a runtime observation",
    "  CHECK: node scripts/verify-leaf.mjs --root --mode honesty",
    "  EXPECT: no unobserved claim reported as pass",
    "  EVIDENCE: pending", "",
    "- [ ] G3: the Phase 1B report remeasures every number immediately before reporting",
    "  EVIDENCE: pending", "",
])

files = sorted(G.glob("*.md"))
print(f"wrote {len(files)} ledgers, plus PLAN.md and GATES.md")
for p in files:
    print(f"   {p.name}")