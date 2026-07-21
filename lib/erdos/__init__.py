"""Reusable components for machine-checkable work on Erdős problems.

The rule this package exists to serve: *a claim only counts if a machine
checked it*. So every module here is split into two halves --

  search   : may be clever, heuristic, fast, and is allowed to be wrong;
  verify   : must be short, dumb, and independently convincing.

Never let a search routine be its own verifier.

Modules
-------
sat      CNF construction on top of python-sat: cardinality encodings,
         exactly-one, and symmetry breaking helpers.
graphs   graph generation (nauty geng/gentreeg), invariants, and the small
         NP-hard subroutines (max-cut, chromatic number, triangle packing)
         that keep recurring in the extremal problems.
numth    segmented sieves, divisor counts, k-full numbers, p-adic valuation.
treedp   linear-time dynamic programming over trees (independence polynomial).
verify   the harness that runs a standalone checker and reports pass/fail.
"""

__all__ = ["sat", "graphs", "numth", "treedp", "verify"]
