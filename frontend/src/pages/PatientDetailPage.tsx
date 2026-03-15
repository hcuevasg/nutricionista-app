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
  id: number; date: string
  weight_kg?: number | null; fat_mass_pct?: number | null; lean_mass_kg?: number | null
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

          {activeTab === 'pliegues' && (
            <div className="bg-white rounded-xl shadow-sm border border-border p-6">
              <p className="text-text-muted text-sm">
                Selecciona una evaluación del historial para ver los pliegues cutáneos.
              </p>
              <div className="mt-4">
                <Link
                  to={`/patients/${id}/isak`}
                  className="inline-block bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm"
                >
                  Ver evaluaciones ISAK
                </Link>
              </div>
            </div>
          )}

          {activeTab === 'resultados' && (
            <div className="bg-white rounded-xl shadow-sm border border-border p-6">
              <p className="text-text-muted text-sm">
                Los resultados calculados aparecen en las evaluaciones ISAK individuales.
              </p>
              <div className="mt-4">
                <Link
                  to={`/patients/${id}/isak`}
                  className="inline-block bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm"
                >
                  Ver evaluaciones ISAK
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
