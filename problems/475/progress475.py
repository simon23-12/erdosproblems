#!/usr/bin/env python3
"""Turn the per-chunk output of run475.sh into a coverage report.

A chunk counts only if its file carries the terminal '# p=... checked=...' line
that search475.c prints on success. Missing chunks are listed explicitly -- the
window is reported as complete only when every (t, first) pair is present and
the subset counts add up to C(p-1, t) exactly.

Usage: python progress475.py 37
"""
from __future__ import annotations

import pathlib
import re
import sys
from math import comb

HERE = pathlib.Path(__file__).resolve().parent
LINE = re.compile(r"^# p=(\d+) t=(\d+) prefix=(\S+) checked=(\d+) fallbacks=(\d+) bad=(\d+)")


def main():
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 37
    # coverage is judged by the SUBSET COUNTS adding up to C(p-1,t) exactly,
    # which catches a missing chunk without needing to re-derive the chunk list
    got, checked, fallbacks, bad, problems = {}, 0, 0, 0, []

    for path in (HERE / "results").glob(f"p{p}_t*.out"):
        for line in path.read_text().splitlines():
            m = LINE.match(line)
            if m:
                t, pre, c, fb, b = (int(m.group(2)), m.group(3),
                                    int(m.group(4)), int(m.group(5)), int(m.group(6)))
                got[(t, pre)] = c
                checked += c
                fallbacks += fb
                bad += b
            elif line.startswith(("NO-VALID-ORDERING", "VERIFY-FAILED")):
                problems.append(line)

    per_t = {}
    for (t, f), c in got.items():
        per_t[t] = per_t.get(t, 0) + c

    print(f"p = {p},  open window t in [21,{p-4}]")
    print(f"chunks recorded: {len(got):,}")
    ok_counts = True
    for t in sorted(per_t):
        exp = comb(p - 1, t)
        mark = "ok" if per_t[t] == exp else f"MISMATCH (expected {exp:,})"
        ok_counts &= per_t[t] == exp
        print(f"  t={t:>2}: {per_t[t]:>15,} subsets  {mark}")
    print(f"total checked        : {checked:,}")
    print(f"exhaustive fallbacks : {fallbacks:,}")
    print(f"subsets with NO valid ordering: {bad}")
    for line in problems:
        print(f"  !! {line}")
    print()
    expected_ts = set(range(21, p - 3))
    complete = ok_counts and bad == 0 and set(per_t) == expected_ts
    if set(per_t) != expected_ts:
        print(f"  missing whole t values: {sorted(expected_ts - set(per_t))}")
    print(f"RESULT: every subset of F_{p}\\{{0}} in the open window has a valid ordering"
          if complete else "RESULT: INCOMPLETE — see missing chunks / mismatches above")


if __name__ == "__main__":
    main()
