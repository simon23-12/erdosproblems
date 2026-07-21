#!/usr/bin/env python3
"""Triage the Erdos problem database for compute-amenable open problems.

Data source: https://github.com/teorth/erdosproblems (data/problems.yaml),
the community "ground truth" mirror of erdosproblems.com.

The database tags a status `state` per problem. The states that matter for
machine-checkable work are:

  decidable   - open, but reduced to a finite computation
  falsifiable - open, but a finite computation disproves it if it is false
  verifiable  - open, but a finite computation proves it if it is true
  open        - completely open

Usage:
    python tools/triage.py                # summary of all states
    python tools/triage.py decidable      # list problems in a given state
"""
import sys
import collections
import pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROBLEMS = ROOT / "data" / "problems.yaml"

# States where a finite computation can settle (part of) the problem.
COMPUTE_STATES = ("decidable", "falsifiable", "verifiable")


def load():
    with open(PROBLEMS) as f:
        return yaml.safe_load(f)


def state_of(p):
    return (p.get("status") or {}).get("state", "unknown")


def main():
    probs = load()
    by_state = collections.defaultdict(list)
    for p in probs:
        by_state[state_of(p)].append(p)

    if len(sys.argv) > 1:
        wanted = sys.argv[1:]
        for st in wanted:
            print(f"===== {st} ({len(by_state[st])}) =====")
            for p in by_state[st]:
                tags = ", ".join(p.get("tags", []))
                note = (p.get("status") or {}).get("note", "")
                oeis = ", ".join(p.get("oeis", []))
                print(f"[{p['number']}] prize={p.get('prize','no')} tags={tags}")
                if oeis:
                    print(f"    oeis: {oeis}")
                if note:
                    print(f"    note: {note}")
        return

    print(f"total problems: {len(probs)}")
    for st, ps in sorted(by_state.items(), key=lambda kv: -len(kv[1])):
        mark = " <-- compute-amenable" if st in COMPUTE_STATES else ""
        print(f"  {st:<28} {len(ps):>4}{mark}")


if __name__ == "__main__":
    main()
