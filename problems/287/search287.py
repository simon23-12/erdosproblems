#!/usr/bin/env python3
"""Erdos problem 287 (https://www.erdosproblems.com/287).

    Let k >= 2. For distinct integers 1 < n_1 < ... < n_k with
        1 = 1/n_1 + ... + 1/n_k,
    must max(n_{i+1} - n_i) >= 3 ?

A COUNTEREXAMPLE is a set S of integers >= 2 whose reciprocals sum to 1 and
whose consecutive gaps are all <= 2. (1 = 1/2+1/3+1/6 has gaps 1,3, so 3 would
be best possible.)  This program shows no counterexample has max(S) <= B.

--------------------------------------------------------------------------
THE EXCLUSION LEMMA  (the whole method; the rest is bookkeeping)

Let S have sum 1, b = max S, and fix a prime p. Put e = max_{n in S} v_p(n) and
T = {n in S : v_p(n) = e}. In Q_p the terms outside T have valuation >= -(e-1),
while sum_{n in T} 1/n = p^-e * sum_{n in T} (n/p^e)^-1 with every n/p^e a unit.
If that unit sum were nonzero mod p, the total would have valuation exactly
-e < 0, contradicting that the total is the integer 1. Hence

        sum_{n in T} (n/p^e)^{-1} == 0   (mod p).                        (*)

Take p > sqrt(b). Every multiple of p up to b then has v_p = 1, so e = 1 and
T = S ∩ pZ. With J = {j : jp in S} and m = floor(b/p) (here j <= m < p, so each
j is invertible mod p), (*) becomes sum_{j in J} j^{-1} == 0 (mod p), i.e.
p | N_J := sum_{j in J} L/j where L = lcm(1..m). So if

        p > Bound(m) := sum_{j=1..m} L/j                                  (**)

then p divides no N_J with J nonempty, forcing J = empty: NO multiple of p is
in S.  Bound(1)=1, Bound(2)=3, Bound(3)=11, Bound(4)=25, Bound(5)=137.

CERTIFICATE. Gaps <= 2 means S meets every pair of consecutive integers in
[min S, b]. So if two CONSECUTIVE integers x, x+1 with min S < x and x+1 <= b
are both forced out by (**), then S has elements below x and above x+1 with
nothing between -- a gap >= 3. Contradiction. Such a pair certifies that no
counterexample has largest element b.

Only x > b/2 is used, and min S <= b/2 holds unconditionally for b >= 3:
if min S > b/2 then min S - 1 >= floor(b/2), so

    1 = sum_{n in S} 1/n <= sum_{n=floor(b/2)+1}^{b} 1/n,

a sum of ceil(b/2) terms each at most 1/(floor(b/2)+1) and all but the first
strictly smaller, hence strictly below ceil(b/2)/(floor(b/2)+1) <= 1 --
contradiction. So the certificate never depends on min S. (certify_range still
re-checks the harmonic bound numerically per b; it is redundant, not load-bearing.)
--------------------------------------------------------------------------

Usage:
    python search287.py brute 37          # direct exhaustive search, small b
    python search287.py certify 200000    # per-b certificates
    python search287.py cover 1e9         # interval covering, large b
    python search287.py all 200000 1e9    # the full three-stage argument
"""
from __future__ import annotations

import sys
from bisect import bisect_left, bisect_right
from fractions import Fraction
from math import gcd, isqrt


def primes_upto(n: int) -> list[int]:
    if n < 2:
        return []
    s = bytearray([1]) * (n + 1)
    s[0:2] = b"\x00\x00"
    for i in range(2, isqrt(n) + 1):
        if s[i]:
            s[i * i:: i] = bytearray(len(s[i * i:: i]))
    return [i for i in range(2, n + 1) if s[i]]


