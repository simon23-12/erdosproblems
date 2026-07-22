#!/bin/bash
# Drive search475 over the whole open window t in [21, p-4] for a given prime,
# chunked by a fixed 3-element prefix so the work parallelises evenly.
#
# Chunking by the single smallest element is NOT good enough at p=37: the chunk
# (t=21, first=1) alone holds C(35,20) = 3.2e9 subsets and would set the
# wall-clock time on its own. A 3-element prefix caps the largest chunk at
# C(33,18) = 1.17e9, below the 1/10-of-total that perfect balance would give.
#
# Each chunk writes results/p<P>_t<T>_<prefix>.out and counts only if the file
# carries the terminal "# p=... checked=..." line, so a killed chunk shows up as
# MISSING rather than as silently reduced coverage.
#
#   ./run475.sh 37 [workers] [prefix_len]
set -u
cd "$(dirname "$0")"
P=${1:?usage: ./run475.sh <prime> [workers] [prefix_len]}
W=${2:-10}
L=${3:-3}
mkdir -p results

../../.venv/bin/python - "$P" "$L" > results/chunks_$P.txt <<'EOF'
import sys
from itertools import combinations
p, L = int(sys.argv[1]), int(sys.argv[2])
for t in range(21, p - 3):
    ell = min(L, t)
    # the prefix takes `ell` of the t elements; the remaining t-ell must still
    # fit strictly above the last prefix element
    for pre in combinations(range(1, p), ell):
        if p - 1 - pre[-1] >= t - ell:
            print(t, ",".join(map(str, pre)))
EOF
echo "chunks: $(wc -l < results/chunks_$P.txt)"

run_one() {
  P=$1; T=$2; PRE=$3
  OUT="results/p${P}_t${T}_${PRE//,/-}.out"
  [ -s "$OUT" ] && grep -q '^# p=' "$OUT" && exit 0
  ./search475 "$P" "$T" "$PRE" > "$OUT.raw" 2>&1 && mv "$OUT.raw" "$OUT"
}
export -f run_one

xargs -P "$W" -n2 bash -c 'run_one '"$P"' "$@"' _ < results/chunks_$P.txt
echo "run475.sh finished at $(date)"
