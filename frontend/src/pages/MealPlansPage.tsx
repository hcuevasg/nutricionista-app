import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

interface MealPlan {
  id: number
  name: string
  date: string
  goal?: string
  calories?: number
  protein_g?: number
  carbs_g?: number
  fat_g?: number
  notes?: string
  created_at: string
}

function fmt(v?: number | null) { return v != null ? v.toFixed(0) : '—' }

export default function MealPlansPage() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()
  const [patientName, setPatientName] = useState('')
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)

  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    if (!token || !id) return
    Promise.all([
      fetch(`${API}/patients/${id}`, { headers: H }).then(r => r.json()),
      fetch(`${API}/meal-plans/${id}`, { headers: H }).then(r => r.json()),
    ])
      .then(([pat, pl]) => { setPatientName(pat.name ?? ''); setPlans(Array.isArray(pl) ? pl : []) })
      .catch(() => setError('Error al cargar planes'))
      .finally(() => setLoading(false))
  }, [id, token])

  const handleDelete = async (planId: number) => {
    if (!confirm('¿Eliminar este plan?')) return
    await fetch(`${API}/meal-plans/${id}/${planId}`, { method: 'DELETE', headers: H })
    setPlans(prev => prev.filter(p => p.id !== planId))
  }

  const handleDownloadPdf = async (plan: MealPlan) => {
    setDownloadingId(plan.id)
    try {
      const res = await fetch(`${API}/meal-plans/${id}/${plan.id}/pdf`, { headers: H })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Plan_${plan.name.replace(/ /g, '_')}_${plan.date}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('No se pudo descargar el PDF')
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <Layout title={`Planes — ${patientName}`}>
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <Link to={`/patients/${id}`} className="hover:text-primary">{patientName || `Paciente ${id}`}</Link>
        <span>/</span>
        <span className="text-primary font-medium">Planes Alimenticios</span>
      </div>

      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      <div className="flex justify-end mb-4">
        <Link to={`/patients/${id}/plans/new`}
          className="bg-primary hover:bg-primary-dark text-white px-5 py-2 rounded-lg">
          + Nuevo Plan
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-text-muted text-sm">Cargando...</div>
        ) : plans.length === 0 ? (
          <div className="p-8 text-center text-text-muted text-sm space-y-3">
            <p>No hay planes registrados.</p>
            <Link to={`/patients/${id}/plans/new`}
              className="inline-block bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm">
              + Crear primer plan
            </Link>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-bg-light border-b border-border">
              <tr>
                {['Plan', 'Fecha', 'Objetivo', 'Kcal', 'Prot.', 'Carbos', 'Grasas', 'PDF', 'Acciones'].map(h => (
                  <th key={h} className={`px-4 py-3 text-xs font-medium text-gray-600 uppercase ${
                    ['Kcal','Prot.','Carbos','Grasas'].includes(h) ? 'text-right' : 'text-left'
                  }`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {plans.map(plan => (
                <tr key={plan.id} className="border-b border-border hover:bg-bg-light">
                  <td className="px-4 py-3 text-sm font-medium text-gray-800">{plan.name}</td>
                  <td className="px-4 py-3 text-sm text-text-muted">{plan.date}</td>
                  <td className="px-4 py-3 text-sm text-text-muted">{plan.goal ?? '—'}</td>
                  <td className="px-4 py-3 text-sm text-right font-medium text-primary">{fmt(plan.calories)}</td>
                  <td className="px-4 py-3 text-sm text-right text-text-muted">{fmt(plan.protein_g)}g</td>
                  <td className="px-4 py-3 text-sm text-right text-text-muted">{fmt(plan.carbs_g)}g</td>
                  <td className="px-4 py-3 text-sm text-right text-text-muted">{fmt(plan.fat_g)}g</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDownloadPdf(plan)}
                      disabled={downloadingId === plan.id}
                      className="text-xs text-terracotta hover:underline disabled:opacity-50"
                    >
                      {downloadingId === plan.id ? '...' : '⬇ PDF'}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-3 text-sm">
                      <Link to={`/patients/${id}/plans/${plan.id}/edit`} className="text-primary hover:underline">Ver / Editar</Link>
                      <button onClick={() => handleDelete(plan.id)} className="text-red-400 hover:underline">Eliminar</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  )
}
