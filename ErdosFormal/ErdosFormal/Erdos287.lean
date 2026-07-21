/-
Erdős problem 287 — the ELIMINATION lemma.
https://www.erdosproblems.com/287

    Let k ≥ 2. For distinct integers 1 < n₁ < ... < n_k with 1 = ∑ 1/nᵢ,
    must max(n_{i+1} - nᵢ) ≥ 3 ?

The computational search in `problems/287` rules out counterexamples by
excluding two CONSECUTIVE integers from any such set, using this lemma. It is
formalised here so that the search result does not rest on a prose argument.

The proof deliberately avoids p-adic valuations. Rather than the lcm of the
whole set it uses the explicit COMMON multiple D = 2·p·L, where L is the lcm of
the members NOT divisible by p. Then every term D/n is visibly a multiple of p
except the two special ones, and everything stays elementary ℕ arithmetic.
-/
import Mathlib

open Finset

namespace Erdos287

/-- A prime dividing none of a finite set's members does not divide their lcm. -/
lemma prime_not_dvd_lcm {p : ℕ} (hp : p.Prime) :
    ∀ (T : Finset ℕ), (∀ n ∈ T, ¬ p ∣ n) → ¬ p ∣ T.lcm id := by
  classical
  intro T
  induction T using Finset.induction with
  | empty =>
      intro _ hdvd
      exact hp.one_lt.ne' (Nat.dvd_one.mp (by simpa using hdvd))
  | insert a T ha ih =>
      intro h hdvd
      rw [Finset.lcm_insert] at hdvd
      have hmul : p ∣ a * T.lcm id := hdvd.trans (Nat.lcm_dvd_mul a (T.lcm id))
      rcases (Nat.Prime.dvd_mul hp).1 hmul with h1 | h2
      · exact h a (Finset.mem_insert_self a T) h1
      · exact ih (fun n hn => h n (Finset.mem_insert_of_mem hn)) h2

