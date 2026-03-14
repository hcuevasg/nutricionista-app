import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'
import {
  calcIsAk1, calcSomatotype, calcArmMuscleArea, calcWaistHeightRatio,
  calcBmi, bmiCategory, fatCategory, whtrCategory,
  type IsAk1Result, type SomatotypeResult,
} from '../utils/calculations'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Patient { id: number; name: string; birth_date?: string; sex: string }

interface Evaluation {
  id: number; date: string; isak_level: string
  weight_kg?: number; height_cm?: number; waist_cm?: number
  fat_mass_pct?: number; fat_mass_kg?: number; lean_mass_kg?: number
  body_density?: number; sum_6_skinfolds?: number
  somatotype_endo?: number; somatotype_meso?: number; somatotype_ecto?: number
  created_at: string
}

type IsakLevel = 'ISAK 1' | 'ISAK 2'

interface FormState {
  date: string; isak_level: IsakLevel
  // Básicos
  weight_kg: string; height_cm: string; waist_cm: string
  // Perímetros — ISAK 1+2
  arm_relaxed_cm: string; arm_contracted_cm: string; hip_glute_cm: string
  thigh_max_cm: string; thigh_mid_cm: string; calf_cm: string
  // Pliegues — ISAK 1+2
  triceps_mm: string; subscapular_mm: string; biceps_mm: string; iliac_crest_mm: string
  supraspinal_mm: string; abdominal_mm: string; medial_thigh_mm: string; max_calf_mm: string
  // Pliegues adicionales — ISAK 2
  pectoral_mm: string; axillary_mm: string; front_thigh_mm: string
  // Perímetros adicionales — ISAK 2
  head_cm: string; neck_cm: string; chest_cm: string; ankle_min_cm: string
  // Diámetros óseos — ISAK 2
  humerus_width_cm: string; femur_width_cm: string; biacromial_cm: string
  biiliocrestal_cm: string; ap_chest_cm: string; transv_chest_cm: string
  foot_length_cm: string; wrist_cm: string; ankle_bimalleolar_cm: string
  // Longitudes — ISAK 2
  acromion_radial_cm: string; radial_styloid_cm: string
  iliospinal_height_cm: string; trochanter_tibial_cm: string
}

