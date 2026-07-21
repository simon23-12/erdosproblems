#!/usr/bin/env python3
"""Turn the per-chunk output files into (a) the largest CONTIGUOUS verified
bound and (b) the list of solutions found.

A chunk counts only if its file carries the terminal '# range [L,R) done' line
that search647.c prints on success -- a half-written or killed chunk is a hole,
and coverage stops at the first hole rather than jumping over it.

Usage: python progress647.py
"""
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
DONE = re.compile(r"^# range \[(\d+),(\d+)\) done: solutions=(\d+)\s+max_tau_seen=(\d+)\s+window=(\d+)")

intervals, sols, tau_max, window = [], [], 0, None
for f in (HERE / "results").glob("*.out"):
    for line in f.read_text().splitlines():
        m = DONE.match(line)
        if m:
            lo, hi, _, tm, w = (int(x) for x in m.groups())
            intervals.append((lo, hi))
            tau_max = max(tau_max, tm)
            window = w
        elif line.startswith("SOLUTION"):
            sols.append(int(line.split("=")[1]))

# The Python reference verifier independently covers [2, 10^7].
intervals.append((2, 10 ** 7))
intervals.sort()

reach = 2
for lo, hi in intervals:
    if lo > reach:
        break            # hole: coverage stops here
    reach = max(reach, hi)

print(f"chunks finished        : {len(intervals) - 1}")
print(f"contiguous verified to : {reach:,}")
print(f"max tau seen           : {tau_max}   (window {window}; needs window+2 > max tau)")
if window is not None and tau_max + 2 >= window:
    print("!! WINDOW TOO SMALL -- results above are NOT valid")
print(f"solutions found        : {sorted(set(sols))}")
print(f"solutions with n > 24  : {sorted(n for n in set(sols) if n > 24) or 'NONE'}")
