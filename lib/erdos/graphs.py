"""Graph generation and the small NP-hard subroutines the extremal problems need.

Used by: [23] [64] [128] [167] [548] [580] [583] [742] [993] and others.

Generation goes through nauty (`geng`, `gentreeg`) because it emits exactly one
representative per isomorphism class -- writing that yourself is the classic
source of silent over/under-counting. Graphs are handled as tuples of int
bitmask adjacency rows, which keeps the inner loops allocation-free.
"""
from __future__ import annotations

import itertools
import shutil
import subprocess

GENG = shutil.which("geng") or "/opt/homebrew/bin/geng"
GENTREEG = shutil.which("gentreeg") or "/opt/homebrew/bin/gentreeg"


# --------------------------------------------------------------------------
# graph6 decoding (nauty's output format)
# --------------------------------------------------------------------------
def graph6_to_adj(line: str) -> tuple[int, tuple[int, ...]]:
    """Decode one graph6 string to (n, adjacency bitmasks)."""
    data = line.strip()
    if not data:
        raise ValueError("empty graph6 line")
    b = [ord(c) - 63 for c in data]
    if b[0] == 63:  # 63 means n >= 63, encoded in the next bytes
        n = (b[1] << 12) | (b[2] << 6) | b[3]
        bits = b[4:]
    else:
        n = b[0]
        bits = b[1:]
    adj = [0] * n
    k = 0
    for j in range(1, n):
        for i in range(j):
            byte = bits[k // 6]
            if (byte >> (5 - (k % 6))) & 1:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
            k += 1
    return n, tuple(adj)


def gen_graphs(n: int, args: str = "", *, connected=False, triangle_free=False,
               min_deg: int | None = None, edges: str | None = None):
    """Yield (n, adj) for every graph on n vertices matching the constraints.

    `args` is passed straight to geng for anything not covered by the keywords
    (see `geng -help`). Streaming, so memory stays flat over billions of graphs.
    """
    cmd = [GENG, "-q"]
    if connected:
        cmd.append("-c")
    if triangle_free:
        cmd.append("-t")
    if min_deg is not None:
        cmd.append(f"-d{min_deg}")
    if args:
        cmd += args.split()
    cmd.append(str(n))
    if edges:
        cmd.append(edges)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=1 << 20)
    try:
        for line in proc.stdout:
            if line.strip():
                yield graph6_to_adj(line)
    finally:
        proc.stdout.close()
        proc.wait()


def gen_trees(n: int, args: str = ""):
    """Yield (n, adj) for every free tree on n vertices (one per iso class)."""
    cmd = [GENTREEG, "-q"] + (args.split() if args else []) + [str(n)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=1 << 20)
    try:
        for line in proc.stdout:
            if line.strip():
                yield graph6_to_adj(line)
    finally:
        proc.stdout.close()
        proc.wait()


# --------------------------------------------------------------------------
# basic invariants
# --------------------------------------------------------------------------
def edges_of(n, adj):
    return [(i, j) for i in range(n) for j in range(i + 1, n) if adj[i] >> j & 1]


def num_edges(n, adj):
    return sum(bin(a).count("1") for a in adj) // 2


def triangles(n, adj):
    """All vertex triples forming a triangle."""
    out = []
    for i in range(n):
        for j in range(i + 1, n):
            if not (adj[i] >> j & 1):
                continue
            common = adj[i] & adj[j]
            k = j + 1
            m = common >> k
            while m:
                if m & 1:
                    out.append((i, j, k))
                m >>= 1
                k += 1
    return out


def cycle_lengths(n, adj) -> set[int]:
    """The exact cycle spectrum: every L with a cycle of length L. Exponential;
    intended for n <= ~22. Used by [64] (cycles of length 2^k)."""
    found = set()
    for start in range(n):
        # only count cycles whose minimum vertex is `start`, to avoid n-fold repeats
        stack = [(start, 1 << start, 1)]
        while stack:
            v, seen, length = stack.pop()
            nbrs = adj[v] & ~seen
            if length >= 3 and (adj[v] >> start & 1):
                found.add(length)
            m, u = nbrs, 0
            while m:
                if m & 1 and u > start:
                    stack.append((u, seen | (1 << u), length + 1))
                m >>= 1
                u += 1
    return found


def max_cut(n, adj) -> int:
    """Exact max-cut by subset enumeration; O(2^n). For n <= ~24. Used by [23]."""
    best = 0
    for s in range(1 << (n - 1)):
        cut = 0
        for i in range(n):
            if s >> i & 1:
                cut += bin(adj[i] & ~s).count("1")
        if cut > best:
            best = cut
    return best


def chromatic_number(n, adj, ub: int | None = None) -> int:
    """Exact chromatic number by SAT with a symmetry-breaking precolouring."""
    from .sat import CNF

    if n == 0:
        return 0
    ub = ub or n
    for k in range(1, ub + 1):
        c = CNF()
        col = lambda v, i: c.var(("col", v, i))
        for v in range(n):
            c.exactly_one([col(v, i) for i in range(k)])
        for v in range(n):
            for w in range(v + 1, n):
                if adj[v] >> w & 1:
                    for i in range(k):
                        c.add(-col(v, i), -col(w, i))
        # break colour-permutation symmetry: vertex v may only use colour i<=v
        for v in range(n):
            for i in range(v + 1, k):
                c.add(-col(v, i))
        ok, _ = c.solve()
        if ok:
            return k
    return n


def is_triangle_free(n, adj) -> bool:
    for i in range(n):
        for j in range(i + 1, n):
            if (adj[i] >> j & 1) and (adj[i] & adj[j]):
                return False
    return True


def to_networkx(n, adj):
    import networkx as nx

    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(edges_of(n, adj))
    return g
