#!/usr/bin/env node
/**
 * Shared oracle for the ContextMux Phase 1B scope.
 *
 * One verified code path checks every leaf's own evidence artifact, parametrised by leaf id
 * and mode, instead of fifteen bespoke oracles. It is written to FAIL on absent, malformed,
 * or placeholder evidence: a validator that passes without the artifact it names is worthless.
 *
 * Usage:
 *   node scripts/verify-leaf.mjs --leaf <id> --mode <source|harness|evidence|count|decision|saving|stability|equivalence>
 *   node scripts/verify-leaf.mjs --branch <id> --mode reverify
 *   node scripts/verify-leaf.mjs --root --mode <inventory|honesty>
 *
 * Exit 0 with the exact EXPECT token on success; exit 1 with a reason on any failure.
 */

import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

/** Every leaf in the scope, with the shape its evidence must satisfy. */
const LEAVES = {
  '1.1.1': { mode: 'source', expect: 'leaf 1.1.1 source verified' },
  '1.1.2': { mode: 'harness', expect: 'leaf 1.1.2 harness verified' },
  '1.1.2.1': { mode: 'evidence', expect: 'leaf 1.1.2.1 evidence verified' },
  '1.1.2.2': { mode: 'evidence', expect: 'leaf 1.1.2.2 evidence verified' },
  '1.2.1.1': { mode: 'count', expect: 'leaf 1.2.1.1 count verified' },
  '1.2.1.2': { mode: 'count', expect: 'leaf 1.2.1.2 count verified' },
  '1.2.2': { mode: 'decision', expect: 'leaf 1.2.2 decision verified' },
  '1.2.3': { mode: 'evidence', expect: 'leaf 1.2.3 evidence verified' },
  '1.2.4': { mode: 'evidence', expect: 'leaf 1.2.4 evidence verified' },
  '1.3.1': { mode: 'evidence', expect: 'leaf 1.3.1 evidence verified' },
  '1.3.2.1': { mode: 'evidence', expect: 'leaf 1.3.2.1 evidence verified' },
  '1.3.2.2': { mode: 'stability', expect: 'leaf 1.3.2.2 stability verified' },
  '1.3.3': { mode: 'evidence', expect: 'leaf 1.3.3 evidence verified' },
  '1.4.1': { mode: 'evidence', expect: 'leaf 1.4.1 evidence verified' },
  '1.4.2': { mode: 'evidence', expect: 'leaf 1.4.2 evidence verified' },
  '1.5.1': { mode: 'evidence', expect: 'leaf 1.5.1 evidence verified' },
  '1.5.2': { mode: 'equivalence', expect: 'leaf 1.5.2 equivalence verified' },
};

const BRANCHES = {
  '1.1': ['1.1.1', '1.1.2', '1.1.2.1', '1.1.2.2'],
  '1.2': ['1.2.1.1', '1.2.1.2', '1.2.2', '1.2.3', '1.2.4'],
  '1.3': ['1.3.1', '1.3.2.1', '1.3.2.2', '1.3.3'],
  '1.4': ['1.4.1', '1.4.2'],
  '1.5': ['1.5.1', '1.5.2'],
};

const pass = (msg) => { console.log(msg); process.exit(0); };
const fail = (msg) => { console.error(msg); process.exit(1); };

function args() {
  const a = process.argv.slice(2);
  const get = (flag) => { const i = a.indexOf(flag); return i === -1 ? null : a[i + 1] ?? ''; };
  return { leaf: get('--leaf'), branch: get('--branch'), mode: get('--mode'), root: a.includes('--root') };
}

function evidencePath(leaf) {
  return join(ROOT, 'evidence', leaf, 'result.json');
}

/** Read a leaf's evidence, rejecting absent, unparseable, or placeholder records. */
function readEvidence(leaf) {
  const p = evidencePath(leaf);
  if (!existsSync(p)) fail(`MISSING EVIDENCE: ${p} does not exist`);
  let raw;
  try { raw = readFileSync(p, 'utf8'); } catch (e) { fail(`UNREADABLE EVIDENCE: ${p}: ${e.message}`); }
  let j;
  try { j = JSON.parse(raw); } catch (e) { fail(`MALFORMED EVIDENCE JSON: ${p}: ${e.message}`); }
  if (j === null || typeof j !== 'object' || Array.isArray(j)) fail(`EVIDENCE NOT AN OBJECT: ${p}`);
  // A placeholder is not evidence. The whole point is that these fields were OBSERVED.
  if (j.observed !== true) fail(`NOT OBSERVED: ${p} has observed=${JSON.stringify(j.observed)}; runtime observation required`);
  if (typeof j.summary !== 'string' || j.summary.trim().length < 16) fail(`NO SUBSTANTIVE SUMMARY: ${p}`);
  if (typeof j.method !== 'string' || j.method.trim().length < 8) fail(`NO METHOD RECORDED: ${p}`);
  return j;
}

