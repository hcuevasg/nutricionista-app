import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'
import IsAkEvolutionChart from '../components/IsAkEvolutionChart'

const ALLERGY_LABELS: Record<string, string> = {
  gluten:       'Gluten',
  lacteos:      'Lácteos',
  huevo:        'Huevo',
  mariscos:     'Mariscos',
  pescado:      'Pescado',
  frutos_secos: 'Frutos Secos',
  mani:         'Maní',
  soya:         'Soya',
  sulfitos:     'Sulfitos',
  fructosa:     'Fructosa',
}

interface Patient {
  id: number
  name: string
  birth_date?: string
  sex: string
  height_cm?: number
  weight_kg?: number
  phone?: string
  email?: string
  address?: string
  occupation?: string
  notes?: string
  allergies?: string[]
  created_at: string
}

function calcAge(birthDate?: string): number | null {
  if (!birthDate) return null
  const bd = new Date(birthDate)
  if (isNaN(bd.getTime())) return null
  const today = new Date()
  let age = today.getFullYear() - bd.getFullYear()
  if (
    today.getMonth() < bd.getMonth() ||
    (today.getMonth() === bd.getMonth() && today.getDate() < bd.getDate())
  )
    age--
  return age >= 0 ? age : null
}

function InfoRow({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div>
      <dt className="text-xs text-text-muted uppercase tracking-wide">{label}</dt>
      <dd className="mt-0.5 text-sm text-gray-800">{value ?? '—'}</dd>
    </div>
  )
}

interface Evaluation {
  id: number; date: string; isak_level?: string
  // Básicos
  weight_kg?: number | null; height_cm?: number | null; waist_cm?: number | null
  // Composición corporal
  body_density?: number | null; fat_mass_pct?: number | null; fat_mass_kg?: number | null
  lean_mass_kg?: number | null; sum_6_skinfolds?: number | null
  // Somatotipo
  somatotype_endo?: number | null; somatotype_meso?: number | null; somatotype_ecto?: number | null
  // Pliegues ISAK 1+2
  triceps_mm?: number | null; subscapular_mm?: number | null; biceps_mm?: number | null
  iliac_crest_mm?: number | null; supraspinal_mm?: number | null; abdominal_mm?: number | null
  medial_thigh_mm?: number | null; max_calf_mm?: number | null
  // Pliegues ISAK 2
  pectoral_mm?: number | null; axillary_mm?: number | null; front_thigh_mm?: number | null
  // Perímetros
  arm_relaxed_cm?: number | null; arm_contracted_cm?: number | null; hip_glute_cm?: number | null
  thigh_max_cm?: number | null; calf_cm?: number | null
  // Diámetros y longitudes ISAK 2
  humerus_width_cm?: number | null; femur_width_cm?: number | null
  biacromial_cm?: number | null; biiliocrestal_cm?: number | null
  acromion_radial_cm?: number | null; radial_styloid_cm?: number | null
  iliospinal_height_cm?: number | null; trochanter_tibial_cm?: number | null
}

function calcBMI(weight?: number | null, height_cm?: number | null): number | null {
  if (!weight || !height_cm || height_cm <= 0) return null
  const h = height_cm / 100
  return +(weight / (h * h)).toFixed(1)
}

function bmiBadge(bmi: number): { label: string; color: string } {
  if (bmi < 18.5) return { label: 'Bajo peso', color: 'text-blue-600 bg-blue-50 border-blue-100' }
  if (bmi < 25)   return { label: 'Normal', color: 'text-green-700 bg-green-50 border-green-100' }
  if (bmi < 30)   return { label: 'Sobrepeso', color: 'text-yellow-600 bg-yellow-50 border-yellow-100' }
  return { label: 'Obesidad', color: 'text-red-600 bg-red-50 border-red-100' }
}

function bmiBarPos(bmi: number): number {
  // Roughly maps bmi 14-40 to 0-100%
  return Math.min(100, Math.max(0, ((bmi - 14) / 26) * 100))
}

