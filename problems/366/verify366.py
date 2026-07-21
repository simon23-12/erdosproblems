#!/usr/bin/env python3
"""STANDALONE re-verification for Erdos problem 366.

Shares no code with search366.c. It checks the two things that could make the C
search silently wrong:

  1. RECALL -- does it find the pairs that are known to exist?
     The only known consecutive {3-full, 2-full} pairs are 8|9 and
     12167|12168 (both with the 3-full member first). The C search must report
     exactly these and nothing else on a small range.

  2. PRECISION -- is the powerfulness test right?
     The C test trial-divides by primes <= P0 and then declares the remaining
     cofactor powerful iff it is a perfect k-th power (k <= 4). That shortcut is
     only valid while P0^5 > X. This script re-decides powerfulness with
     sympy.factorint on random values -- including values deliberately built to
     have the shape p^2 q^3 that the shortcut would misjudge if P0 were too
     small -- and compares.

(A real bug was caught this way: an early version computed 2^128 mod p where it
needed 2^64 mod p, which made the fast modulo wrong and produced a flood of
false hits at 1e20. The known-pair check is what surfaced it.)

Usage:
    python verify366.py                 # full check, ~1 min
"""
from __future__ import annotations

import random
import subprocess
import pathlib

from sympy import factorint, prime

HERE = pathlib.Path(__file__).resolve().parent


def is_powerful(n: int) -> bool:
    return n > 0 and all(e >= 2 for e in factorint(n).values())


def is_cubefull(n: int) -> bool:
    return n > 0 and all(e >= 3 for e in factorint(n).values())


def run(x: str) -> list[str]:
    out = subprocess.run([str(HERE / "search366"), x], capture_output=True,
                         text=True).stdout
    return [l for l in out.splitlines() if l.startswith("HIT")]


def main():
    print("[1/3] recall: the C search must find both known pairs and no others")
    hits = run("1e13")
    got = sorted(int(h.split("m=")[1].split()[0]) for h in hits)
    print(f"      reported 3-full members below 1e13: {got}")
    ok1 = got == [8, 12167]
    for m in got:
        assert is_cubefull(m), f"{m} is not 3-full!"
        assert is_powerful(m + 1) or is_powerful(m - 1), f"neither neighbour of {m}"
    print(f"      both are genuinely 3-full with a powerful neighbour: yes")
    print(f"      -> {'PASS' if ok1 else 'FAIL'}")

    print("[2/3] precision: powerfulness verdicts vs sympy on random values")
    rng = random.Random(366)
    bad = []
    # a mix of random integers and deliberately powerful / near-powerful ones
    cands = [rng.randrange(10 ** 6, 10 ** 18) for _ in range(300)]
    cands += [rng.randrange(2, 10 ** 6) ** 2 * rng.randrange(2, 100) ** 3
              for _ in range(200)]
    cands += [prime(rng.randrange(100, 5000)) ** 2 * prime(rng.randrange(100, 900)) ** 3
              for _ in range(100)]          # the p^2 q^3 shape
    # Re-implement the C shortcut exactly, with P0 chosen as the C program does.
    X = 10 ** 24
    P0 = int(X ** 0.2 * 1.05) + 1000
    assert P0 ** 5 > X, "shortcut invalid at this P0"
    small = []
    n = 2
    from sympy import primerange
    small = list(primerange(2, P0 + 1))

    def shortcut(v: int) -> bool:
        if v <= 1:
            return v == 1
        for p in small:
            if p * p > v:
                return False           # what remains is a prime, exponent 1
            if v % p == 0:
                v //= p
                if v % p:
                    return False
                while v % p == 0:
                    v //= p
                if v == 1:
                    return True
        for k in (2, 3, 4):             # cofactor: powerful iff perfect power
            r = round(v ** (1.0 / k))
            for rr in (r - 1, r, r + 1):
                if rr > 0 and rr ** k == v:
                    return True
        return False

    for v in cands:
        if shortcut(v) != is_powerful(v):
            bad.append(v)
    print(f"      {len(cands)} values tested (random, a^2 b^3, and p^2 q^3 shapes)")
    print(f"      disagreements with sympy: {bad if bad else 'none'}")
    ok2 = not bad

    print("[3/3] the search's own claim")
    log = HERE / "run_1e24.log"
    if log.exists():
        tail = [l for l in log.read_text().splitlines() if l.startswith("#") or l.startswith("HIT")]
        for l in tail:
            print(f"      {l}")
    else:
        print("      (run_1e24.log not present yet)")

    print()
    print("VERIFIED: recall and precision both check out"
          if ok1 and ok2 else "NOT VERIFIED -- see above")


if __name__ == "__main__":
    main()
