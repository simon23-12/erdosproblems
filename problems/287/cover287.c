/* Erdos problem 287 -- stage 3 (interval covering) at scale.
 *
 * See search287.py for the exclusion lemma. The witness used here:
 *
 *   if p >= 5 and 2p-1 are both prime, then for every b in [2p, 3p) the two
 *   CONSECUTIVE integers 2p-1 and 2p are both forced out of S:
 *       - 2p-1 is prime with floor(b/(2p-1)) = 1  (since b < 3p < 2(2p-1)),
 *         and Bound(1) = 1, so no multiple of it is in S;
 *       - p is prime with floor(b/p) = 2 (since 2p <= b < 3p), p >= 5 > Bound(2)=3,
 *         so neither p nor 2p is in S.
 *     Both exceed b/2 >= min(S), so S would need a gap >= 3. Contradiction.
 *
 *   if instead 2p+1 is prime, the pair (2p, 2p+1) works for b in [2p+1, 3p).
 *
 * So each such p certifies a whole interval of b, and all this program does is
 * check that the intervals cover [b0, B] with no hole. Two synchronised
 * segmented sieves are kept: one window to walk p, a second (twice as wide,
 * twice as far out) to test 2p +- 1.
 *
 * Build: cc -O3 -o cover287 cover287.c -lm
 * Run:   ./cover287 <b0> <B>
 *
 * b0 is the FIRST value of b still needing coverage (everything below it must
 * already be settled some other way). max(S) <= 37 is settled by the exhaustive
 * search in search287.py, so the intended invocation is `./cover287 38 <B>`.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

typedef unsigned long long u64;

static u64 *base;            /* primes up to sqrt(2B+4) */
static u64 nbase;

static void build_base(u64 limit)
{
    char *c = calloc(limit + 1, 1);
    for (u64 i = 2; i * i <= limit; i++)
        if (!c[i]) for (u64 j = i * i; j <= limit; j += i) c[j] = 1;
    nbase = 0;
    for (u64 i = 2; i <= limit; i++) if (!c[i]) nbase++;
    base = malloc(nbase * sizeof(u64));
    u64 k = 0;
    for (u64 i = 2; i <= limit; i++) if (!c[i]) base[k++] = i;
    free(c);
}

/* mark composites of [lo,hi) into flags (1 = prime) */
static void segment(u64 lo, u64 hi, char *flags)
{
    memset(flags, 1, hi - lo);
    if (lo < 2) for (u64 v = lo; v < 2 && v < hi; v++) flags[v - lo] = 0;
    for (u64 i = 0; i < nbase; i++) {
        u64 p = base[i];
        if (p * p >= hi) break;
        u64 start = (lo + p - 1) / p * p;
        if (start < p * p) start = p * p;
        for (u64 m = start; m < hi; m += p) flags[m - lo] = 0;
    }
}

int main(int argc, char **argv)
{
    if (argc != 3) { fprintf(stderr, "usage: %s b0 B\n", argv[0]); return 1; }
    u64 b0 = strtoull(argv[1], NULL, 10);
    u64 B  = strtoull(argv[2], NULL, 10);

    u64 top = 2 * B + 4;
    build_base((u64)(sqrt((double)top) + 2));

    const u64 W = 1u << 22;
    char *fa = malloc(W + 2);            /* window on p */
    char *fb = malloc(2 * W + 8);        /* window on 2p +- 1 */

    u64 reach = b0, used = 0, pmax = (B + 1) / 2;
    u64 hole = 0;

    for (u64 lo = 0; lo <= pmax && !hole; lo += W) {
        u64 hi = lo + W; if (hi > pmax + 1) hi = pmax + 1;
        segment(lo, hi, fa);
        u64 blo = (lo >= 1 ? 2 * lo - 1 : 0), bhi = 2 * hi + 2;
        segment(blo, bhi, fb);

        for (u64 p = (lo < 5 ? 5 : lo); p < hi; p++) {
            if (!fa[p - lo]) continue;
            u64 l, h = 3 * p;
            if (fb[(2 * p - 1) - blo])      l = 2 * p;
            else if (fb[(2 * p + 1) - blo]) l = 2 * p + 1;
            else continue;
            if (l > reach) { hole = reach; break; }   /* uncovered gap */
            if (h > reach) { reach = h; used++; }
            if (reach > B) break;
        }
        if (reach > B) break;
    }

    if (hole) {
        printf("# HOLE: coverage stops at b=%llu (no witness interval starts <= it)\n",
               (unsigned long long)hole);
        return 2;
    }
    u64 got = reach - 1; if (got > B) got = B;
    printf("# covered contiguously from b0=%llu to b=%llu using %llu witness primes\n",
           (unsigned long long)b0, (unsigned long long)got, (unsigned long long)used);
    return got >= B ? 0 : 3;
}
