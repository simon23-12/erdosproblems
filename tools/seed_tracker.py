#!/usr/bin/env python3
"""Seed RESEARCH_TRACKER.json with the feasibility triage.

Kept as code (not hand-written JSON) so the reasoning behind each priority is
version-controlled next to the number it produces. Re-running MERGES: fields the
work loop owns (status, bounds, compute time, results) are preserved; only the
triage fields are refreshed.

    python tools/seed_tracker.py
"""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRACKER = ROOT / "RESEARCH_TRACKER.json"

# problem_id: (title, tags, priority, runtime, p_verifiable, novelty, scales, rationale)
#
# priority is expected machine-verifiable value per unit compute, in [0,1].
# p_machine_verifiable = my honest odds this yields ANY machine-checked artifact
#   (including "exhaustively verified up to X", not only a counterexample).
# novelty = how likely the artifact is to be new rather than a redo.
T = {
 "647": ("Is there n>24 with max_{m<n}(m+tau(m)) <= n+2?  (GBP 25 prize)",
   ["NUMBER SEARCH", "BRUTE-FORCE"], 0.80, "hours", 0.95, "high", True,
   "Condition is LOCAL: tau(n-j)<=j+2 for j<=max tau, so the range splits across cores. "
   "Segmented divisor sieve at ~1.75s per 1e8 even at 1e13. No published search bound found."),

 "617": ("r=5: can K_26 be 5-coloured so every K_6 sees all 5 colours?",
   ["SAT"], 0.75, "hours", 0.60, "high", False,
   "1625 vars / ~1.2M clauses. Erdos-Gyarfas did r=3,4 by hand; r=5 is the first open case and "
   "looks computationally untouched. SAT => counterexample (trivially checkable). UNSAT is hard "
   "(26! vertex symmetry) but symmetry breaking may reach it. Does not scale past r=5."),

 "287": ("Unit fractions summing to 1 must have a consecutive gap >= 3?",
   ["NUMBER SEARCH", "BRUTE-FORCE", "DYNAMIC PROGRAMMING"], 0.70, "hours", 0.80, "high", True,
   "A counterexample is a set with all gaps <=2 and reciprocals summing to 1. The largest-prime-power "
   "valuation argument forces exclusions (p in (b/2,b] cannot appear), which prunes brutally. "
   "No published computational bound located."),

 "743": ("Tree packing: is K_10 the edge-disjoint union of trees T_2..T_10?",
   ["BRUTE-FORCE", "SAT", "GRAPH ENUMERATION"], 0.65, "hours-days", 0.70, "high", False,
   "Fishburn settled n<=9 in 1983; n=10 is 428,076 tree-collections x one exact-cover each. "
   "Sum of tree sizes is exactly 45 = |E(K_10)|, so it is a perfect packing. n=11 is ~50x worse."),

 "64": ("Does every graph with min degree >= 3 contain a cycle of length 2^k?  ($1000)",
   ["GRAPH ENUMERATION", "SAT"], 0.60, "hours", 0.60, "high", False,
   "A counterexample must avoid C_4, C_8, C_16, ... Avoiding C_4 forces girth >= 5, and cubic "
   "girth-5 graphs are generable up to ~26 vertices. Cycle spectrum is cheap. Liu-Montgomery "
   "proved it above an absolute degree constant, so only small degree can fail."),

 "366": ("Is there a 2-full n with n+1 3-full?",
   ["NUMBER SEARCH", "BRUTE-FORCE"], 0.60, "hours", 0.85, "medium", True,
   "Enumerate 3-full m <= X (only ~c*X^(1/3) of them, so 1e26 is ~1e9 candidates) and test whether "
   "m-1 is powerful. Small-prime trial division rejects essentially all candidates instantly. "
   "Current published bound is 1e22, so 1e25-1e26 is a genuine extension."),

 "835": ("Is chi(J(20,10)) = 11?  (Erdos-Rosenfeld k>2 question)",
   ["SAT", "BRUTE-FORCE", "GRAPH ENUMERATION"], 0.60, "hours", 0.45, "high", False,
   "Equivalent to an 11-colouring of the Johnson graph J(20,10): 184,756 vertices, 100-regular. "
   "k=10 is the smallest open case (false for k<=8; Ma-Tang killed all k+1 composite). "
   "A FOUND colouring answers the problem YES and is verifiable in seconds -- excellent asymmetry. "
   "Failure to find proves nothing."),

 "699": ("For all 1<=i<j<=n/2, is there a prime p>=i dividing gcd(C(n,i),C(n,j))?",
   ["NUMBER SEARCH", "DYNAMIC PROGRAMMING"], 0.60, "hours", 0.75, "medium", True,
   "Kummer's theorem gives v_p(C(n,i)) from base-p carries, so no binomial is ever formed. "
   "O(n^2) pairs per n. A counterexample is a single (n,i,j) triple -- instantly re-checkable."),

 "167": ("Tuza: if G has <=k edge-disjoint triangles, can <=2k edges kill all triangles?",
   ["ILP", "GRAPH ENUMERATION", "BRUTE-FORCE"], 0.55, "hours", 0.80, "low", False,
   "nu (max edge-disjoint triangle packing) and tau (min triangle edge cover) are both small ILPs. "
   "Exhaustive over geng graphs to ~11 vertices. Famous conjecture, but small cases are very "
   "likely already checked by others -- novelty is the weak point, not feasibility."),

 "488": ("Is |B cap [1,m]|/m < 2|B cap [1,n]|/n for multiples of a finite set A?",
   ["NUMBER SEARCH", "BRUTE-FORCE", "ILP"], 0.55, "minutes-hours", 0.80, "medium", True,
   "Fully concrete and cheap: choose A, compute two densities exactly. Search over A subset of a "
   "small window. Counterexamples to the mis-typed variant already exist, so the search machinery "
   "is known to be exercising the right object."),

 "1020": ("Erdos matching conjecture: f(n;r,k) = max(C(rk-1,r), C(n,r)-C(n-k+1,r))",
   ["ILP", "BRUTE-FORCE"], 0.55, "hours", 0.70, "medium", False,
   "For fixed small (r,k,n) this is one ILP over C(n,r) binary variables with a matching "
   "constraint. r=4,5 in the mid range n ~ (r+1)k is where it is open and instances stay under "
   "a few thousand variables."),

 "458": ("Is [1..p_{k+1}-1] < p_k [1..p_k] for all k?",
   ["NUMBER SEARCH", "BRUTE-FORCE"], 0.50, "minutes", 0.90, "low", True,
   "The lcm ratio is exactly the product of primes q having a power q^e (e>=2) inside the gap "
   "(p_k, p_{k+1}). So the check is a cheap prime-power scan over prime gaps. Very likely already "
   "done informally, but it is nearly free."),

 "475": ("Graham: does every A in F_p\\{0} have an ordering with distinct partial sums?",
   ["BRUTE-FORCE", "DYNAMIC PROGRAMMING", "SAT"], 0.50, "hours", 0.75, "medium", False,
   "Proved for t<=12 and t>=p-3, so the open window is middle-sized A at p >= 17. Subsets modulo "
   "the scaling action of F_p^*: ~2^(p-1)/(p-1) orbits, feasible to p ~ 31, hopeless by p ~ 41."),

 "548": ("Erdos-Sos: (k-1)n/2+1 edges forces every tree on k+1 vertices  ($100)",
   ["GRAPH ENUMERATION", "BRUTE-FORCE"], 0.50, "hours", 0.60, "low", False,
   "Exhaustive over geng graphs with the exact edge count, testing subtree containment. "
   "Feasible to n ~ 11. Small cases near-certainly already verified."),

 "583": ("Erdos-Gallai: partition any connected graph into <= ceil(n/2) edge-disjoint paths",
   ["SAT", "ILP", "GRAPH ENUMERATION"], 0.50, "hours", 0.65, "low", False,
   "Minimum path partition is NP-hard but tiny at n<=10; SAT per graph over geng output. "
   "Already proved for planar, max degree <=5, and 2-degenerate, which covers most small graphs."),

 "848": ("Is the max A in [1,N] with ab+1 never squarefree given by n = 7 mod 25?",
   ["NUMBER SEARCH", "ILP", "BRUTE-FORCE"], 0.50, "hours", 0.70, "medium", True,
   "Max-clique on the graph over [1,N] with a~b iff ab+1 is not squarefree. Sawhney settled large N; "
   "small N is the open part and is exactly where exact max-clique is affordable."),

 "375": ("Grimm: distinct prime representatives for a run of composites",
   ["NUMBER SEARCH", "BRUTE-FORCE"], 0.45, "days", 0.60, "medium", True,
   "Only MAXIMAL composite runs need checking (an SDR restricts to subsets), so it is one bipartite "
   "matching per prime gap. But the published bound is already 1.9e10 and beating it means sieving "
   "past 1e12 -- expensive relative to payoff."),

 "23": ("Can every triangle-free graph on 5n vertices be made bipartite by deleting n^2 edges?",
   ["GRAPH ENUMERATION", "BRUTE-FORCE", "ILP"], 0.45, "hours", 0.70, "low", False,
   "Max-cut by subset enumeration is exact and cheap below ~24 vertices; geng -t streams the "
   "triangle-free graphs. n=2 (10 vertices) and n=3 (15) are reachable, n=4 (20) is not."),

 "742": ("Do diameter-2-critical graphs have at most n^2/4 edges?",
   ["GRAPH ENUMERATION", "BRUTE-FORCE"], 0.45, "hours", 0.75, "low", False,
   "Both the diameter-2 test and the edge-criticality test are O(n^3) bit operations. geng to 11 "
   "vertices is affordable, 12 is not. Furedi proved it for large n."),

 "128": ("Erdos-Rousseau: every half-subgraph having > n^2/50 edges forces a triangle  ($250)",
   ["GRAPH ENUMERATION", "ILP"], 0.40, "hours", 0.60, "low", False,
   "Needs a triangle-free graph on n vertices whose every floor(n/2)-subset spans > n^2/50 edges. "
   "Enumeration is fine to n ~ 14; the extremal examples are C_5 blow-ups which only bite at "
   "n divisible by 5, and the interesting n are larger than the reachable range."),

 "580": ("Loebl-Komlos-Sos: n/2 vertices of degree >= n/2 forces every tree on n/2 vertices",
   ["GRAPH ENUMERATION", "BRUTE-FORCE"], 0.40, "hours", 0.60, "low", False,
   "Exhaustive over geng graphs plus subtree containment. Reachable to n ~ 12, i.e. trees on <= 6 "
   "vertices. Zhao proved it for all large n, so only a small window is genuinely open."),

 "993": ("Is the independent-set sequence of every tree unimodal?",
   ["BRUTE-FORCE", "GRAPH ENUMERATION", "DYNAMIC PROGRAMMING"], 0.30, "days", 0.50, "low", False,
   "Already verified to 29 vertices (literature, 2026). n=30 is 1.48e10 free trees x O(n^2) DP "
   "~= 1.3e13 operations: reachable only with a heavily optimised C implementation over many hours, "
   "for a one-vertex improvement. Kept as a fallback for spare compute."),

 "547": ("R(T) <= 2n-2 for every tree T on n vertices",
   ["SAT", "GRAPH ENUMERATION"], 0.30, "hours-days", 0.50, "low", False,
   "Each Ramsey number is a 2-colouring SAT instance on K_m; feasible only for trees up to ~8 "
   "vertices before the instances explode. Zhao proved it for all large n."),

 "628": ("Erdos-Lovasz Tihany: is every k-chromatic K_k-free graph (a,b)-splittable?",
   ["GRAPH ENUMERATION", "SAT"], 0.25, "days", 0.35, "medium", False,
   "The first open case needs chi = 6 with no K_6; the smallest such graphs are already beyond "
   "exhaustive enumeration, so this becomes an unguided search over a huge space."),

 "551": ("R(C_k,K_n) = (k-1)(n-1)+1 for k >= n >= 3",
   ["SAT", "GRAPH ENUMERATION"], 0.25, "days", 0.35, "low", False,
   "Exact two-colour Ramsey numbers; the smallest unresolved instances are already at the edge of "
   "what dedicated Ramsey codes achieve after years of CPU time."),

 "1082": ("Do n points with no 3 collinear determine >= floor(n/2) distinct distances?",
   ["SMT/Z3", "BRUTE-FORCE"], 0.25, "days", 0.30, "medium", False,
   "Needs exact real coordinates; rational/integer point searches only cover a measure-zero slice "
   "of configurations, so a null result says almost nothing. The second half is already answered no."),

 "506": ("Minimum number of circles determined by n points, not all concyclic",
   ["SMT/Z3", "BRUTE-FORCE"], 0.20, "days", 0.30, "medium", False,
   "Open only for small n but requires exact incidence geometry over the reals; the degenerate "
   "configurations that matter are exactly the ones floating-point search cannot certify."),

 "97": ("Does every convex polygon have a vertex with no 4 others equidistant?  ($100)",
   ["SMT/Z3", "SYMBOLIC"], 0.20, "days", 0.25, "high", False,
   "A counterexample is a set of real coordinates satisfying many equidistance equations plus "
   "convexity. Z3 over the reals on this many degree-2 constraints is unlikely to close, and a "
   "numerical near-solution certifies nothing."),

 "982": ("Convex n-gon: some vertex has >= floor(n/2) distinct distances to the others",
   ["SMT/Z3", "BRUTE-FORCE"], 0.20, "hours-days", 0.30, "medium", False,
   "Same exact-arithmetic obstruction as [1082]/[97]. Best known bound (13/36+eps)n is far from "
   "1/2, so a small-n search would have to be lucky as well as exact."),

 "7":  ("Is there a distinct covering system with all moduli odd?  ($25/$2000)",
   ["SAT", "NUMBER SEARCH"], 0.15, "days", 0.15, "very high", False,
   "The search space over odd modulus sets is astronomical and has absorbed decades of dedicated "
   "effort; known constraints (lcm divisible by 9 or 15) barely dent it. Very high payoff, but the "
   "probability of a SAT instance closing is small enough that the expected value stays low."),

 "779": ("Deaconescu: prime p in (p_n, P) with P+p prime, P the n-th primorial",
   ["NUMBER SEARCH"], 0.15, "hours", 0.20, "medium", True,
   "Extending past n=1000 means primality of numbers with thousands of digits. Only BPSW/PRP is "
   "affordable, and a PRP is not a proof -- so the artifact would fail the trust rule. Rejected on "
   "verifiability, not on cost."),

 "556": ("R_3(C_n) <= 4n-3",
   ["SAT"], 0.15, "days", 0.20, "low", False,
   "Three-colour Ramsey numbers for cycles; instance sizes explode immediately and the conjecture "
   "is already settled for all large n in both parities."),

 "672": ("Can a product of an AP of length >= 4 be a perfect power?",
   ["NUMBER SEARCH"], 0.10, "days", 0.15, "low", False,
   "Ruled out for 4<=k<=34 by deep Diophantine methods. Compute cannot reach k>=35, and no finite "
   "search settles the general statement."),

 "307": ("Two finite prime sets P,Q with (sum 1/p)(sum 1/q) = 1",
   ["NUMBER SEARCH", "SMT/Z3"], 0.08, "days", 0.10, "high", False,
   "|P union Q| >= 60 is forced, so any search is over 60+ primes with an exact rational product "
   "constraint. The space is astronomically larger than meet-in-the-middle can bridge."),

 "19": ("Erdos-Faber-Lovasz: chi(G)=n for an edge-disjoint union of n copies of K_n  ($500)",
   ["NOT COMPUTE-AMENABLE"], 0.05, "-", 0.05, "-", False,
   "Settled for n<10 and for all sufficiently large n, but the Kang-Kelly-Kuhn-Methuku-Osthus "
   "threshold is astronomically large. The 'finite check' is finite only in principle."),

 "242": ("Erdos-Straus: 4/n = 1/x+1/y+1/z for all n>2",
   ["NOT COMPUTE-AMENABLE"], 0.05, "-", 0.10, "none", True,
   "Already verified to 1e18. Matching that needs a dedicated distributed effort and beating it "
   "needs more; no realistic novelty here."),

 "364": ("Are there three consecutive powerful numbers?",
   ["NOT COMPUTE-AMENABLE"], 0.05, "-", 0.10, "none", True,
   "Checked past 7.38e28 via OEIS A076445. Enumerating powerful numbers that far requires ~1e14 "
   "objects; no path to improvement on this hardware."),

 "723": ("Must a finite projective plane have prime power order?",
   ["NOT COMPUTE-AMENABLE"], 0.05, "-", 0.05, "very high", False,
   "The open case is order 12. Order 10 alone consumed thousands of CPU-hours in 1989 and order 12 "
   "is vastly harder; this is a known multi-CPU-year problem."),

 "107": ("Happy ending: f(n) = 2^(n-2)+1  ($500)",
   ["NOT COMPUTE-AMENABLE"], 0.05, "-", 0.05, "very high", False,
   "f(6)=17 already required a major dedicated computation. f(7) means deciding configurations of "
   "33 points -- far beyond exhaustive reach."),

 "106": ("Squares packed in the unit square: is f(k^2+1) = k?",
   ["NOT COMPUTE-AMENABLE"], 0.05, "-", 0.10, "high", False,
   "A continuous packing optimum. Numerical optimisation gives no certificate, and the "
   "axis-parallel case (which IS combinatorial) is already fully solved by Baek-Koizumi-Ueoro."),

 "114": ("Is the lemniscate length maximised by z^n - 1?  ($250)",
   ["NOT COMPUTE-AMENABLE"], 0.03, "-", 0.05, "none", False,
   "Analytic extremal problem over all monic polynomials, and Tao has already proved it for all "
   "sufficiently large n. Nothing finite to check."),

 "1041": ("A path of length < 2 in {|f|<1} joining two roots",
   ["NOT COMPUTE-AMENABLE"], 0.03, "-", 0.05, "medium", False,
   "Continuous: needs a certified bound on a path length in a sublevel set of |f|. Floating-point "
   "sampling cannot certify either direction."),
}

