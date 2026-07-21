"""Linear-time dynamic programming over trees.

Used by: [993] independence polynomial unimodality, and reusable for any
tree-indexed counting problem ([547], [580], [743] all touch trees).
"""
from __future__ import annotations


def independence_polynomial(n: int, adj) -> list[int]:
    """Coefficients [i_0, i_1, ...] where i_k = #independent sets of size k.

    Rooted DP: for each vertex v, `out[v]` counts independent sets of v's
    subtree that exclude v and `inn[v]` those that include it. Merging a child c
    into v multiplies out[v] by (out[c] + inn[c]) and inn[v] by out[c] -- i.e.
    polynomial multiplication on the coefficient lists.

    Iterative (explicit post-order) rather than recursive so it survives the
    deep path-like trees that dominate large n.
    """
    if n == 0:
        return [1]
    parent = [-1] * n
    order = []
    seen = [False] * n
    stack = [0]
    seen[0] = True
    while stack:
        v = stack.pop()
        order.append(v)
        m, u = adj[v], 0
        while m:
            if m & 1 and not seen[u]:
                seen[u] = True
                parent[u] = v
                stack.append(u)
            m >>= 1
            u += 1

    out = [[1] for _ in range(n)]   # sets excluding the vertex
    inn = [[0, 1] for _ in range(n)]  # sets including it
    for v in reversed(order):        # children are processed before parents
        p = parent[v]
        if p < 0:
            continue
        both = _add(out[v], inn[v])
        out[p] = _mul(out[p], both)
        inn[p] = _mul(inn[p], out[v])
    return _add(out[order[0]], inn[order[0]])


def _mul(a: list[int], b: list[int]) -> list[int]:
    r = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                if bj:
                    r[i + j] += ai * bj
    while len(r) > 1 and r[-1] == 0:
        r.pop()
    return r


def _add(a: list[int], b: list[int]) -> list[int]:
    if len(a) < len(b):
        a, b = b, a
    r = list(a)
    for i, bi in enumerate(b):
        r[i] += bi
    return r


def is_unimodal(seq: list[int]) -> bool:
    """True iff seq rises (weakly) then falls (weakly)."""
    i, n = 0, len(seq)
    while i + 1 < n and seq[i] <= seq[i + 1]:
        i += 1
    while i + 1 < n and seq[i] >= seq[i + 1]:
        i += 1
    return i == n - 1


def is_log_concave(seq: list[int]) -> bool:
    """True iff a_k^2 >= a_{k-1} a_{k+1} throughout. Implies unimodality for
    sequences with no internal zeros."""
    return all(seq[k] * seq[k] >= seq[k - 1] * seq[k + 1]
               for k in range(1, len(seq) - 1))


def unimodality_defect(seq: list[int]):
    """None if unimodal, else the first index where the sequence turns back up
    after having turned down -- the witness a human would want to see."""
    i, n = 0, len(seq)
    while i + 1 < n and seq[i] <= seq[i + 1]:
        i += 1
    peak = i
    while i + 1 < n and seq[i] >= seq[i + 1]:
        i += 1
    if i == n - 1:
        return None
    return {"peak_index": peak, "rises_again_at": i + 1,
            "values": seq[max(0, i - 1): i + 3]}
