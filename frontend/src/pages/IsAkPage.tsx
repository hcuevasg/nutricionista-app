import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'
import { useToast } from '../context/ToastContext'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ScatterChart, Scatter, ReferenceLine, Label,
} from 'recharts'
import {
  calcIsAk1, calcSomatotype, calcArmMuscleArea, calcWaistHeightRatio,
  calcBmi, bmiCategory, fatCategory, whtrCategory,
  calcWaistHipRatio, calcAdiposeMuscularRatio, calcConicityIndex,
  calcBoneMassMartin, calcMuscleBoneRatio,
  calcIresUpper, calcIresLower, calcIntermembralIndex, calcBrachialIndex,
  calcCruralIndex, calcCormicIndex, calcSkeletalIndexManouvrier,
  calcAcromioIliacIndex, calcRelativeWingspan,
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
  // Perímetros
  arm_relaxed_cm?: number; arm_contracted_cm?: number; hip_glute_cm?: number
  thigh_max_cm?: number; thigh_mid_cm?: number; calf_cm?: number
  // Pliegues
  triceps_mm?: number; subscapular_mm?: number; biceps_mm?: number; iliac_crest_mm?: number
  supraspinal_mm?: number; abdominal_mm?: number; medial_thigh_mm?: number; max_calf_mm?: number
  pectoral_mm?: number; axillary_mm?: number; front_thigh_mm?: number
  // ISAK 2 perímetros
  head_cm?: number; neck_cm?: number; chest_cm?: number; ankle_min_cm?: number
  // Diámetros
  humerus_width_cm?: number; femur_width_cm?: number; biacromial_cm?: number
  biiliocrestal_cm?: number; ap_chest_cm?: number; transv_chest_cm?: number
  foot_length_cm?: number; wrist_cm?: number; ankle_bimalleolar_cm?: number
  // Longitudes
  acromion_radial_cm?: number; radial_styloid_cm?: number
  iliospinal_height_cm?: number; trochanter_tibial_cm?: number
  tibiale_height_cm?: number; arm_span_cm?: number
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
  tibiale_height_cm: string; arm_span_cm: string
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
  tibiale_height_cm: '', arm_span_cm: '',
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
  return v != null ? v.toFixed(d) : '--'
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
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const [downloadingComparativo, setDownloadingComparativo] = useState(false)
  const [editingEvalId, setEditingEvalId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({})
  const toast = useToast()

  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  const toggleSection = (key: string) =>
    setCollapsedSections(prev => ({ ...prev, [key]: !prev[key] }))

  useEffect(() => {
    if (!token || !id) return

    fetch(`${API}/patients/${id}`, { headers: H })
      .then(r => { if (!r.ok) throw new Error(`${r.status}`); return r.json() })
      .then(pat => setPatient(pat))
      .catch(() => setError('Error al cargar paciente'))

    fetch(`${API}/anthropometrics/${id}`, { headers: H })
      .then(r => { if (!r.ok) throw new Error(`${r.status}`); return r.json() })
      .then(evals => setEvaluations(Array.isArray(evals) ? evals : []))
      .catch(() => setEvaluations([]))
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

  const closeForm = () => {
    setShowForm(false); setForm(EMPTY_FORM); setResult(null); setSoma(null)
    setEditingEvalId(null)
  }

  const s = (v?: number | null) => v != null ? String(v) : ''

  const handleStartEdit = (ev: Evaluation) => {
    setEditingEvalId(ev.id)
    setForm({
      date: ev.date, isak_level: (ev.isak_level as IsakLevel) || 'ISAK 1',
      weight_kg: s(ev.weight_kg), height_cm: s(ev.height_cm), waist_cm: s(ev.waist_cm),
      arm_relaxed_cm: s(ev.arm_relaxed_cm), arm_contracted_cm: s(ev.arm_contracted_cm),
      hip_glute_cm: s(ev.hip_glute_cm), thigh_max_cm: s(ev.thigh_max_cm),
      thigh_mid_cm: s(ev.thigh_mid_cm), calf_cm: s(ev.calf_cm),
      triceps_mm: s(ev.triceps_mm), subscapular_mm: s(ev.subscapular_mm),
      biceps_mm: s(ev.biceps_mm), iliac_crest_mm: s(ev.iliac_crest_mm),
      supraspinal_mm: s(ev.supraspinal_mm), abdominal_mm: s(ev.abdominal_mm),
      medial_thigh_mm: s(ev.medial_thigh_mm), max_calf_mm: s(ev.max_calf_mm),
      pectoral_mm: s(ev.pectoral_mm), axillary_mm: s(ev.axillary_mm),
      front_thigh_mm: s(ev.front_thigh_mm), head_cm: s(ev.head_cm),
      neck_cm: s(ev.neck_cm), chest_cm: s(ev.chest_cm), ankle_min_cm: s(ev.ankle_min_cm),
      humerus_width_cm: s(ev.humerus_width_cm), femur_width_cm: s(ev.femur_width_cm),
      biacromial_cm: s(ev.biacromial_cm), biiliocrestal_cm: s(ev.biiliocrestal_cm),
      ap_chest_cm: s(ev.ap_chest_cm), transv_chest_cm: s(ev.transv_chest_cm),
      foot_length_cm: s(ev.foot_length_cm), wrist_cm: s(ev.wrist_cm),
      ankle_bimalleolar_cm: s(ev.ankle_bimalleolar_cm),
      acromion_radial_cm: s(ev.acromion_radial_cm), radial_styloid_cm: s(ev.radial_styloid_cm),
      iliospinal_height_cm: s(ev.iliospinal_height_cm), trochanter_tibial_cm: s(ev.trochanter_tibial_cm),
      tibiale_height_cm: s(ev.tibiale_height_cm), arm_span_cm: s(ev.arm_span_cm),
    })
    setShowForm(true)
  }

  const handleDeleteEval = async (evalId: number) => {
    if (!confirm('¿Eliminar esta evaluación? Esta acción no se puede deshacer.')) return
    setDeletingId(evalId)
    try {
      const res = await fetch(`${API}/anthropometrics/${id}/${evalId}`, { method: 'DELETE', headers: H })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      setEvaluations(prev => prev.filter(e => e.id !== evalId))
      toast.success('Evaluación eliminada')
    } catch {
      toast.error('No se pudo eliminar la evaluación')
      setError('No se pudo eliminar la evaluación')
    } finally {
      setDeletingId(null)
    }
  }

  const handleSave = async () => {
    if (!result) { setError('Completa los 4 pliegues D&W (*) y el peso para guardar'); return }
    setSaving(true); setError(null)

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
        tibiale_height_cm: pf(form.tibiale_height_cm),
        arm_span_cm: pf(form.arm_span_cm),
        somatotype_endo: soma?.endo ?? null,
        somatotype_meso: soma?.meso ?? null,
        somatotype_ecto: soma?.ecto ?? null,
      })
    }

    try {
      const url = editingEvalId
        ? `${API}/anthropometrics/${id}/${editingEvalId}`
        : `${API}/anthropometrics?patient_id=${id}`
      const method = editingEvalId ? 'PUT' : 'POST'
      const res = await fetch(url, { method, headers: H, body: JSON.stringify(payload) })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d.detail ?? `Error ${res.status}`)
      }
      const saved = await res.json()
      if (editingEvalId) {
        setEvaluations(prev => prev.map(e => e.id === editingEvalId ? saved : e))
      } else {
        setEvaluations(prev => [saved, ...prev])
      }
      closeForm()
      toast.success(editingEvalId ? 'Evaluación actualizada' : 'Evaluación guardada')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error al guardar'
      toast.error(msg)
      setError(msg)
    } finally {
      setSaving(false)
    }
  }

  const handleDownloadIsak = async (evalId: number, date: string) => {
    setDownloadingId(evalId)
    try {
      const res = await fetch(`${API}/anthropometrics/${id}/${evalId}/pdf`, { headers: H })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ISAK_${patient?.name.replace(/ /g, '_') ?? id}_${date}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('No se pudo descargar el PDF')
    } finally {
      setDownloadingId(null)
    }
  }

  const handleDownloadComparativo = async () => {
    setDownloadingComparativo(true)
    try {
      const res = await fetch(`${API}/anthropometrics/${id}/pdf/comparativo`, { headers: H })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ISAK_Comparativo_${patient?.name.replace(/ /g, '_') ?? id}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('No se pudo descargar el PDF comparativo')
    } finally {
      setDownloadingComparativo(false)
    }
  }

  const age = patient ? calcAge(patient.birth_date) : null
  const bmi = calcBmi(pf(form.weight_kg), pf(form.height_cm))
  const whtr = calcWaistHeightRatio(pf(form.waist_cm), pf(form.height_cm))
  const amb = calcArmMuscleArea(pf(form.arm_relaxed_cm), pf(form.triceps_mm))
  const difBrBc = pf(form.arm_contracted_cm) != null && pf(form.arm_relaxed_cm) != null
    ? Math.round(((pf(form.arm_contracted_cm)! - pf(form.arm_relaxed_cm)!) + Number.EPSILON) * 10) / 10
    : null

  // Índices disponibles desde mediciones básicas (ISAK 1+2)
  const waistHipRatio = calcWaistHipRatio(pf(form.waist_cm), pf(form.hip_glute_cm))
  const adiposeMuscular = result ? calcAdiposeMuscularRatio(result.fat_mass_kg, result.lean_mass_kg) : null
  const conicityIdx = calcConicityIndex(pf(form.waist_cm), pf(form.weight_kg), pf(form.height_cm))

  // Índices ISAK 2
  const boneMass = calcBoneMassMartin(pf(form.height_cm), pf(form.humerus_width_cm), pf(form.femur_width_cm))
  const muscleBone = result ? calcMuscleBoneRatio(result.lean_mass_kg, boneMass) : null
  const iresUpper = calcIresUpper(pf(form.acromion_radial_cm), pf(form.radial_styloid_cm), pf(form.height_cm))
  const iresLower = calcIresLower(pf(form.iliospinal_height_cm), pf(form.height_cm))
  const intermembral = calcIntermembralIndex(pf(form.acromion_radial_cm), pf(form.radial_styloid_cm), pf(form.iliospinal_height_cm))
  const brachial = calcBrachialIndex(pf(form.radial_styloid_cm), pf(form.acromion_radial_cm))
  const crural = calcCruralIndex(pf(form.tibiale_height_cm), pf(form.trochanter_tibial_cm))
  const cormic = calcCormicIndex(pf(form.height_cm), pf(form.iliospinal_height_cm))
  const skeletal = calcSkeletalIndexManouvrier(pf(form.iliospinal_height_cm), pf(form.height_cm))
  const acromioIliac = calcAcromioIliacIndex(pf(form.biacromial_cm), pf(form.biiliocrestal_cm))
  const wingspan = calcRelativeWingspan(pf(form.arm_span_cm), pf(form.height_cm))

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <Layout title={`ISAK -- ${patient?.name ?? '...'}`}>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <Link to={`/patients/${id}`} className="hover:text-primary">{patient?.name ?? `Paciente ${id}`}</Link>
        <span>/</span>
        <span className="text-primary font-medium">Evaluaciones ISAK</span>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">{error}</div>
      )}

      {showForm ? (
        <div className="bg-white rounded-xl shadow-sm border border-border p-6 mb-6 space-y-6">
          {/* Edit banner */}
          {editingEvalId && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg text-sm font-medium">
              Editando evaluacion del {form.date}
            </div>
          )}

          <div className="flex justify-between items-center">
            <h3 className="text-2xl font-extrabold tracking-tight text-gray-900">
              {editingEvalId ? 'Editar Evaluacion' : 'Nueva Evaluacion'}
            </h3>
            <button onClick={closeForm} className="border border-border hover:bg-bg-light text-gray-700 px-4 py-2 rounded-lg font-medium text-sm">Cancelar</button>
          </div>

          {!patient?.birth_date && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-2 rounded-lg text-sm">
              El paciente no tiene fecha de nacimiento -- no se puede calcular % grasa.{' '}
              <Link to={`/patients/${id}/edit`} className="underline font-medium">Editar paciente</Link>
            </div>
          )}

          {/* ISAK level selector — pill tabs */}
          <div className="flex gap-2">
            {(['ISAK 1', 'ISAK 2'] as IsakLevel[]).map(level => (
              <button key={level} type="button" onClick={() => set('isak_level', level)}
                className={`px-6 py-2 rounded-full text-sm font-bold border-2 transition-colors ${
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
            <div className="space-y-4">

              {/* Datos basicos */}
              <CollapsibleSection title="Datos Basicos" sectionKey="basicos" collapsed={collapsedSections} toggle={toggleSection}>
                <div className="grid grid-cols-3 gap-3">
                  <Field label="Fecha sesion *" value={form.date} onChange={v => set('date', v)} type="date" cols={3} />
                  <Field label="Peso (kg)" value={form.weight_kg} onChange={v => set('weight_kg', v)} placeholder="70.0" />
                  <Field label="Talla (cm)" value={form.height_cm} onChange={v => set('height_cm', v)} placeholder="170.0" />
                  <Field label="Cintura min. (cm)" value={form.waist_cm} onChange={v => set('waist_cm', v)} placeholder="80.0" />
                </div>
              </CollapsibleSection>

              {/* Perimetros */}
              <CollapsibleSection title="Perimetros (cm)" sectionKey="perimetros" collapsed={collapsedSections} toggle={toggleSection}>
                <div className="grid grid-cols-3 gap-3">
                  <Field label="Brazo relajado (BR)" value={form.arm_relaxed_cm} onChange={v => set('arm_relaxed_cm', v)} />
                  <Field label="Brazo contraido (BC)" value={form.arm_contracted_cm} onChange={v => set('arm_contracted_cm', v)} />
                  <Field label='Cadera "gluteo"' value={form.hip_glute_cm} onChange={v => set('hip_glute_cm', v)} />
                  <Field label="Muslo maximo" value={form.thigh_max_cm} onChange={v => set('thigh_max_cm', v)} />
                  <Field label="Muslo medio" value={form.thigh_mid_cm} onChange={v => set('thigh_mid_cm', v)} />
                  <Field label="Pantorrilla" value={form.calf_cm} onChange={v => set('calf_cm', v)} />
                </div>
              </CollapsibleSection>

              {/* Pliegues cutaneos */}
              <CollapsibleSection title="Pliegues Cutaneos (mm)" sectionKey="pliegues" collapsed={collapsedSections} toggle={toggleSection}>
                <div className="grid grid-cols-3 gap-3">
                  <Field label="Triceps (D&W *)" value={form.triceps_mm} onChange={v => set('triceps_mm', v)} highlight />
                  <Field label="Subescapular (D&W *)" value={form.subscapular_mm} onChange={v => set('subscapular_mm', v)} highlight />
                  <Field label="Biceps (D&W *)" value={form.biceps_mm} onChange={v => set('biceps_mm', v)} highlight />
                  <Field label="Cresta iliaca (D&W *)" value={form.iliac_crest_mm} onChange={v => set('iliac_crest_mm', v)} highlight />
                  <Field label="Supraespinal (S6 *)" value={form.supraspinal_mm} onChange={v => set('supraspinal_mm', v)} />
                  <Field label="Abdominal (S6 *)" value={form.abdominal_mm} onChange={v => set('abdominal_mm', v)} />
                  <Field label="Muslo medial (S6 *)" value={form.medial_thigh_mm} onChange={v => set('medial_thigh_mm', v)} />
                  <Field label="Pantorrilla max. (S6 *)" value={form.max_calf_mm} onChange={v => set('max_calf_mm', v)} />
                </div>
                <p className="text-xs text-text-muted mt-2">
                  D&amp;W * = Durnin &amp; Womersley | S6 * = Suma 6 pliegues
                </p>
              </CollapsibleSection>

              {/* ISAK 2 extra */}
              {form.isak_level === 'ISAK 2' && (
                <>
                  <CollapsibleSection title="Pliegues Adicionales (mm) -- ISAK 2" sectionKey="pliegues2" collapsed={collapsedSections} toggle={toggleSection}>
                    <div className="grid grid-cols-3 gap-3">
                      <Field label="Pectoral (torax)" value={form.pectoral_mm} onChange={v => set('pectoral_mm', v)} />
                      <Field label="Axilar medio" value={form.axillary_mm} onChange={v => set('axillary_mm', v)} />
                      <Field label="Muslo anterior" value={form.front_thigh_mm} onChange={v => set('front_thigh_mm', v)} />
                    </div>
                  </CollapsibleSection>

                  <CollapsibleSection title="Perimetros Adicionales (cm) -- ISAK 2" sectionKey="perimetros2" collapsed={collapsedSections} toggle={toggleSection}>
                    <div className="grid grid-cols-3 gap-3">
                      <Field label="Cabeza" value={form.head_cm} onChange={v => set('head_cm', v)} />
                      <Field label="Cuello" value={form.neck_cm} onChange={v => set('neck_cm', v)} />
                      <Field label="Torax mesoesternal" value={form.chest_cm} onChange={v => set('chest_cm', v)} />
                      <Field label="Tobillo minimo" value={form.ankle_min_cm} onChange={v => set('ankle_min_cm', v)} />
                    </div>
                  </CollapsibleSection>

                  <CollapsibleSection title="Diametros Oseos (cm) -- ISAK 2" sectionKey="diametros" collapsed={collapsedSections} toggle={toggleSection}>
                    <div className="grid grid-cols-3 gap-3">
                      <Field label="Humero bicondileo (HC *)" value={form.humerus_width_cm} onChange={v => set('humerus_width_cm', v)} />
                      <Field label="Femur bicondileo (HC *)" value={form.femur_width_cm} onChange={v => set('femur_width_cm', v)} />
                      <Field label="Biacromial" value={form.biacromial_cm} onChange={v => set('biacromial_cm', v)} />
                      <Field label="Biiliocrestal" value={form.biiliocrestal_cm} onChange={v => set('biiliocrestal_cm', v)} />
                      <Field label="Ant-post. torax" value={form.ap_chest_cm} onChange={v => set('ap_chest_cm', v)} />
                      <Field label="Transv. torax" value={form.transv_chest_cm} onChange={v => set('transv_chest_cm', v)} />
                      <Field label="Longitud pie" value={form.foot_length_cm} onChange={v => set('foot_length_cm', v)} />
                      <Field label="Muneca biestiloideo" value={form.wrist_cm} onChange={v => set('wrist_cm', v)} />
                      <Field label="Tobillo bimaleolar" value={form.ankle_bimalleolar_cm} onChange={v => set('ankle_bimalleolar_cm', v)} />
                    </div>
                    <p className="text-xs text-text-muted mt-2">HC * = requeridos para somatotipo Heath &amp; Carter</p>
                  </CollapsibleSection>

                  <CollapsibleSection title="Longitudes (cm) -- ISAK 2" sectionKey="longitudes" collapsed={collapsedSections} toggle={toggleSection}>
                    <div className="grid grid-cols-3 gap-3">
                      <Field label="Acromio-radial" value={form.acromion_radial_cm} onChange={v => set('acromion_radial_cm', v)} />
                      <Field label="Radio-estiloide" value={form.radial_styloid_cm} onChange={v => set('radial_styloid_cm', v)} />
                      <Field label="Iliospinal (pierna)" value={form.iliospinal_height_cm} onChange={v => set('iliospinal_height_cm', v)} />
                      <Field label="Trocanter-tibial" value={form.trochanter_tibial_cm} onChange={v => set('trochanter_tibial_cm', v)} />
                      <Field label="Tibiale (altura tibia)" value={form.tibiale_height_cm} onChange={v => set('tibiale_height_cm', v)} />
                      <Field label="Envergadura (arm span)" value={form.arm_span_cm} onChange={v => set('arm_span_cm', v)} />
                    </div>
                  </CollapsibleSection>
                </>
              )}
            </div>

            {/* ── RIGHT: results ── */}
            <div className="space-y-4">
              <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest">
                Resultados -- Durnin &amp; Womersley (1974)
              </h4>

              {result ? (
                <div className="space-y-2">
                  <ResultCard label="S4 pliegues (D&W)" value={`${result.sigma4} mm`} />
                  {result.sum_6_skinfolds != null && (
                    <ResultCard label="S6 pliegues" value={`${result.sum_6_skinfolds} mm`} />
                  )}
                  {difBrBc != null && (
                    <ResultCard label="Diferencia BC - BR" value={`${difBrBc} cm`} />
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
                  {bmi != null && <ResultCard label="IMC / Body Mass Index" value={`${bmi}`} sub={bmiCategory(bmi)} />}
                  {whtr != null && <ResultCard label="Indice Cin./Talla" value={`${whtr}`} sub={whtrCategory(whtr)} />}
                  {amb != null && <ResultCard label="Area Musc. Brazo" value={`${amb} cm2`} />}
                  {waistHipRatio != null && <ResultCard label="Coc. Cintura-Cadera" value={`${waistHipRatio}`} />}
                  {adiposeMuscular != null && <ResultCard label="Coc. Adiposo-Muscular" value={`${adiposeMuscular}`} />}
                  {conicityIdx != null && <ResultCard label="Indice de Conicidad" value={`${conicityIdx}`} />}
                  {age && (
                    <p className="text-xs text-text-muted pt-1">
                      Edad: {age} anos | Sexo: {patient?.sex}
                    </p>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 bg-bg-light rounded-xl border border-dashed border-border text-text-muted text-sm text-center p-4">
                  Ingresa los 4 pliegues D&amp;W * y el peso para ver resultados
                </div>
              )}

              {form.isak_level === 'ISAK 2' && (
                <>
                  <div className="mt-4 space-y-2">
                    <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest">
                      Somatotipo -- Heath &amp; Carter (1990)
                    </h4>
                    {soma ? (
                      <div className="grid grid-cols-3 gap-2">
                        <ResultCard label="Endomorfia" value={`${soma.endo}`} />
                        <ResultCard label="Mesomorfia" value={`${soma.meso}`} />
                        <ResultCard label="Ectomorfia" value={`${soma.ecto}`} />
                      </div>
                    ) : (
                      <div className="text-xs text-text-muted bg-bg-light rounded-lg p-3">
                        Requiere: triceps, subescapular, supraespinal, diametros humero y femur, brazo contraido, pantorrilla y su pliegue, altura y peso.
                      </div>
                    )}
                  </div>

                  <div className="mt-4 space-y-2">
                    <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest">
                      Indices ISAK 2
                    </h4>
                    <div className="space-y-1.5">
                      {boneMass != null && <ResultCard label="Masa Osea (Martin 1990)" value={`${boneMass} kg`} />}
                      {muscleBone != null && <ResultCard label="Coc. Musculo-Hueso" value={`${muscleBone}`} highlight />}
                      {iresUpper != null && <ResultCard label="I.R.E.S. Superior" value={`${iresUpper}`} />}
                      {iresLower != null && <ResultCard label="I.R.E.S. Inferior" value={`${iresLower}`} />}
                      {intermembral != null && <ResultCard label="Indice Intermembral" value={`${intermembral}`} />}
                      {brachial != null && <ResultCard label="Indice Braquial" value={`${brachial}`} />}
                      {crural != null && <ResultCard label="Indice Crural" value={`${crural}`} />}
                      {cormic != null && <ResultCard label="Indice Cormico" value={`${cormic}`} />}
                      {skeletal != null && <ResultCard label="Indice Esqueletico (Manouvrier)" value={`${skeletal}`} />}
                      {acromioIliac != null && <ResultCard label="Indice Acromio-Iliaco" value={`${acromioIliac}`} />}
                      {wingspan != null && <ResultCard label="Envergadura Relativa" value={`${wingspan}`} />}
                      {boneMass == null && muscleBone == null && iresUpper == null && cormic == null && (
                        <div className="text-xs text-text-muted bg-bg-light rounded-lg p-3">
                          Completa longitudes y diametros oseos para ver los indices ISAK 2.
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-border">
            <button
              onClick={handleSave} disabled={saving || !result}
              className="flex-1 bg-primary hover:bg-primary-dark text-white px-4 py-3 rounded-lg font-medium disabled:opacity-50"
            >
              {saving ? 'Guardando...' : editingEvalId ? 'Actualizar evaluacion' : 'Guardar evaluacion'}
            </button>
            <button
              onClick={closeForm}
              className="flex-1 border border-border hover:bg-bg-light text-gray-700 px-4 py-3 rounded-lg font-medium"
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-gray-900">Evaluaciones ISAK</h1>
            <p className="text-text-muted font-medium mt-0.5">
              Paciente: <span className="text-gray-900">{patient?.name}</span>
            </p>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 bg-primary hover:bg-primary-dark text-white px-5 py-2.5 rounded-xl font-bold shadow-sm transition-all"
          >
            + Nueva evaluacion
          </button>
        </div>
      )}

      {/* Evolution chart -- only shown when >= 2 evaluations */}
      {evaluations.length >= 2 && (() => {
        const chartData = [...evaluations].reverse().map(ev => ({
          fecha: ev.date,
          'Peso kg': ev.weight_kg ?? null,
          '% Grasa': ev.fat_mass_pct ?? null,
          'Magra kg': ev.lean_mass_kg ?? null,
          'S6 mm': ev.sum_6_skinfolds ?? null,
        }))
        return (
          <div className="bg-white rounded-xl shadow-sm border border-border p-6 mb-6">
            <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-4">Evolucion</h3>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5EAE7" />
                <XAxis dataKey="fecha" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="kg" tick={{ fontSize: 11 }} unit=" kg" width={52} />
                <YAxis yAxisId="pct" orientation="right" tick={{ fontSize: 11 }} unit="%" width={40} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line yAxisId="kg"  type="monotone" dataKey="Peso kg"  stroke="#4b7c60" strokeWidth={2} dot={{ r: 4 }} connectNulls />
                <Line yAxisId="kg"  type="monotone" dataKey="Magra kg" stroke="#8da399" strokeWidth={2} dot={{ r: 4 }} connectNulls />
                <Line yAxisId="pct" type="monotone" dataKey="% Grasa"  stroke="#c06c52" strokeWidth={2} dot={{ r: 4 }} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )
      })()}

      {/* Somatocarta -- ISAK 2 only */}
      {(() => {
        const somaEvals = evaluations.filter(
          ev => ev.isak_level === 'ISAK 2' &&
            ev.somatotype_endo != null && ev.somatotype_meso != null && ev.somatotype_ecto != null
        )
        if (somaEvals.length === 0) return null
        const points = somaEvals.map(ev => ({
          x: +(ev.somatotype_ecto! - ev.somatotype_endo!).toFixed(2),
          y: +(2 * ev.somatotype_meso! - (ev.somatotype_endo! + ev.somatotype_ecto!)).toFixed(2),
          label: ev.date,
        }))
        const CustomDot = (props: any) => {
          const { cx, cy, payload } = props
          return (
            <g>
              <circle cx={cx} cy={cy} r={6} fill="#4b7c60" stroke="white" strokeWidth={2} />
              <text x={cx} y={cy - 10} textAnchor="middle" fontSize={10} fill="#6b7280">{payload.label}</text>
            </g>
          )
        }
        return (
          <div className="bg-white rounded-xl shadow-sm border border-border p-6 mb-6">
            <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-1">Somatocarta -- Heath & Carter</h3>
            <p className="text-xs text-text-muted mb-4">Eje X: Ecto - Endo | Eje Y: 2xMeso - (Endo + Ecto)</p>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ top: 20, right: 30, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5EAE7" />
                <XAxis type="number" dataKey="x" domain={[-8, 8]} tick={{ fontSize: 11 }}>
                  <Label value="<- Endomorfo | Ectomorfo ->" position="bottom" style={{ fontSize: 11, fill: '#6b7280' }} />
                </XAxis>
                <YAxis type="number" dataKey="y" domain={[-8, 8]} tick={{ fontSize: 11 }}>
                  <Label value="Mesomorfo ->" angle={-90} position="insideLeft" style={{ fontSize: 11, fill: '#6b7280' }} />
                </YAxis>
                <ReferenceLine x={0} stroke="#8da399" strokeDasharray="4 4" />
                <ReferenceLine y={0} stroke="#8da399" strokeDasharray="4 4" />
                <Tooltip
                  content={({ payload }) => {
                    if (!payload?.length) return null
                    const d = payload[0].payload
                    return (
                      <div className="bg-white border border-border rounded-lg shadow-sm p-2 text-xs">
                        <p className="font-medium text-primary">{d.label}</p>
                        <p>X: {d.x} | Y: {d.y}</p>
                      </div>
                    )
                  }}
                />
                <Scatter data={points} shape={<CustomDot />} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        )
      })()}

      {/* History table */}
      <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest">Historial de evaluaciones</h3>
          {evaluations.length >= 2 && (
            <button
              onClick={handleDownloadComparativo}
              disabled={downloadingComparativo}
              className="text-xs bg-terracotta hover:opacity-90 text-white px-3 py-1.5 rounded-lg font-bold disabled:opacity-50"
            >
              {downloadingComparativo ? 'Generando...' : '\u2B07 PDF Comparativo'}
            </button>
          )}
        </div>
        {loadingHistory ? (
          <div className="px-6 py-8 text-center text-text-muted text-sm">Cargando...</div>
        ) : evaluations.length === 0 ? (
          <div className="p-10 text-center text-text-muted text-sm space-y-4">
            <div className="text-4xl mb-2">&#128203;</div>
            <p className="font-medium">No hay evaluaciones registradas.</p>
            <button
              onClick={() => setShowForm(true)}
              className="inline-block bg-primary hover:bg-primary-dark text-white px-5 py-2.5 rounded-xl font-bold"
            >
              + Crear primera evaluacion
            </button>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Fecha', 'Nivel', 'Peso', '% Grasa', 'Grasa kg', 'Magra kg', 'S6 mm', 'IMC', 'Somatotipo', 'PDF', 'Acciones'].map(h => (
                  <th key={h} className={`px-4 py-3 text-xs font-bold text-gray-400 uppercase tracking-wider ${
                    h === 'Fecha' || h === 'Nivel' || h === 'Acciones' ? 'text-left' : 'text-right'
                  }`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {evaluations.map(ev => {
                const evBmi = calcBmi(ev.weight_kg ?? null, ev.height_cm ?? null)
                const hasSoma = ev.somatotype_endo != null
                return (
                  <tr key={ev.id} className="hover:bg-bg-light/50 transition-colors">
                    <td className="px-4 py-3.5 text-sm font-semibold text-gray-800">{ev.date}</td>
                    <td className="px-4 py-3.5">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                        ev.isak_level === 'ISAK 2' ? 'bg-primary/10 text-primary' : 'bg-sage/20 text-gray-600'
                      }`}>{ev.isak_level}</span>
                    </td>
                    <td className="px-4 py-3.5 text-sm text-gray-700 text-right">{fmt(ev.weight_kg)}</td>
                    <td className="px-4 py-3.5 text-sm font-bold text-right">
                      <span className={ev.fat_mass_pct != null ? 'text-primary' : 'text-text-muted'}>
                        {fmt(ev.fat_mass_pct)}%
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-sm text-gray-700 text-right">{fmt(ev.fat_mass_kg)}</td>
                    <td className="px-4 py-3.5 text-sm text-gray-700 text-right">{fmt(ev.lean_mass_kg)}</td>
                    <td className="px-4 py-3.5 text-sm text-gray-700 text-right">{fmt(ev.sum_6_skinfolds)}</td>
                    <td className="px-4 py-3.5 text-sm text-gray-700 text-right">{evBmi != null ? evBmi.toFixed(1) : '--'}</td>
                    <td className="px-4 py-3.5 text-sm text-gray-700 text-right">
                      {hasSoma ? `${ev.somatotype_endo}-${ev.somatotype_meso}-${ev.somatotype_ecto}` : '--'}
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <button
                        onClick={() => handleDownloadIsak(ev.id, ev.date)}
                        disabled={downloadingId === ev.id}
                        className="text-xs font-bold text-terracotta hover:underline disabled:opacity-50"
                      >
                        {downloadingId === ev.id ? '...' : '\u2B07 PDF'}
                      </button>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex gap-2 justify-start">
                        <button
                          onClick={() => handleStartEdit(ev)}
                          className="text-xs text-primary font-medium hover:underline"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => handleDeleteEval(ev.id)}
                          disabled={deletingId === ev.id}
                          className="text-xs text-red-400 font-medium hover:underline disabled:opacity-50"
                        >
                          {deletingId === ev.id ? '...' : 'Eliminar'}
                        </button>
                      </div>
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

function CollapsibleSection({
  title, sectionKey, collapsed, toggle, children,
}: {
  title: string; sectionKey: string
  collapsed: Record<string, boolean>; toggle: (key: string) => void
  children: React.ReactNode
}) {
  const isCollapsed = collapsed[sectionKey] ?? false
  return (
    <div className="bg-white rounded-xl border border-border overflow-hidden">
      <button
        type="button"
        onClick={() => toggle(sectionKey)}
        className="w-full bg-primary/10 px-4 py-2.5 flex items-center justify-between"
      >
        <span className="text-xs font-bold text-primary uppercase tracking-widest">{title}</span>
        <span className="text-primary text-sm font-bold">{isCollapsed ? '+' : '-'}</span>
      </button>
      {!isCollapsed && <div className="p-4">{children}</div>}
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
    <div className={cols === 2 ? 'col-span-2' : cols === 3 ? 'col-span-3' : ''}>
      <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">{label}</label>
      <input
        type={type}
        step={type === 'number' ? '0.1' : undefined}
        min={type === 'number' ? '0' : undefined}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary ${
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
    <div className={`flex justify-between items-center px-4 py-2.5 rounded-xl ${highlight ? 'bg-primary/10 border border-primary/20' : 'bg-bg-light border border-border'}`}>
      <span className="text-sm text-gray-600">{label}</span>
      <div className="text-right">
        <span className={`text-sm font-bold ${highlight ? 'text-primary' : 'text-gray-800'}`}>{value}</span>
        {sub && <div className="text-xs text-text-muted">{sub}</div>}
      </div>
    </div>
  )
}
