/* Erdos problem 647  (https://www.erdosproblems.com/647)
 *
 *   Let tau(n) count divisors.  Is there some n > 24 with
 *       max_{m < n} (m + tau(m))  <=  n + 2 ?
 *
 * Erdos offered GBP 25 for such an n.  This program searches a range [L,R).
 *
 * ---------------------------------------------------------------------------
 * Why the test is LOCAL (this is the only non-obvious step, so spelled out):
 *
 *   The condition is  m + tau(m) <= n + 2  for every m < n.
 *   Equivalently      tau(n-j)   <= j + 2  for every j >= 1.
 *   Since tau(m) <= TAUMAX for every m in range, the constraint for
 *   j >= TAUMAX - 2 is satisfied automatically.  So only the window
 *   j = 1 .. W matters, provided W + 2 >= TAUMAX.
 *
 *   max tau(m) is 6720 for m < 10^12 and 10752 for m < 10^13 (OEIS A066150),
 *   so W = 16384 is safe well past 10^13.  The program MEASURES the largest
 *   tau it actually sees and refuses to report success if that measurement
 *   ever reaches W + 2, so the assumption is checked rather than trusted.
 *
 *   Being local is what makes the range splittable across cores.
 * ---------------------------------------------------------------------------
 *
 * tau is obtained by a segmented factoring sieve: hold the running cofactor
 * rem[i] = (lo+i) with all primes p <= sqrt(R) divided out.  Whatever remains
 * is 1 or a single prime (it cannot be a product of two primes > sqrt(R),
 * as that would exceed R), which is why the final "if rem > 1 then tau *= 2".
 *
 * Build: cc -O3 -o search647 search647.c -lm
 * Run:   ./search647 <L> <R>
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#define W 16384              /* window of j values that can matter */

static uint32_t *primes;
static uint32_t nprimes;

/* primes up to `limit` inclusive, plain sieve of Eratosthenes */
static void build_primes(uint32_t limit)
{
    char *comp = calloc((size_t)limit + 1, 1);
    if (!comp) { fprintf(stderr, "oom\n"); exit(1); }
    for (uint64_t i = 2; i * i <= limit; i++)
        if (!comp[i])
            for (uint64_t j = i * i; j <= limit; j += i) comp[j] = 1;
    nprimes = 0;
    for (uint32_t i = 2; i <= limit; i++) if (!comp[i]) nprimes++;
    primes = malloc((size_t)nprimes * sizeof(uint32_t));
    uint32_t k = 0;
    for (uint32_t i = 2; i <= limit; i++) if (!comp[i]) primes[k++] = i;
    free(comp);
}

int main(int argc, char **argv)
{
    if (argc != 3) { fprintf(stderr, "usage: %s L R\n", argv[0]); return 1; }
    uint64_t L = strtoull(argv[1], NULL, 10);
    uint64_t R = strtoull(argv[2], NULL, 10);
    if (L < 2) L = 2;
    if (R <= L) { fprintf(stderr, "empty range\n"); return 1; }

    uint32_t sqrtR = (uint32_t)(sqrt((double)R) + 2);
    build_primes(sqrtR);

    const uint64_t BLOCK = 1u << 22;          /* ~4.2M numbers per block */
    uint64_t span_max = BLOCK + W + 2;
    uint16_t *tau = malloc(span_max * sizeof(uint16_t));
    uint64_t *rem = malloc(span_max * sizeof(uint64_t));
    if (!tau || !rem) { fprintf(stderr, "oom\n"); return 1; }

    uint32_t tau_max_seen = 0;
    uint64_t found = 0;

    for (uint64_t blockL = L; blockL < R; blockL += BLOCK) {
        uint64_t blockR = blockL + BLOCK; if (blockR > R) blockR = R;
        /* need tau on [lo, blockR) to test every n in [blockL, blockR) */
        uint64_t lo = (blockL > (uint64_t)W + 2) ? blockL - (W + 2) : 1;
        uint64_t span = blockR - lo;

        for (uint64_t i = 0; i < span; i++) { rem[i] = lo + i; tau[i] = 1; }

        for (uint32_t pi = 0; pi < nprimes; pi++) {
            uint64_t p = primes[pi];
            if (p * p >= blockR && p >= blockR) break;
            uint64_t start = ((lo + p - 1) / p) * p;
            if (start < p) start = p;          /* don't treat p itself oddly */
            for (uint64_t m = start; m < blockR; m += p) {
                uint64_t i = m - lo;
                uint32_t e = 0;
                while (rem[i] % p == 0) { rem[i] /= p; e++; }
                tau[i] *= (uint16_t)(e + 1);
            }
        }
        for (uint64_t i = 0; i < span; i++) {
            if (rem[i] > 1) tau[i] *= 2;
            if (tau[i] > tau_max_seen) tau_max_seen = tau[i];
        }

        /* test each n in this block */
        for (uint64_t n = blockL; n < blockR; n++) {
            int ok = 1;
            uint64_t jmax = (n - 1 < (uint64_t)W) ? n - 1 : (uint64_t)W;
            for (uint64_t j = 1; j <= jmax; j++) {
                if (tau[(n - j) - lo] > j + 2) { ok = 0; break; }
            }
            if (ok) { printf("SOLUTION n=%llu\n", (unsigned long long)n); found++; fflush(stdout); }
        }
    }

    printf("# range [%llu,%llu) done: solutions=%llu  max_tau_seen=%u  window=%d\n",
           (unsigned long long)L, (unsigned long long)R,
           (unsigned long long)found, tau_max_seen, W);
    if (tau_max_seen + 2 >= W) {
        printf("# FATAL: max tau reached the window bound; result NOT valid\n");
        return 2;
    }
    return 0;
}