STATE = {  # erdosproblems.com status per problem
 "7": "verifiable", "19": "decidable", "23": "falsifiable", "64": "falsifiable",
 "97": "falsifiable", "106": "falsifiable", "107": "falsifiable", "114": "falsifiable",
 "128": "falsifiable", "167": "falsifiable", "242": "falsifiable", "287": "falsifiable",
 "307": "verifiable", "364": "verifiable", "366": "verifiable", "375": "falsifiable",
 "398": "falsifiable", "458": "falsifiable", "475": "decidable", "488": "falsifiable",
 "506": "decidable", "547": "decidable", "548": "falsifiable", "551": "decidable",
 "556": "decidable", "580": "decidable", "583": "falsifiable", "617": "falsifiable",
 "628": "falsifiable", "647": "verifiable", "672": "verifiable", "699": "falsifiable",
 "723": "falsifiable", "742": "decidable", "743": "falsifiable", "779": "falsifiable",
 "835": "verifiable", "848": "decidable", "982": "falsifiable", "993": "falsifiable",
 "1020": "falsifiable", "1041": "falsifiable", "1082": "falsifiable",
}

# [398] gets its priority set only after checking the current record, see LOG.md
T["398"] = ("Brocard-Ramanujan: are n=4,5,7 the only solutions of n! = x^2 - 1?",
   ["NUMBER SEARCH"], 0.60, "hours", 0.85, "unknown", True,
   "Jacobi-symbol sieve: maintain n! mod p for primes p > N and reject n when n!+1 is a quadratic "
   "non-residue. ~2 symbols per n expected, so 1e10 is roughly an hour in C. The erdosproblems page "
   "cites 1e9; the true current record must be confirmed before spending compute.")


