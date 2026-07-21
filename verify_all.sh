#!/bin/bash
# Re-verify every claim in RESULTS.md bucket 1, from scratch.
#
# This is the script a skeptic runs. Each check is independent of the code that
# produced the result: the Python verifiers re-derive their claims with sympy and
# separate logic, and the Lean check rebuilds the proofs and prints their axiom
# dependencies (anything beyond propext / Classical.choice / Quot.sound, or any
# `sorry`, is a failure).
#
#   ./verify_all.sh          # fast tier, a few minutes
#   ./verify_all.sh --full   # also the slow bounds (458 to 1e14, 287 to 1e10)
set -u
cd "$(dirname "$0")"
PY=.venv/bin/python
FULL=${1:-}
pass=0; fail=0

say()  { printf '\n\033[1m== %s\033[0m\n' "$1"; }
ok()   { echo "   PASS: $1"; pass=$((pass+1)); }
bad()  { echo "   FAIL: $1"; fail=$((fail+1)); }

# ---------------------------------------------------------------- 647
say "[647] Erdos-Selfridge: no n in (24, B] with max_{m<n}(m+tau(m)) <= n+2"
out=$($PY problems/647/verify647.py 1000000 2>&1)
echo "$out" | grep -q "solutions with n > 24: NONE" \
  && ok "independent brute force over [2,1e6] finds nothing above 24" \
  || bad "brute force disagreed: $out"

( cd problems/647 && cc -O3 -o search647 search647.c -lm 2>/dev/null )
c_out=$(cd problems/647 && ./search647 2 1000000 | grep SOLUTION | sed 's/SOLUTION n=//' | tr '\n' ' ')
[ "$c_out" = "2 3 4 5 6 8 10 12 24 " ] \
  && ok "C search agrees exactly with the brute force on [2,1e6]" \
  || bad "C search gave: $c_out"

if [ -d problems/647/results ]; then
  b=$($PY problems/647/progress647.py 2>/dev/null | grep "contiguous verified to" | tr -dc '0-9')
  w=$($PY problems/647/progress647.py 2>/dev/null | grep -c "WINDOW TOO SMALL")
  [ "$w" = "0" ] && ok "full search: contiguous bound $b, tau window still valid" \
                 || bad "tau exceeded the locality window -- bound invalid"
fi

# ---------------------------------------------------------------- 287
say "[287] Unit fractions: no gap-<=2 set with reciprocal sum 1 below B"
B=$([ "$FULL" = "--full" ] && echo 1e8 || echo 1e6)
out=$($PY problems/287/verify287.py $B --spot 25 2>&1)
echo "$out" | grep -q "^VERIFIED" \
  && ok "standalone re-derivation (sympy) up to max(S) <= $B" \
  || bad "verifier did not confirm: $(echo "$out" | tail -3)"

( cd problems/287 && cc -O3 -o cover287 cover287.c -lm 2>/dev/null )
CB=$([ "$FULL" = "--full" ] && echo 10000000000 || echo 1000000000)
out=$(cd problems/287 && ./cover287 38 $CB 2>&1)
echo "$out" | grep -q "covered contiguously" \
  && ok "C covering, no hole: $(echo "$out" | sed 's/^# //')" \
  || bad "covering reported a hole: $out"

# ---------------------------------------------------------------- 287 Lean
say "[287] Lean: elimination + certificate_sub + certificate_add"
if command -v ~/.elan/bin/lake >/dev/null 2>&1; then
  export PATH="$HOME/.elan/bin:$PATH"
  if grep -qE '\bsorry\b|\badmit\b' ErdosFormal/ErdosFormal/Erdos287.lean; then
    bad "source contains sorry/admit"
  else
    ok "no sorry/admit in the Lean source"
  fi
  ( cd ErdosFormal && lake build >/dev/null 2>&1 ) \
    && ok "lake build succeeds" || bad "lake build failed"
  ax=$(cd ErdosFormal && lake env lean ErdosFormal/AxiomCheck.lean 2>&1)
  n_ok=$(echo "$ax" | grep -c "depends on axioms: \[propext, Classical.choice, Quot.sound\]")
  n_all=$(echo "$ax" | grep -c "depends on axioms")
  [ "$n_ok" = "3" ] && [ "$n_ok" = "$n_all" ] \
    && ok "all 3 theorems use only [propext, Classical.choice, Quot.sound]" \
    || bad "unexpected axioms: $ax"
else
  echo "   SKIP: lean/elan not installed"
fi

# ---------------------------------------------------------------- 458
say "[458] lcm inequality [1..p_{k+1}-1] < p_k [1..p_k]"
X=$([ "$FULL" = "--full" ] && echo 1e14 || echo 1e9)
out=$($PY problems/458/check458.py $X 2>&1)
echo "$out" | grep -q "violations (R >= p_k): NONE" \
  && ok "no violation for any prime gap with p_k <= $X" \
  || bad "violation reported: $(echo "$out" | tail -3)"

# ---------------------------------------------------------------- 488
say "[488] Density of multiples: |B cap [1,m]|/m < 2|B cap [1,n]|/n"
out=$($PY problems/488/search488.py --K 24 --L 3 --X 4000 2>&1)
echo "$out" | grep -q "counterexamples   : NONE" \
  && ok "no counterexample over antichains in [2,24], |A|<=3, n<m<=4000" \
  || bad "counterexample reported: $(echo "$out" | tail -3)"

# ---------------------------------------------------------------- 699
say "[699] gcd of binomial coefficients (Erdos-Szekeres)"
$PY problems/699/search699.py --selftest >/dev/null 2>&1 \
  && ok "selftest reproduces gcd(C(28,5),C(28,14)) and Sylvester-Schur" \
  || bad "selftest failed"
out=$($PY problems/699/search699.py 400 2>&1)
echo "$out" | grep -q "0 counterexamples" \
  && ok "no counterexample for n <= 400" \
  || bad "counterexample reported: $out"

# ---------------------------------------------------------------- 366
say "[366] 2-full n with n+1 3-full (and the reverse order)"
( cd problems/366 && cc -O3 -o search366 search366.c -lm 2>/dev/null )
out=$($PY problems/366/verify366.py 2>&1)
echo "$out" | grep -q "^VERIFIED" \
  && ok "recall (finds 8|9 and 12167|12168, nothing else) and precision vs sympy" \
  || bad "verifier did not confirm: $(echo "$out" | tail -4)"

# ---------------------------------------------------------------- 835
say "[835] Johnson graph chi(J(2k,k)) -- checked parts of the Steiner reduction"
out=$($PY problems/835/johnson835.py --primes 259 2>&1)
echo "$out" | grep -q "mismatches: NONE" \
  && ok "S(k-1,k,2k) admissible <=> k+1 prime, for all k <= 259" \
  || bad "mismatch found: $out"

# ----------------------------------------------------------------
printf '\n\033[1m%s\033[0m\n' "-------------------------------------------"
printf '\033[1mPASS %d   FAIL %d\033[0m\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
