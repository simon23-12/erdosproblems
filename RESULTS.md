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

**Re-verify everything with one command:**

```
./verify_all.sh            # fast tier, ~5 min      (--full for the slow bounds)
```

It rebuilds the Lean proofs, prints their axiom dependencies, and re-runs every
standalone checker. Last run: **16 checks, 16 pass, 0 fail.**

**Before any new work, run the sync phase:**

```
python tools/sync.py            # what changed upstream + who already did what
python tools/sync.py --apply    # ...and update the local snapshot
```

It diffs `teorth/erdosproblems` for added / modified / **solved** problems and
reads the official AI-contributions page, so published work is not duplicated.
Priorities in `RESEARCH_TRACKER.json` are ROI-ranked:
`expected_value × novelty × p_verifiable / compute_cost`.

---

## 1. VERIFIED — machine-checked, safe to show a mathematician

### [287] Unit fractions summing to 1 must have a consecutive gap ≥ 3
`[LEAN-VERIFIED]` reduction + `[COMPUTATION-VERIFIED]` finite check.

**Claim.** No finite set `S` of integers ≥ 2 with `Σ 1/n = 1` and all consecutive
gaps ≤ 2 has **max(S) ≤ 10¹²**. The covering used 1,321,198,806 witness primes
and reported no hole.

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
`[COMPUTATION-VERIFIED]` — holds for **every prime gap lying entirely below
9,999,997,800,000,077** (≈10¹⁶). 5,782,467 prime powers examined.

The bound is stated that way on purpose: the last group of prime powers sits in a
gap that may continue above the search limit and contain prime powers never
enumerated, which would make its product too small. That final group is dropped
rather than counted.

The lcm ratio is *exactly* the product of the primes `q` having a power `q^e`
(`e ≥ 2`) inside the gap `(p_k, p_{k+1})` — so the conjecture is literally
`∏ q < p_k`. Since only ~`π(√X)` prime powers exist below `X`, the check walks
the prime powers rather than the gaps. Every grouping decision is settled by
exhibiting an explicit prime, never by assuming one exists.

Only **5** gaps in the whole range contain two prime powers — `{8,9}`, `{25,27}`,
`{121,125}`, `{2187,2197}`, `{32761,32768}` — and the tightest case overall is
the very first one, `p_k = 7` with ratio `6/7`.

```
cd problems/458 && python check458.py 1e14        # ~3 min
cd problems/458 && python check458.py 1e16        # the full run, ~25 min
```

### [647] Erdős–Selfridge: is there n > 24 with max_{m<n}(m + τ(m)) ≤ n + 2?
`[COMPUTATION-VERIFIED]` — exhaustive negative. Erdős offered £25 for such an n.

**Claim.** The only n ≥ 2 with the property and n ≤ **1.52×10¹²** are
n = 2, 3, 4, 5, 6, 8, 10, 12, 24. So there is **no** such n with
24 < n ≤ 1.52×10¹². 152 contiguous chunks, max τ encountered 6912 (window
16384). Stopped there deliberately: at the observed ≈1.1×10¹¹/hour, reaching
10¹³ would take ~78 more hours.

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

### [475] Graham's rearrangement conjecture at p = 29 and p = 31
`[COMPUTATION-VERIFIED]` — every subset of F₂₉\{0} of size 21–25, and every
subset of F₃₁\{0} of size 21–27, has a valid ordering. **24,646,432 subsets,
0 counterexamples, 0 exhaustive fallbacks.** These are the complete open windows
for both primes.

Computed twice by independent implementations: the Python reference
(`graham475.py`, ~16 min) and a C version (`search475.c`, 10 s for p=31) that is
30× faster and reproduces every per-slice count exactly.

**p = 37 is NOT claimed.** That run was stopped at 13,916,749,013 of
13,916,801,341 subsets — 99.9996%, short by 52,328 in the two smallest slices
(t=32, 33). `progress475.py` correctly refuses to call it complete, and neither
do I. It is resumable (`./run475.sh 37 10 3` skips finished chunks) and would
need well under a minute.

One thing that run did establish: it triggered the exhaustive DFS fallback
**7 times** — the first time in a production sweep — and all 7 resolved to valid
orderings. The sound-fallback design was exercised, not merely carried.

**Scope, stated precisely.** What is machine-checked here is the window
`t ∈ [21,25]`. The rest of p = 29 is covered by *cited* theorems — `|A| ≤ 20` in
any abelian group (Costa–Pellegrini) and `p−3 ≤ t ≤ p−1` (Hicks–Ollis–Schmitt).
So "Graham's conjecture holds for p = 29" is my computation *plus* the
literature; only the computation is mine. (Note erdosproblems.com still says
`t ≤ 12` is proved. Using that stale figure would have made this look far more
novel than it is — and would have put p = 17 and 19 wrongly in the open window.)

