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

> **None of these solves an Erdős problem.** Each is an exhaustive negative over
> a finite range, or a formalized reduction. They are the honest kind of progress
> a compute budget buys; a mathematician should read them as "no counterexample
> below X", not as "solved".

---

## 1. VERIFIED — machine-checked, safe to show a mathematician

### [287] Unit fractions summing to 1 must have a consecutive gap ≥ 3
`[LEAN-VERIFIED]` reduction + `[COMPUTATION-VERIFIED]` finite check.

**Claim.** No finite set `S` of integers ≥ 2 with `Σ 1/n = 1` and all consecutive
gaps ≤ 2 has `max(S) ≤ 10¹⁰`. *(A covering to 10¹² is running.)*

**The mathematics is formalized.** `ErdosFormal/ErdosFormal/Erdos287.lean`
compiles with **no `sorry`**, depending only on `[propext, Classical.choice,
Quot.sound]`:

| theorem | statement |
|---|---|
| `elimination` | If `Σ 1/n = 1`, `p ≥ 5` prime, and the only members of `S` divisible by `p` lie in `{p, 2p}`, then `p ∉ S` and `2p ∉ S`. |
| `certificate_sub` | If `p ≥ 5` and `2p−1` are prime, no counterexample has `max(S) ∈ [2p, 3p)`. |
| `certificate_add` | If `p ≥ 5` and `2p+1` are prime, no counterexample has `max(S) ∈ [2p+1, 3p)`. |

`elimination` avoids p-adic valuations: instead of the lcm of all of `S` it uses
the explicit common multiple `D = 2pL` (`L` = lcm of the members not divisible by
`p`), so every term `D/n` is visibly a multiple of `p` except the two special
ones, and the whole thing collapses to `p | cL` with `1 ≤ c ≤ 3 < p`.

**What is left to compute** is only: (a) an exhaustive search for `max(S) ≤ 37`,
and (b) that the certificate intervals `[2p, 3p)` cover `(37, B]`. Both witness
forms are needed — `2p−1` alone already leaves `b = 57` uncovered.

```
cd ErdosFormal && lake build && lake env lean ErdosFormal/AxiomCheck.lean
cd ../problems/287
python verify287.py 1e6 --spot 30                 # standalone, ~4s
cc -O3 -o cover287 cover287.c -lm && ./cover287 38 10000000000     # ~60s
```
`verify287.py` re-derives everything from `sympy.isprime` and shares no code with
`search287.py` or `cover287.c`.

### [458] Is `[1,…,p_{k+1}−1] < p_k·[1,…,p_k]` for all k?
`[COMPUTATION-VERIFIED]` — holds for **every prime gap with p_k ≤ 10¹⁴**.

The lcm ratio is *exactly* the product of the primes `q` having a power `q^e`
(`e ≥ 2`) inside the gap `(p_k, p_{k+1})` — so the conjecture is literally
`∏ q < p_k`. Since only ~`π(√X)` prime powers exist below `X`, the check walks
the prime powers rather than the gaps. Every grouping decision is settled by
exhibiting an explicit prime, never by assuming one exists.

Only **5** gaps below 10¹⁴ contain two prime powers — `{8,9}`, `{25,27}`,
`{121,125}`, `{2187,2197}`, `{32761,32768}` — and the tightest case overall is
the very first one, `p_k = 7` with ratio `6/7`.

```
cd problems/458 && python check458.py 1e14        # ~3 min
```

### [647] Erdős–Selfridge: is there n > 24 with max_{m<n}(m + τ(m)) ≤ n + 2?
`[COMPUTATION-VERIFIED]` — exhaustive negative. Erdős offered £25 for such an n.

**Claim.** The only n ≥ 2 with the property and n ≤ 4.8×10¹¹ are
n = 2, 3, 4, 5, 6, 8, 10, 12, 24. So there is **no** such n with
24 < n ≤ 4.8×10¹¹. *(Search running; live bound from `progress647.py`.)*

The condition rewrites as `τ(n−j) ≤ j+2` for all `j ≥ 1`, and `τ(m) ≤ 6720` for
`m < 10¹²`, so only `j ≤ W = 16384` can matter — which makes the test local and
splittable across cores. The program **measures** the largest τ it meets and
refuses to report success unless `max τ + 2 < W`, so the cutoff is checked at
runtime, not assumed.

```
cd problems/647
python verify647.py 1000000        # independent brute force, ~0.5s
cc -O3 -o search647 search647.c -lm && ./search647 2 1000000   # C agrees exactly
./run647.sh && python progress647.py
```
`verify647.py` shares no code with the C search: it sieves τ by brute force and
tracks the running maximum directly, with no locality argument at all.

---

## 2. LEADS — unverified, needs an expert. NOT trustworthy yet.

*(empty — nothing is currently sitting in this bucket)*

---

## 3. DEAD ENDS — tried, didn't pan out

### [617] Erdős–Gyárfás balanced colourings — r = 5 not reachable by SAT
r = 3 confirmed UNSAT (`[COMPUTATION-VERIFIED]`, but it reproduces a known
theorem, so no novelty). Symmetry breaking — sorting the star at vertex 0 —
cut r = 3 from 47s to 0.3s. r = 4 (also known) did not finish in ~2 hours, which
puts r = 5, the first *open* case, far out of reach for an UNSAT proof.
A counterexample would still be trivially checkable if local search ever found
one; `check_colouring()` exists for that.

```
cd problems/617 && python encode617.py 3      # UNSAT in ~0.3s
```

### [993] Independence-sequence unimodality for trees — rejected at triage
Verified in the literature to 29 vertices (2026). The next case n = 30 is
1.48×10¹⁰ free trees × O(n²) DP ≈ 1.3×10¹³ operations for a one-vertex
improvement. Recorded rather than run.

### [287] direct exhaustive search — wrong method
DFS over gap-≤2 chains with exact rational sums is exponential and stalls around
max(S) ≈ 40. That is why the elimination lemma exists. Retained only to settle
`max(S) ≤ 37`.

---

## Appendix: candidate selection

1217 problems from <https://www.erdosproblems.com> via the community mirror
<https://github.com/teorth/erdosproblems>. 43 are flagged settleable by finite
computation (`decidable` 9, `falsifiable` 27, `verifiable` 7); all 43 are triaged
with approach tags, runtime / P(verifiable) / novelty estimates and a priority
score in `RESEARCH_TRACKER.json`.

```
python tools/triage.py                        # counts per state
python tools/tracker.py show                  # full triage table
python tools/tracker.py next                  # highest-priority untouched
python tools/build_dashboard.py               # regenerate docs/index.html
```
