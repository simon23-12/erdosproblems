#!/usr/bin/env python3
"""Migrate RESEARCH_TRACKER.json to the ROI + knowledge-graph schema.

Adds, per problem:
    roi                       {expected_value, novelty, p_verifiable,
                               compute_cost, score}
    published_search_bounds   what the literature/OEIS already reached
    prior_work                entries from the AI-contributions page etc.
    verification_artifacts    paths a skeptic runs
    reusable_modules_created  assets this problem contributed to lib/
    knowledge_dependencies    lib/ modules this problem consumes
    related_problems          edges in the knowledge graph

and, at the top level, `knowledge_graph` linking problems through the shared
modules and techniques.

    ROI = expected_value * novelty * p_verifiable / compute_cost

compute_cost is on a log-ish scale: 1 = minutes, 3 = hours, 10 = days,
30 = beyond this hardware. Everything work-loop-owned is preserved verbatim.

    python tools/upgrade_tracker.py
"""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRACKER = ROOT / "RESEARCH_TRACKER.json"

# problem_id -> (expected_value, novelty, p_verifiable, compute_cost)
# expected_value : how much a machine-checkable artifact here is worth (0-1)
# novelty        : odds the artifact is new rather than a redo (0-1)
# p_verifiable   : odds of getting ANY machine-checked artifact (0-1)
# compute_cost   : 1 minutes, 3 hours, 10 days, 30 infeasible
ROI_INPUTS = {
    "647":  (0.85, 0.80, 0.95, 3),
    "287":  (0.80, 0.85, 0.90, 3),
    "366":  (0.60, 0.75, 0.90, 3),
    "458":  (0.45, 0.70, 0.95, 1),
    "699":  (0.55, 0.70, 0.85, 3),
    "488":  (0.50, 0.60, 0.85, 1),
    "835":  (0.75, 0.35, 0.55, 3),
    "743":  (0.70, 0.70, 0.55, 10),
    "64":   (0.75, 0.55, 0.45, 10),
    "167":  (0.70, 0.25, 0.75, 3),
    "1020": (0.60, 0.45, 0.60, 3),
    "475":  (0.55, 0.45, 0.70, 3),
    "848":  (0.50, 0.40, 0.65, 3),
    "548":  (0.55, 0.25, 0.60, 3),
    "583":  (0.50, 0.30, 0.60, 3),
    "742":  (0.45, 0.30, 0.70, 3),
    "23":   (0.50, 0.30, 0.65, 3),
    "375":  (0.60, 0.45, 0.55, 10),
    "128":  (0.50, 0.25, 0.55, 3),
    "580":  (0.45, 0.25, 0.55, 3),
    "398":  (0.60, 0.40, 0.80, 3),
    "993":  (0.40, 0.20, 0.55, 10),
    "547":  (0.40, 0.25, 0.45, 10),
    "628":  (0.55, 0.35, 0.30, 10),
    "551":  (0.40, 0.20, 0.30, 10),
    "1082": (0.55, 0.25, 0.25, 10),
    "506":  (0.45, 0.25, 0.25, 10),
    "97":   (0.70, 0.30, 0.20, 10),
    "982":  (0.50, 0.25, 0.25, 10),
    "617":  (0.75, 0.60, 0.20, 10),
    "7":    (0.95, 0.60, 0.10, 30),
    "779":  (0.40, 0.50, 0.10, 3),
    "556":  (0.35, 0.20, 0.15, 30),
    "672":  (0.35, 0.10, 0.10, 30),
    "307":  (0.60, 0.30, 0.05, 30),
    "19":   (0.70, 0.05, 0.05, 30),
    "242":  (0.50, 0.02, 0.05, 30),
    "364":  (0.45, 0.02, 0.05, 30),
    "723":  (0.90, 0.20, 0.03, 30),
    "107":  (0.90, 0.15, 0.03, 30),
    "106":  (0.60, 0.20, 0.05, 30),
    "114":  (0.30, 0.05, 0.03, 30),
    "1041": (0.35, 0.10, 0.03, 30),
}