const EMPTY_FORM: FormState = {
  date: new Date().toISOString().split('T')[0], isak_level: 'ISAK 1',
  weight_kg: '', height_cm: '', waist_cm: '',
  arm_relaxed_cm: '', arm_contracted_cm: '', hip_glute_cm: '',
  thigh_max_cm: '', thigh_mid_cm: '', calf_cm: '',
  triceps_mm: '', subscapular_mm: '', biceps_mm: '', iliac_crest_mm: '',
  supraspinal_mm: '', abdominal_mm: '', medial_thigh_mm: '', max_calf_mm: '',
  pectoral_mm: '', axillary_mm: '', front_thigh_mm: '',
  head_cm: '', neck_cm: '', chest_cm: '', ankle_min_cm: '',
  humerus_width_cm: '', femur_width_cm: '', biacromial_cm: '',
  biiliocrestal_cm: '', ap_chest_cm: '', transv_chest_cm: '',
  foot_length_cm: '', wrist_cm: '', ankle_bimalleolar_cm: '',
  acromion_radial_cm: '', radial_styloid_cm: '',
  iliospinal_height_cm: '', trochanter_tibial_cm: '',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function calcAge(bd?: string): number | null {
  if (!bd) return null
  const d = new Date(bd)
  if (isNaN(d.getTime())) return null
  const t = new Date()
  let age = t.getFullYear() - d.getFullYear()
  if (t.getMonth() < d.getMonth() || (t.getMonth() === d.getMonth() && t.getDate() < d.getDate())) age--
  return age >= 0 ? age : null
}

function pf(v: string): number | null {
  const n = parseFloat(v); return isNaN(n) ? null : n
}

function fmt(v: number | null | undefined, d = 1): string {
  return v != null ? v.toFixed(d) : '—'
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function IsAkPage() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()

  const [patient, setPatient] = useState<Patient | null>(null)
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [result, setResult] = useState<IsAk1Result | null>(null)
  const [soma, setSoma] = useState<SomatotypeResult | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  useEffect(() => {
    if (!token || !id) return
    Promise.all([
      fetch(`${API}/patients/${id}`, { headers: H }).then(r => r.json()),
      fetch(`${API}/anthropometrics/${id}`, { headers: H }).then(r => r.json()),
    ])
      .then(([pat, evals]) => { setPatient(pat); setEvaluations(Array.isArray(evals) ? evals : []) })
      .catch(() => setError('Error al cargar datos'))
      .finally(() => setLoadingHistory(false))
  }, [id, token])

  // Auto-calculate ISAK 1 results on field change
  useEffect(() => {
    if (!patient) return
    const age = calcAge(patient.birth_date)
    setResult(calcIsAk1(
      pf(form.biceps_mm), pf(form.triceps_mm), pf(form.subscapular_mm), pf(form.iliac_crest_mm),
      pf(form.weight_kg), age, patient.sex,
      pf(form.supraspinal_mm), pf(form.abdominal_mm), pf(form.medial_thigh_mm), pf(form.max_calf_mm),
    ))
  }, [
    form.biceps_mm, form.triceps_mm, form.subscapular_mm, form.iliac_crest_mm,
    form.weight_kg, form.supraspinal_mm, form.abdominal_mm, form.medial_thigh_mm, form.max_calf_mm,
    patient,
  ])

  // Auto-calculate ISAK 2 somatotype
  useEffect(() => {
    if (form.isak_level !== 'ISAK 2') { setSoma(null); return }
    setSoma(calcSomatotype(
      pf(form.height_cm), pf(form.weight_kg),
      pf(form.triceps_mm), pf(form.subscapular_mm), pf(form.supraspinal_mm),
      pf(form.humerus_width_cm), pf(form.femur_width_cm),
      pf(form.arm_contracted_cm), pf(form.calf_cm), pf(form.max_calf_mm),
    ))
  }, [
    form.isak_level, form.height_cm, form.weight_kg,
    form.triceps_mm, form.subscapular_mm, form.supraspinal_mm,
    form.humerus_width_cm, form.femur_width_cm, form.arm_contracted_cm,
    form.calf_cm, form.max_calf_mm,
  ])

  const set = (f: keyof FormState, v: string) => setForm(p => ({ ...p, [f]: v }))

  const closeForm = () => { setShowForm(false); setForm(EMPTY_FORM); setResult(null); setSoma(null) }

  const handleSave = async () => {
    if (!result) { setError('Completa los 4 pliegues D&W (*) y el peso para guardar'); return }
    setSaving(true); setError(null)

    const arm = pf(form.arm_relaxed_cm)
    const tri = pf(form.triceps_mm)

    const payload: Record<string, unknown> = {
      date: form.date, isak_level: form.isak_level,
      weight_kg: pf(form.weight_kg), height_cm: pf(form.height_cm), waist_cm: pf(form.waist_cm),
      // Perímetros básicos
      arm_relaxed_cm: pf(form.arm_relaxed_cm), arm_contracted_cm: pf(form.arm_contracted_cm),
      hip_glute_cm: pf(form.hip_glute_cm), thigh_max_cm: pf(form.thigh_max_cm),
      thigh_mid_cm: pf(form.thigh_mid_cm), calf_cm: pf(form.calf_cm),
      // Pliegues
      triceps_mm: tri, subscapular_mm: pf(form.subscapular_mm),
      biceps_mm: pf(form.biceps_mm), iliac_crest_mm: pf(form.iliac_crest_mm),
      supraspinal_mm: pf(form.supraspinal_mm), abdominal_mm: pf(form.abdominal_mm),
      medial_thigh_mm: pf(form.medial_thigh_mm), max_calf_mm: pf(form.max_calf_mm),
      // Calculados ISAK 1
      body_density: result.body_density, fat_mass_pct: result.fat_mass_pct,
      fat_mass_kg: result.fat_mass_kg, lean_mass_kg: result.lean_mass_kg,
      sum_6_skinfolds: result.sum_6_skinfolds,
    }

    if (form.isak_level === 'ISAK 2') {
      Object.assign(payload, {
        pectoral_mm: pf(form.pectoral_mm), axillary_mm: pf(form.axillary_mm),
        front_thigh_mm: pf(form.front_thigh_mm),
        head_cm: pf(form.head_cm), neck_cm: pf(form.neck_cm),
        chest_cm: pf(form.chest_cm), ankle_min_cm: pf(form.ankle_min_cm),
        humerus_width_cm: pf(form.humerus_width_cm), femur_width_cm: pf(form.femur_width_cm),
        biacromial_cm: pf(form.biacromial_cm), biiliocrestal_cm: pf(form.biiliocrestal_cm),
        ap_chest_cm: pf(form.ap_chest_cm), transv_chest_cm: pf(form.transv_chest_cm),
        foot_length_cm: pf(form.foot_length_cm), wrist_cm: pf(form.wrist_cm),
        ankle_bimalleolar_cm: pf(form.ankle_bimalleolar_cm),
        acromion_radial_cm: pf(form.acromion_radial_cm),
        radial_styloid_cm: pf(form.radial_styloid_cm),
        iliospinal_height_cm: pf(form.iliospinal_height_cm),
        trochanter_tibial_cm: pf(form.trochanter_tibial_cm),
        somatotype_endo: soma?.endo ?? null,
        somatotype_meso: soma?.meso ?? null,
        somatotype_ecto: soma?.ecto ?? null,
      })
    }

    try {
      const res = await fetch(`${API}/anthropometrics?patient_id=${id}`, {
        method: 'POST', headers: H, body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d.detail ?? `Error ${res.status}`)
      }
      const saved = await res.json()
      setEvaluations(prev => [saved, ...prev])
      closeForm()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const age = patient ? calcAge(patient.birth_date) : null
  const bmi = calcBmi(pf(form.weight_kg), pf(form.height_cm))
  const whtr = calcWaistHeightRatio(pf(form.waist_cm), pf(form.height_cm))
  const amb = calcArmMuscleArea(pf(form.arm_relaxed_cm), pf(form.triceps_mm))
  const difBrBc = pf(form.arm_contracted_cm) != null && pf(form.arm_relaxed_cm) != null
    ? Math.round(((pf(form.arm_contracted_cm)! - pf(form.arm_relaxed_cm)!) + Number.EPSILON) * 10) / 10
    : null

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <Layout title={`ISAK — ${patient?.name ?? '...'}`}>
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <Link to={`/patients/${id}`} className="hover:text-primary">{patient?.name ?? `Paciente ${id}`}</Link>
        <span>/</span>
        <span className="text-primary font-medium">Evaluaciones ISAK</span>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>
      )}

      {showForm ? (
        <div className="bg-white rounded-lg shadow p-6 mb-6 space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-bold text-primary">Nueva Evaluación</h3>
            <button onClick={closeForm} className="text-text-muted hover:text-gray-700 text-sm">Cancelar</button>
          </div>

          {!patient?.birth_date && (
            <div className="bg-yellow-50 border border-yellow-300 text-yellow-800 px-4 py-2 rounded text-sm">
              El paciente no tiene fecha de nacimiento — no se puede calcular % grasa.{' '}
              <Link to={`/patients/${id}/edit`} className="underline font-medium">Editar paciente</Link>
            </div>
          )}

          {/* ISAK level selector */}
          <div className="flex gap-3">
            {(['ISAK 1', 'ISAK 2'] as IsakLevel[]).map(level => (
              <button key={level} type="button" onClick={() => set('isak_level', level)}
                className={`px-6 py-2 rounded-full text-sm font-medium border transition-colors ${
                  form.isak_level === level
                    ? 'bg-primary text-white border-primary'
                    : 'bg-white text-text-muted border-border hover:border-primary'
                }`}>
                {level}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* ── LEFT: inputs ── */}
            <div className="space-y-5">

              {/* Datos básicos */}
              <Section title="Datos básicos">
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Fecha sesión *" value={form.date} onChange={v => set('date', v)} type="date" cols={2} />
                  <Field label="Peso (kg)" value={form.weight_kg} onChange={v => set('weight_kg', v)} placeholder="70.0" />
                  <Field label="Talla (cm)" value={form.height_cm} onChange={v => set('height_cm', v)} placeholder="170.0" />
                  <Field label="Circ. cintura mínima (cm)" value={form.waist_cm} onChange={v => set('waist_cm', v)} placeholder="80.0" cols={2} />
                </div>
              </Section>

              {/* Perímetros */}
              <Section title="Perímetros (cm)">
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Brazo relajado (BR)" value={form.arm_relaxed_cm} onChange={v => set('arm_relaxed_cm', v)} />
                  <Field label="Brazo contraído (BC)" value={form.arm_contracted_cm} onChange={v => set('arm_contracted_cm', v)} />
                  <Field label='Cadera "glúteo"' value={form.hip_glute_cm} onChange={v => set('hip_glute_cm', v)} />
                  <Field label="Muslo máximo" value={form.thigh_max_cm} onChange={v => set('thigh_max_cm', v)} />
                  <Field label="Muslo medio" value={form.thigh_mid_cm} onChange={v => set('thigh_mid_cm', v)} />
                  <Field label="Pantorrilla" value={form.calf_cm} onChange={v => set('calf_cm', v)} />
                </div>
              </Section>

              {/* Pliegues cutáneos */}
              <Section title="Pliegues cutáneos (mm)">
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Tríceps (D&W *)" value={form.triceps_mm} onChange={v => set('triceps_mm', v)} highlight />
                  <Field label="Subescapular (D&W *)" value={form.subscapular_mm} onChange={v => set('subscapular_mm', v)} highlight />
                  <Field label="Bíceps (D&W *)" value={form.biceps_mm} onChange={v => set('biceps_mm', v)} highlight />
                  <Field label="Cresta iliaca (D&W *)" value={form.iliac_crest_mm} onChange={v => set('iliac_crest_mm', v)} highlight />
                  <Field label="Supraespinal (Σ6 *)" value={form.supraspinal_mm} onChange={v => set('supraspinal_mm', v)} />
                  <Field label="Abdominal (Σ6 *)" value={form.abdominal_mm} onChange={v => set('abdominal_mm', v)} />
                  <Field label="Muslo medial (Σ6 *)" value={form.medial_thigh_mm} onChange={v => set('medial_thigh_mm', v)} />
                  <Field label="Pantorrilla máx. (Σ6 *)" value={form.max_calf_mm} onChange={v => set('max_calf_mm', v)} />
                </div>
                <p className="text-xs text-text-muted mt-1">
                  D&W * = Durnin &amp; Womersley · Σ6 * = Suma 6 pliegues
                </p>
              </Section>

              {/* ISAK 2 extra */}
              {form.isak_level === 'ISAK 2' && (
                <>
                  <Section title="Pliegues adicionales (mm) — ISAK 2">
                    <div className="grid grid-cols-2 gap-3">
                      <Field label="Pectoral (tórax)" value={form.pectoral_mm} onChange={v => set('pectoral_mm', v)} />
                      <Field label="Axilar medio" value={form.axillary_mm} onChange={v => set('axillary_mm', v)} />
                      <Field label="Muslo anterior" value={form.front_thigh_mm} onChange={v => set('front_thigh_mm', v)} />
                    </div>
                  </Section>

                  <Section title="Perímetros adicionales (cm) — ISAK 2">
                    <div className="grid grid-cols-2 gap-3">
                      <Field label="Cabeza" value={form.head_cm} onChange={v => set('head_cm', v)} />
                      <Field label="Cuello" value={form.neck_cm} onChange={v => set('neck_cm', v)} />
                      <Field label="Tórax mesoesternal" value={form.chest_cm} onChange={v => set('chest_cm', v)} />
                      <Field label="Tobillo mínimo" value={form.ankle_min_cm} onChange={v => set('ankle_min_cm', v)} />
                    </div>
                  </Section>

                  <Section title="Diámetros óseos (cm) — ISAK 2">
                    <div className="grid grid-cols-2 gap-3">
                      <Field label="Húmero bicondíleo (HC *)" value={form.humerus_width_cm} onChange={v => set('humerus_width_cm', v)} />
                      <Field label="Fémur bicondíleo (HC *)" value={form.femur_width_cm} onChange={v => set('femur_width_cm', v)} />
                      <Field label="Biacromial" value={form.biacromial_cm} onChange={v => set('biacromial_cm', v)} />
                      <Field label="Biiliocrestal" value={form.biiliocrestal_cm} onChange={v => set('biiliocrestal_cm', v)} />
                      <Field label="Ant-post. tórax" value={form.ap_chest_cm} onChange={v => set('ap_chest_cm', v)} />
                      <Field label="Transv. tórax" value={form.transv_chest_cm} onChange={v => set('transv_chest_cm', v)} />
                      <Field label="Longitud pie" value={form.foot_length_cm} onChange={v => set('foot_length_cm', v)} />
                      <Field label="Muñeca biestiloideo" value={form.wrist_cm} onChange={v => set('wrist_cm', v)} />
                      <Field label="Tobillo bimaleolar" value={form.ankle_bimalleolar_cm} onChange={v => set('ankle_bimalleolar_cm', v)} />
                    </div>
                    <p className="text-xs text-text-muted mt-1">HC * = requeridos para somatotipo Heath &amp; Carter</p>
                  </Section>

                  <Section title="Longitudes (cm) — ISAK 2">
                    <div className="grid grid-cols-2 gap-3">
                      <Field label="Acromio-radial" value={form.acromion_radial_cm} onChange={v => set('acromion_radial_cm', v)} />
                      <Field label="Radio-estiloide" value={form.radial_styloid_cm} onChange={v => set('radial_styloid_cm', v)} />
                      <Field label="Iliospinal (pierna)" value={form.iliospinal_height_cm} onChange={v => set('iliospinal_height_cm', v)} />
                      <Field label="Trocánter-tibial" value={form.trochanter_tibial_cm} onChange={v => set('trochanter_tibial_cm', v)} />
                    </div>
                  </Section>
                </>
              )}
            </div>

            {/* ── RIGHT: results ── */}
            <div className="space-y-4">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Resultados — Durnin &amp; Womersley (1974)
              </h4>

              {result ? (
                <div className="space-y-2">
                  <ResultCard label="Σ4 pliegues (D&W)" value={`${result.sigma4} mm`} />
                  {result.sum_6_skinfolds != null && (
                    <ResultCard label="Σ6 pliegues" value={`${result.sum_6_skinfolds} mm`} />
                  )}
                  {difBrBc != null && (
                    <ResultCard label="Diferencia BC − BR" value={`${difBrBc} cm`} />
                  )}
                  <ResultCard label="Densidad corporal" value={`${result.body_density} g/mL`} />
                  <ResultCard
                    label="% Masa grasa (D&W)"
                    value={`${result.fat_mass_pct}%`}
                    sub={patient ? fatCategory(result.fat_mass_pct, patient.sex) : undefined}
                    highlight
                  />
                  <ResultCard label="Masa grasa (kg)" value={`${result.fat_mass_kg} kg`} />
                  <ResultCard label="Masa magra (kg)" value={`${result.lean_mass_kg} kg`} highlight />
                  {bmi != null && <ResultCard label="IMC (kg/m²)" value={`${bmi}`} sub={bmiCategory(bmi)} />}
                  {whtr != null && <ResultCard label="Índice Cin./Talla" value={`${whtr}`} sub={whtrCategory(whtr)} />}
                  {amb != null && <ResultCard label="Área Musc. Brazo" value={`${amb} cm²`} />}
                  {age && (
                    <p className="text-xs text-text-muted pt-1">
                      Edad: {age} años · Sexo: {patient?.sex}
                    </p>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 bg-bg-light rounded-lg border border-dashed border-border text-text-muted text-sm text-center p-4">
                  Ingresa los 4 pliegues D&amp;W * y el peso para ver resultados
                </div>
              )}

              {form.isak_level === 'ISAK 2' && (
                <div className="mt-4 space-y-2">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Somatotipo — Heath &amp; Carter (1990)
                  </h4>
                  {soma ? (
                    <div className="grid grid-cols-3 gap-2">
                      <ResultCard label="Endomorfia" value={`${soma.endo}`} />
                      <ResultCard label="Mesomorfia" value={`${soma.meso}`} />
                      <ResultCard label="Ectomorfia" value={`${soma.ecto}`} />
                    </div>
                  ) : (
                    <div className="text-xs text-text-muted bg-bg-light rounded p-3">
                      Requiere: tríceps, subescapular, supraespinal, diámetros húmero y fémur, brazo contraído, pantorrilla y su pliegue, altura y peso.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-border">
            <button
              onClick={handleSave} disabled={saving || !result}
              className="flex-1 bg-primary hover:bg-primary-dark text-white py-3 rounded-lg font-medium disabled:opacity-50"
            >
              {saving ? 'Guardando...' : 'Guardar evaluación'}
            </button>
            <button
              onClick={closeForm}
              className="flex-1 border border-border text-text-muted hover:bg-bg-light py-3 rounded-lg font-medium"
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <div className="flex justify-end mb-4">
          <button
            onClick={() => setShowForm(true)}
            className="bg-primary hover:bg-primary-dark text-white px-5 py-2 rounded-lg"
          >
            + Nueva evaluación
          </button>
        </div>
      )}

      {/* History table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="font-bold text-primary">Historial de evaluaciones</h3>
        </div>
        {loadingHistory ? (
          <div className="px-6 py-8 text-center text-text-muted text-sm">Cargando...</div>
        ) : evaluations.length === 0 ? (
          <div className="px-6 py-8 text-center text-text-muted text-sm">No hay evaluaciones registradas.</div>
        ) : (
          <table className="w-full">
            <thead className="bg-bg-light border-b border-border">
              <tr>
                {['Fecha', 'Nivel', 'Peso', '% Grasa', 'Grasa kg', 'Magra kg', 'Σ6 mm', 'IMC', 'Somatotipo'].map(h => (
                  <th key={h} className={`px-4 py-3 text-xs font-medium text-gray-600 uppercase ${
                    h === 'Fecha' || h === 'Nivel' ? 'text-left' : 'text-right'
                  }`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {evaluations.map(ev => {
                const evBmi = calcBmi(ev.weight_kg ?? null, ev.height_cm ?? null)
                const hasSoma = ev.somatotype_endo != null
                return (
                  <tr key={ev.id} className="border-b border-border hover:bg-bg-light">
                    <td className="px-4 py-3 text-sm text-gray-700">{ev.date}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        ev.isak_level === 'ISAK 2' ? 'bg-primary/10 text-primary' : 'bg-sage/20 text-gray-600'
                      }`}>{ev.isak_level}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 text-right">{fmt(ev.weight_kg)}</td>
                    <td className="px-4 py-3 text-sm font-medium text-right">
                      <span className={ev.fat_mass_pct != null ? 'text-primary' : 'text-text-muted'}>
                        {fmt(ev.fat_mass_pct)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 text-right">{fmt(ev.fat_mass_kg)}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 text-right">{fmt(ev.lean_mass_kg)}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 text-right">{fmt(ev.sum_6_skinfolds)}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 text-right">{evBmi != null ? evBmi.toFixed(1) : '—'}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 text-right">
                      {hasSoma ? `${ev.somatotype_endo}-${ev.somatotype_meso}-${ev.somatotype_ecto}` : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="bg-primary/10 rounded px-3 py-1.5 mb-2">
        <span className="text-xs font-bold text-primary uppercase tracking-wide">{title}</span>
      </div>
      {children}
    </div>
  )
}

function Field({
  label, value, onChange, type = 'number', placeholder, highlight, cols,
}: {
  label: string; value: string; onChange: (v: string) => void
  type?: string; placeholder?: string; highlight?: boolean; cols?: number
}) {
  return (
    <div className={cols === 2 ? 'col-span-2' : ''}>
      <label className="block text-xs text-text-muted mb-1">{label}</label>
      <input
        type={type}
        step={type === 'number' ? '0.1' : undefined}
        min={type === 'number' ? '0' : undefined}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary ${
          highlight ? 'border-primary/40 bg-primary/5' : 'border-border'
        }`}
      />
    </div>
  )
}

function ResultCard({
  label, value, sub, highlight,
}: { label: string; value: string; sub?: string; highlight?: boolean }) {
  return (
    <div className={`flex justify-between items-center px-4 py-2.5 rounded-lg ${highlight ? 'bg-primary/10' : 'bg-bg-light'}`}>
      <span className="text-sm text-gray-600">{label}</span>
      <div className="text-right">
        <span className={`text-sm font-bold ${highlight ? 'text-primary' : 'text-gray-800'}`}>{value}</span>
        {sub && <div className="text-xs text-text-muted">{sub}</div>}
      </div>
    </div>
  )
}
