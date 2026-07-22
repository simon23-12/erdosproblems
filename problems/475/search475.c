/* Erdos problem 475 -- Graham's rearrangement conjecture, at scale.
 *
 *   Given A subset of F_p \ {0}, is there an ordering of A whose partial sums
 *   are pairwise distinct?
 *
 * Only t in [21, p-4] is open (|A| <= 20 holds in any abelian group by
 * Costa-Pellegrini; p-3 <= t <= p-1 by Hicks-Ollis-Schmitt). This program
 * exhausts that window. See graham475.py for the reference implementation --
 * this C version exists only because p=37 needs 1.4e10 subsets, which python
 * would take ~120 hours to walk.
 *
 * SOUNDNESS. Same rule as the python version: randomised greedy with restarts
 * may only ever answer YES; if it fails, a COMPLETE DFS runs, and only DFS
 * exhaustion reports "no valid ordering". Every ordering found is re-verified by
 * verify(), which recomputes the partial sums and checks the multiset.
 *
 * The restart count matters: measured greedy failure rates at p=29 were
 * 420/2000 at t=25 with 60 restarts, and 0/2000 with 500. Default is 500.
 *
 * Build: cc -O3 -o search475 search475.c
 * Run:   ./search475 <p> <t> [prefix]    prefix = comma-separated smallest
 *                                        elements, fixed, for chunking
 *        ./search475 37 21 3             all 21-subsets whose least element is 3
 *        ./search475 37 21 1,5           ...starting exactly 1,5
 *
 * A longer prefix gives finer chunks. That matters: chunking p=37 by the single
 * smallest element leaves one chunk of C(35,20) = 3.2e9 subsets, which alone
 * would set the wall-clock time.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAXT 64

static int P;
static int TRIES = 500;
static uint64_t rs = 88172645463325252ULL;

static inline uint64_t rnd64(void)
{
    rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs;
}

static long long n_checked = 0, n_bad = 0, n_fallback = 0;
static int scratch[MAXT], order[MAXT];
static char seen[512], used[MAXT];

/* randomised greedy with restarts -- may only answer YES */
static int greedy(const int *A, int t)
{
    for (int attempt = 0; attempt < TRIES; attempt++) {
        memcpy(scratch, A, (size_t)t * sizeof(int));
        for (int i = t - 1; i > 0; i--) {           /* Fisher-Yates */
            int j = (int)(rnd64() % (uint64_t)(i + 1));
            int tmp = scratch[i]; scratch[i] = scratch[j]; scratch[j] = tmp;
        }
        memset(seen, 0, (size_t)P);
        int cur = 0, placed = 0, rem = t;
        while (rem > 0) {
            int found = -1;
            for (int i = 0; i < rem; i++) {
                int s = cur + scratch[i]; if (s >= P) s -= P;
                if (!seen[s]) { found = i; break; }
            }
            if (found < 0) break;
            int v = scratch[found];
            int s = cur + v; if (s >= P) s -= P;
            seen[s] = 1; order[placed++] = v; cur = s;
            scratch[found] = scratch[--rem];        /* swap-remove; already shuffled */
        }
        if (rem == 0) return 1;
    }
    return 0;
}

/* COMPLETE search -- the only thing entitled to answer NO */
static int dfs(const int *A, int t, int depth, int cur)
{
    if (depth == t) return 1;
    for (int i = 0; i < t; i++) {
        if (used[i]) continue;
        int s = cur + A[i]; if (s >= P) s -= P;
        if (seen[s]) continue;
        used[i] = 1; seen[s] = 1; order[depth] = A[i];
        if (dfs(A, t, depth + 1, s)) return 1;
        used[i] = 0; seen[s] = 0;
    }
    return 0;
}

/* independent re-check: multiset equality + pairwise distinct partial sums */
static int verify(const int *A, int t)
{
    int cnt[512] = {0}, sums[512] = {0};
    for (int i = 0; i < t; i++) { cnt[A[i]]++; cnt[order[i]]--; }
    for (int v = 0; v < P; v++) if (cnt[v]) return 0;
    int cur = 0;
    for (int i = 0; i < t; i++) {
        cur += order[i]; if (cur >= P) cur -= P;
        if (sums[cur]) return 0;
        sums[cur] = 1;
    }
    return 1;
}

static void check(const int *A, int t)
{
    n_checked++;
    if (!greedy(A, t)) {
        n_fallback++;
        memset(seen, 0, (size_t)P);
        memset(used, 0, (size_t)t);
        if (!dfs(A, t, 0, 0)) {
            printf("NO-VALID-ORDERING p=%d t=%d A=", P, t);
            for (int i = 0; i < t; i++) printf("%d%s", A[i], i + 1 < t ? "," : "\n");
            fflush(stdout);
            n_bad++;
            return;
        }
    }
    if (!verify(A, t)) {
        printf("VERIFY-FAILED p=%d t=%d A=", P, t);
        for (int i = 0; i < t; i++) printf("%d%s", A[i], i + 1 < t ? "," : "\n");
        fflush(stdout);
        n_bad++;
    }
}

static int A[MAXT];

static void enumerate(int len, int t, int start)
{
    if (len == t) { check(A, t); return; }
    int need = t - len;
    for (int v = start; v <= P - need; v++) {
        A[len] = v;
        enumerate(len + 1, t, v + 1);
    }
}

int main(int argc, char **argv)
{
    if (argc < 3) { fprintf(stderr, "usage: %s p t [first]\n", argv[0]); return 1; }
    P = atoi(argv[1]);
    int t = atoi(argv[2]);
    /* parse the comma-separated fixed prefix */
    int plen = 0;
    char pbuf[128] = "0";
    if (argc > 3) {
        snprintf(pbuf, sizeof pbuf, "%s", argv[3]);
        for (char *tok = strtok(argv[3], ","); tok; tok = strtok(NULL, ",")) {
            if (plen >= MAXT) { fprintf(stderr, "prefix too long\n"); return 1; }
            A[plen++] = atoi(tok);
        }
        for (int i = 1; i < plen; i++)
            if (A[i] <= A[i - 1]) { fprintf(stderr, "prefix must increase\n"); return 1; }
    }
    if (P > 500 || t >= MAXT) { fprintf(stderr, "p or t too large\n"); return 1; }
    rs ^= (uint64_t)(P * 1000003 + t * 10007 + (plen ? A[0] * 101 + A[plen - 1] : 0) + 1);

    if (plen) enumerate(plen, t, A[plen - 1] + 1);
    else      enumerate(0, t, 1);

    printf("# p=%d t=%d prefix=%s checked=%lld fallbacks=%lld bad=%lld\n",
           P, t, pbuf, n_checked, n_fallback, n_bad);
    return n_bad ? 2 : 0;
}