# What the literature / OEIS already reached, so novelty is judged honestly.
PUBLISHED_BOUNDS = {
    "647":  "no published computational bound located; AI attempts (Jan 2026) produced only incorrect proofs",
    "287":  "no published computational bound located",
    "366":  "10^22 via OEIS A060355 (consecutive powerful pairs); Aktas-Murty (2017) and an "
            "automated pipeline (Apr 2026) give conditional partial results, not a search bound",
    "458":  "no published computational bound located",
    "699":  "no published computational bound located; GPT 5.6 proved the cases j <= 3i/2 and n = 2j",
    "488":  "no published computational bound located; Cambie (2025) and Aristotle solved a VARIANT",
    "835":  "false for 3 <= k <= 8 (published chromatic numbers); Ma-Tang: chi > k+1 when k+1 is composite. "
            "An AlphaProof contribution (Dec 2025) is logged upstream as 'likely folklore' -- "
            "my Steiner reduction may well BE that folklore",
    "242":  "verified to 10^18",
    "364":  "verified past 7.38*10^28 (OEIS A076445)",
    "375":  "verified to 1.9*10^10 (Laishram-Shorey)",
    "398":  "no other solutions below 10^9 per the OEIS page",
    "993":  "unimodality verified to 29 vertices (literature, 2026)",
    "723":  "order 10 ruled out by computer search (Lam 1989); order 12 open",
    "107":  "f(6)=17 (Szekeres-Peters); f(7) unknown",
    "19":   "true for n < 10 (Hindman) and all sufficiently large n (KKKMO 2021)",
    "475":  "true for t <= 12 and p-3 <= t <= p-1, and all sufficiently large p",
    "167":  "GPT-5 partial results (Oct 2025); Haxell's (3 - 3/23)k bound",
    "848":  "Sawhney: solved for all sufficiently large N; explicit bound derived (Mar 2026)",
    "1082": "second question answered NO by an 8-point construction (Harborth); "
            "DeepMind prover agent produced a Lean counterexample to one part (Feb 2026)",
}

# lib/ modules each problem consumes, and assets it contributed.
DEPS = {
    "647":  (["problems/647/search647.c (segmented tau sieve)"], []),
    "287":  (["erdos.numth"], ["ErdosFormal/Erdos287.lean", "problems/287/cover287.c"]),
    "458":  (["erdos.numth"], ["erdos.numth.prime_powers_upto", "erdos.numth.prime_between"]),
    "699":  (["erdos.numth"], ["erdos.numth.kummer_carries"]),
    "366":  ([], ["problems/366/search366.c (cubefull enumerator + powerfulness test)"]),
    "488":  ([], []),
    "617":  (["erdos.sat"], ["erdos.sat.CNF", "star-sort symmetry breaking"]),
    "835":  (["erdos.graphs", "erdos.sat"], ["erdos.graphs.chromatic_number"]),
    "993":  (["erdos.treedp", "erdos.graphs"], ["erdos.treedp"]),
}

# Knowledge-graph edges: (a, b, why). Recorded so that solving one suggests the other.
EDGES = [
    ("287", "458", "both reduce a statement about lcm/reciprocals to a prime-gap scan; "
                   "share erdos.numth prime primitives"),
    ("287", "366", "both are 'exhaustive negative over a range' number searches whose "
                   "correctness hinges on an exactly-stated cofactor test"),
    ("458", "366", "both walk a sparse set (prime powers / cubefull numbers) instead of "
                   "the dense set the obvious approach would use -- the same trick"),
    ("699", "458", "both use exact prime-power valuations rather than forming big integers"),
    ("617", "835", "both are graph-colouring feasibility questions attacked with the same "
                   "SAT encoder and symmetry-breaking idea"),
    ("835", "723", "both ask whether a highly structured design exists (Steiner system / "
                   "projective plane); a large-set search engine would serve both"),
    ("835", "1020", "both are extremal set-system problems over k-subsets; the same "
                    "ILP/packing bounds apply"),
    ("167", "23",  "both need exact small-graph optimisation (triangle packing / max-cut) "
                   "over geng output"),
    ("548", "580", "both ask when an edge/degree condition forces every tree of a given "
                   "size; the same subtree-containment routine serves both"),
    ("547", "551", "both need exact Ramsey numbers via SAT on K_m"),
    ("993", "743", "both enumerate free trees with gentreeg and do per-tree DP"),
    ("64",  "583", "both are questions about cycle/path structure in bounded-degree graphs "
                   "over geng output"),
    ("366", "364", "consecutive powerful numbers; the same cubefull enumerator and "
                   "powerfulness test apply, but 364's published bound is far out of reach"),
    ("242", "287", "both are unit-fraction problems; 242's 10^18 bound shows what a "
                   "dedicated effort achieves and why 287 needed a different idea"),
]