def bound(m: int) -> int:
    """Bound(m) = sum_{j=1..m} lcm(1..m)/j  -- see (**)."""
    L = 1
    for j in range(1, m + 1):
        L = L * j // gcd(L, j)
    return sum(L // j for j in range(1, m + 1))


JMAX = 6
BOUND = {m: bound(m) for m in range(1, JMAX + 1)}


# --------------------------------------------------------------------------
# stage 1: direct exhaustive search for small b
# --------------------------------------------------------------------------
def brute(bmax: int):
    """Every S subset [2,bmax] with gaps <= 2, exact rational sum.

    DFS over 'next element is +1 or +2', pruned by sum > 1 and by the exact
    harmonic tail (the most that could still be added while staying <= bmax).
    """
    tail = [Fraction(0)] * (bmax + 2)
    for n in range(bmax, 1, -1):
        tail[n] = tail[n + 1] + Fraction(1, n)

    found = []

    def dfs(cur: int, total: Fraction, chain: list[int]):
        if total == 1:
            found.append(list(chain))
            return
        if total > 1:
            return
        for step in (1, 2):
            nxt = cur + step
            if nxt > bmax or total + tail[nxt] < 1:
                continue
            chain.append(nxt)
            dfs(nxt, total + Fraction(1, nxt), chain)
            chain.pop()

    for a in range(2, bmax + 1):
        if tail[a] < 1:
            break
        dfs(a, Fraction(1, a), [a])
    return found


# --------------------------------------------------------------------------
# stage 2: exact per-b certificates
# --------------------------------------------------------------------------
def certify_range(bmax: int, verbose: bool = False):
    """Find a certificate pair for every b in [38, bmax]. Returns the list of b
    with no certificate (which must then be handled by another stage)."""
    ps = primes_upto(bmax)
    # harmonic prefix sums, to re-check min S <= b/2 for each b
    H = [0.0] * (bmax + 2)
    for n in range(1, bmax + 1):
        H[n] = H[n - 1] + 1.0 / n

    bad, witnesses = [], {}
    for b in range(38, bmax + 1):
        half = b // 2
        if H[b] - H[half] >= 0.99:        # would break "min S <= b/2"
            bad.append(b)
            continue
        excl = set()
        root = isqrt(b)
        for m in range(1, JMAX + 1):
            lo, hi = b // (m + 1), b // m
            i = bisect_right(ps, max(lo, root, BOUND[m]))
            j = bisect_right(ps, hi)
            for p in ps[i:j]:
                if b // p != m:
                    continue
                for t in range(1, m + 1):
                    x = t * p
                    if 2 * x > b:
                        excl.add(x)
        hit = None
        for x in excl:
            if (x + 1) in excl and x + 1 <= b:
                hit = (x, x + 1)
                break
        if hit is None:
            bad.append(b)
        elif verbose:
            witnesses[b] = hit
    return bad, witnesses


# --------------------------------------------------------------------------
# stage 3: interval covering for large b
# --------------------------------------------------------------------------
def cover(B: int, b0: int):
    """If p >= 5 and 2p-1 are both prime, the pair (2p-1, 2p) is forced out for
    every b in [2p, 3p): 2p-1 is a prime > b/2 (m=1), and p is a prime in
    (b/3, b/2] (m=2, p >= 5 > Bound(2)=3) so p and 2p are both forced out.
    Likewise p and 2p+1 prime gives the pair (2p, 2p+1) for b in [2p+1, 3p).

    Each such p therefore certifies a whole interval of b, so the sieve only has
    to show the intervals cover [b0, B] contiguously.
    """
    ps = primes_upto(B + 2)
    pset = set(ps)
    iv = []
    for p in ps:
        if p < 5 or 2 * p > B + 1:
            continue
        if (2 * p - 1) in pset:
            iv.append((2 * p, 3 * p))
        elif (2 * p + 1) in pset:
            iv.append((2 * p + 1, 3 * p))
    iv.sort()
    reach, used = b0, 0
    for lo, hi in iv:
        if lo > reach:
            break
        if hi > reach:
            reach, used = hi, used + 1
        if reach > B:
            break
    return min(reach - 1, B), used


# --------------------------------------------------------------------------
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    N = int(float(sys.argv[2])) if len(sys.argv) > 2 else 200000

    if mode == "brute":
        sols = brute(N)
        print(f"exhaustive over all S subset [2,{N}] with gaps <= 2: "
              f"{sols if sols else 'NO counterexample'}")

    elif mode == "certify":
        bad, w = certify_range(N, verbose=True)
        print(f"certificates for 38 <= b <= {N}: {len(bad)} without one -> {bad}")
        for b in (38, 100, 1000, 99991):
            if b in w:
                print(f"  example: b={b} certificate pair {w[b]}")

    elif mode == "cover":
        b0 = int(float(sys.argv[3])) if len(sys.argv) > 3 else 200000
        reach, used = cover(N, b0)
        print(f"covering from b0={b0}: contiguous to b={reach:,} ({used} witness primes)")

    elif mode == "all":
        C = int(float(sys.argv[3])) if len(sys.argv) > 3 else 10 ** 9
        print("stage 1: exhaustive search, max(S) <= 37")
        s = brute(37)
        print(f"         -> {s if s else 'no counterexample'}")
        print(f"stage 2: exclusion certificates, 38 <= b <= {N:,}")
        bad, _ = certify_range(N)
        print(f"         -> b without a certificate: {bad if bad else 'none'}")
        print(f"stage 3: interval covering, {N:,} < b <= {C:,}")
        reach, used = cover(C, N + 1)
        print(f"         -> contiguous to b={reach:,} ({used} witness primes)")
        ok = (not s) and (not bad) and reach >= C
        print()
        print(f"RESULT: no counterexample with max(S) <= {min(reach, C):,}"
              if ok else "RESULT: INCOMPLETE -- see gaps above")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