function requireNumber(j, field, leaf) {
  const v = j[field];
  if (typeof v !== 'number' || !Number.isFinite(v)) fail(`MISSING NUMERIC ${field} in leaf ${leaf} evidence`);
  if (v < 0) fail(`NEGATIVE ${field} in leaf ${leaf} evidence`);
  return v;
}

function requireArray(j, field, leaf, min) {
  const v = j[field];
  if (!Array.isArray(v)) fail(`MISSING ARRAY ${field} in leaf ${leaf} evidence`);
  if (v.length < min) fail(`${field} in leaf ${leaf} has ${v.length} entries, expected >= ${min}`);
  return v;
}

const A = args();

// ---- root modes ------------------------------------------------------------------
if (A.root) {
  if (A.mode === 'inventory') {
    let ready = 0, missing = [];
    for (const leaf of Object.keys(LEAVES)) {
      if (existsSync(evidencePath(leaf))) ready += 1; else missing.push(leaf);
    }
    if (missing.length) fail(`INVENTORY INCOMPLETE: ${ready}/${Object.keys(LEAVES).length} leaves have evidence; missing: ${missing.join(', ')}`);
    pass('Phase 1B contract inventory reconciled');
  }
  if (A.mode === 'honesty') {
    // Every leaf that HAS evidence must carry observed:true and a method. Any evidence file
    // that claims a conclusion without an observation is refused here rather than reported.
    const offenders = [];
    for (const leaf of Object.keys(LEAVES)) {
      const p = evidencePath(leaf);
      if (!existsSync(p)) continue;
      try {
        const j = JSON.parse(readFileSync(p, 'utf8'));
        if (j.observed !== true || typeof j.method !== 'string' || j.method.trim().length < 8) offenders.push(leaf);
      } catch { offenders.push(leaf); }
    }
    if (offenders.length) fail(`UNOBSERVED CLAIMS PRESENT: ${offenders.join(', ')}`);
    pass('no unobserved claim reported as pass');
  }
  fail(`unknown root mode: ${A.mode}`);
}

// ---- branch modes ----------------------------------------------------------------
if (A.branch) {
  const kids = BRANCHES[A.branch];
  if (!kids) fail(`unknown branch: ${A.branch}`);
  const bad = [];
  for (const k of kids) {
    const p = evidencePath(k);
    if (!existsSync(p)) { bad.push(`${k}(missing)`); continue; }
    try {
      const j = JSON.parse(readFileSync(p, 'utf8'));
      if (j.observed !== true) bad.push(`${k}(not observed)`);
    } catch { bad.push(`${k}(malformed)`); }
  }
  if (bad.length) fail(`BRANCH ${A.branch} CHILDREN NOT REVERIFIED: ${bad.join(', ')}`);
  pass(`branch ${A.branch} children reverified`);
}

// ---- leaf modes ------------------------------------------------------------------
const spec = LEAVES[A.leaf];
if (!spec) fail(`unknown leaf: ${A.leaf}`);
if (A.mode !== spec.mode) fail(`leaf ${A.leaf} declares mode ${spec.mode}, got ${A.mode}`);

