#!/usr/bin/env python3
"""Erdos problem 617 (https://www.erdosproblems.com/617).

    Let r >= 3. If the edges of K_{r^2+1} are r-coloured then there exist r+1
    vertices with at least one colour missing on the induced K_{r+1}.

A counterexample is a "balanced" colouring: an r-colouring of K_{r^2+1} in which
EVERY (r+1)-subset sees all r colours. Erdos and Gyarfas proved no such colouring
exists for r=3 and r=4, and observed r=2 is false. r=5 (K_26, 5 colours) is the
first open case.

Encoding
--------
x[e,c]  edge e of K_n has colour c,  n = r^2+1.
  (1)   exactly one colour per edge;
  (2)   for every (r+1)-subset S and every colour c:  some edge inside S is c.

Note (2) says exactly "K_n minus colour class c is K_{r+1}-free", for each c.
Turan then forces |colour class c| >= C(n,2) - ex(n, K_{r+1}); that bound is
added as a redundant cardinality constraint because it prunes hard and costs
little. For r=5 it says every colour class has >= 55 of the 325 edges.

SAT  => a counterexample; check_colouring() re-verifies it from scratch.
UNSAT => the conjecture holds for that r.

Usage:
    python encode617.py 3            # known: UNSAT
    python encode617.py 4            # known: UNSAT
    python encode617.py 5            # OPEN
    python encode617.py 5 --dimacs out.cnf   # export for an external solver
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "lib"))
from erdos.sat import CNF  # noqa: E402


def turan_edges(n: int, s: int) -> int:
    """ex(n, K_{s+1}) = edges of the Turan graph T(n,s) (complete s-partite,
    parts as equal as possible)."""
    q, rem = divmod(n, s)
    sizes = [q + 1] * rem + [q] * (s - rem)
    return n * (n - 1) // 2 - sum(a * (a - 1) // 2 for a in sizes)


def build(r: int, *, turan: bool = True, sym: bool = True):
    n = r * r + 1
    verts = range(n)
    edges = list(itertools.combinations(verts, 2))
    c = CNF()
    X = lambda e, k: c.var(("x", e, k))

    # (1) exactly one colour per edge
    for e in edges:
        c.exactly_one([X(e, k) for k in range(r)])

    # (2) every (r+1)-subset sees every colour
    for S in itertools.combinations(verts, r + 1):
        inner = list(itertools.combinations(S, 2))
        for k in range(r):
            c.add_clause([X(e, k) for e in inner])

    # (redundant) Turan lower bound on each colour class size
    if turan:
        lo = len(edges) - turan_edges(n, r)
        for k in range(r):
            # at least `lo` edges have colour k  <=>  at most |E|-lo have colour != k
            c.at_most_k_sequential([-X(e, k) for e in edges], len(edges) - lo)

    # (3) SYMMETRY BREAKING.
    # The symmetry group is S_n on vertices times S_r on colours -- for r=5 that
    # is 26!*120, and CDCL cannot re-derive the same contradiction that many
    # times. Relabelling vertices 1..n-1 lets us sort the star at vertex 0, so
    # require colour(0,1) <= colour(0,2) <= ... <= colour(0,n-1). Sorting makes
    # the colour classes of that star contiguous blocks listed in increasing
    # label order, which simultaneously consumes the colour symmetry (whenever
    # every colour occurs at vertex 0, which a balanced colouring forces since
    # otherwise {0} u S would miss it). What survives is only the permutations
    # inside each block.
    if sym:
        for i in range(1, n - 1):
            for a in range(r):
                for b in range(a):          # forbid colour(0,i)=a > colour(0,i+1)=b
                    c.add(-X((0, i), a), -X((0, i + 1), b))

    return n, edges, c, X


def check_colouring(r: int, colour: dict) -> tuple[bool, str]:
    """Independent re-verification of a claimed balanced colouring.

    Recomputed from the colour map alone -- shares nothing with the encoder.
    """
    n = r * r + 1
    edges = list(itertools.combinations(range(n), 2))
    for e in edges:
        if e not in colour:
            return False, f"edge {e} uncoloured"
        if not 0 <= colour[e] < r:
            return False, f"edge {e} has colour {colour[e]} outside 0..{r-1}"
    for S in itertools.combinations(range(n), r + 1):
        seen = {colour[e] for e in itertools.combinations(S, 2)}
        if len(seen) != r:
            return False, f"subset {S} misses colour(s) {sorted(set(range(r)) - seen)}"
    return True, f"OK: all C({n},{r+1}) subsets of K_{n} see all {r} colours"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r", type=int)
    ap.add_argument("--dimacs", help="write DIMACS here instead of solving")
    ap.add_argument("--no-turan", action="store_true")
    ap.add_argument("--no-sym", action="store_true")
    ap.add_argument("--solver", default="cadical153")
    a = ap.parse_args()

    t0 = time.time()
    n, edges, c, X = build(a.r, turan=not a.no_turan, sym=not a.no_sym)
    print(f"r={a.r}  K_{n}  {len(edges)} edges  |  {c.stats()}  "
          f"(built in {time.time()-t0:.1f}s)")

    if a.dimacs:
        c.to_dimacs(a.dimacs)
        print(f"wrote {a.dimacs}")
        return

    t0 = time.time()
    sat, keys = c.solve(a.solver)
    dt = time.time() - t0
    print(f"solver: {'SAT' if sat else 'UNSAT'}  ({dt:.1f}s)")

    if not sat:
        print(f"=> no balanced colouring of K_{n} with {a.r} colours exists; "
              f"the conjecture HOLDS for r={a.r}.")
        return

    colour = {e: k for (tag, e, k) in (t for t in keys if isinstance(t, tuple)
                                       and t and t[0] == "x")}
    ok, msg = check_colouring(a.r, colour)
    print(f"re-verification: {msg}")
    if ok:
        out = pathlib.Path(__file__).parent / f"counterexample_r{a.r}.json"
        out.write_text(json.dumps({"r": a.r, "n": n,
                                   "colouring": {f"{u},{v}": k for (u, v), k in colour.items()}},
                                  indent=1))
        print(f"COUNTEREXAMPLE written to {out}")


if __name__ == "__main__":
    main()
