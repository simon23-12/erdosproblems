# Machine-verified work on open Erdős problems

Autonomous computational attacks on open problems from
[erdosproblems.com](https://www.erdosproblems.com) (Thomas Bloom's database of
Paul Erdős's problems), under one rule:

> **A claim counts only if a machine checked it.** Either Lean/mathlib compiles
> it with no `sorry` and no added axioms, or a short standalone script recomputes
> it from scratch. Everything else is labelled a *lead* and is explicitly not
> trustworthy.

**No Erdős problem here is solved.** What is here are exhaustive negatives over
finite ranges ("no counterexample below X") and one formalized reduction. That
is the honest kind of progress a compute budget buys.

## Start here

| file | what it is |
|---|---|
| [`RESULTS.md`](RESULTS.md) | the ledger — three buckets: verified / leads / dead ends, with repro commands |
| [`LOG.md`](LOG.md) | chronological journal, including what failed and why I stopped |
| [`RESEARCH_TRACKER.json`](RESEARCH_TRACKER.json) | machine-readable state for all 43 triaged problems |
| [`docs/index.html`](docs/index.html) | generated overview page |

## Check the work yourself

```bash
./verify_all.sh              # re-runs every claim; ~5 min   (--full for slow bounds)
```

It rebuilds the Lean proofs and prints their axiom dependencies (any `sorry` or
extra axiom fails), then runs each standalone checker. The checkers deliberately
share no code with the searches that produced the results — several re-derive
everything from `sympy` along a different route.

## What is verified

| # | problem | result |
|---|---|---|
| [287](https://www.erdosproblems.com/287) | unit fractions summing to 1 must have a consecutive gap ≥ 3 | **Lean-verified reduction** + no counterexample with max(S) ≤ 10¹⁰ |
| [647](https://www.erdosproblems.com/647) | is there n > 24 with max_{m<n}(m+τ(m)) ≤ n+2? (£25) | no such n below the live bound in `RESULTS.md` |
| [458](https://www.erdosproblems.com/458) | is [1..p_{k+1}−1] < p_k·[1..p_k]? | holds for every prime gap with p_k ≤ 10¹⁴ |
| [488](https://www.erdosproblems.com/488) | density inequality for multiples of a finite set | no counterexample over 21,550 antichains |
| [699](https://www.erdosproblems.com/699) | a prime p ≥ i dividing gcd(C(n,i), C(n,j)) | holds for all n ≤ 3000 |
| [366](https://www.erdosproblems.com/366) | a 2-full n with n+1 3-full | search past the published bound; see `RESULTS.md` |

The Lean development lives in [`ErdosFormal/`](ErdosFormal/ErdosFormal/Erdos287.lean).

## Layout

```
lib/erdos/       reusable components (SAT encodings, graph generation,
                 number theory, tree DP) — shared across problems
tools/           triage, tracker CLI, statement fetcher, dashboard generator
problems/<n>/    one directory per problem: search code + standalone verifier
ErdosFormal/     Lean 4 + mathlib project
data/            problem metadata and cached statements
```

Problem metadata comes from the community mirror
[teorth/erdosproblems](https://github.com/teorth/erdosproblems). Of its 1217
problems, 43 are flagged as settleable by a finite computation; all 43 are
triaged in the tracker with approach tags, cost/novelty estimates and a priority
score, so work resumes where it left off rather than restarting.

## Reproducing the environment

```bash
python3.12 -m venv .venv && .venv/bin/pip install sympy numpy networkx z3-solver python-sat pyyaml
brew install nauty                      # geng / gentreeg
curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh
cd ErdosFormal && lake exe cache get && lake build
```