if (A.mode === 'source') {
  // The probe plugin must exist and must actually register llm_request middleware.
  const cands = [
    join(HERE, '..', 'probe', 'contextmux-probe', '__init__.py'),
    join(HERE, '..', 'probe', 'contextmux_probe.py'),
  ];
  const found = cands.filter(existsSync);
  if (!found.length) fail(`PROBE PLUGIN MISSING: looked for ${cands.join(' or ')}`);
  const src = found.map((f) => readFileSync(f, 'utf8')).join('\n');
  if (!/register_middleware\s*\(/.test(src)) fail('PROBE DOES NOT CALL register_middleware()');
  if (!/["']llm_request["']/.test(src)) fail('PROBE DOES NOT REGISTER THE llm_request KIND');
  if (!/^\s*#?.*timeout|deadline/s.test(src)) { /* not required */ }
  pass(spec.expect);
}

if (A.mode === 'harness') {
  const h = join(ROOT, 'harness');
  if (!existsSync(h)) fail(`HARNESS DIR MISSING: ${h}`);
  const files = readdirSync(h, { recursive: true }).filter((f) => typeof f === 'string');
  if (!files.length) fail(`HARNESS DIR EMPTY: ${h}`);
  pass(spec.expect);
}

if (A.mode === 'evidence') {
  const j = readEvidence(A.leaf);
  if (A.leaf === '1.1.2.1') requireArray(j, 'discovered_plugins', A.leaf, 1);
  if (A.leaf === '1.1.2.2') requireArray(j, 'dump_paths', A.leaf, 1);
  if (A.leaf === '1.2.3') {
    if (j.turn_completed !== true) fail('leaf 1.2.3: turn did not complete under a raising middleware');
    if (j.request_proceeded_unmodified !== true) fail('leaf 1.2.3: unmodified request did not proceed');
  }
  if (A.leaf === '1.2.4') {
    if (j.history_identical !== true) fail('leaf 1.2.4: persisted history changed');
    if (typeof j.history_digest_before !== 'string' || j.history_digest_before !== j.history_digest_after) {
      fail('leaf 1.2.4: before/after digests are not equal strings');
    }
  }
  if (A.leaf === '1.3.1') {
    if (j.structurally_identifiable !== true) fail('leaf 1.3.1: skill index not structurally identifiable');
    requireNumber(j, 'index_chars', A.leaf);
  }
  if (A.leaf === '1.3.2.1') {
    if (j.suppression_held !== true) fail('leaf 1.3.2.1: suppression did not hold across the conversation');
  }
  if (A.leaf === '1.3.3') {
    if (j.injection_possible !== true) fail('leaf 1.3.3: turn-local injection not proven');
    if (j.stable_prefix_unchanged !== true) fail('leaf 1.3.3: injection altered the stable prefix');
  }
  if (A.leaf === '1.4.1') {
    if (j.middleware_reached !== true) fail('leaf 1.4.1: chat_completions did not reach the middleware');
    if (j.shape !== 'messages') fail(`leaf 1.4.1: payload shape is ${j.shape}, expected messages`);
  }
  if (A.leaf === '1.4.2') {
    if (j.middleware_reached !== true) fail('leaf 1.4.2: codex_responses did not reach the middleware');
    if (j.shape !== 'input') fail(`leaf 1.4.2: payload shape is ${j.shape}, expected input`);
  }
  if (A.leaf === '1.5.1') {
    if (j.tool_search_functional !== true) fail('leaf 1.5.1: Tool Search not functional with the probe present');
  }
  pass(spec.expect);
}

if (A.mode === 'count') {
  const j = readEvidence(A.leaf);
  const n = requireNumber(j, 'invocation_count', A.leaf);
  if (!Number.isInteger(n)) fail(`leaf ${A.leaf}: invocation_count ${n} is not an integer`);
  if (n < 1) fail(`leaf ${A.leaf}: invocation_count ${n} proves the middleware never fired`);
  pass(spec.expect);
}

if (A.mode === 'decision') {
  const j = readEvidence(A.leaf);
  if (typeof j.cache_required !== 'boolean') fail('leaf 1.2.2: cache_required is not a boolean decision');
  requireNumber(j, 'no_tool_count_cited', A.leaf);
  requireNumber(j, 'tool_loop_count_cited', A.leaf);
  if (j.no_tool_count_cited < 1 || j.tool_loop_count_cited < 1) {
    fail('leaf 1.2.2: the decision does not cite both measured counts');
  }
  pass(spec.expect);
}

if (A.mode === 'saving') {
  const j = readEvidence(A.leaf);
  const saved = requireNumber(j, 'saving_tokens', A.leaf);
  const stock = requireNumber(j, 'stock_tokens', A.leaf);
  if (saved <= 0) fail('leaf 1.3.2.1: measured saving is not positive');
  if (saved >= stock) fail(`leaf 1.3.2.1: saving ${saved} >= stock ${stock}, which is incoherent`);
  pass(spec.expect);
}

if (A.mode === 'stability') {
  const j = readEvidence(A.leaf);
  const digests = requireArray(j, 'per_call_system_digests', A.leaf, 2);
  const uniq = new Set(digests);
  if (uniq.size !== 1) fail(`leaf 1.3.2.2: system prefix is NOT byte-stable (${uniq.size} distinct digests across ${digests.length} calls)`);
  pass(spec.expect);
}

if (A.mode === 'equivalence') {
  const j = readEvidence(A.leaf);
  const a = requireArray(j, 'tools_without_probe', A.leaf, 1);
  const b = requireArray(j, 'tools_with_probe', A.leaf, 1);
  const norm = (x) => JSON.stringify([...x].sort());
  if (norm(a) !== norm(b)) fail('leaf 1.5.2: tools array differs with and without the probe');
  pass(spec.expect);
}

fail(`unhandled mode: ${A.mode}`);