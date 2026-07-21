#!/usr/bin/env python3
"""Erdos problem 458 (https://www.erdosproblems.com/458).

    Let [1,...,n] denote lcm{1,...,n}. Is it true that for all k >= 1,
        [1,...,p_{k+1}-1]  <  p_k [1,...,p_k]  ?

REDUCTION (exact, no approximation).
  lcm(1..N) = prod_q q^{floor(log_q N)}. Going from N = p_k to N = p_{k+1}-1 the
  exponent of q rises by the number of prime powers q^e lying in the interval
  (p_k, p_{k+1}). There is no PRIME in that interval, so every such q^e has
  e >= 2, and each contributes one extra factor of q. Hence

      [1..p_{k+1}-1] / [1..p_k]  =  prod  q     over prime powers q^e, e >= 2,
                                                with p_k < q^e < p_{k+1}.

  So the conjecture is exactly:  R_k := prod q  <  p_k,  for every k.

WHY THIS IS CHEAP. R_k = 1 (empty product) for all but the prime gaps that
actually contain a prime power, and there are only about pi(sqrt(X)) prime
powers below X -- 78,498 of them below 10^12. So instead of walking every prime
gap we walk the prime powers, group the ones sharing a gap, and test those gaps
only. Each grouping decision is settled by exhibiting an explicit prime between
two prime powers, never by assuming one exists.

Usage:
    python check458.py 1e12
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "lib"))
from erdos.numth import (  # noqa: E402
    is_prime, prev_prime, prime_between, prime_powers_upto,
)


def main():
    X = int(float(sys.argv[1])) if len(sys.argv) > 1 else 10 ** 12
    pps = prime_powers_upto(X)
    print(f"prime powers q^e <= {X:g} with e >= 2: {len(pps):,}")

    # group prime powers that share a prime gap
    groups, cur = [], [pps[0]]
    for prev, nxt in zip(pps, pps[1:]):
        if prime_between(prev[0], nxt[0]) is None:
            cur.append(nxt)          # no prime in between -> same gap
        else:
            groups.append(cur)
            cur = [nxt]
    groups.append(cur)

    # The final group is NOT trustworthy: its prime gap may extend above X and
    # hold further prime powers we never enumerated, which would make its R too
    # small. Drop it and report the bound as the largest p_k fully accounted for.
    incomplete = groups.pop()
    bound = prev_prime(incomplete[0][0])

    worst_ratio, worst = 0.0, None
    violations = []
    multi = 0
    for g in groups:
        pk = prev_prime(g[0][0])     # largest prime below the gap's contents
        R = 1
        for _, q in g:
            R *= q
        if len(g) > 1:
            multi += 1
        if R >= pk:
            violations.append((pk, [v for v, _ in g], R))
        ratio = R / pk
        if ratio > worst_ratio:
            worst_ratio, worst = ratio, (pk, [v for v, _ in g], R)

    for g in groups:
        if len(g) > 1:
            pk = prev_prime(g[0][0]); R = 1
            for _, q in g: R *= q
            print(f"  multi-gap: p_k={pk}, prime powers {[v for v,_ in g]}, "
                  f"R={R}, R/p_k={R/pk:.4f}")
    print(f"prime gaps containing >= 1 prime power : {len(groups):,}")
    print(f"final gap dropped as incomplete        : p_k={bound} "
          f"(its gap may extend past X)")
    print(f"                       >= 2 prime powers: {multi:,}")
    print(f"tightest case: p_k={worst[0]}, prime powers {worst[1]}, "
          f"R={worst[2]}, R/p_k={worst_ratio:.4f}")
    print(f"violations (R >= p_k): {violations if violations else 'NONE'}")
    print()
    print(f"RESULT: [1..p_(k+1)-1] < p_k [1..p_k] holds for every prime gap "
          f"lying entirely below {bound:,}"
          if not violations else "RESULT: VIOLATION FOUND")


if __name__ == "__main__":
    main()
