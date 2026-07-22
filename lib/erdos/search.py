"""Search harnesses that stay sound when the fast path fails.

Extracted from [475] (Graham's rearrangement), where a naive DFS cost 175 ms per
instance and randomised greedy cost 0.04 ms -- a 4000x speedup that would have
been worthless if used carelessly, because *a heuristic failing to find a
solution is not evidence that none exists*.

The rule this module enforces:

    a heuristic may only ever answer YES.
    only an exhaustive search may answer NO.

`greedy_then_complete` bakes that in: the randomised phase can return a
solution, but if it comes up empty the call falls through to a complete DFS, and
only DFS exhaustion produces `None`. The returned flag says which path answered,
so callers can report how often the expensive branch was actually needed.

Reused by: [475]; applicable to [743] tree packing, [835] Johnson colouring,
and any "order these items subject to a running constraint" problem.
"""
from __future__ import annotations

import random
from typing import Callable, Iterable, Sequence, TypeVar

Item = TypeVar("Item")
State = TypeVar("State")


def greedy_then_complete(
    items: Sequence[Item],
    initial: State,
    step: Callable[[State, Item], State | None],
    *,
    tries: int = 60,
    rnd: random.Random | None = None,
) -> tuple[list[Item] | None, bool]:
    """Order every element of `items` so each step is legal.

    `step(state, item)` returns the successor state, or None if placing `item`
    now is illegal. A solution is an ordering consuming every item.

    Returns `(ordering, used_exhaustive)`. `ordering is None` can only happen
    after the complete search has exhausted the space, so it is a genuine
    "no such ordering exists" -- never a heuristic giving up.
    """
    rnd = rnd or random.Random(0)
    n = len(items)

    # -- fast path: randomised greedy with restarts (may only answer YES)
    for _ in range(tries):
        rem = list(items)
        rnd.shuffle(rem)
        state, order = initial, []
        while rem:
            for i, it in enumerate(rem):
                nxt = step(state, it)
                if nxt is not None:
                    state = nxt
                    order.append(it)
                    rem.pop(i)
                    break
            else:
                break
        if not rem:
            return order, False

    # -- slow path: complete DFS (the only branch allowed to answer NO)
    order: list[Item] = []
    used = [False] * n

    def go(state: State) -> bool:
        if len(order) == n:
            return True
        for i, it in enumerate(items):
            if used[i]:
                continue
            nxt = step(state, it)
            if nxt is None:
                continue
            used[i] = True
            order.append(it)
            if go(nxt):
                return True
            order.pop()
            used[i] = False
        return False

    return (order, True) if go(initial) else (None, True)


def distinct_partial_sums_step(p: int):
    """`step` for 'order A so the partial sums are pairwise distinct' in F_p.

    State is (current sum, frozenset of sums used so far). This is the concrete
    instance [475] needs; it lives here so the harness has a worked example and
    so any other modular-partial-sum problem can reuse it verbatim.
    """
    def step(state, v):
        cur, seen = state
        s = (cur + v) % p
        if s in seen:
            return None
        return (s, seen | {s})
    return step


def verify_distinct_partial_sums(order: Iterable[int], A: Sequence[int], p: int) -> bool:
    """Independent re-check: recompute the partial sums and test distinctness.

    Deliberately shares no code with the search -- this is what a result is
    allowed to rest on.
    """
    order = list(order)
    if sorted(order) != sorted(A):
        return False
    sums, cur = [], 0
    for v in order:
        cur = (cur + v) % p
        sums.append(cur)
    return len(set(sums)) == len(sums)
