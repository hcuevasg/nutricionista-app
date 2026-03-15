import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'
import { SkeletonTableRows } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'

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

function fmt(v?: number | null) { return v != null ? v.toFixed(0) : '--' }

function macroBadge(g: number | null | undefined, kcal: number | null | undefined, factor: number) {
  if (g == null) return '--'
  const pct = kcal ? ((g * factor) / kcal * 100).toFixed(0) : '?'
  return `${g.toFixed(0)}g (${pct}%)`
}

export default function MealPlansPage() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()
  const [patientName, setPatientName] = useState('')
  const [plans, setPlans] = useState<MealPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const toast = useToast()

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
    toast.success('Plan eliminado')
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
      toast.error('No se pudo descargar el PDF')
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <Layout title={`Planes -- ${patientName}`}>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <Link to={`/patients/${id}`} className="hover:text-primary">{patientName || `Paciente ${id}`}</Link>
        <span>/</span>
        <span className="text-primary font-medium">Planes Alimenticios</span>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">{error}</div>}

      {/* Page header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-gray-900">Planes Alimenticios</h1>
          <p className="text-text-muted font-medium mt-0.5">
            Paciente: <span className="text-gray-900">{patientName}</span>
          </p>
        </div>
        <Link
          to={`/patients/${id}/plans/new`}
          className="flex items-center gap-2 bg-primary hover:bg-primary-dark text-white px-5 py-2.5 rounded-xl font-bold shadow-sm transition-all"
        >
          + Nuevo Plan
        </Link>
      </div>

      {/* Plans table */}
      <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-200 overflow-hidden">
        {loading ? (
          <table className="w-full"><tbody><SkeletonTableRows cols={8} rows={4} /></tbody></table>
        ) : plans.length === 0 ? (
          <div className="p-10 text-center text-text-muted text-sm space-y-4">
            <div className="text-4xl mb-2">&#9744;</div>
            <p className="font-medium">No hay planes registrados.</p>
            <Link to={`/patients/${id}/plans/new`}
              className="inline-block bg-primary hover:bg-primary-dark text-white px-5 py-2.5 rounded-xl font-bold">
              + Crear primer plan
            </Link>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Plan', 'Fecha', 'Objetivo', 'Kcal', 'Proteinas', 'Carbos', 'Grasas', 'PDF', 'Acciones'].map(h => (
                  <th key={h} className={`px-4 py-3.5 text-xs font-bold text-gray-400 uppercase tracking-wider ${
                    ['Kcal','Proteinas','Carbos','Grasas'].includes(h) ? 'text-right' : 'text-left'
                  }`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {plans.map(plan => (
                <tr key={plan.id} className="hover:bg-bg-light/50 transition-colors">
                  <td className="px-4 py-3.5 text-sm font-semibold text-gray-800">{plan.name}</td>
                  <td className="px-4 py-3.5 text-sm text-text-muted">{plan.date}</td>
                  <td className="px-4 py-3.5 text-sm text-text-muted">{plan.goal ?? '--'}</td>
                  <td className="px-4 py-3.5 text-sm text-right font-bold text-primary">{fmt(plan.calories)} kcal</td>
                  <td className="px-4 py-3.5 text-sm text-right text-text-muted">
                    {macroBadge(plan.protein_g, plan.calories, 4)}
                  </td>
                  <td className="px-4 py-3.5 text-sm text-right text-text-muted">
                    {macroBadge(plan.carbs_g, plan.calories, 4)}
                  </td>
                  <td className="px-4 py-3.5 text-sm text-right text-text-muted">
                    {macroBadge(plan.fat_g, plan.calories, 9)}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <button
                      onClick={() => handleDownloadPdf(plan)}
                      disabled={downloadingId === plan.id}
                      className="text-xs font-bold text-terracotta hover:underline disabled:opacity-50"
                    >
                      {downloadingId === plan.id ? '...' : '\u2B07 PDF'}
                    </button>
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex gap-3 text-sm">
                      <Link to={`/patients/${id}/plans/${plan.id}/edit`} className="text-primary font-medium hover:underline">Ver / Editar</Link>
                      <button onClick={() => handleDelete(plan.id)} className="text-red-400 font-medium hover:underline">Eliminar</button>
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