def blank(pid: str) -> dict:
    title, tags, pri, runtime, pv, nov, scales, why = T[pid]
    return {
        "problem_id": pid,
        "title": title,
        "url": f"https://www.erdosproblems.com/{pid}",
        "erdos_status": STATE[pid],
        "status": "untouched",
        "tags": tags,
        "priority": pri,
        "estimates": {"runtime": runtime, "p_machine_verifiable": pv,
                      "novelty": nov, "scales": scales},
        "triage_rationale": why,
        "approaches_attempted": [],
        "search_bounds_reached": "",
        "compute_time_spent_sec": 0,
        "best_verified_result": "",
        "best_unverified_lead": "",
        "reason_for_stopping": "",
        "artifacts": [],
        "last_commit": "",
        "last_modified": "",
    }


OWNED_BY_WORK_LOOP = ("status", "approaches_attempted", "search_bounds_reached",
                      "compute_time_spent_sec", "best_verified_result",
                      "best_unverified_lead", "reason_for_stopping", "artifacts",
                      "last_commit", "last_modified")


def main():
    old = {}
    if TRACKER.exists():
        for p in json.loads(TRACKER.read_text())["problems"]:
            old[p["problem_id"]] = p

    problems = []
    for pid in T:
        entry = blank(pid)
        if pid in old:
            for k in OWNED_BY_WORK_LOOP:
                if k in old[pid]:
                    entry[k] = old[pid][k]
        problems.append(entry)
    problems.sort(key=lambda p: -p["priority"])

    data = {
        "meta": {
            "description": "Persistent research tracker for machine-checkable work on "
                           "open Erdos problems (erdosproblems.com).",
            "source": "https://github.com/teorth/erdosproblems + https://www.erdosproblems.com",
            "trust_rule": "A claim counts only if Lean compiles it with no sorry, or a short "
                          "standalone script recomputes it from scratch. Everything else is a lead.",
            "tag_vocabulary": ["BRUTE-FORCE", "SAT", "SMT/Z3", "ILP", "GRAPH ENUMERATION",
                               "NUMBER SEARCH", "DYNAMIC PROGRAMMING", "FORMALIZATION",
                               "SYMBOLIC", "NOT COMPUTE-AMENABLE"],
            "status_vocabulary": ["untouched", "active", "paused", "verified",
                                  "lead", "dead-end"],
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "last_modified": "",
            "last_commit": "",
        },
        "problems": problems,
    }
    TRACKER.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"seeded {len(problems)} problems -> {TRACKER}")


if __name__ == "__main__":
    main()