def main():
    data = json.loads(TRACKER.read_text())
    for p in data["problems"]:
        pid = p["problem_id"]
        ev, nov, pv, cost = ROI_INPUTS.get(pid, (0.3, 0.3, 0.3, 10))
        score = ev * nov * pv / cost
        p["roi"] = {"expected_value": ev, "novelty": nov, "p_verifiable": pv,
                    "compute_cost": cost, "score": round(score, 4)}
        p["priority"] = round(min(1.0, score * 12), 3)   # keep a 0-1 display value
        p.setdefault("published_search_bounds", "")
        if pid in PUBLISHED_BOUNDS:
            p["published_search_bounds"] = PUBLISHED_BOUNDS[pid]
        p.setdefault("prior_work", [])
        deps, made = DEPS.get(pid, ([], []))
        p.setdefault("knowledge_dependencies", [])
        p.setdefault("reusable_modules_created", [])
        if deps:
            p["knowledge_dependencies"] = deps
        if made:
            p["reusable_modules_created"] = made
        p["verification_artifacts"] = p.pop("artifacts", []) or p.get("verification_artifacts", [])
        p.setdefault("related_problems", [])

    rel: dict[str, list] = {}
    for a, b, why in EDGES:
        rel.setdefault(a, []).append({"problem": b, "why": why})
        rel.setdefault(b, []).append({"problem": a, "why": why})
    for p in data["problems"]:
        p["related_problems"] = rel.get(p["problem_id"], [])

    data["problems"].sort(key=lambda p: -p["roi"]["score"])
    data["meta"]["roi_formula"] = ("expected_value * novelty * p_verifiable / compute_cost; "
                                   "compute_cost 1=minutes 3=hours 10=days 30=infeasible")
    data["meta"]["knowledge_graph"] = {
        "modules": {
            "erdos.sat": "CNF builder, cardinality encodings, symmetry breaking (lex_leq)",
            "erdos.graphs": "nauty geng/gentreeg wrappers, cycle spectrum, max-cut, "
                            "exact chromatic number by SAT",
            "erdos.numth": "sieves, deterministic Miller-Rabin, prime_between witnesses, "
                           "prime_powers_upto, k-full numbers, Kummer carries",
            "erdos.treedp": "linear-time tree DP (independence polynomial, unimodality)",
            "ErdosFormal": "Lean 4 + mathlib; Erdos287 elimination/certificate lemmas",
        },
        "edges": [{"a": a, "b": b, "why": w} for a, b, w in EDGES],
    }
    data["meta"]["last_modified"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    TRACKER.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"upgraded {len(data['problems'])} problems; {len(EDGES)} knowledge-graph edges")
    print("\ntop 10 by ROI:")
    for p in data["problems"][:10]:
        r = p["roi"]
        print(f"  [{p['problem_id']:>4}] ROI={r['score']:.4f}  "
              f"(EV {r['expected_value']} x nov {r['novelty']} x P {r['p_verifiable']} "
              f"/ cost {r['compute_cost']})  {p['status']:<10} {p['title'][:44]}")


if __name__ == "__main__":
    main()
