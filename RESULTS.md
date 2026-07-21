# RESULTS — Erdős problems ledger

**Status of this file:** live ledger. Every claim carries an explicit status tag.
Nothing is called a "result" unless a machine checked it.

Status tags:
- `[LEAN-VERIFIED]` — Lean/mathlib compiles it, no `sorry`, no extra axioms.
- `[COMPUTATION-VERIFIED]` — a short standalone script recomputes the claim from
  scratch; a skeptic can run it without trusting me.
- `[UNVERIFIED-LEAD]` — prose/heuristic only. **NOT trustworthy.**
- `[DEAD-END]` — attempted, no machine-checkable progress.

Machine-readable state: `RESEARCH_TRACKER.json`. Overview page: `docs/index.html`.

---

## 1. VERIFIED — machine-checked, safe to show a mathematician

### [647] Erdős–Selfridge: is there n > 24 with max_{m<n}(m + τ(m)) ≤ n + 2?
`[COMPUTATION-VERIFIED]` — **partial: an exhaustive negative over a range, not a
solution to the problem.** Erdős offered £25 for such an n.

**Claim.** The only n ≥ 2 with max_{m<n}(m + τ(m)) ≤ n+2 and n ≤ 3.2×10¹¹ are
n = 2, 3, 4, 5, 6, 8, 10, 12, 24. In particular there is **no** such n with
24 < n ≤ 3.2×10¹¹. *(Search still running; see LOG.md for the live bound.)*

**Why it is checkable.** The condition rewrites as τ(n−j) ≤ j+2 for all j ≥ 1,
and τ(m) ≤ 6720 for m < 10¹², so only j ≤ W = 16384 can ever matter. That makes
the test local, hence splittable across cores. The program **measures** the
largest τ it meets and refuses to report success unless max τ + 2 < W, so the
cutoff is checked at runtime rather than assumed.

Reproduce:
```
cd problems/647
cc -O3 -o search647 search647.c -lm
python verify647.py 1000000        # independent brute force, ~0.5s
./search647 2 1000000              # C agrees exactly on the same range
./run647.sh                        # full parallel search
python progress647.py              # contiguous bound + solutions
```
`verify647.py` shares no code with the C search — it sieves τ by brute force and
tracks the running maximum directly, with no locality argument at all.

---

## 2. LEADS — unverified, needs an expert. NOT trustworthy yet.

### [287] Unit fractions summing to 1 must have a consecutive gap ≥ 3
**Computation verified; conclusion conditional on one unformalized lemma.**

**Finite claim, `[COMPUTATION-VERIFIED]`:** no set S of integers ≥ 2 with all
consecutive gaps ≤ 2 and Σ 1/n = 1 has max(S) ≤ 10⁶ — and the covering that
extends this to 10¹² is running.

**What is NOT yet machine-checked** is the ELIMINATION lemma the covering rests on:

> If S has Σ 1/n = 1, p ≥ 5 is prime, and the only multiples of p that are ≤ max S
> are p and 2p, then p ∉ S and 2p ∉ S.

Its proof is elementary (multiply through by 2pM where M = lcm(S \ {p,2p}), which
is coprime to p; one gets p | cM with c ∈ {1,2,3}, so p | 6 — contradiction). It is
written out in `verify287.py`. **It is still prose, so the overall statement is a
LEAD, not a verified result.** A Lean formalization is in progress; only when that
compiles does this move to bucket 1.

Reproduce the computation:
```
cd problems/287
python verify287.py 1e6 --spot 30      # standalone, ~4s, independent of the search code
cc -O3 -o cover287 cover287.c -lm && ./cover287 100000 1000000000    # ~5s
```
`verify287.py` re-derives coverage using `sympy.isprime` and audits random
certificates against every hypothesis; it shares no code with `search287.py`
or `cover287.c`.

### [617] Erdős–Gyárfás balanced colourings — r = 3 confirmed, r = 4 running
`[COMPUTATION-VERIFIED]` for r = 3 (reproduces a known theorem, so no novelty):
no 3-colouring of K₁₀ has every K₄ seeing all 3 colours. Symmetry breaking
(sorting the star at vertex 0) cut this from 47s to 0.3s. r = 4 is running; r = 5
is the first open case and is not expected to be reachable by UNSAT.

```
cd problems/617 && python encode617.py 3      # UNSAT in ~0.3s
```

---

## 3. DEAD ENDS — tried, didn't pan out

### [993] Independence-sequence unimodality for trees — not attempted after triage
`[DEAD-END]` on novelty grounds. Verified in the literature to 29 vertices
(2026); the next case n = 30 is 1.48×10¹⁰ free trees × O(n²) DP ≈ 1.3×10¹³
operations for a one-vertex improvement. Recorded rather than run.

### [287] direct exhaustive search
`[DEAD-END]` as a method. DFS over gap-≤2 chains with exact rational sums is
exponential and stalls around max(S) ≈ 40 — which is why the exclusion lemma
above exists. Retained only to settle max(S) ≤ 37.

---

## Appendix: candidate selection

1217 problems from <https://www.erdosproblems.com> via the community mirror
<https://github.com/teorth/erdosproblems>. 43 are flagged settleable by finite
computation (`decidable` 9, `falsifiable` 27, `verifiable` 7); all 43 are triaged
with approach tags and priority scores in `RESEARCH_TRACKER.json`.

```
python tools/triage.py                        # counts per state
python tools/tracker.py show                  # full triage table
python tools/tracker.py next                  # highest-priority untouched
python tools/build_dashboard.py               # regenerate docs/index.html
```
