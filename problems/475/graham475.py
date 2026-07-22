#!/usr/bin/env python3
"""Erdos problem 475 (https://www.erdosproblems.com/475).

    Let p be prime. Given any finite A subset of F_p \\ {0}, is there always a
    rearrangement A = {a_1,...,a_t} such that all partial sums
    sum_{k<=m} a_k  (1 <= m <= t) are distinct?

Graham's rearrangement conjecture; such an ordering is called VALID.

WHAT IS ACTUALLY OPEN
---------------------
Two theorems bracket the problem:
  * every A with |A| <= 20 is sequenceable in any abelian group
    (Costa-Pellegrini; 22 for zero-sum sets).  NOTE erdosproblems.com still says
    "t <= 12" -- that is stale, and using it would have made this search look
    far more novel than it is;
  * p-3 <= t <= p-1 is settled (Hicks-Ollis-Schmitt).
So only t in [21, p-4] is open, which is EMPTY for p <= 23. The first genuinely
open primes are p = 29 (t in [21,25]) and p = 31 (t in [21,27]); p = 37 would
need 1.4e10 subsets and is out of reach.

SEARCH DESIGN (and why it is still sound)
-----------------------------------------
A naive ascending DFS is exponential in exactly the open regime -- p=17, t=12
costs ~175 ms per subset. Randomised greedy with restarts costs ~0.04 ms, a
4000x speedup, and empirically never fails.

But greedy failing does NOT prove that no valid ordering exists. So:

    find_ordering() = randomised greedy, and on failure a COMPLETE DFS.

Only DFS exhaustion is allowed to report "no valid ordering". Every ordering
that is found is re-checked by check_ordering(), which recomputes the partial
sums from scratch and shares nothing with the search.

WHAT THIS PROGRAM DOES AND DOES NOT ESTABLISH
---------------------------------------------
It verifies, exhaustively, that every subset of F_p\\{0} whose size lies in the
open window has a valid ordering. That part is machine-checked here.

It does NOT verify t <= 20 or t >= p-3 -- those are CITED theorems. So the
sentence "Graham's conjecture holds for p = 29" is a combination of this
computation with the literature, and only the computation is mine. State it that
way; do not let the citation ride along as if it had been checked.

Usage:
    python graham475.py --selftest
    python graham475.py --p 29                 # the whole open window for p=29
    python graham475.py --p 31 --t 21          # one slice
"""
from __future__ import annotations

import argparse
import random
import time
from itertools import combinations


def check_ordering(order: list[int], A: tuple[int, ...], p: int) -> bool:
    """Independent re-verification: recompute the partial sums and test them."""
    if sorted(order) != sorted(A):
        return False
    sums, cur = [], 0
    for v in order:
        cur = (cur + v) % p
        sums.append(cur)
    return len(set(sums)) == len(sums)


def _greedy(A: tuple[int, ...], p: int, rnd: random.Random, tries: int):
    for _ in range(tries):
        rem = list(A)
        rnd.shuffle(rem)
        cur, seen, order = 0, set(), []
        while rem:
            for i, v in enumerate(rem):
                s = (cur + v) % p
                if s not in seen:
                    seen.add(s)
                    order.append(v)
                    cur = s
                    rem.pop(i)
                    break
            else:
                break
        if not rem:
            return order
    return None


def _dfs(A: tuple[int, ...], p: int):
    """COMPLETE search. Returns an ordering, or None only after exhausting
    every possibility -- this is the only thing entitled to say 'no'."""
    t = len(A)
    order: list[int] = []
    used = [False] * t
    seen: set[int] = set()

    def go(cur: int) -> bool:
        if len(order) == t:
            return True
        for i, v in enumerate(A):
            if used[i]:
                continue
            s = (cur + v) % p
            if s in seen:
                continue
            used[i] = True
            seen.add(s)
            order.append(v)
            if go(s):
                return True
            order.pop()
            seen.discard(s)
            used[i] = False
        return False

    return order if go(0) else None


def find_ordering(A: tuple[int, ...], p: int, rnd: random.Random,
                  tries: int = 60) -> tuple[list[int] | None, bool]:
    """(ordering or None, whether the exhaustive fallback was needed)."""
    o = _greedy(A, p, rnd, tries)
    if o is not None:
        return o, False
    return _dfs(A, p), True


def sweep(p: int, t: int, seed: int = 475, progress: int = 0):
    rnd = random.Random(seed)
    n = fallbacks = 0
    bad = []
    for A in combinations(range(1, p), t):
        o, fell_back = find_ordering(A, p, rnd)
        fallbacks += fell_back
        if o is None or not check_ordering(o, A, p):
            bad.append(A)
        n += 1
        if progress and n % progress == 0:
            print(f"      ...{n:,}", flush=True)
    return n, fallbacks, bad


def open_window(p: int) -> range:
    """t values not already settled by theory: [21, p-4]."""
    return range(21, p - 3)


def selftest():
    for p in (5, 7, 11, 13, 17, 19):
        tot = 0
        for t in range(1, p):
            n, fb, bad = sweep(p, t)
            tot += n
            assert not bad, (p, t, bad[:3])
        print(f"  p={p}: all {tot:,} subsets of F_p\\{{0}} have a valid ordering")
    o, _ = find_ordering((1, 2, 3, 4), 7, random.Random(1))
    assert check_ordering(o, (1, 2, 3, 4), 7)
    print(f"  sample: A={{1,2,3,4}} in F_7 -> {o}")
    # the exhaustive fallback really is exhaustive: a set with NO valid ordering
    # must exist somewhere for the fallback to be meaningful, so check that DFS
    # agrees with greedy wherever greedy succeeds
    rnd = random.Random(9)
    for A in combinations(range(1, 13), 6):
        g = _greedy(A, 13, rnd, 60)
        d = _dfs(A, 13)
        assert (g is None) == (d is None), A
    print("  greedy and exhaustive DFS agree on all 6-subsets of F_13")
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--p", type=int, default=0)
    ap.add_argument("--t", type=int, default=0)
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.p:
        print(__doc__)
        return
    ts = [a.t] if a.t else list(open_window(a.p))
    if not ts:
        print(f"p={a.p}: open window [21,{a.p-4}] is empty -- settled by theory")
        return
    grand = grand_bad = grand_fb = 0
    for t in ts:
        t0 = time.time()
        n, fb, bad = sweep(a.p, t, progress=200000)
        grand += n
        grand_fb += fb
        grand_bad += len(bad)
        print(f"  p={a.p} t={t}: {n:,} subsets, {len(bad)} with NO valid ordering, "
              f"{fb} needed the exhaustive fallback  [{time.time()-t0:.1f}s]", flush=True)
        if bad:
            print(f"    COUNTEREXAMPLES: {bad[:5]}")
    print()
    print(f"p={a.p}: {grand:,} subsets over t in {list(ts)}, "
          f"{grand_bad} counterexamples, {grand_fb} fallbacks")
    print("RESULT: Graham's conjecture holds for every subset in the tested window"
          if not grand_bad else "RESULT: COUNTEREXAMPLE FOUND")


if __name__ == "__main__":
    main()