/-- Clearing denominators: if every member of `S` divides `D`, then `∑ 1/n = 1`
becomes the ℕ-identity `∑ D/n = D`. -/
lemma sum_div_eq {S : Finset ℕ} {D : ℕ}
    (hdvd : ∀ n ∈ S, n ∣ D) (hpos : ∀ n ∈ S, 0 < n)
    (hsum : ∑ n ∈ S, (1 : ℚ) / n = 1) :
    ∑ n ∈ S, D / n = D := by
  have key : ((∑ n ∈ S, D / n : ℕ) : ℚ) = (D : ℚ) := by
    push_cast
    have h1 : ∀ n ∈ S, ((D / n : ℕ) : ℚ) = (D : ℚ) * (1 / (n : ℚ)) := by
      intro n hn
      rw [Nat.cast_div (hdvd n hn) (by exact_mod_cast (hpos n hn).ne')]
      ring
    rw [Finset.sum_congr rfl h1, ← Finset.mul_sum, hsum, mul_one]
  exact_mod_cast key

/-- **Elimination.** Let `S` be a finite set of integers ≥ 2 whose reciprocals
sum to `1`. If `p ≥ 5` is prime and the only members of `S` divisible by `p` lie
in `{p, 2p}`, then neither `p` nor `2p` belongs to `S`.

This is what the search uses: for a certificate prime `p` it excludes `2p`, and
applying the lemma again to the prime `q = 2p ± 1` (whose only multiple ≤ max S
is `q` itself) excludes `q`. Those two are consecutive integers. -/
theorem elimination
    (S : Finset ℕ) (hS2 : ∀ n ∈ S, 2 ≤ n)
    (hsum : ∑ n ∈ S, (1 : ℚ) / n = 1)
    (p : ℕ) (hp : p.Prime) (hp5 : 5 ≤ p)
    (hmul : ∀ n ∈ S, p ∣ n → n = p ∨ n = 2 * p) :
    p ∉ S ∧ 2 * p ∉ S := by
  classical
  have hppos : 0 < p := hp.pos
  obtain ⟨B, hB⟩ : ∃ B, B = S.filter (fun n => ¬ p ∣ n) := ⟨_, rfl⟩
  obtain ⟨L, hL⟩ : ∃ L, L = B.lcm id := ⟨_, rfl⟩
  obtain ⟨D, hD⟩ : ∃ D, D = 2 * p * L := ⟨_, rfl⟩

  have hpL : ¬ p ∣ L := by
    rw [hL]
    refine prime_not_dvd_lcm hp B ?_
    intro n hn
    rw [hB] at hn
    exact (Finset.mem_filter.mp hn).2
  have hposS : ∀ n ∈ S, 0 < n := fun n hn => lt_of_lt_of_le two_pos (hS2 n hn)

  have hdvdD : ∀ n ∈ S, n ∣ D := by
    intro n hn
    by_cases hpn : p ∣ n
    · rcases hmul n hn hpn with rfl | rfl
      · exact ⟨2 * L, by rw [hD]; ring⟩
      · exact ⟨L, by rw [hD]⟩
    · have hnB : n ∈ B := by rw [hB]; exact Finset.mem_filter.mpr ⟨hn, hpn⟩
      have : n ∣ L := by rw [hL]; exact Finset.dvd_lcm hnB
      exact this.trans ⟨2 * p, by rw [hD]; ring⟩

  have hnat : ∑ n ∈ S, D / n = D := sum_div_eq hdvdD hposS hsum

  have hsplit : (∑ n ∈ S.filter (fun n => p ∣ n), D / n)
              + (∑ n ∈ B, D / n) = D := by
    rw [hB, Finset.sum_filter_add_sum_filter_not S (fun n => p ∣ n)]
    exact hnat

  -- each term over B is a multiple of p, since n ∣ L there
  have hpB : p ∣ ∑ n ∈ B, D / n := by
    refine Finset.dvd_sum ?_
    intro n hn
    have hnS : n ∈ S := by rw [hB] at hn; exact (Finset.mem_filter.mp hn).1
    have hn0 : 0 < n := hposS n hnS
    obtain ⟨c, hc⟩ : n ∣ L := by rw [hL]; exact Finset.dvd_lcm hn
    have hstep : D / n = 2 * p * c := by
      rw [hD, hc, show 2 * p * (n * c) = n * (2 * p * c) by ring,
          Nat.mul_div_cancel_left _ hn0]
    rw [hstep]
    exact ⟨2 * c, by ring⟩

  have hpA : p ∣ ∑ n ∈ S.filter (fun n => p ∣ n), D / n := by
    have hpD : p ∣ D := ⟨2 * L, by rw [hD]; ring⟩
    have hsum2 : p ∣ (∑ n ∈ S.filter (fun n => p ∣ n), D / n)
                   + (∑ n ∈ B, D / n) := by rw [hsplit]; exact hpD
    exact (Nat.dvd_add_iff_left hpB).mpr hsum2

  have hne : p ≠ 2 * p := by omega
  have hDp : D / p = 2 * L := by
    rw [hD, show 2 * p * L = p * (2 * L) by ring, Nat.mul_div_cancel_left _ hppos]
  have hD2p : D / (2 * p) = L := by
    rw [hD, Nat.mul_div_cancel_left _ (by omega : 0 < 2 * p)]

  -- p ∣ c * L with 1 ≤ c ≤ 3 < p is impossible
  have hkill : ∀ c : ℕ, 0 < c → c ≤ 3 → ¬ p ∣ c * L := by
    intro c hc0 hc3 hdvd
    rcases (Nat.Prime.dvd_mul hp).1 hdvd with h | h
    · have := Nat.le_of_dvd hc0 h; omega
    · exact hpL h

  have hboth : p ∈ S → 2 * p ∈ S → False := by
    intro h1 h2
    have hset : S.filter (fun n => p ∣ n) = ({p, 2 * p} : Finset ℕ) := by
      apply Finset.Subset.antisymm
      · intro n hn
        obtain ⟨hnS, hpn⟩ := Finset.mem_filter.mp hn
        rcases hmul n hnS hpn with rfl | rfl <;> simp
      · intro n hn
        simp only [Finset.mem_insert, Finset.mem_singleton] at hn
        rcases hn with rfl | rfl
        · exact Finset.mem_filter.mpr ⟨h1, dvd_refl _⟩
        · exact Finset.mem_filter.mpr ⟨h2, ⟨2, by ring⟩⟩
    rw [hset, Finset.sum_pair hne, hDp, hD2p,
        show 2 * L + L = 3 * L by ring] at hpA
    exact hkill 3 (by norm_num) (by norm_num) hpA

  have honly1 : p ∈ S → 2 * p ∉ S → False := by
    intro h1 h2
    have hset : S.filter (fun n => p ∣ n) = ({p} : Finset ℕ) := by
      apply Finset.Subset.antisymm
      · intro n hn
        obtain ⟨hnS, hpn⟩ := Finset.mem_filter.mp hn
        rcases hmul n hnS hpn with rfl | rfl
        · simp
        · exact absurd hnS h2
      · intro n hn
        simp only [Finset.mem_singleton] at hn
        subst hn
        exact Finset.mem_filter.mpr ⟨h1, dvd_refl _⟩
    rw [hset, Finset.sum_singleton, hDp] at hpA
    exact hkill 2 (by norm_num) (by norm_num) hpA

  have honly2 : p ∉ S → 2 * p ∈ S → False := by
    intro h1 h2
    have hset : S.filter (fun n => p ∣ n) = ({2 * p} : Finset ℕ) := by
      apply Finset.Subset.antisymm
      · intro n hn
        obtain ⟨hnS, hpn⟩ := Finset.mem_filter.mp hn
        rcases hmul n hnS hpn with rfl | rfl
        · exact absurd hnS h1
        · simp
      · intro n hn
        simp only [Finset.mem_singleton] at hn
        subst hn
        exact Finset.mem_filter.mpr ⟨h2, ⟨2, by ring⟩⟩
    rw [hset, Finset.sum_singleton, hD2p, show L = 1 * L by ring] at hpA
    exact hkill 1 (by norm_num) (by norm_num) hpA

  refine ⟨fun h1 => ?_, fun h2 => ?_⟩
  · by_cases h2 : 2 * p ∈ S
    · exact hboth h1 h2
    · exact honly1 h1 h2
  · by_cases h1 : p ∈ S
    · exact hboth h1 h2
    · exact honly2 h1 h2

end Erdos287
