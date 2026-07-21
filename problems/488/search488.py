#!/usr/bin/env python3
"""Erdos problem 488 (https://www.erdosproblems.com/488).

    Let A be a finite set and B = { n >= 1 : a | n for some a in A }.
    Is it true that for every m > n >= max(A),

        |B cap [1,m]| / m   <   2 |B cap [1,n]| / n   ?

The constant 2 is best possible: A = {a}, n = 2a-1, m = 2a gives ratio 2 - 1/a.

METHOD. Everything is exact integer arithmetic -- the test
`n * f(m) < 2 * m * f(n)` never touches a float, so a near-miss cannot be
mistaken for a hit. For each candidate A we sieve B up to X, form prefix counts
f, and then for each n take the exact maximum of f(m)/m over m > n (kept as a
fraction via cross-multiplication) and compare.

Two reductions keep the enumeration honest and small:
  * If a | a' for distinct a, a' in A then a' contributes no new multiples, so
    B is unchanged by dropping it. Only ANTICHAINS under divisibility matter.
  * 1 in A makes B = all of N, where the ratio is identically 1 < 2.

What is verified is the exact finite statement: for every divisibility-antichain
A contained in [1,K] with |A| <= L, and every max(A) <= n < m <= X, the
inequality holds -- together with the largest ratio actually attained.

Usage:
    python search488.py --K 24 --L 3 --X 20000
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from itertools import combinations


def is_antichain(A: tuple[int, ...]) -> bool:
    return not any(b % a == 0 for a in A for b in A if a != b)


def counts(A: tuple[int, ...], X: int) -> list[int]:
    """f[x] = |B cap [1,x]| for x = 0..X."""
    mark = bytearray(X + 1)
    for a in A:
        mark[a:: a] = b"\x01" * len(mark[a:: a])
    f = [0] * (X + 1)
    c = 0
    for x in range(1, X + 1):
        c += mark[x]
        f[x] = c
    return f


def worst_for(A: tuple[int, ...], X: int):
    """Return (best_ratio, witness) where best_ratio = max over m>n>=max(A) of
    (f(m)/m) / (f(n)/n). A counterexample is best_ratio >= 2."""
    lo = max(A)
    f = counts(A, X)
    # suffix maximum of f(m)/m, kept exactly
    best_m = [0] * (X + 2)
    bm = X
    for m in range(X, lo, -1):
        # compare f(m)/m with f(bm)/bm  =>  f(m)*bm  vs  f(bm)*m
        if m == X or f[m] * bm > f[bm] * m:
            bm = m
        best_m[m] = bm
    best = Fraction(0)
    wit = None
    for n in range(lo, X):
        m = best_m[n + 1]
        if f[n] == 0:
            continue
        r = Fraction(f[m] * n, m * f[n])
        if r > best:
            best, wit = r, (A, n, m, f[n], f[m])
    return best, wit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--K", type=int, default=24, help="A is a subset of [1,K]")
    ap.add_argument("--L", type=int, default=3, help="max |A|")
    ap.add_argument("--X", type=int, default=20000, help="test all n<m<=X")
    a = ap.parse_args()

    best, wit, tested, viol = Fraction(0), None, 0, []
    for size in range(1, a.L + 1):
        for A in combinations(range(2, a.K + 1), size):
            if not is_antichain(A):
                continue
            tested += 1
            r, w = worst_for(A, a.X)
            if r > best:
                best, wit = r, w
            if r >= 2:
                viol.append(w)
    print(f"antichains tested : {tested}  (A subset of [2,{a.K}], |A| <= {a.L})")
    print(f"range tested      : max(A) <= n < m <= {a.X}")
    if wit:
        A, n, m, fn, fm = wit
        print(f"largest ratio     : {float(best):.6f} = {best}")
        print(f"  attained by A={list(A)}, n={n}, m={m}  "
              f"(|B∩[1,n]|={fn}, |B∩[1,m]|={fm})")
    print(f"counterexamples   : {viol if viol else 'NONE'}")
    print()
    print("RESULT: the inequality holds throughout the tested range"
          if not viol else "RESULT: COUNTEREXAMPLE FOUND")


if __name__ == "__main__":
    main()
