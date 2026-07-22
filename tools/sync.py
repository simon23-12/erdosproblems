#!/usr/bin/env python3
"""SYNC PHASE — reconcile the repository with upstream before doing any work.

Run this at the start of every session. It answers four questions:

  1. Have any problems been ADDED upstream?
  2. Have any problem STATUSES changed -- in particular, has anything I am
     working on been SOLVED (in which case: archive, stop spending compute)?
  3. Have any STATEMENTS changed (in which case: re-triage, because my cached
     reading may be stale)?
  4. What has already been done by other people -- the AI-contributions page and
     any published computational bounds -- so I do not duplicate a search?

Everything is diffed against the snapshot in data/, so re-running is cheap and
the output is only the delta.

    python tools/sync.py            # report the delta
    python tools/sync.py --apply    # ...and update the local snapshot
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MIRROR = DATA / "upstream"          # clone of teorth/erdosproblems
SNAPSHOT = DATA / "problems.yaml"   # last-synced copy
STATEMENTS = DATA / "statements"
SYNCLOG = DATA / "sync_state.json"

UPSTREAM = "https://github.com/teorth/erdosproblems.git"
# NB: the wiki page name contains "Erdős"; the non-ASCII character must be
# percent-encoded or urllib raises before it ever reaches the network.
AI_PAGE = ("https://raw.githubusercontent.com/wiki/teorth/erdosproblems/"
           + urllib.parse.quote("AI-contributions-to-Erdős-problems.md"))

COMPUTE_STATES = ("decidable", "falsifiable", "verifiable")
SOLVED_STATES = ("proved", "disproved", "solved", "proved (Lean)",
                 "disproved (Lean)", "solved (Lean)")


def sh(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def fetch_mirror() -> str:
    """Clone or pull the community mirror. Returns the upstream HEAD sha."""
    if not (MIRROR / ".git").exists():
        MIRROR.parent.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(MIRROR, ignore_errors=True)
        sh("git", "clone", "--depth", "1", UPSTREAM, str(MIRROR))
    else:
        sh("git", "fetch", "--depth", "1", "origin", cwd=MIRROR)
        sh("git", "reset", "--hard", "origin/HEAD", cwd=MIRROR)
    return sh("git", "rev-parse", "HEAD", cwd=MIRROR).stdout.strip()


def load_yaml(path: pathlib.Path) -> dict:
    import yaml
    if not path.exists():
        return {}
    return {p["number"]: p for p in yaml.safe_load(path.read_text())}


def state_of(p) -> str:
    return (p.get("status") or {}).get("state", "unknown")


def statement_digest(n: str) -> str | None:
    f = STATEMENTS / f"{n}.txt"
    if not f.exists():
        return None
    # hash only the mathematical body, not the "last edited" footer
    body = f.read_text().split("View the LaTeX source")[0]
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def fetch_statement(n: str) -> str | None:
    sys.path.insert(0, str(ROOT / "tools"))
    from fetch_statements import fetch  # reuse, do not reimplement
    try:
        return fetch(n)
    except Exception as e:  # noqa: BLE001
        print(f"    (could not refetch {n}: {e})")
        return None


def ai_contributions() -> dict[str, list[str]]:
    """Problem number -> lines mentioning it on the AI-contributions wiki page.

    This is the page the brief says to check so I do not redo work someone else
    already did. Failure to reach it is reported, never silently ignored.
    """
    try:
        req = urllib.request.Request(AI_PAGE, headers={"User-Agent": "erdos-research/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not fetch AI-contributions page: {e}")
        return {}
    hits: dict[str, list[str]] = {}
    for line in text.splitlines():
        for m in re.finditer(r"erdosproblems\.com/(\d+)", line):
            hits.setdefault(m.group(1), []).append(line.strip()[:300])
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="update the local snapshot and refetch changed statements")
    a = ap.parse_args()

    print("SYNC PHASE")
    print("=" * 70)
    sha = fetch_mirror()
    print(f"upstream teorth/erdosproblems @ {sha[:10]}")

    old = load_yaml(SNAPSHOT)
    new = load_yaml(MIRROR / "data" / "problems.yaml")
    print(f"problems: {len(old)} local -> {len(new)} upstream")

    added = sorted(set(new) - set(old), key=lambda s: int(s.split("-")[0]))
    removed = sorted(set(old) - set(new), key=lambda s: int(s.split("-")[0]))
    changed = {n: (state_of(old[n]), state_of(new[n]))
               for n in set(old) & set(new)
               if state_of(old[n]) != state_of(new[n])}

    print()
    print(f"[1] newly added problems: {added if added else 'none'}")
    if removed:
        print(f"    removed upstream: {removed}")

    print(f"[2] status changes: {len(changed)}")
    my_ids = set()
    tracker = ROOT / "RESEARCH_TRACKER.json"
    if tracker.exists():
        my_ids = {p["problem_id"] for p in json.loads(tracker.read_text())["problems"]}
    newly_solved_mine = []
    for n, (o, w) in sorted(changed.items(), key=lambda kv: int(kv[0].split("-")[0])):
        mine = " <-- IN MY TRACKER" if n in my_ids else ""
        print(f"    [{n}] {o} -> {w}{mine}")
        if w in SOLVED_STATES and n in my_ids:
            newly_solved_mine.append(n)
    if newly_solved_mine:
        print(f"    !! SOLVED upstream, stop spending compute: {newly_solved_mine}")

    # new compute-amenable problems worth triaging
    fresh = [n for n in added if state_of(new[n]) in COMPUTE_STATES]
    became = [n for n, (o, w) in changed.items()
              if w in COMPUTE_STATES and o not in COMPUTE_STATES]
    if fresh or became:
        print(f"    newly compute-amenable -> TRIAGE THESE: "
              f"{sorted(set(fresh) | set(became))}")

    print("[3] statement drift (cached vs upstream)")
    digests_old = json.loads(SYNCLOG.read_text())["statement_digests"] if SYNCLOG.exists() else {}
    drifted = []
    for n in sorted(STATEMENTS.glob("*.txt")):
        num = n.stem
        d = statement_digest(num)
        if num in digests_old and digests_old[num] != d:
            drifted.append(num)
    print(f"    locally modified since last sync: {drifted if drifted else 'none'}")
    print("    (a full re-fetch of every cached statement runs with --apply)")

    print("[4] AI-contributions page (avoid duplicating others' searches)")
    ai = ai_contributions()
    if ai:
        overlap = sorted(set(ai) & my_ids, key=int)
        print(f"    problems mentioned there that I have touched: {overlap}")
        for n in overlap:
            for line in ai[n][:1]:
                print(f"      [{n}] {line}")
    else:
        print("    (page unavailable this run — reported, not assumed empty)")

    if a.apply:
        shutil.copy(MIRROR / "data" / "problems.yaml", SNAPSHOT)
        refetched = 0
        for n in sorted(set(fresh) | set(became) | set(changed) & set(my_ids)):
            f = STATEMENTS / f"{n}.txt"
            if f.exists():
                f.unlink()
            if fetch_statement(n):
                refetched += 1
        digests = {p.stem: statement_digest(p.stem) for p in STATEMENTS.glob("*.txt")}
        SYNCLOG.write_text(json.dumps({
            "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "upstream_sha": sha,
            "statement_digests": digests,
        }, indent=2) + "\n")
        print()
        print(f"applied: snapshot updated, {refetched} statements refetched, "
              f"{len(digests)} digests recorded")
    else:
        print()
        print("(dry run — pass --apply to update the snapshot)")


if __name__ == "__main__":
    main()
