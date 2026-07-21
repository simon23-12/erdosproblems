#!/usr/bin/env python3
"""Erdos problem 835 (https://www.erdosproblems.com/835).

    Is there some k > 2 such that the k-subsets of {1,...,2k} can be coloured
    with k+1 colours so that for every A of size k+1, all k+1 colours appear
    among the k-subsets of A?

As the problem page notes, this asks exactly whether chi(J(2k,k)) = k+1 for the
Johnson graph J(2k,k) (adjacency = intersecting in k-1 points). It is false for
3 <= k <= 8, and Ma and Tang proved chi > k+1 whenever k+1 is not prime, so the
smallest open case is k = 10 (k+1 = 11).

--------------------------------------------------------------------------
REDUCTION (this is the point of the file; the arithmetic is checked below).

An independent set in J(2k,k) is a family of k-subsets no two of which meet in
k-1 points. Each block contains exactly k subsets of size k-1, and two distinct
blocks sharing a (k-1)-subset would intersect in exactly k-1 points. So the
blocks' (k-1)-subsets are all distinct, giving

        alpha(J(2k,k)) * k  <=  C(2k, k-1),   i.e.   alpha <= C(2k,k)/(k+1),

using C(2k,k-1) = C(2k,k)*k/(k+1). Equality forces every (k-1)-subset to be
covered exactly once -- that is, the independent set IS a Steiner system
S(k-1, k, 2k).

Since |V| = C(2k,k) = (k+1) * (C(2k,k)/(k+1)), a proper (k+1)-colouring must
split V into k+1 classes each of exactly the maximum size. Hence

    chi(J(2k,k)) = k+1
      <=>  there is a LARGE SET of k+1 pairwise disjoint Steiner systems
           S(k-1, k, 2k) partitioning all k-subsets of {1,...,2k}.

Sanity checks this reproduces:
  k=2: S(1,2,4) = a perfect matching of 4 points; a large set of 3 of them is a
       1-factorisation of K_4, which exists -- and k=2 is exactly the case that
       works.
  k=3: S(2,3,6) is a Steiner triple system on 6 points, which does not exist
       (STS(v) needs v = 1 or 3 mod 6). So chi > 4, matching the known answer.
  k=10: S(9,10,20) passes every divisibility condition (checked below) but no
       Steiner system with t >= 6 is known to exist at all, so the open case
       sits on top of a famously hard question.

The reduction is a PROSE argument -- it is not machine-checked. What this script
does check is (a) the arithmetic it relies on, and (b) the small cases, by
computing chi(J(2k,k)) exactly with a SAT solver.
--------------------------------------------------------------------------

Usage:
    python johnson835.py --arith 12      # reduction arithmetic for k <= 12
    python johnson835.py --chi 4         # exact chi(J(2k,k)) for k <= 4
"""
from __future__ import annotations

import argparse
import itertools
import pathlib
import sys
from math import comb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "lib"))
from erdos.graphs import chromatic_number  # noqa: E402


def johnson(k: int):
    """J(2k,k) as (n, adjacency bitmasks); adjacency = |A cap B| = k-1."""
    verts = list(itertools.combinations(range(2 * k), k))
    idx = {v: i for i, v in enumerate(verts)}
    n = len(verts)
    adj = [0] * n
    for v in verts:
        sv = set(v)
        out = [x for x in range(2 * k) if x not in sv]
        for a in v:
            for b in out:
                w = tuple(sorted(sv - {a} | {b}))
                adj[idx[v]] |= 1 << idx[w]
    return n, tuple(adj)


def steiner_divisibility(t: int, kk: int, v: int):
    """The necessary conditions for S(t,k,v): C(v-i, t-i) divisible by
    C(k-i, t-i) for i = 0..t-1. Returns (all_ok, list of (i, quotient))."""
    rows, ok = [], True
    for i in range(t):
        num, den = comb(v - i, t - i), comb(kk - i, t - i)
        q, r = divmod(num, den)
        rows.append((i, num, den, q, r == 0))
        ok &= (r == 0)
    return ok, rows


def arithmetic(kmax: int):
    print(f"{'k':>3} {'|V|=C(2k,k)':>13} {'alpha bound':>12} {'(k+1)*bound':>13} "
          f"{'tight?':>7} {'S(k-1,k,2k) divisibility':>26}")
    for k in range(2, kmax + 1):
        V = comb(2 * k, k)
        # alpha * k <= C(2k, k-1)
        bound, rem = divmod(comb(2 * k, k - 1), k)
        tight = (k + 1) * bound == V and rem == 0
        ok, _ = steiner_divisibility(k - 1, k, 2 * k)
        print(f"{k:>3} {V:>13,} {bound:>12,} {(k+1)*bound:>13,} "
              f"{'yes' if tight else 'NO':>7} {'admissible' if ok else 'ruled out':>26}")
    print()
    print("'tight?' = yes means a (k+1)-colouring must use k+1 MAXIMUM independent")
    print("sets, i.e. k+1 disjoint Steiner systems S(k-1,k,2k).")
    print()
    k = 10
    ok, rows = steiner_divisibility(9, 10, 20)
    print(f"k=10 detail -- S(9,10,20) necessary conditions:")
    for i, num, den, q, good in rows:
        print(f"   i={i}: C({20-i},{9-i})/C({10-i},{9-i}) = {num}/{den} = {q}"
              f"{'' if good else '   <-- FAILS'}")
    print(f"   all conditions hold: {ok}  (so S(9,10,20) is admissible but "
          f"its existence is open)")


def prime_coincidence(kmax: int):
    """The divisibility conditions for S(k-1,k,2k) appear to hold exactly when
    k+1 is prime. Combined with the reduction, that reproves Ma and Tang's
    theorem (chi > k+1 whenever k+1 is not prime) on the checked range."""
    from sympy import isprime
    bad = [k for k in range(2, kmax + 1)
           if steiner_divisibility(k - 1, k, 2 * k)[0] != isprime(k + 1)]
    print(f"k in [2,{kmax}]: S(k-1,k,2k) admissible  <=>  k+1 prime")
    print(f"   mismatches: {bad if bad else 'NONE'}")
    print("   => on this range, k+1 composite kills the Steiner system, hence the")
    print("      maximum independent set is too small, hence chi(J(2k,k)) > k+1.")
    print("      (This is Ma and Tang's theorem, reached a different way.)")
    return not bad


def exact_chi(kmax: int):
    for k in range(2, kmax + 1):
        n, adj = johnson(k)
        deg = bin(adj[0]).count("1")
        print(f"k={k}: J({2*k},{k}) has {n} vertices, {deg}-regular ... ", end="", flush=True)
        c = chromatic_number(n, adj, ub=2 * k)
        verdict = "= k+1  (colouring EXISTS)" if c == k + 1 else f"> k+1"
        print(f"chi = {c}   {verdict}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arith", type=int, default=0)
    ap.add_argument("--chi", type=int, default=0)
    ap.add_argument("--primes", type=int, default=0)
    a = ap.parse_args()
    if a.arith:
        arithmetic(a.arith)
    if a.primes:
        prime_coincidence(a.primes)
    if a.chi:
        exact_chi(a.chi)
    if not a.arith and not a.chi and not a.primes:
        print(__doc__)


if __name__ == "__main__":
    main()
