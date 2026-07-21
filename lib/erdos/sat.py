"""CNF construction helpers on top of python-sat.

Used by: [617] balanced edge colourings, [743] tree packing, [835] Johnson
graph colouring, [583] path partition, [547] Ramsey numbers of trees.

Design note: `CNF.var(key)` maps any hashable key to a DIMACS variable index
and remembers the mapping, so encodings read like the mathematics
(`c.var(("colour", edge, k))`) instead of like index arithmetic. `decode()`
turns a model back into the set of true keys, which is what a verifier wants.
"""
from __future__ import annotations

import itertools


class CNF:
    """A CNF formula with named variables."""

    def __init__(self):
        self._ids: dict = {}
        self._names: list = [None]      # 1-indexed, parallel to DIMACS ids
        self.clauses: list[list[int]] = []

    # -- variables ---------------------------------------------------------
    def var(self, key) -> int:
        """DIMACS index for `key`, allocating on first use."""
        v = self._ids.get(key)
        if v is None:
            v = len(self._names)
            self._ids[key] = v
            self._names.append(key)
        return v

    def fresh(self) -> int:
        """An auxiliary variable with no external meaning."""
        return self.var(("_aux", len(self._names)))

    @property
    def nvars(self) -> int:
        return len(self._names) - 1

    def name(self, v: int):
        return self._names[abs(v)]

    # -- clauses -----------------------------------------------------------
    def add(self, *lits: int):
        self.clauses.append(list(lits))

    def add_clause(self, lits):
        self.clauses.append(list(lits))

    # -- cardinality -------------------------------------------------------
    def at_least_one(self, lits):
        self.clauses.append(list(lits))

    def at_most_one(self, lits):
        """Pairwise encoding: O(k^2) clauses, no auxiliary variables.

        Fine for the small k (<= ~8) these problems use; for large k prefer a
        commander/sequential encoding.
        """
        lits = list(lits)
        for a, b in itertools.combinations(lits, 2):
            self.clauses.append([-a, -b])

    def exactly_one(self, lits):
        lits = list(lits)
        self.at_least_one(lits)
        self.at_most_one(lits)

    def at_most_k_sequential(self, lits, k: int):
        """Sinz sequential counter: O(n*k) clauses and auxiliaries."""
        lits = list(lits)
        n = len(lits)
        if k >= n:
            return
        if k == 0:
            for x in lits:
                self.clauses.append([-x])
            return
        s = [[self.fresh() for _ in range(k)] for _ in range(n)]
        self.clauses.append([-lits[0], s[0][0]])
        for j in range(1, k):
            self.clauses.append([-s[0][j]])
        for i in range(1, n):
            self.clauses.append([-lits[i], s[i][0]])
            self.clauses.append([-s[i - 1][0], s[i][0]])
            for j in range(1, k):
                self.clauses.append([-lits[i], -s[i - 1][j - 1], s[i][j]])
                self.clauses.append([-s[i - 1][j], s[i][j]])
            self.clauses.append([-lits[i], -s[i - 1][k - 1]])

    # -- solving -----------------------------------------------------------
    def solve(self, solver_name: str = "cadical153", assumptions=()):
        """Return (sat: bool, true_keys: set | None).

        Deliberately returns the decoded KEYS, not the raw model, so callers
        write verifiers against the mathematical objects.
        """
        from pysat.formula import CNF as PysatCNF
        from pysat.solvers import Solver

        f = PysatCNF(from_clauses=self.clauses)
        with Solver(name=solver_name, bootstrap_with=f) as s:
            ok = s.solve(assumptions=list(assumptions))
            if not ok:
                return False, None
            model = s.get_model()
        true_keys = {self._names[v] for v in model if v > 0 and v <= self.nvars}
        return True, true_keys

    def to_dimacs(self, path):
        """Write DIMACS so an external solver (kissat, cryptominisat) can run it."""
        with open(path, "w") as fh:
            fh.write(f"p cnf {self.nvars} {len(self.clauses)}\n")
            for cl in self.clauses:
                fh.write(" ".join(map(str, cl)) + " 0\n")
        return path

    def stats(self) -> str:
        return f"{self.nvars} vars, {len(self.clauses)} clauses"


def lex_leq(cnf: CNF, xs, ys):
    """Assert the bit-vector xs <=_lex ys. Standard symmetry-breaking primitive.

    Used to quotient out vertex-permutation symmetry, which is what makes UNSAT
    proofs on highly symmetric graph problems tractable.
    """
    xs, ys = list(xs), list(ys)
    assert len(xs) == len(ys)
    if not xs:
        return
    eq_prefix = None
    for i in range(len(xs)):
        if eq_prefix is None:
            cnf.add(-xs[i], ys[i])
        else:
            cnf.add(-eq_prefix, -xs[i], ys[i])
        if i + 1 < len(xs):
            nxt = cnf.fresh()
            # nxt -> (prefix equal up to i)
            cnf.add(-nxt, -xs[i], ys[i])
            cnf.add(-nxt, xs[i], -ys[i])
            if eq_prefix is not None:
                cnf.add(-nxt, eq_prefix)
            eq_prefix = nxt