**The restart count was the whole ballgame.** The search is randomised greedy
with a complete DFS fallback, and only DFS exhaustion may answer "no ordering
exists". But the fallback is exponential, so any instance reaching it stalls the
sweep. Measured greedy failure rate over 2000 random subsets:

| restarts | t=21 | t=23 | t=25 |
|---|---|---|---|
| 60 | 0/2000 | 29/2000 | **420/2000** |
| 500 | 0/2000 | 0/2000 | 0/2000 |

At 60 restarts a fifth of the t=25 subsets fell through to the exponential
branch and the sweep effectively hung. At 500 restarts nothing falls through and
the cost rises only from 0.17 to 0.22 ms. The fallback is still there and still
the only thing entitled to say "no" — it just stops being the common case.

```
cd problems/475
python graham475.py --selftest      # exhausts all 333,120 subsets for p <= 19
python graham475.py --p 29          # python reference, ~73 s
cc -O3 -o search475 search475.c && ./run475.sh 31 10 && python progress475.py 31
```
`progress475.py` judges coverage by checking that the per-slice subset counts
add up to C(p−1,t) **exactly**, so a killed chunk shows up as a mismatch rather
than as silently reduced coverage.

### [488] Is |B∩[1,m]|/m < 2|B∩[1,n]|/n for the multiples of a finite set?
`[COMPUTATION-VERIFIED]` — no counterexample in two exhaustive sweeps.

`B` = the integers divisible by some member of `A`. Verified for every
divisibility-*antichain* `A ⊆ [2,40]` with `|A| ≤ 3` and all `max(A) ≤ n < m ≤ 8000`,
and for every antichain `A ⊆ [2,30]` with `|A| ≤ 4` and `n < m ≤ 6000`
(21,550 sets in total). Antichains suffice because `a | a′` makes `a′`
contribute no new multiples. The test is exact integer arithmetic —
`n·f(m) < 2·m·f(n)`, no floats — so a near-miss cannot read as a hit.

The largest ratio found is always attained by a **singleton**: `A = {a}`, `n = 2a−1`,
giving `2 − 1/a` (79/40 at a=40). No multi-element set beat it, which matches the
known extremal example and is mild evidence that singletons are extremal in general.

```
cd problems/488 && python search488.py --K 40 --L 3 --X 8000     # ~2 min
```

### [366] Is there a 2-full n with n+1 3-full?
`[COMPUTATION-VERIFIED]` — no such pair, in **either** order, with the 3-full
member up to **10²⁴**. 460,160,082 cubefull numbers examined; exactly two hits,
both already known (8|9 and 12167|12168), and **both in the opposite order** to
the one the problem asks about.

