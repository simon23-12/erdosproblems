#!/usr/bin/env python3
"""Generate docs/index.html -- a self-contained overview of the research state.

Reads RESEARCH_TRACKER.json (and the VERIFIED section of RESULTS.md) and emits
one static page with no external assets, so it works from a file:// URL or
GitHub Pages without a build step.

    python tools/build_dashboard.py
"""
from __future__ import annotations

import html
import json
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRACKER = ROOT / "RESEARCH_TRACKER.json"
OUT = ROOT / "docs" / "index.html"

STATUS_ORDER = ["verified", "active", "lead", "paused", "untouched", "dead-end"]
STATUS_LABEL = {
    "verified": "Machine-verified",
    "active": "In progress",
    "lead": "Unverified lead",
    "paused": "Paused",
    "untouched": "Not yet attempted",
    "dead-end": "Dead end",
}


def fmt_time(sec) -> str:
    sec = float(sec or 0)
    if sec <= 0:
        return "—"
    if sec < 90:
        return f"{sec:.0f}s"
    if sec < 5400:
        return f"{sec / 60:.0f}m"
    return f"{sec / 3600:.1f}h"


def main():
    data = json.loads(TRACKER.read_text())
    problems = data["problems"]
    meta = data["meta"]

    by_status: dict[str, list] = {s: [] for s in STATUS_ORDER}
    for p in problems:
        by_status.setdefault(p["status"], []).append(p)

    n_verified = len(by_status.get("verified", []))
    n_leads = len(by_status.get("lead", []))
    n_dead = len(by_status.get("dead-end", []))
    n_active = len(by_status.get("active", []))
    total_compute = sum(float(p.get("compute_time_spent_sec") or 0) for p in problems)

    rows = []
    for p in sorted(problems, key=lambda p: (STATUS_ORDER.index(p["status"])
                                             if p["status"] in STATUS_ORDER else 99,
                                             -p["priority"])):
        tags = "".join(
            f'<span class="tag t-{html.escape(t.split("/")[0].split(" ")[0].lower())}">'
            f'{html.escape(t)}</span>' for t in p["tags"])
        e = p["estimates"]
        best = p["best_verified_result"] or p["best_unverified_lead"] or ""
        bound = p["search_bounds_reached"] or ""
        rows.append(f"""
      <tr class="s-{p['status']}" data-status="{p['status']}">
        <td class="num"><a href="{p['url']}" target="_blank" rel="noopener">#{p['problem_id']}</a></td>
        <td class="title">
          <div class="t">{html.escape(p['title'])}</div>
          <div class="tags">{tags}</div>
          <div class="why">{html.escape(p['triage_rationale'])}</div>
        </td>
        <td><span class="pill p-{p['status']}">{STATUS_LABEL.get(p['status'], p['status'])}</span></td>
        <td class="pri"><div class="bar"><i style="width:{p['priority']*100:.0f}%"></i></div>
            <span>{p['priority']:.2f}</span></td>
        <td class="est">
          <div>runtime <b>{html.escape(str(e['runtime']))}</b></div>
          <div>P(verif) <b>{e['p_machine_verifiable']}</b></div>
          <div>novelty <b>{html.escape(str(e['novelty']))}</b></div>
        </td>
        <td class="prog">
          <div>{html.escape(bound) if bound else '—'}</div>
          <div class="dim">{fmt_time(p['compute_time_spent_sec'])} compute</div>
          {f'<div class="best">{html.escape(best)}</div>' if best else ''}
        </td>
      </tr>""")

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Erdős problems — machine-verified research log</title>
<style>
  :root {{
    --bg:#fbfaf8; --fg:#1a1917; --dim:#6b6862; --line:#e4e0d8; --card:#fff;
    --acc:#8a5a2b; --ok:#2f7d4f; --warn:#a8761c; --bad:#8a3b3b; --idle:#8b8781;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#16161a; --fg:#e9e6e0; --dim:#9a958c; --line:#2c2c33; --card:#1d1d22;
             --acc:#d3a06a; --ok:#5fb883; --warn:#d6a748; --bad:#d1706e; --idle:#75726c; }}
  }}
  :root[data-theme="dark"] {{ --bg:#16161a; --fg:#e9e6e0; --dim:#9a958c; --line:#2c2c33;
    --card:#1d1d22; --acc:#d3a06a; --ok:#5fb883; --warn:#d6a748; --bad:#d1706e; --idle:#75726c; }}
  :root[data-theme="light"] {{ --bg:#fbfaf8; --fg:#1a1917; --dim:#6b6862; --line:#e4e0d8;
    --card:#fff; --acc:#8a5a2b; --ok:#2f7d4f; --warn:#a8761c; --bad:#8a3b3b; --idle:#8b8781; }}
  * {{ box-sizing:border-box }}
  body {{ margin:0; background:var(--bg); color:var(--fg);
    font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:2.5rem 1.25rem 5rem; }}
  h1 {{ font-size:1.75rem; margin:0 0 .3rem; letter-spacing:-.02em; }}
  .sub {{ color:var(--dim); margin:0 0 2rem; }}
  .sub a {{ color:var(--acc); }}
  .trust {{ border-left:3px solid var(--acc); background:var(--card); padding:.9rem 1.1rem;
    border-radius:0 8px 8px 0; margin:0 0 2rem; font-size:.92rem; }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
    gap:.75rem; margin-bottom:2rem; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:.9rem 1rem; }}
  .card b {{ display:block; font-size:1.9rem; line-height:1.1; font-variant-numeric:tabular-nums; }}
  .card span {{ color:var(--dim); font-size:.8rem; text-transform:uppercase; letter-spacing:.05em; }}
  .card.ok b {{ color:var(--ok) }} .card.warn b {{ color:var(--warn) }}
  .card.bad b {{ color:var(--bad) }} .card.acc b {{ color:var(--acc) }}
  .empty {{ color:var(--dim); font-style:italic; }}
  .tablewrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:10px;
    background:var(--card); }}
  table {{ border-collapse:collapse; width:100%; min-width:900px; }}
  th {{ text-align:left; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em;
    color:var(--dim); padding:.7rem .8rem; border-bottom:1px solid var(--line); font-weight:600; }}
  td {{ padding:.8rem; border-bottom:1px solid var(--line); vertical-align:top; }}
  tr:last-child td {{ border-bottom:none }}
  .num a {{ color:var(--acc); text-decoration:none; font-weight:600;
    font-variant-numeric:tabular-nums; }}
  .num a:hover {{ text-decoration:underline }}
  .title {{ max-width:430px }}
  .title .t {{ font-weight:550; margin-bottom:.35rem }}
  .why {{ color:var(--dim); font-size:.82rem; margin-top:.4rem }}
  .tags {{ display:flex; flex-wrap:wrap; gap:.25rem }}
  .tag {{ font-size:.68rem; padding:.1rem .4rem; border-radius:4px; border:1px solid var(--line);
    color:var(--dim); white-space:nowrap; }}
  .tag.t-not {{ border-color:var(--bad); color:var(--bad) }}
  .pill {{ font-size:.74rem; padding:.2rem .5rem; border-radius:999px; white-space:nowrap;
    border:1px solid currentColor; }}
  .p-verified {{ color:var(--ok) }} .p-active {{ color:var(--acc) }}
  .p-lead {{ color:var(--warn) }} .p-dead-end {{ color:var(--bad) }}
  .p-untouched, .p-paused {{ color:var(--idle) }}
  .pri {{ white-space:nowrap; font-variant-numeric:tabular-nums; }}
  .bar {{ height:5px; background:var(--line); border-radius:3px; overflow:hidden;
    margin-bottom:.25rem; width:66px; }}
  .bar i {{ display:block; height:100%; background:var(--acc) }}
  .est, .prog {{ font-size:.82rem; color:var(--dim) }}
  .est b, .prog b {{ color:var(--fg); font-weight:600 }}
  .prog .dim {{ font-size:.76rem }}
  .prog .best {{ color:var(--ok); margin-top:.3rem }}
  footer {{ margin-top:2rem; color:var(--dim); font-size:.82rem }}
  code {{ background:var(--line); padding:.1rem .35rem; border-radius:4px; font-size:.85em }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Erdős problems — machine-verified research log</h1>
  <p class="sub">Autonomous work on open problems from
    <a href="https://www.erdosproblems.com" target="_blank" rel="noopener">erdosproblems.com</a>.
    Generated {generated} · commit <code>{html.escape(meta.get('last_commit') or 'unknown')}</code></p>

  <div class="trust"><b>Trust rule.</b> {html.escape(meta['trust_rule'])}
    Counts below are deliberately conservative: a problem is
    <b>Machine-verified</b> only when a standalone script or a Lean file reproduces the claim.</div>

  <div class="cards">
    <div class="card {'ok' if n_verified else ''}"><b>{n_verified}</b><span>Verified</span></div>
    <div class="card acc"><b>{n_active}</b><span>In progress</span></div>
    <div class="card warn"><b>{n_leads}</b><span>Leads (unverified)</span></div>
    <div class="card bad"><b>{n_dead}</b><span>Dead ends</span></div>
    <div class="card"><b>{len(problems)}</b><span>Triaged</span></div>
    <div class="card"><b>{fmt_time(total_compute)}</b><span>Compute spent</span></div>
  </div>

  {'<p class="empty">Nothing has been machine-verified yet — the Verified column is honestly empty.</p>' if not n_verified else ''}

  <div class="tablewrap">
  <table>
    <thead><tr>
      <th>Problem</th><th>Statement &amp; triage</th><th>Status</th>
      <th>Priority</th><th>Estimates</th><th>Progress</th>
    </tr></thead>
    <tbody>{''.join(rows)}
    </tbody>
  </table>
  </div>

  <footer>
    Problem metadata from <a href="https://github.com/teorth/erdosproblems">teorth/erdosproblems</a>.
    Full journal in <code>LOG.md</code>, ledger in <code>RESULTS.md</code>,
    machine-readable state in <code>RESEARCH_TRACKER.json</code>.
  </footer>
</div>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc)
    print(f"wrote {OUT}  ({len(doc):,} bytes, {len(problems)} problems)")


if __name__ == "__main__":
    main()
