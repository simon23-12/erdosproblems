#!/bin/bash
# Drive search647 over [START, END) in CHUNK-sized pieces, WORKERS at a time.
#
# Each chunk writes results/<L>.out on success.  A chunk is only counted as
# verified if its file exists AND ends with a "# range ... done" line, so a
# killed worker never silently turns into claimed coverage.  progress647.py
# turns the set of finished chunks into the largest CONTIGUOUS verified bound.
#
#   ./run647.sh [START] [END] [CHUNK] [WORKERS]
set -u
cd "$(dirname "$0")"

START=${1:-10000000}          # 10^7 (below this, verify647.py covers it)
END=${2:-10000000000000}      # 10^13
CHUNK=${3:-10000000000}       # 10^10
WORKERS=${4:-8}

mkdir -p results
# NB: BSD seq renders large integers in scientific notation, so build the
# chunk list in python instead.
../../.venv/bin/python -c "
import sys
start, end, chunk = (int(x) for x in sys.argv[1:])
L = start
while L < end:
    print(L)
    L += chunk
" "$START" "$END" "$CHUNK" > results/chunks.txt

run_one() {
    L=$1; CHUNK=$2; END=$3
    R=$((L + CHUNK)); [ "$R" -gt "$END" ] && R=$END
    OUT="results/${L}.out"
    [ -s "$OUT" ] && grep -q '^# range' "$OUT" && exit 0     # already done
    ./search647 "$L" "$R" > "$OUT.tmp" 2>&1 && mv "$OUT.tmp" "$OUT"
}
export -f run_one

xargs -P "$WORKERS" -I{} bash -c 'run_one {} '"$CHUNK $END" < results/chunks.txt
echo "run647.sh finished at $(date)"
