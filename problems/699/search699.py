#!/usr/bin/env python3
"""Erdos problem 699 (https://www.erdosproblems.com/699).

    Is it true that for every 1 <= i < j <= n/2 there exists some prime p >= i
    with  p | gcd( C(n,i), C(n,j) ) ?

A problem of Erdos and Szekeres. A COUNTEREXAMPLE is a single triple (n,i,j) --
so it is instantly re-checkable, which is what makes this worth compute.

METHOD. Binomial coefficients are never formed. Kummer's theorem says
v_p(C(n,i)) equals the number of carries when adding i and n-i in base p, so
for each prime p <= n we can mark, in one pass, the set

    A_p = { i in [1, n/2] : p | C(n,i) }

as a bitmask. Then for a fixed i the set of j that ARE covered is

    U_i = OR of A_p over all primes p >= i with i in A_p,

and the conjecture at (n,i) says U_i contains every j in (i, n/2]. Bitmask ORs
make the inner loop essentially free.

Known data points used as tests:
  * Sylvester-Schur: for every 1 <= i <= n/2 some prime p > i divides C(n,i),
    so every A_p family is nonempty -- checked by --selftest.
  * gcd(C(28,5), C(28,14)) = 2^3 * 3^3 * 5, the Erdos-Szekeres example where
    p >= i is satisfiable (p=5) but p > i is not.

Usage:
    python search699.py --selftest
    python search699.py 2000            # scan n = 4 .. 2000
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "lib"))
from erdos.numth import primes_upto, kummer_carries as carries  # noqa: E402


def scan(n: int, primes: list[int]):
    """Return a counterexample (n,i,j) for this n, or None."""
    half = n // 2
    # A[p] as a bitmask over i in [1, half]
    masks: dict[int, int] = {}
    for p in primes:
        if p > n:
            break
        m = 0
        for i in range(1, half + 1):
            if carries(n, i, p) > 0:
                m |= 1 << i
        if m:
            masks[p] = m
    full = ((1 << (half + 1)) - 2)          # bits 1..half
    for i in range(1, half):
        u = 0
        for p, m in masks.items():
            if p >= i and (m >> i) & 1:
                u |= m
        # every j with i < j <= half must be covered
        need = full & ~((1 << (i + 1)) - 1)
        missing = need & ~u
        if missing:
            j = (missing & -missing).bit_length() - 1
            return (n, i, j)
    return None


def selftest():
    ps = primes_upto(64)
    # Erdos-Szekeres example: gcd(C(28,5), C(28,14)) = 2^3 * 3^3 * 5
    from math import comb, gcd
    g = gcd(comb(28, 5), comb(28, 14))
    assert g == 2 ** 3 * 3 ** 3 * 5, g
    for p, e in ((2, 3), (3, 3), (5, 1)):
        assert min(carries(28, 5, p), carries(28, 14, p)) == e, (p, e)
    print(f"  Kummer reproduces gcd(C(28,5),C(28,14)) = {g} = 2^3*3^3*5")
    # p >= i is satisfied here (p=5) but p > i is not -- matches the problem text
    assert 5 >= 5 and carries(28, 5, 5) > 0 and carries(28, 14, 5) > 0
    bigger = [p for p in ps if p > 5 and carries(28, 5, p) > 0 and carries(28, 14, p) > 0]
    assert bigger == [], bigger
    print("  (28,5,14): p=5 works for 'p >= i'; no prime p > 5 works -- as documented")
    # Sylvester-Schur: some prime > i divides C(n,i)
    for n in range(10, 120):
        for i in range(1, n // 2 + 1):
            assert any(p > i and carries(n, i, p) > 0 for p in primes_upto(n)), (n, i)
    print("  Sylvester-Schur holds for all n < 120")
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("N", type=int, nargs="?", default=500)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    primes = primes_upto(a.N)
    hits = []
    for n in range(4, a.N + 1):
        r = scan(n, primes)
        if r:
            hits.append(r)
            print(f"COUNTEREXAMPLE {r}")
    print(f"scanned n = 4..{a.N}: {len(hits)} counterexamples"
          f"{'' if hits else ' (conjecture holds throughout)'}")


if __name__ == "__main__":
    main()