The published bound is 10²² (OEIS A060355's consecutive-powerful-pair tables), so
this extends it by a factor of 100. Prior AI work on this problem (April 2026,
logged upstream) is a *conditional* partial result, not a search bound.

The two known consecutive {3-full, 2-full} pairs — 8|9 and 12167|12168 — both
have the **3-full member first**, so the question as literally asked (2-full,
then 3-full) has no known example at all. The search covers both orders.

**Why this can go past the published bound.** The cited 10²² comes from OEIS
A060355, a table of consecutive *powerful* pairs, and powerful numbers number
~2.17√X. But one member must be 3-full, and 3-full numbers number only ~cX^(1/3)
— 21 million below 10²⁰ against ~2×10¹⁰ powerful ones. So: enumerate the 3-full
member and test its two neighbours.

Powerfulness is decided by trial division to `P0`, then "the surviving cofactor
is powerful iff it is a perfect k-th power (k ≤ 4)" — valid exactly while
`P0⁵ > X`, since the smallest non-perfect-power shape `p²q³` needs exponent sum 5.
The program asserts `P0⁵ > X` at startup rather than assuming it.

```
cd problems/366
cc -O3 -o search366 search366.c -lm && ./search366 1e20   # ~1 min
./search366 1e24                                          # the full run, ~2 h
python verify366.py                                        # independent check
```
`verify366.py` checks both directions of failure: **recall** (the search must
find 8|9 and 12167|12168 and nothing else) and **precision** (600 powerfulness
verdicts against `sympy`, including `p²q³` values built to break a too-small P0).
That recall check earned its keep — it caught a real bug, a fast 128-bit modulo
that computed `2^128 mod p` where it needed `2^64 mod p`.

### [699] Erdős–Szekeres: a prime p ≥ i dividing gcd(C(n,i), C(n,j))
`[COMPUTATION-VERIFIED]` — holds for all `n ≤ 3000` and all `1 ≤ i < j ≤ n/2`.

No binomial coefficient is ever formed: `v_p(C(n,i))` is the number of carries
when adding `i` and `n−i` in base `p` (Kummer), so each `A_p = {i : p | C(n,i)}`
is one sieve pass, and the covered-`j` set for a given `i` is a single bitmask OR.

The self-test reproduces two documented facts before any search runs:
`gcd(C(28,5), C(28,14)) = 2³·3³·5` — the Erdős–Szekeres example where `p ≥ i` is
satisfiable (`p = 5`) but `p > i` is not — and Sylvester–Schur for all `n < 120`.

```
cd problems/699 && python search699.py --selftest && python search699.py 3000
```

---

## 2. LEADS — unverified, needs an expert. NOT trustworthy yet.

### [835] χ(J(20,10)) = 11 is equivalent to a large set of Steiner systems S(9,10,20)
`[UNVERIFIED-LEAD]` — **the reduction below is a prose argument. It is not
machine-checked. Do not rely on it.** The arithmetic it rests on, and the small
cases, *are* checked.

**The reduction.** An independent set in J(2k,k) is a family of k-subsets no two
meeting in k−1 points. Each block contains k subsets of size k−1, and two blocks
sharing one would intersect in exactly k−1 points — so those (k−1)-subsets are
all distinct across the family, giving

    α(J(2k,k)) · k ≤ C(2k, k−1),  i.e.  α ≤ C(2k,k)/(k+1).

Equality forces every (k−1)-subset to be covered exactly once — the independent
set *is* a Steiner system S(k−1, k, 2k). Since |V| = (k+1)·C(2k,k)/(k+1)
exactly, a proper (k+1)-colouring must use k+1 classes of exactly maximum size.
Hence

> χ(J(2k,k)) = k+1  ⟺  there is a **large set** of k+1 pairwise disjoint Steiner
> systems S(k−1, k, 2k) partitioning all k-subsets of {1,…,2k}.

For the smallest open case k = 10 this says: χ(J(20,10)) = 11 iff eleven disjoint
copies of **S(9,10,20)** partition the 10-subsets of a 20-set. No nontrivial
Steiner system with t ≥ 6 is known to exist at all, so the open case sits on top
of a famously hard question — which is a useful thing to know before spending
compute on a colouring search.

**What *is* machine-checked** (`[COMPUTATION-VERIFIED]`):

- The reduction's arithmetic is exact for every k ≤ 12: |V| = (k+1)·⌊C(2k,k−1)/k⌋,
  so the "must use maximum independent sets" step is tight, not approximate.
- **For every k ≤ 259, the divisibility conditions for S(k−1,k,2k) hold if and only
  if k+1 is prime** — no mismatches. Via the reduction, that gives an independent
  route to Ma and Tang's theorem (χ > k+1 when k+1 is not prime) on that range.
- Exact chromatic numbers by SAT: χ(J(4,2)) = 3 (= k+1, the one case that works),
  χ(J(6,3)) = 6 and χ(J(8,4)) = 6 (both > k+1), reproducing the known failures.

```
cd problems/835
python johnson835.py --arith 12       # reduction arithmetic
python johnson835.py --primes 259     # admissible <=> k+1 prime
python johnson835.py --chi 4          # exact chi, ~1 min
```

**To upgrade this out of the LEADS bucket** the double-counting bound
`α·k ≤ C(2k,k−1)` and the tightness step would need formalizing in Lean, the way
[287]'s elimination lemma was.

---

## 3. DEAD ENDS — tried, didn't pan out

### [617] Erdős–Gyárfás balanced colourings — r = 5 not reachable by SAT
r = 3 confirmed UNSAT (`[COMPUTATION-VERIFIED]`, but it reproduces a known
theorem, so no novelty). Symmetry breaking — sorting the star at vertex 0 —
cut r = 3 from 47s to 0.3s. r = 4 (also known) had still not finished after ~1.75
hours, when I killed it to free a core — so r = 5, the first *open* case and a far
bigger instance, is out of reach for an UNSAT proof.
A counterexample would still be trivially checkable if local search ever found
one; `check_colouring()` exists for that.

```
cd problems/617 && python encode617.py 3      # UNSAT in ~0.3s
```

### [398] Brocard–Ramanujan — closed on NOVELTY, no compute spent
`[DEAD-END]`. The erdosproblems page says "no other solutions below 10⁹". The
literature is at **10¹⁵** (Epstein & Glickman, after Matson's 10¹²). My
Jacobi-symbol sieve needs ~2 Legendre symbols per n, so merely *matching* the
record is ~2×10¹⁵ modular operations — days on this hardware — and beating it
needs 10× more.

Worth recording twice over: the upstream page understates the known bound by six
orders of magnitude, and had I trusted it I would have burned hours to land far
short of the record. This is what the sync phase is for.

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
