#!/usr/bin/env python3
"""Read/update RESEARCH_TRACKER.json -- the persistent record of every problem
ever examined.

The tracker is the thing consulted BEFORE starting an attempt, so that a search
already pushed to n <= 18 resumes at 19 instead of restarting at 2.

Usage:
    python tools/tracker.py show                 # table of everything
    python tools/tracker.py show 647             # one problem in full
    python tools/tracker.py next                 # highest-priority untouched
    python tools/tracker.py resume 647           # bounds already reached
    python tools/tracker.py set 647 status=active reason_for_stopping=""
    python tools/tracker.py note 647 "free text appended to approaches"
    python tools/tracker.py stamp                # refresh commit hash + times
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRACKER = ROOT / "RESEARCH_TRACKER.json"


def load() -> dict:
    return json.loads(TRACKER.read_text())


def save(data: dict):
    data["meta"]["last_modified"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data["meta"]["last_commit"] = git_hash()
    TRACKER.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def git_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True,
            stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def get(data: dict, pid: str) -> dict:
    for p in data["problems"]:
        if p["problem_id"] == str(pid):
            return p
    raise KeyError(f"problem {pid} not in tracker")


def touch(p: dict):
    p["last_modified"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    p["last_commit"] = git_hash()


# --------------------------------------------------------------------------
def cmd_show(args):
    data = load()
    if args:
        p = get(data, args[0])
        print(json.dumps(p, indent=2, ensure_ascii=False))
        return
    rows = sorted(data["problems"], key=lambda p: -p["priority"])
    print(f"{'id':>5} {'pri':>5} {'status':<12} {'bound reached':<26} title")
    print("-" * 110)
    for p in rows:
        print(f"{p['problem_id']:>5} {p['priority']:>5.2f} {p['status']:<12} "
              f"{(p['search_bounds_reached'] or '-')[:25]:<26} {p['title'][:48]}")
    counts: dict[str, int] = {}
    for p in data["problems"]:
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    print("-" * 110)
    print("  ".join(f"{k}={v}" for k, v in sorted(counts.items())))


def cmd_next(args):
    data = load()
    cands = [p for p in data["problems"] if p["status"] in ("untouched", "paused")]
    cands.sort(key=lambda p: -p["priority"])
    for p in cands[: int(args[0]) if args else 5]:
        print(f"[{p['problem_id']}] pri={p['priority']:.2f}  {p['title']}")
        print(f"      tags: {', '.join(p['tags'])}")
        print(f"      est : runtime={p['estimates']['runtime']}, "
              f"P(verifiable)={p['estimates']['p_machine_verifiable']}, "
              f"novelty={p['estimates']['novelty']}, scales={p['estimates']['scales']}")
        if p["search_bounds_reached"]:
            print(f"      RESUME FROM: {p['search_bounds_reached']}")


def cmd_resume(args):
    data = load()
    p = get(data, args[0])
    print(f"[{p['problem_id']}] {p['title']}")
    print(f"status              : {p['status']}")
    print(f"bounds reached      : {p['search_bounds_reached'] or '(none)'}")
    print(f"approaches attempted: {p['approaches_attempted'] or '(none)'}")
    print(f"reason for stopping : {p['reason_for_stopping'] or '(n/a)'}")
    print(f"best verified       : {p['best_verified_result'] or '(none)'}")
    print(f"best lead           : {p['best_unverified_lead'] or '(none)'}")
    print(f"compute spent       : {p['compute_time_spent_sec']} s")


def cmd_set(args):
    data = load()
    p = get(data, args[0])
    for kv in args[1:]:
        k, _, v = kv.partition("=")
        if k == "priority":
            v = float(v)
        elif k == "compute_time_spent_sec":
            v = float(v)
        elif k in ("tags",):
            v = [t.strip() for t in v.split(",") if t.strip()]
        p[k] = v
    touch(p)
    save(data)
    print(f"updated {p['problem_id']}")


def cmd_note(args):
    data = load()
    p = get(data, args[0])
    p["approaches_attempted"].append(" ".join(args[1:]))
    touch(p)
    save(data)
    print(f"noted on {p['problem_id']}")


def cmd_stamp(args):
    data = load()
    save(data)
    print(f"stamped at commit {data['meta']['last_commit']}")


COMMANDS = {"show": cmd_show, "next": cmd_next, "resume": cmd_resume,
            "set": cmd_set, "note": cmd_note, "stamp": cmd_stamp}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
