import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'
import IsAkEvolutionChart from '../components/IsAkEvolutionChart'

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

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()
  const navigate = useNavigate()
  const [patient, setPatient] = useState<Patient | null>(null)
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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

  return (
    <Layout title={patient.name}>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <span className="text-primary font-medium">{patient.name}</span>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Main content */}
        <div className="col-span-2 space-y-6">
          {/* Patient info card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-xl font-bold text-gray-800">{patient.name}</h2>
                <p className="text-sm text-text-muted mt-1">
                  {patient.sex}{age != null ? ` · ${age} años` : ''}
                  {patient.birth_date ? ` · Nacido: ${patient.birth_date}` : ''}
                </p>
              </div>
              <Link
                to={`/patients/${id}/edit`}
                className="text-sm text-primary hover:underline"
              >
                Editar
              </Link>
            </div>

            <dl className="grid grid-cols-2 gap-x-8 gap-y-4">
              <InfoRow label="Teléfono" value={patient.phone} />
              <InfoRow label="Correo electrónico" value={patient.email} />
              <InfoRow label="Ocupación" value={patient.occupation} />
              <InfoRow label="Dirección" value={patient.address} />
              <InfoRow label="Talla" value={patient.height_cm != null ? `${patient.height_cm} cm` : null} />
              <InfoRow label="Peso" value={patient.weight_kg != null ? `${patient.weight_kg} kg` : null} />
            </dl>

            {patient.notes && (
              <div className="mt-6 pt-6 border-t border-border">
                <dt className="text-xs text-text-muted uppercase tracking-wide mb-1">Notas / Antecedentes</dt>
                <dd className="text-sm text-gray-700 whitespace-pre-wrap">{patient.notes}</dd>
              </div>
            )}
          </div>

          <IsAkEvolutionChart evaluations={evaluations} />
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-bold text-primary mb-4 text-sm">Acciones Rápidas</h3>
            <div className="space-y-2">
              <Link
                to={`/patients/${id}/isak`}
                className="block w-full bg-primary hover:bg-primary-dark text-white py-2 rounded text-sm text-center"
              >
                + Nueva evaluación ISAK
              </Link>
              <Link
                to={`/patients/${id}/plans/new`}
                className="block w-full bg-terracotta hover:opacity-90 text-white py-2 rounded text-sm text-center"
              >
                + Plan alimenticio
              </Link>
              <button className="w-full bg-sage hover:opacity-90 text-white py-2 rounded text-sm">
                + Pauta nutricional
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-bold text-primary mb-3 text-sm">Navegación</h3>
            <div className="space-y-1">
              <Link
                to={`/patients/${id}/isak`}
                className="block px-3 py-2 rounded text-sm text-gray-700 hover:bg-bg-light hover:text-primary"
              >
                Evaluaciones ISAK
              </Link>
              <Link
                to={`/patients/${id}/plans`}
                className="block px-3 py-2 rounded text-sm text-gray-700 hover:bg-bg-light hover:text-primary"
              >
                Planes alimenticios
              </Link>
              <button className="block w-full text-left px-3 py-2 rounded text-sm text-gray-400 cursor-not-allowed">
                Pautas nutricionales
              </button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
