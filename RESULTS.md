# RESULTS — Erdős problems ledger

**Status of this file:** live ledger. Every claim carries an explicit status tag.
Nothing is called a "result" unless a machine checked it.

Status tags used:
- `[LEAN-VERIFIED]` — Lean/mathlib compiles it, no `sorry`, no extra axioms.
- `[COMPUTATION-VERIFIED]` — a short standalone script recomputes the claim from
  scratch; a skeptic can run it in seconds/minutes without trusting me.
- `[UNVERIFIED-LEAD]` — a prose/heuristic argument only. **NOT trustworthy.**
- `[DEAD-END]` — attempted, no machine-checkable progress.

---

## 1. VERIFIED — machine-checked, safe to show a mathematician

*(empty)*

**Nothing has been machine-verified yet.** Setup just completed.

---

## 2. LEADS — unverified, needs an expert. NOT trustworthy yet.

*(empty)*

---

## 3. DEAD ENDS — tried, didn't pan out

*(empty)*

---

## Appendix: candidate selection

Source of problems: <https://www.erdosproblems.com>, via the community mirror
<https://github.com/teorth/erdosproblems> (`data/problems.yaml`, 1217 problems).

The database tags each problem with a status. The compute-relevant ones are:

| state | count | meaning |
|---|---|---|
| `decidable` | 9 | open, but reduced to a finite computation |
| `falsifiable` | 27 | open, but a finite computation disproves it *if it is false* |
| `verifiable` | 7 | open, but a finite computation proves it *if it is true* |

Reproduce the triage:

```
.venv/bin/python tools/triage.py                       # counts per state
.venv/bin/python tools/triage.py decidable falsifiable verifiable
.venv/bin/python tools/fetch_statements.py --compute   # cache statements
```
