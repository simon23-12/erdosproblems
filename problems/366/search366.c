/* Erdos problem 366  (https://www.erdosproblems.com/366)
 *
 *   Are there any 2-full n such that n+1 is 3-full?
 *   (n is k-full when p | n implies p^k | n.)
 *
 * The two known consecutive {3-full, 2-full} pairs both have the 3-full member
 * FIRST -- 8|9 and 12167|12168 -- so the question as stated (2-full then 3-full)
 * has no known example at all. This program searches both orders at once.
 *
 * WHY THIS IS CHEAPER THAN THE PUBLISHED BOUND. The cited 10^22 comes from
 * OEIS A060355, a table of consecutive POWERFUL pairs, and powerful numbers are
 * ~2.17*sqrt(X) in number. But one member of the pair has to be 3-full, and
 * 3-full numbers are only ~c*X^(1/3) -- about 3*10^7 below 10^24 versus 2*10^12
 * powerful ones. So: enumerate the 3-full member, test its two neighbours.
 *
 * POWERFULNESS TEST (this is the only subtle part, so it is spelled out).
 * Trial-divide v by every prime <= P0, rejecting the moment some prime appears
 * to exponent exactly 1. Let c be what remains; every prime factor of c exceeds
 * P0. Suppose c > 1 is powerful, so c = prod p_i^e_i with every e_i >= 2. The
 * smallest shape that is NOT a perfect power is p^2 q^3 (exponents coprime),
 * which needs sum(e_i) = 5 and hence c > P0^5. So as long as
 *
 *              P0^5 > X,
 *
 * every possible c is p^2, p^3, p^4 or p^2 q^2 = (pq)^2 -- all perfect powers, and
 *
 *              c is powerful  <=>  c is a perfect k-th power, k in 2..4.
 *
 * P0 is therefore chosen as X^(1/5) rounded up (with margin), and the program
 * asserts P0^5 > X before trusting a single answer.
 *
 * Build: cc -O3 -o search366 search366.c -lm
 * Run:   ./search366 <X>        e.g. ./search366 1e23
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

typedef unsigned __int128 u128;
typedef unsigned long long u64;

static u64 P0;                            /* trial-division bound, > X^(1/5)   */
static uint32_t *sp; static int nsp;      /* primes <= P0                       */
static u64 *r64;                          /* r64[i] = 2^64 mod sp[i]            */
static uint32_t *cp; static u64 ncp;      /* primes <= cbrt(X), for generation */

static void sieve(u64 limit, uint32_t **out, u64 *cnt)
{
    char *c = calloc(limit + 1, 1);
    if (!c) { fprintf(stderr, "oom sieving to %llu\n", limit); exit(1); }
    for (u64 i = 2; i * i <= limit; i++)
        if (!c[i]) for (u64 j = i * i; j <= limit; j += i) c[j] = 1;
    u64 k = 0;
    for (u64 i = 2; i <= limit; i++) if (!c[i]) k++;
    *out = malloc(k * sizeof(uint32_t));
    *cnt = k; k = 0;
    for (u64 i = 2; i <= limit; i++) if (!c[i]) (*out)[k++] = (uint32_t)i;
    free(c);
}

/* exact integer k-th root of v (floor), no float rounding at the boundary */
static u128 iroot(u128 v, int k)
{
    if (v < 2) return v;
    long double g = powl((long double)v, 1.0L / k);
    u128 x = (u128)g;
    if (x > 2) x -= 2;
    for (;;) {
        u128 p = 1; int ov = 0;
        for (int i = 0; i < k; i++) {
            if (p > (~(u128)0) / (x + 1)) { ov = 1; break; }
            p *= (x + 1);
        }
        if (ov || p > v) break;
        x++;
    }
    return x;
}

static int is_perfect_power(u128 v)
{
    for (int k = 2; k <= 4; k++) {
        u128 r = iroot(v, k), p = 1;
        for (int i = 0; i < k; i++) p *= r;
        if (p == v) return 1;
    }
    return 0;
}

