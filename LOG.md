# LOG — chronological journal

Newest entries at the bottom. Every attempt gets an entry, including failures.

---

## 2026-07-21 — Session 0: setup and triage

**Environment provisioned**
- Python 3.12.13 venv at `.venv` with `sympy 1.14.0`, `numpy 2.5.1`,
  `networkx 3.6.1`, `z3-solver 5.0.0`, `python-sat`, `pyyaml`.
- `elan` (Lean toolchain manager) installed to `~/.elan`. Lean+mathlib itself is
  deferred until there is something worth formalizing (multi-GB download).
- Git repo initialised in `/Users/sim/Documents/erdosproblems`.

**Problem source**
Rather than scraping 1217 pages, I cloned the community mirror
<https://github.com/teorth/erdosproblems>, whose `data/problems.yaml` is the
declared ground truth for problem metadata (number, status, prize, tags, OEIS
links). Statements themselves are fetched from erdosproblems.com and cached in
`data/statements/`.

**Triage**
`tools/triage.py` buckets all 1217 problems by status. 43 are explicitly flagged
as settleable by finite computation (`decidable` 9, `falsifiable` 27,
`verifiable` 7). I fetched all 43 statements and read them.

**Shortlist chosen for attack** (in priority order), with the reason each is
compute-amenable:

1. **[993]** Is the independent-set sequence of every tree/forest unimodal?
   *Exhaustive*: free trees on n vertices are cheap to generate, and the
   independence polynomial of a tree is computable in O(n) by DP. A counterexample
   is a single tree — trivially re-verifiable.
2. **[647]** Is there some n > 24 with max_{m<n}(m + τ(m)) ≤ n+2? (£25 prize)
   *Sieve*: equivalent to a running-max condition over a divisor-count sieve. O(N).
3. **[617]** r=5 case: can K_26 be 5-coloured so every K_6 sees all 5 colours?
   *SAT*: 1625 vars. A SAT answer is a counterexample to an Erdős–Gyárfás
   conjecture; UNSAT confirms the first open case.
4. **[287]** Unit fractions summing to 1 with all consecutive gaps ≤ 2.
   *p-adic sieve*: the largest-prime-power argument forces many exclusions.
5. **[743]** Tree packing conjecture at n=10 (Fishburn did n ≤ 9).
   *Exact cover*: ~428k tree-collections, each an edge-disjoint packing question.
6. **[835]** Does J(20,10) have chromatic number 11? A found colouring answers an
   Erdős–Rosenfeld question YES and is trivially verifiable.
7. **[167]** Tuza's conjecture (τ ≤ 2ν) on small graphs — two ILPs per graph.
8. **[475]** Graham's rearrangement conjecture in F_p, exhaustive for small p.
9. **[366]**, **[398]**, **[458]** — number-theoretic range extensions.

Deliberately skipped: [107] (happy-ending, search space astronomical), [242]
(Erdős–Straus, already verified to 10^18), [723] (projective plane of order 12,
a known multi-CPU-year problem), [114]/[1041]/[106] (continuous/analytic, no
exact certification path), [364] (already checked past 7×10^28).
