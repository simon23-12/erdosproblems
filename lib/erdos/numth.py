"""Number-theoretic search primitives.

Used by: [287] [366] [375] [398] [458] [647] [699] [848].

Everything here is exact integer arithmetic -- no floats in any code path that
can influence a reported result. Floats appear only in loop bounds that are
padded generously and then re-checked exactly.
"""
from __future__ import annotations

import itertools


# --------------------------------------------------------------------------
# sieves
# --------------------------------------------------------------------------
def primes_upto(n: int) -> list[int]:
    """Sieve of Eratosthenes."""
    if n < 2:
        return []
    sieve = bytearray([1]) * (n + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i:: i] = bytearray(len(sieve[i * i:: i]))
    return [i for i in range(2, n + 1) if sieve[i]]


def smallest_prime_factor(n: int) -> list[int]:
    """spf[k] = least prime factor of k, for k <= n. Enables O(log k) factoring."""
    spf = list(range(n + 1))
    for i in range(2, int(n ** 0.5) + 1):
        if spf[i] == i:
            for j in range(i * i, n + 1, i):
                if spf[j] == j:
                    spf[j] = i
    return spf


def divisor_counts(n: int) -> list[int]:
    """tau[k] for k <= n, by the direct multiples sieve. O(n log n)."""
    tau = [0] * (n + 1)
    for d in range(1, n + 1):
        for m in range(d, n + 1, d):
            tau[m] += 1
    return tau


def factor_with_spf(k: int, spf: list[int]) -> dict[int, int]:
    f: dict[int, int] = {}
    while k > 1:
        p = spf[k]
        while k % p == 0:
            k //= p
            f[p] = f.get(p, 0) + 1
    return f


# --------------------------------------------------------------------------
# valuations and k-full numbers
# --------------------------------------------------------------------------
def vp(n: int, p: int) -> int:
    """p-adic valuation of a nonzero integer."""
    e = 0
    while n % p == 0:
        n //= p
        e += 1
    return e


def is_kfull(n: int, k: int = 2, trial_limit: int = 100000) -> bool | None:
    """Is every prime dividing n present to exponent >= k?

    Returns True/False when decided by trial division, and None when a cofactor
    survives that is too large to settle here -- callers must handle None rather
    than assume. (`is_kfull_exact` resolves it with sympy at higher cost.)
    """
    if n <= 0:
        return False
    if n == 1:
        return True
    m = n
    for p in _small_primes(trial_limit):
        if p * p > m and m > 1:
            break
        if m % p == 0:
            e = 0
            while m % p == 0:
                m //= p
                e += 1
            if e < k:
                return False
    if m == 1:
        return True
    r = _int_root(m, 2)
    if r * r == m:
        return True
    for e in range(k, 7):
        r = _int_root(m, e)
        if r ** e == m:
            return True
    if m < trial_limit ** 2:
        return False        # m is a single prime to the first power
    return None             # undecided: cofactor too big for trial division


def is_kfull_exact(n: int, k: int = 2) -> bool:
    """Definitive answer via full factorisation (sympy). Slower."""
    from sympy import factorint

    if n <= 0:
        return False
    return all(e >= k for e in factorint(n).values())


def kfull_upto(limit: int, k: int = 2):
    """Yield every k-full number <= limit, unsorted.

    Every k-full number is uniquely a product a^k * b^(k+1) * ... ; for k=2 the
    classic parametrisation n = a^2 * b^3 with b squarefree is used, and for
    k=3 the analogous n = a^3 * b^4 * c^5 with the usual coprimality handling.
    Correctness is checked in tests/test_numth.py against a brute-force filter.
    """
    if k == 2:
        for b in itertools.count(1):
            b3 = b ** 3
            if b3 > limit:
                break
            if not _is_squarefree_small(b):
                continue
            a = 1
            while a * a * b3 <= limit:
                yield a * a * b3
                a += 1
    elif k == 3:
        seen = set()
        c = 1
        while c ** 5 <= limit:
            b = 1
            while (c ** 5) * (b ** 4) <= limit:
                a = 1
                while (c ** 5) * (b ** 4) * (a ** 3) <= limit:
                    v = (c ** 5) * (b ** 4) * (a ** 3)
                    if v not in seen:
                        seen.add(v)
                        yield v
                    a += 1
                b += 1
            c += 1
    else:
        raise NotImplementedError("kfull_upto supports k=2,3")


_SMALL_PRIMES_CACHE: list[int] = []


def _small_primes(limit: int) -> list[int]:
    global _SMALL_PRIMES_CACHE
    if not _SMALL_PRIMES_CACHE or _SMALL_PRIMES_CACHE[-1] < limit:
        _SMALL_PRIMES_CACHE = primes_upto(limit)
    return _SMALL_PRIMES_CACHE


def _is_squarefree_small(n: int) -> bool:
    d = 2
    while d * d <= n:
        if n % (d * d) == 0:
            return False
        if n % d == 0:
            n //= d
        d += 1
    return True


def _int_root(n: int, k: int) -> int:
    """Floor of the k-th root, exactly (no float rounding at the boundary)."""
    if n < 0:
        raise ValueError
    if n == 0:
        return 0
    x = int(round(n ** (1.0 / k)))
    while x ** k > n:
        x -= 1
    while (x + 1) ** k <= n:
        x += 1
    return x


# --------------------------------------------------------------------------
# binomial / Kummer
# --------------------------------------------------------------------------
def kummer_carries(n: int, i: int, p: int) -> int:
    """Number of carries when adding i and n-i in base p.

    Kummer: this equals v_p(C(n,i)). Lets us read off prime divisors of huge
    binomial coefficients without ever forming them. Used by [699].
    """
    j = n - i
    carries = c = 0
    while i or j:
        s = (i % p) + (j % p) + c
        c = 1 if s >= p else 0
        carries += c
        i //= p
        j //= p
    return carries
