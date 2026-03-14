/**
 * Anthropometric calculations — TypeScript port of utils/calculations.py
 * All skinfolds in mm, weight in kg, height/perimeters/diameters in cm.
 */

// ── Durnin & Womersley (1974) tables ─────────────────────────────────────────
// Body density = C - M × log10(Σ4 skinfolds)
// Σ4 = biceps + triceps + subscapular + iliac_crest
const DW_WOMEN: [number, number, number, number][] = [
  [17, 19, 1.1549, 0.0678],
  [20, 29, 1.1599, 0.0717],
  [30, 39, 1.1423, 0.0632],
  [40, 49, 1.1333, 0.0612],
  [50, 999, 1.1339, 0.0645],
]

const DW_MEN: [number, number, number, number][] = [
  [17, 19, 1.162, 0.063],
  [20, 29, 1.1631, 0.0632],
  [30, 39, 1.1422, 0.0544],
  [40, 49, 1.162, 0.07],
  [50, 999, 1.1715, 0.0779],
]

// ── Types ─────────────────────────────────────────────────────────────────────

export interface IsAk1Result {
  sigma4: number
  body_density: number
  fat_mass_pct: number
  fat_mass_kg: number
  lean_mass_kg: number
  sum_6_skinfolds: number | null
}

export interface SomatotypeResult {
  endo: number
  meso: number
  ecto: number
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function isMale(sex: string): boolean {
  const s = sex.toLowerCase()
  return s.includes('masculino') || s === 'm' || s === 'hombre'
}

function round(value: number, decimals: number): number {
  const f = 10 ** decimals
  return Math.round(value * f) / f
}

function validNum(v: number | null | undefined): boolean {
  return v != null && !isNaN(v) && isFinite(v)
}

// ── ISAK 1 — Durnin & Womersley (1974) ───────────────────────────────────────

/**
 * Calculates body density and fat % using Durnin & Womersley (1974).
 * Returns null if any required value is missing or invalid.
 */
export function calcIsAk1(
  biceps_mm: number | null,
  triceps_mm: number | null,
  subscapular_mm: number | null,
  iliac_crest_mm: number | null,
  weight_kg: number | null,
  age: number | null,
  sex: string,
  // Optional for sum_6 calculation
  supraspinal_mm?: number | null,
  abdominal_mm?: number | null,
  medial_thigh_mm?: number | null,
  max_calf_mm?: number | null,
): IsAk1Result | null {
  if (
    !validNum(biceps_mm) || !validNum(triceps_mm) ||
    !validNum(subscapular_mm) || !validNum(iliac_crest_mm) ||
    !validNum(weight_kg) || !validNum(age) ||
    biceps_mm! <= 0 || triceps_mm! <= 0 ||
    subscapular_mm! <= 0 || iliac_crest_mm! <= 0 ||
    weight_kg! <= 0 || age! <= 0
  ) return null

  const sigma4 = biceps_mm! + triceps_mm! + subscapular_mm! + iliac_crest_mm!
  if (sigma4 <= 0) return null

  const logS = Math.log10(sigma4)
  const table = isMale(sex) ? DW_MEN : DW_WOMEN

  let C = table[table.length - 1][2]
  let M = table[table.length - 1][3]
  for (const [minA, maxA, c, m] of table) {
    if (age! >= minA && age! <= maxA) { C = c; M = m; break }
  }

  const body_density = C - M * logS
  const fat_pct = (4.95 / body_density - 4.5) * 100
  const fat_kg = (weight_kg! * fat_pct) / 100
  const lean_kg = weight_kg! - fat_kg

  // Σ6 = triceps + subscapular + supraspinal + abdominal + medial_thigh + max_calf
  let sum6: number | null = null
  if (
    validNum(triceps_mm) && validNum(subscapular_mm) &&
    validNum(supraspinal_mm) && validNum(abdominal_mm) &&
    validNum(medial_thigh_mm) && validNum(max_calf_mm)
  ) {
    sum6 = round(
      triceps_mm! + subscapular_mm! + supraspinal_mm! +
      abdominal_mm! + medial_thigh_mm! + max_calf_mm!,
      1,
    )
  }

  return {
    sigma4: round(sigma4, 1),
    body_density: round(body_density, 4),
    fat_mass_pct: round(fat_pct, 1),
    fat_mass_kg: round(fat_kg, 2),
    lean_mass_kg: round(lean_kg, 2),
    sum_6_skinfolds: sum6,
  }
}

// ── ISAK 2 — Heath & Carter (1990) Somatotype ────────────────────────────────

/**
 * Heath & Carter (1990) somatotype.
 * Returns null if any required value is missing.
 */
export function calcSomatotype(
  height_cm: number | null,
  weight_kg: number | null,
  triceps_mm: number | null,
  subscapular_mm: number | null,
  supraspinal_mm: number | null,
  humerus_width_cm: number | null,
  femur_width_cm: number | null,
  arm_contracted_cm: number | null,
  calf_cm: number | null,
  max_calf_mm: number | null,
): SomatotypeResult | null {
  const vals = [
    height_cm, weight_kg, triceps_mm, subscapular_mm, supraspinal_mm,
    humerus_width_cm, femur_width_cm, arm_contracted_cm, calf_cm, max_calf_mm,
  ]
  if (vals.some((v) => !validNum(v) || v! <= 0)) return null

  try {
    // Endomorphy — Σ3 skinfolds corrected to 170.18 cm height
    const sigma3 = triceps_mm! + subscapular_mm! + supraspinal_mm!
    const sigma3_corr = sigma3 * (170.18 / height_cm!)
    const endo =
      -0.7182 +
      0.1451 * sigma3_corr -
      0.00068 * sigma3_corr ** 2 +
      0.0000014 * sigma3_corr ** 3

    // Mesomorphy — corrected arm and calf perimeters
    const arm_corr = arm_contracted_cm! - triceps_mm! / 10
    const calf_corr = calf_cm! - max_calf_mm! / 10
    const meso =
      0.858 * humerus_width_cm! +
      0.601 * femur_width_cm! +
      0.188 * arm_corr +
      0.161 * calf_corr -
      height_cm! * 0.131 +
      4.5

    // Ectomorphy via Height-Weight Ratio
    const hwr = height_cm! / Math.cbrt(weight_kg!)
    let ecto: number
    if (hwr > 40.75) ecto = 0.732 * hwr - 28.58
    else if (hwr > 38.25) ecto = 0.463 * hwr - 17.63
    else ecto = 0.1

    return {
      endo: round(Math.max(0.1, endo), 2),
      meso: round(Math.max(0.1, meso), 2),
      ecto: round(Math.max(0.1, ecto), 2),
    }
  } catch {
    return null
  }
}

// ── Área Muscular del Brazo ───────────────────────────────────────────────────

/**
 * AMB = (C - π × T/10)² / (4π)
 * C = perím. brazo relajado (cm), T = tríceps (mm)
 */
export function calcArmMuscleArea(
  arm_relaxed_cm: number | null,
  triceps_mm: number | null,
): number | null {
  if (!validNum(arm_relaxed_cm) || !validNum(triceps_mm)) return null
  const musclePerim = arm_relaxed_cm! - Math.PI * (triceps_mm! / 10)
  if (musclePerim <= 0) return null
  return round(musclePerim ** 2 / (4 * Math.PI), 2)
}

// ── Índice Cintura/Talla ──────────────────────────────────────────────────────

export function calcWaistHeightRatio(
  waist_cm: number | null,
  height_cm: number | null,
): number | null {
  if (!validNum(waist_cm) || !validNum(height_cm) || height_cm! <= 0) return null
  return round(waist_cm! / height_cm!, 3)
}

export function whtrCategory(ratio: number): string {
  if (ratio < 0.5) return 'Saludable'
  if (ratio < 0.6) return 'Sobrepeso'
  return 'Obesidad'
}

// ── IMC ───────────────────────────────────────────────────────────────────────

export function calcBmi(weight_kg: number | null, height_cm: number | null): number | null {
  if (!validNum(weight_kg) || !validNum(height_cm) || height_cm! <= 0) return null
  return round(weight_kg! / (height_cm! / 100) ** 2, 1)
}

export function bmiCategory(bmi: number): string {
  if (bmi < 18.5) return 'Bajo peso'
  if (bmi < 25.0) return 'Normal'
  if (bmi < 30.0) return 'Sobrepeso'
  if (bmi < 35.0) return 'Obesidad I'
  if (bmi < 40.0) return 'Obesidad II'
  return 'Obesidad III'
}

// ── Clasificación % grasa ─────────────────────────────────────────────────────

export function fatCategory(pct: number, sex: string): string {
  if (isMale(sex)) {
    if (pct < 6)  return 'Esencial'
    if (pct < 14) return 'Atleta'
    if (pct < 18) return 'En forma'
    if (pct < 25) return 'Aceptable'
    return 'Obesidad'
  } else {
    if (pct < 14) return 'Esencial'
    if (pct < 21) return 'Atleta'
    if (pct < 25) return 'En forma'
    if (pct < 32) return 'Aceptable'
    return 'Obesidad'
  }
}
