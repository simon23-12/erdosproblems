#!/usr/bin/env python3
"""STANDALONE re-verification for Erdos problem 287.

Shares no code with search287.py / cover287.c. It re-derives everything from
sympy.isprime and integer arithmetic, so running it is a genuine independent
check rather than a re-run of the same logic.

What is being claimed, precisely
--------------------------------
A counterexample to [287] is a finite set S of integers >= 2 with
sum_{n in S} 1/n = 1 whose consecutive elements differ by at most 2.
The claim is: no such S has max(S) <= B.

The argument has one mathematical input, ELIMINATION (proved elementarily
below, no p-adics needed), and one finite computation, COVERAGE.

ELIMINATION. Let S be a counterexample, b = max S, p a prime, and suppose the
only multiples of p that are <= b are p and 2p (i.e. 2p <= b < 3p), with p >= 5.
Then p not in S and 2p not in S.
  Proof. Let M = lcm(S \\ {p, 2p}); p is coprime to M since no element of that
  set is a multiple of p. Multiply 1 = sum_{n in S} 1/n by 2pM.
    - if S contains p only:    2pM = 2M + 2p*K  =>  2M = 2p(M-K) => p | 2M
    - if S contains 2p only:   2pM = M + 2p*K   =>   M = 2p(M-K) => p | M
    - if S contains both:      2pM = 3M + 2p*K  =>  3M = 2p(M-K) => p | 3M
  where K is an integer (a sum of terms M/n, each an integer). In every case
  p | 6M, and gcd(p,M) = 1 with p >= 5 forces p | 6, a contradiction.
  The same argument with b < 2p (so p is the only multiple of p) gives p not in S.

COVERAGE. If p >= 5 and 2p-1 are both prime then, for every b in [2p, 3p):
2p-1 is a prime exceeding b/2 (so it is the only multiple of itself that is
<= b) and p satisfies the hypothesis above. Hence BOTH of the consecutive
integers 2p-1 and 2p are excluded from S. Since min(S) <= b/2 < 2p-1 (see
below) and 2p <= b, S must contain an element below 2p-1 and one above 2p, with
neither of the two in between -- a gap of at least 3. Contradiction.
Symmetrically, p and 2p+1 both prime excludes the pair (2p, 2p+1) for
b in [2p+1, 3p).

  min(S) <= b/2: if min(S) > b/2 then min(S)-1 >= floor(b/2), so
  1 = sum 1/n <= sum_{n=floor(b/2)+1}^{b} 1/n, which has ceil(b/2) terms, the
  largest being 1/(floor(b/2)+1) and the rest strictly smaller; the total is
  therefore strictly below ceil(b/2)/(floor(b/2)+1) <= 1. Contradiction.

So it remains to check that the intervals [2p, 3p) / [2p+1, 3p) cover every
b in (b0, B], and to settle b <= b0 by direct exhaustive search. That is what
this script does.

Usage:
    python verify287.py 1000000            # verify the claim up to B = 10^6
    python verify287.py 1000000 --spot 40  # also audit 40 random certificates
"""
from __future__ import annotations

import argparse
import random
from fractions import Fraction

from sympy import isprime


# --------------------------------------------------------------------------
def exhaustive_small(bmax: int):
    """Every S in [2,bmax] with gaps <= 2 and reciprocal sum exactly 1."""
    tail = [Fraction(0)] * (bmax + 2)
    for n in range(bmax, 1, -1):
        tail[n] = tail[n + 1] + Fraction(1, n)
    hits = []

    def go(cur, tot, chain):
        if tot == 1:
            hits.append(list(chain))
            return
        if tot > 1:
            return
        for step in (1, 2):
            nxt = cur + step
            if nxt <= bmax and tot + tail[nxt] >= 1:
                chain.append(nxt)
                go(nxt, tot + Fraction(1, nxt), chain)
                chain.pop()

    for a in range(2, bmax + 1):
        if tail[a] < 1:
            break
        go(a, Fraction(1, a), [a])
    return hits


def witness_for(b: int, search_span: int = 4000):
    """Find a prime p certifying b, checking every hypothesis with sympy."""
    lo = b // 3 + 1                       # need 2p <= b < 3p  =>  b/3 < p <= b/2
    hi = b // 2
    for p in range(max(5, hi), max(4, lo - 1), -1):
        if p < 5 or not isprime(p):
            continue
        if not (2 * p <= b < 3 * p):
            continue
        if isprime(2 * p - 1):
            return p, (2 * p - 1, 2 * p)
        if 2 * p + 1 <= b and isprime(2 * p + 1):
            return p, (2 * p, 2 * p + 1)
    return None, None


def audit(b: int) -> bool:
    """Re-check a single certificate from first principles."""
    p, pair = witness_for(b)
    if p is None:
        return False
    x, y = pair
    assert y == x + 1 and x + 1 <= b, "pair must be consecutive and inside [.,b]"
    assert 2 * x > b, "x must exceed b/2 so that x > min(S)"
    assert isprime(p) and p >= 5 and 2 * p <= b < 3 * p, "p hypothesis"
    q = x if x % 2 else y                 # the odd one of the pair is the prime
    assert isprime(q) and 2 * q > b, "q must be a prime exceeding b/2"
    even = y if x % 2 else x
    assert even == 2 * p, "the even one of the pair must be 2p"
    return True


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("B", type=lambda s: int(float(s)))
    ap.add_argument("--b0", type=int, default=37)
    ap.add_argument("--spot", type=int, default=25)
    a = ap.parse_args()

    print(f"[1/3] exhaustive search over max(S) <= {a.b0} ...")
    hits = exhaustive_small(a.b0)
    print(f"      counterexamples found: {hits if hits else 'NONE'}")

    print(f"[2/3] interval coverage of ({a.b0}, {a.B:,}] ...")
    reach, used = a.b0 + 1, 0
    p = 5
    while reach <= a.B:
        if isprime(p) and 2 * p <= a.B + 1:
            if isprime(2 * p - 1):
                lo, hi = 2 * p, 3 * p
            elif isprime(2 * p + 1):
                lo, hi = 2 * p + 1, 3 * p
            else:
                p += 1
                continue
            if lo > reach:
                print(f"      HOLE at b={reach}: no witness interval covers it")
                return
            if hi > reach:
                reach, used = hi, used + 1
        p += 1
    print(f"      covered to b={min(reach - 1, a.B):,} using {used} witness primes")

    print(f"[3/3] auditing {a.spot} random certificates against sympy ...")
    rng = random.Random(20260721)
    bad = [b for b in (rng.randint(a.b0 + 1, a.B) for _ in range(a.spot))
           if not audit(b)]
    print(f"      failed audits: {bad if bad else 'none'}")

    ok = (not hits) and (not bad) and reach - 1 >= a.B
    print()
    print(f"VERIFIED: no counterexample to Erdos 287 has max(S) <= {a.B:,}"
          if ok else "NOT VERIFIED -- see above")


if __name__ == "__main__":
    main()
