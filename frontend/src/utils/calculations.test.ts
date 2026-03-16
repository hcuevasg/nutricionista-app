import { describe, it, expect } from 'vitest'
import { calcIsAk1, calcSomatotype, calcBmi, calcWaistHeightRatio } from './calculations'

// ── calcBmi ───────────────────────────────────────────────────────────────────

describe('calcBmi', () => {
  it('calculates BMI correctly', () => {
    // 70kg / (1.70m)^2 = 24.22
    expect(calcBmi(70, 170)).toBeCloseTo(24.22, 1)
  })

  it('returns null when weight is null', () => {
    expect(calcBmi(null, 170)).toBeNull()
  })

  it('returns null when height is null', () => {
    expect(calcBmi(70, null)).toBeNull()
  })

  it('returns null when height is zero', () => {
    expect(calcBmi(70, 0)).toBeNull()
  })
})

// ── calcWaistHeightRatio ──────────────────────────────────────────────────────

describe('calcWaistHeightRatio', () => {
  it('calculates WHTR correctly', () => {
    expect(calcWaistHeightRatio(80, 170)).toBeCloseTo(0.47, 2)
  })

  it('returns null with missing values', () => {
    expect(calcWaistHeightRatio(null, 170)).toBeNull()
    expect(calcWaistHeightRatio(80, null)).toBeNull()
    expect(calcWaistHeightRatio(80, 0)).toBeNull()
  })
})

// ── calcIsAk1 — Durnin & Womersley (1974) ────────────────────────────────────

describe('calcIsAk1', () => {
  // Reference values for a 25-year-old woman: biceps=8, triceps=15, subscapular=12, iliac_crest=10
  // Sigma4 = 45mm. Using DW_WOMEN 20-29: C=1.1599, M=0.0717
  // body_density = 1.1599 - 0.0717 * log10(45) = 1.1599 - 0.0717 * 1.6532 = 1.0413
  // fat% = (4.95 / 1.0413 - 4.5) * 100 ≈ 25.5%
  it('calculates body density and fat% for a woman aged 25', () => {
    const result = calcIsAk1(8, 15, 12, 10, 65, 25, 'F')
    expect(result).not.toBeNull()
    expect(result!.sigma4).toBe(45)
    expect(result!.body_density).toBeCloseTo(1.041, 2)
    expect(result!.fat_mass_pct).toBeGreaterThan(20)
    expect(result!.fat_mass_pct).toBeLessThan(35)
    expect(result!.fat_mass_kg).toBeCloseTo((65 * result!.fat_mass_pct) / 100, 1)
    expect(result!.lean_mass_kg).toBeCloseTo(65 - result!.fat_mass_kg, 1)
  })

  it('calculates for a male aged 30', () => {
    const result = calcIsAk1(6, 10, 11, 9, 80, 30, 'M')
    expect(result).not.toBeNull()
    expect(result!.sigma4).toBe(36)
    expect(result!.fat_mass_pct).toBeGreaterThan(10)
    expect(result!.fat_mass_pct).toBeLessThan(25)
  })

  it('calculates sum_6_skinfolds when all 6 values provided', () => {
    const result = calcIsAk1(8, 15, 12, 10, 65, 25, 'F', 9, 11, 13, 8)
    expect(result).not.toBeNull()
    expect(result!.sum_6_skinfolds).toBe(15 + 12 + 9 + 11 + 13 + 8) // triceps + subscapular + supra + abd + medialThigh + calf
  })

  it('returns null_6 when optional skinfolds are missing', () => {
    const result = calcIsAk1(8, 15, 12, 10, 65, 25, 'F')
    expect(result).not.toBeNull()
    expect(result!.sum_6_skinfolds).toBeNull()
  })

  it('returns null when any required value is missing', () => {
    expect(calcIsAk1(null, 15, 12, 10, 65, 25, 'F')).toBeNull()
    expect(calcIsAk1(8, null, 12, 10, 65, 25, 'F')).toBeNull()
    expect(calcIsAk1(8, 15, 12, 10, null, 25, 'F')).toBeNull()
    expect(calcIsAk1(8, 15, 12, 10, 65, null, 'F')).toBeNull()
  })

  it('returns null when any value is zero or negative', () => {
    expect(calcIsAk1(0, 15, 12, 10, 65, 25, 'F')).toBeNull()
    expect(calcIsAk1(8, 15, 12, 10, 0, 25, 'F')).toBeNull()
    expect(calcIsAk1(8, 15, 12, 10, 65, 0, 'F')).toBeNull()
  })
})

// ── calcSomatotype — Heath & Carter (1990) ────────────────────────────────────

describe('calcSomatotype', () => {
  it('returns a result with endo, meso, ecto for valid inputs', () => {
    const result = calcSomatotype(
      170,   // height_cm
      70,    // weight_kg
      15,    // triceps_mm
      12,    // subscapular_mm
      10,    // supraspinal_mm
      6.5,   // humerus_width_cm
      9.5,   // femur_width_cm
      32,    // arm_contracted_cm
      36,    // calf_cm
      7,     // max_calf_mm
    )
    expect(result).not.toBeNull()
    expect(result!.endo).toBeGreaterThan(0)
    expect(result!.meso).toBeGreaterThan(0)
    expect(result!.ecto).toBeGreaterThan(0)
    // All components should be in reasonable range (0.1–12)
    expect(result!.endo).toBeLessThan(12)
    expect(result!.meso).toBeLessThan(12)
    expect(result!.ecto).toBeLessThan(12)
  })

  it('returns null when any required value is null', () => {
    expect(calcSomatotype(null, 70, 15, 12, 10, 6.5, 9.5, 32, 36, 7)).toBeNull()
    expect(calcSomatotype(170, null, 15, 12, 10, 6.5, 9.5, 32, 36, 7)).toBeNull()
  })

  it('returns null when any value is zero', () => {
    expect(calcSomatotype(0, 70, 15, 12, 10, 6.5, 9.5, 32, 36, 7)).toBeNull()
  })
})