/* v mod p for small p, via the 64-bit halves -- avoids the slow __umodti3.
   Safe because (hi%p) * (2^64 mod p) < p^2 < 2^64 for every p we use. */
static inline u64 mod_u128(u128 v, u64 p, u64 r)
{
    return (((u64)(v >> 64) % p) * r + (u64)v % p) % p;
}

static int is_powerful(u128 v)
{
    if (v <= 1) return v == 1;
    for (int i = 0; i < nsp; i++) {
        u64 p = sp[i], r = r64[i];
        if ((u128)p * p > v) {            /* fully factored: what's left is prime */
            return 0;                     /* ... to exponent 1, so not powerful  */
        }
        if (mod_u128(v, p, r) == 0) {
            v /= p;
            if (mod_u128(v, p, r) != 0) return 0;     /* exponent exactly 1 */
            while (mod_u128(v, p, r) == 0) v /= p;
            if (v == 1) return 1;
        }
    }
    return is_perfect_power(v);           /* justified in the header comment */
}

static u128 X;
static u64 n_cubefull = 0, n_hits = 0;

static void report(u128 m, int dir)
{
    /* dir = -1 : m-1 is 2-full and m is 3-full  (the question as asked)
       dir = +1 : m is 3-full and m+1 is 2-full  (the 8|9, 12167|12168 shape) */
    char buf[64]; int i = 0;
    u128 t = m;
    do { buf[i++] = '0' + (int)(t % 10); t /= 10; } while (t);
    buf[i] = 0;
    for (int a = 0, b = i - 1; a < b; a++, b--) { char s = buf[a]; buf[a] = buf[b]; buf[b] = s; }
    printf("HIT dir=%+d  3-full m=%s  (neighbour m%+d is 2-full)\n", dir, buf, dir);
    fflush(stdout);
    n_hits++;
}

static void check(u128 m)
{
    n_cubefull++;
    if (m >= 2 && is_powerful(m - 1)) report(m, -1);
    if (is_powerful(m + 1)) report(m, +1);
}

/* enumerate 3-full numbers: every prime taken to exponent >= 3 */
static void gen(u64 idx, u128 val)
{
    check(val);
    for (u64 i = idx; i < ncp; i++) {
        u128 p = cp[i], pe = p * p * p;
        if (pe > X / val) break;
        for (u128 v = val * pe; ; ) {
            gen(i + 1, v);
            if (p > X / v) break;
            v *= p;
        }
    }
}

int main(int argc, char **argv)
{
    double xd = (argc > 1) ? atof(argv[1]) : 1e23;
    X = (u128)xd;
    u64 cbrt_x = (u64)(cbrt(xd) + 2);

    /* P0 must satisfy P0^5 > X; take X^(1/5) with a safety margin and CHECK it */
    P0 = (u64)(pow(xd, 0.2) * 1.05) + 1000;
    u128 p5 = 1; for (int i = 0; i < 5; i++) p5 *= P0;
    if (!(p5 > X)) { fprintf(stderr, "# FATAL: P0^5 <= X, test invalid\n"); return 2; }

    u64 tmp;
    sieve(P0, &sp, &tmp); nsp = (int)tmp;
    r64 = malloc(nsp * sizeof(u64));
    for (int i = 0; i < nsp; i++) r64[i] = (u64)((~(u64)0 % sp[i] + 1) % sp[i]);   /* 2^64 mod p */
    sieve(cbrt_x, &cp, &ncp);
    fprintf(stderr, "# X=%.3g  P0=%llu (P0^5 > X: ok)  primes<=P0:%d  "
            "primes<=cbrt(X):%llu\n", xd, (unsigned long long)P0, nsp,
            (unsigned long long)ncp);

    gen(0, 1);

    printf("# 3-full numbers examined: %llu\n", (unsigned long long)n_cubefull);
    printf("# hits: %llu\n", (unsigned long long)n_hits);
    printf(n_hits ? "" : "# no 2-full/3-full consecutive pair in either order up to X\n");
    return 0;
}
