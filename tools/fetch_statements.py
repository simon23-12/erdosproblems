#!/usr/bin/env python3
"""Fetch and cache problem statements from erdosproblems.com.

The statement lives in a <div class="problem-text">, followed by zero or more
<div class="problem-additional-text"> blocks holding commentary/known results.

Usage:
    python tools/fetch_statements.py 375 376 ...   # fetch specific problems
    python tools/fetch_statements.py --compute     # fetch all compute-amenable ones

Cached as data/statements/<n>.txt so we only hit the site once per problem.
"""
import html
import pathlib
import re
import sys
import time
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "statements"
COMPUTE_STATES = ("decidable", "falsifiable", "verifiable")

TAG_RE = re.compile(r"<[^>]+>")


def strip_html(frag: str) -> str:
    frag = re.sub(r"<br\s*/?>", "\n", frag)
    frag = re.sub(r"</p>", "\n\n", frag)
    frag = TAG_RE.sub("", frag)
    frag = html.unescape(frag)
    # collapse runs of blank lines / trailing spaces
    frag = re.sub(r"[ \t]+", " ", frag)
    frag = re.sub(r"\n\s*\n\s*\n+", "\n\n", frag)
    return frag.strip()


def extract_divs(page: str, cls: str):
    """Extract inner HTML of every <div class="cls"> ... </div>, brace-matched."""
    out = []
    for m in re.finditer(r'<div class="%s"[^>]*>' % re.escape(cls), page):
        start = m.end()
        depth = 1
        i = start
        while depth > 0 and i < len(page):
            nxt_open = page.find("<div", i)
            nxt_close = page.find("</div>", i)
            if nxt_close == -1:
                break
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                i = nxt_open + 4
            else:
                depth -= 1
                i = nxt_close + 6
        out.append(page[start:i - 6])
    return out


def fetch(n: str) -> str:
    dest = CACHE / f"{n}.txt"
    if dest.exists():
        return dest.read_text()
    url = f"https://www.erdosproblems.com/{n}"
    req = urllib.request.Request(url, headers={"User-Agent": "erdos-research/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        page = r.read().decode("utf-8", "replace")

    parts = [f"=== PROBLEM {n} ===", f"source: {url}", ""]
    stmts = extract_divs(page, "problem-text")
    for s in stmts[:1]:  # first one is the statement; second is a duplicate/preview
        parts.append(strip_html(s))
    extra = extract_divs(page, "problem-additional-text")
    for e in extra:
        t = strip_html(e)
        if t:
            parts.append("\n--- additional ---\n" + t)
    text = "\n".join(parts)
    CACHE.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)
    time.sleep(1.0)  # be polite to the site
    return text


def main():
    args = sys.argv[1:]
    if args and args[0] == "--compute":
        probs = yaml.safe_load((ROOT / "data" / "problems.yaml").read_text())
        nums = [p["number"] for p in probs
                if (p.get("status") or {}).get("state") in COMPUTE_STATES]
    else:
        nums = args
    for n in nums:
        try:
            fetch(n)
            print(f"ok {n}")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {n}: {e}")


if __name__ == "__main__":
    main()
