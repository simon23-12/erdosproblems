#!/usr/bin/env python3
"""Erdos problem 647 (https://www.erdosproblems.com/647) -- reference implementation.

    Let tau(n) count the divisors of n. Is there some n > 24 with
        max_{m < n} (m + tau(m))  <=  n + 2 ?

This is the slow, obviously-correct version: it sieves tau by brute force
(for every d, bump every multiple of d) and then walks n upwards keeping the
running maximum of m + tau(m) over all m < n. No cleverness, nothing to trust.

It exists to pin down the answer on a range small enough to check by hand, and
to serve as a cross-check oracle for the fast C search in search647.c.

Usage:
    python verify647.py [N]          # default N = 10**7

Prints every n <= N satisfying the condition.
"""
import sys


def solutions_up_to(N: int):
    # tau[m] = number of divisors of m, for m <= N. Brute force on purpose.
    tau = bytearray(N + 1)          # counts stay < 256 for N <= 10**7
    tau_big = None
    for d in range(1, N + 1):
        for m in range(d, N + 1, d):
            tau[m] += 1
            if tau[m] == 0:         # wrapped a byte -> need wider counters
                raise OverflowError("tau exceeded 255; use the C version")

    out = []
    running = 0                     # max over m < n of (m + tau(m))
    for n in range(1, N + 1):
        if n >= 2 and running <= n + 2:
            out.append(n)
        s = n + tau[n]
        if s > running:
            running = s
    return out


def main():
    N = int(float(sys.argv[1])) if len(sys.argv) > 1 else 10 ** 7
    sols = solutions_up_to(N)
    print(f"N = {N}")
    print(f"n with max_{{m<n}}(m+tau(m)) <= n+2 :  {sols}")
    big = [n for n in sols if n > 24]
    print(f"solutions with n > 24: {big if big else 'NONE'}")


if __name__ == "__main__":
    main()