type TabKey = 'basico' | 'pliegues' | 'resultados'

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()
  const navigate = useNavigate()
  const [patient, setPatient] = useState<Patient | null>(null)
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabKey>('basico')
  const [selectedEvalIdx, setSelectedEvalIdx] = useState(0)

  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    if (!token || !id) return
    fetch(`${API}/patients/${id}`, { headers: H })
      .then(r => { if (!r.ok) throw new Error(`${r.status}`); return r.json() })
      .then(setPatient)
      .catch(() => setError('No se pudo cargar el paciente'))
      .finally(() => setLoading(false))

    fetch(`${API}/anthropometrics/${id}`, { headers: H })
      .then(r => r.ok ? r.json() : [])
      .then(evals => setEvaluations(Array.isArray(evals) ? evals : []))
      .catch(() => {})
  }, [id, token])

  if (loading) {
    return (
      <Layout title="Detalle del Paciente">
        <div className="text-center py-12 text-text-muted">Cargando...</div>
      </Layout>
    )
  }

  if (error || !patient) {
    return (
      <Layout title="Detalle del Paciente">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error ?? 'Paciente no encontrado'}
        </div>
      </Layout>
    )
  }

  const age = calcAge(patient.birth_date)
  const initials = patient.name.slice(0, 2).toUpperCase()

  // Use last evaluation's weight if available
  const lastEval = evaluations.length > 0 ? evaluations[evaluations.length - 1] : null
  const displayWeight = lastEval?.weight_kg ?? patient.weight_kg
  const bmi = calcBMI(displayWeight, patient.height_cm)
  const bmiInfo = bmi != null ? bmiBadge(bmi) : null

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'basico',     label: 'Básico' },
    { key: 'pliegues',   label: 'Pliegues' },
    { key: 'resultados', label: 'Resultados' },
  ]

  return (
    <Layout title={patient.name}>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <span className="text-primary font-medium">{patient.name}</span>
      </div>

      {/* Patient hero card */}
      <div className="bg-white rounded-xl shadow-sm border border-border p-8 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            {/* Avatar */}
            <div className="relative flex-shrink-0">
              <div className="w-[72px] h-[72px] rounded-full bg-primary/10 border-4 border-primary/20 flex items-center justify-center text-2xl font-bold text-primary">
                {initials}
              </div>
              <div className="absolute bottom-0 right-0 w-5 h-5 bg-green-500 border-2 border-white rounded-full"></div>
            </div>
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h2 className="text-2xl font-bold text-gray-900">{patient.name}</h2>
                <span className="bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border border-primary/20">
                  Activo
                </span>
              </div>
              <p className="text-text-muted font-medium mt-1">
                {age != null ? `${age} años` : '—'} · {patient.sex}
                {patient.id != null ? ` · ID: #PT-${String(patient.id).padStart(5, '0')}` : ''}
              </p>
              <div className="flex gap-2 mt-3 flex-wrap">
                {bmi != null && bmiInfo && (
                  <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${bmiInfo.color}`}>
                    IMC: {bmi} ({bmiInfo.label})
                  </div>
                )}
                {lastEval?.fat_mass_pct != null && (
                  <div className="flex items-center gap-1.5 bg-green-50 text-green-700 px-3 py-1 rounded-full text-xs font-semibold border border-green-100">
                    Grasa: {lastEval.fat_mass_pct.toFixed(1)}%
                  </div>
                )}
                {patient.allergies && patient.allergies.length > 0 && patient.allergies.map((key) => (
                  <div
                    key={key}
                    className="bg-terracotta/10 text-terracotta border border-terracotta/20 text-xs font-semibold px-2 py-0.5 rounded-full"
                  >
                    ⚠ {ALLERGY_LABELS[key] ?? key}
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              to={`/patients/${id}/edit`}
              className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm font-semibold hover:bg-bg-light transition-colors"
            >
              Editar
            </Link>
            <Link
              to={`/patients/${id}/isak`}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-dark transition-colors"
            >
              + Nueva eval
            </Link>
          </div>
        </div>
      </div>

      {/* Body: eval history sidebar + details panel */}
      <div className="flex flex-col lg:flex-row gap-0 bg-white rounded-xl shadow-sm border border-border overflow-hidden">

        {/* Left: evaluation timeline */}
        <aside className="w-full lg:w-[260px] border-r border-border bg-bg-light/30 p-5 flex flex-col flex-shrink-0">
          <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-4">
            Historial de Evaluaciones
          </h3>
          {evaluations.length === 0 ? (
            <p className="text-xs text-text-muted italic">Sin evaluaciones registradas</p>
          ) : (
            <div className="space-y-2 flex-1 overflow-y-auto">
              {evaluations.map((ev, idx) => (
                <div
                  key={ev.id}
                  onClick={() => setSelectedEvalIdx(idx)}
                  className={`p-3 bg-white rounded-xl border-l-4 shadow-sm cursor-pointer transition-all ${
                    idx === selectedEvalIdx
                      ? 'border-terracotta'
                      : 'border-transparent hover:border-border'
                  }`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-sm font-bold text-gray-800">{ev.date}</span>
                    {idx === selectedEvalIdx && (
                      <span className="text-terracotta text-xs">↓</span>
                    )}
                  </div>
                  {ev.weight_kg != null && (
                    <p className="text-xs text-text-muted font-mono">Peso: {ev.weight_kg} kg</p>
                  )}
                  {idx === 0 && (
                    <p className="text-[10px] text-text-muted mt-1 uppercase font-bold">Sesión Actual</p>
                  )}
                </div>
              ))}
            </div>
          )}
          <Link
            to={`/patients/${id}/isak`}
            className="mt-4 w-full flex items-center justify-center gap-2 py-3 bg-white border-2 border-dashed border-primary/30 text-primary rounded-xl font-bold text-sm hover:bg-primary/5 transition-all"
          >
            + Nueva evaluación
          </Link>
        </aside>

        {/* Right: detail panel */}
        <div className="flex-1 p-6 bg-bg-light min-w-0">
          {/* Pill tabs */}
          <div className="flex gap-2 p-1 bg-border/40 rounded-xl w-fit mb-6">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-5 py-2 rounded-lg text-sm font-bold transition-colors ${
                  activeTab === tab.key
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-gray-600 hover:text-primary'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {activeTab === 'basico' && (
            <>
              {/* Metric cards grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
                {/* Peso */}
                <div className="bg-white p-5 rounded-2xl shadow-sm border border-primary/5">
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Peso</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-gray-900">
                      {displayWeight != null ? displayWeight : '—'}
                    </span>
                    {displayWeight != null && <span className="text-text-muted font-medium">kg</span>}
                  </div>
                </div>

                {/* Estatura */}
                <div className="bg-white p-5 rounded-2xl shadow-sm border border-primary/5">
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Estatura</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-gray-900">
                      {patient.height_cm != null ? (patient.height_cm / 100).toFixed(2) : '—'}
                    </span>
                    {patient.height_cm != null && <span className="text-text-muted font-medium">m</span>}
                  </div>
                  <p className="mt-3 text-xs text-gray-400 italic">Constante registrado</p>
                </div>

                {/* IMC */}
                <div className="bg-white p-5 rounded-2xl shadow-sm border border-primary/5">
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">IMC</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-gray-900">{bmi ?? '—'}</span>
                  </div>
                  {bmi != null && (
                    <>
                      <div className="mt-3 w-full h-1.5 bg-gray-100 rounded-full overflow-hidden flex">
                        <div className="w-[30%] h-full bg-yellow-400"></div>
                        <div className="w-[40%] h-full bg-primary border-x-2 border-white"></div>
                        <div className="w-[30%] h-full bg-red-400"></div>
                      </div>
                      <div className="flex justify-between text-[10px] mt-1 text-gray-400 font-bold">
                        <span>BAJO</span>
                        <span className="text-primary">NORMAL</span>
                        <span>ALTO</span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Info fields */}
              <div className="bg-white rounded-xl shadow-sm border border-border p-5 mb-6">
                <dl className="grid grid-cols-2 gap-x-8 gap-y-4">
                  <InfoRow label="Teléfono" value={patient.phone} />
                  <InfoRow label="Correo electrónico" value={patient.email} />
                  <InfoRow label="Ocupación" value={patient.occupation} />
                  <InfoRow label="Dirección" value={patient.address} />
                </dl>
                {patient.notes && (
                  <div className="mt-4 pt-4 border-t border-border">
                    <dt className="text-xs text-text-muted uppercase tracking-wide mb-1">Notas / Antecedentes</dt>
                    <dd className="text-sm text-gray-700 whitespace-pre-wrap">{patient.notes}</dd>
                  </div>
                )}
              </div>

              {/* Acciones rápidas */}
              <div className="bg-white rounded-xl shadow-sm border border-border p-5 mb-6">
                <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-3">Acciones Rápidas</h4>
                <div className="flex flex-wrap gap-2">
                  <Link
                    to={`/patients/${id}/isak`}
                    className="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-lg text-sm font-medium"
                  >
                    + Nueva evaluación ISAK
                  </Link>
                  <Link
                    to={`/patients/${id}/plans/new`}
                    className="px-4 py-2 bg-terracotta hover:opacity-90 text-white rounded-lg text-sm font-medium"
                  >
                    + Plan alimenticio
                  </Link>
                  <Link
                    to={`/patients/${id}/pautas/new`}
                    className="px-4 py-2 bg-sage hover:opacity-90 text-white rounded-lg text-sm font-medium"
                  >
                    + Pauta nutricional
                  </Link>
                </div>
              </div>

              {/* Evolution chart — full width */}
              <div className="bg-white rounded-2xl shadow-sm border border-primary/5 p-2">
                <IsAkEvolutionChart evaluations={evaluations} />
              </div>
            </>
          )}

          {activeTab === 'pliegues' && (() => {
            const ev = evaluations[selectedEvalIdx]
            if (!ev) return (
              <div className="bg-white rounded-xl border border-border p-6 text-sm text-text-muted">
                Sin evaluaciones registradas.
              </div>
            )
            const f = (v?: number | null) => v != null ? `${v} mm` : '—'
            const rows: [string, string][] = [
              ['Tríceps',           f(ev.triceps_mm)],
              ['Subescapular',      f(ev.subscapular_mm)],
              ['Bíceps',            f(ev.biceps_mm)],
              ['Cresta iliaca',     f(ev.iliac_crest_mm)],
              ['Supraespinal',      f(ev.supraspinal_mm)],
              ['Abdominal',         f(ev.abdominal_mm)],
              ['Muslo medial',      f(ev.medial_thigh_mm)],
              ['Pantorrilla máx.',  f(ev.max_calf_mm)],
            ]
            if (ev.isak_level === 'ISAK 2') {
              rows.push(
                ['Pectoral',        f(ev.pectoral_mm)],
                ['Axilar medio',    f(ev.axillary_mm)],
                ['Muslo anterior',  f(ev.front_thigh_mm)],
              )
            }
            return (
              <div className="bg-white rounded-xl shadow-sm border border-border overflow-hidden">
                <div className="px-5 py-3 border-b border-border bg-bg-light flex items-center justify-between">
                  <span className="text-xs font-bold text-text-muted uppercase tracking-widest">Pliegues Cutáneos — {ev.date}</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${ev.isak_level === 'ISAK 2' ? 'bg-primary/10 text-primary' : 'bg-sage/20 text-gray-600'}`}>{ev.isak_level ?? 'ISAK 1'}</span>
                </div>
                <table className="w-full">
                  <tbody className="divide-y divide-gray-100">
                    {rows.map(([label, val]) => (
                      <tr key={label} className="hover:bg-bg-light/50">
                        <td className="px-5 py-3 text-sm text-text-muted w-1/2">{label}</td>
                        <td className="px-5 py-3 text-sm font-semibold text-gray-800 text-right">{val}</td>
                      </tr>
                    ))}
                    {ev.sum_6_skinfolds != null && (
                      <tr className="bg-primary/5">
                        <td className="px-5 py-3 text-sm font-bold text-primary">Σ6 Pliegues</td>
                        <td className="px-5 py-3 text-sm font-bold text-primary text-right">{ev.sum_6_skinfolds} mm</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )
          })()}

          {activeTab === 'resultados' && (() => {
            const ev = evaluations[selectedEvalIdx]
            if (!ev) return (
              <div className="bg-white rounded-xl border border-border p-6 text-sm text-text-muted">
                Sin evaluaciones registradas.
              </div>
            )
            const evBmi = ev.weight_kg && ev.height_cm ? +((ev.weight_kg / ((ev.height_cm / 100) ** 2)).toFixed(1)) : null
            const f = (v?: number | null, d = 1) => v != null ? v.toFixed(d) : '—'
            const rows: [string, string, boolean][] = [
              ['Densidad corporal',   ev.body_density    != null ? `${f(ev.body_density, 4)} g/mL` : '—', false],
              ['% Masa grasa',        ev.fat_mass_pct    != null ? `${f(ev.fat_mass_pct)}%`         : '—', true],
              ['Masa grasa (kg)',     ev.fat_mass_kg     != null ? `${f(ev.fat_mass_kg)} kg`        : '—', false],
              ['Masa magra (kg)',     ev.lean_mass_kg    != null ? `${f(ev.lean_mass_kg)} kg`       : '—', true],
              ['IMC',                 evBmi              != null ? `${evBmi}`                        : '—', false],
              ['Cintura (cm)',        ev.waist_cm        != null ? `${ev.waist_cm} cm`               : '—', false],
            ]
            return (
              <div className="space-y-4">
                <div className="bg-white rounded-xl shadow-sm border border-border overflow-hidden">
                  <div className="px-5 py-3 border-b border-border bg-bg-light flex items-center justify-between">
                    <span className="text-xs font-bold text-text-muted uppercase tracking-widest">Composición Corporal — {ev.date}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${ev.isak_level === 'ISAK 2' ? 'bg-primary/10 text-primary' : 'bg-sage/20 text-gray-600'}`}>{ev.isak_level ?? 'ISAK 1'}</span>
                  </div>
                  <table className="w-full">
                    <tbody className="divide-y divide-gray-100">
                      {rows.map(([label, val, highlight]) => (
                        <tr key={label} className={highlight ? 'bg-primary/5' : 'hover:bg-bg-light/50'}>
                          <td className={`px-5 py-3 text-sm w-1/2 ${highlight ? 'font-bold text-primary' : 'text-text-muted'}`}>{label}</td>
                          <td className={`px-5 py-3 text-sm text-right ${highlight ? 'font-bold text-primary' : 'font-semibold text-gray-800'}`}>{val}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {ev.somatotype_endo != null && (
                  <div className="bg-white rounded-xl shadow-sm border border-border overflow-hidden">
                    <div className="px-5 py-3 border-b border-border bg-bg-light">
                      <span className="text-xs font-bold text-text-muted uppercase tracking-widest">Somatotipo — Heath & Carter</span>
                    </div>
                    <div className="grid grid-cols-3 divide-x divide-gray-100">
                      {[['Endomorfia', ev.somatotype_endo], ['Mesomorfia', ev.somatotype_meso], ['Ectomorfia', ev.somatotype_ecto]].map(([label, val]) => (
                        <div key={String(label)} className="p-5 text-center">
                          <p className="text-xs text-text-muted uppercase tracking-wide mb-1">{label}</p>
                          <p className="text-2xl font-bold text-primary">{val != null ? Number(val).toFixed(2) : '—'}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })()}
        </div>
      </div>
    </Layout>
  )
}
