import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'
import { SkeletonTableRows } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'

interface Pauta {
  id: number
  name: string
  date: string
  tipo_pauta: string
  kcal_objetivo: number
  prot_g: number
  lip_g: number
  cho_g: number
  prot_pct: number
  lip_pct: number
  cho_pct: number
  created_at: string
}

const TIPO_LABELS: Record<string, string> = {
  omnivoro: 'Omnívoro',
  ovolacto: 'Ovo-lacto vegetariano',
  vegano: 'Vegano',
  vegetariano: 'Vegetariano',
  renal: 'Renal',
  diabetico: 'Diabético',
  hipocalorico: 'Hipocalórico',
}

function fmt(v?: number | null, d = 0) { return v != null ? v.toFixed(d) : '—' }

export default function PautasPage() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()
  const [patientName, setPatientName] = useState('')
  const [pautas, setPautas] = useState<Pauta[]>([])
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
      fetch(`${API}/pautas/${id}`, { headers: H }).then(r => r.json()),
    ])
      .then(([pat, pl]) => {
        setPatientName(pat.name ?? '')
        setPautas(Array.isArray(pl) ? pl : [])
      })
      .catch(() => setError('Error al cargar pautas'))
      .finally(() => setLoading(false))
  }, [id, token])

  const handleDelete = async (pautaId: number) => {
    if (!confirm('¿Eliminar esta pauta?')) return
    await fetch(`${API}/pautas/${id}/${pautaId}`, { method: 'DELETE', headers: H })
    setPautas(prev => prev.filter(p => p.id !== pautaId))
    toast.success('Pauta eliminada')
  }

  const handleDownloadPdf = async (p: Pauta) => {
    setDownloadingId(p.id)
    try {
      const res = await fetch(`${API}/pautas/${id}/${p.id}/pdf`, { headers: H })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Pauta_${p.name.replace(/ /g, '_')}_${p.date}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('No se pudo descargar el PDF')
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <Layout title={`Pautas — ${patientName}`}>
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <Link to={`/patients/${id}`} className="hover:text-primary">{patientName || `Paciente ${id}`}</Link>
        <span>/</span>
        <span className="text-primary font-medium">Pautas Nutricionales</span>
      </div>

      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      <div className="flex justify-end mb-4">
        <Link to={`/patients/${id}/pautas/new`}
          className="bg-primary hover:bg-primary-dark text-white px-5 py-2 rounded-lg">
          + Nueva Pauta
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <table className="w-full"><tbody><SkeletonTableRows cols={8} rows={4} /></tbody></table>
        ) : pautas.length === 0 ? (
          <div className="p-8 text-center text-text-muted text-sm space-y-3">
            <p>No hay pautas nutricionales registradas.</p>
            <Link to={`/patients/${id}/pautas/new`}
              className="inline-block bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm">
              + Crear primera pauta
            </Link>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-bg-light border-b border-border">
              <tr>
                {['Nombre', 'Fecha', 'Tipo', 'Kcal obj.', 'Prot.', 'Lip.', 'CHO', 'PDF', 'Acciones'].map(h => (
                  <th key={h} className={`px-4 py-3 text-xs font-medium text-gray-600 uppercase ${
                    ['Kcal obj.', 'Prot.', 'Lip.', 'CHO'].includes(h) ? 'text-right' : 'text-left'
                  }`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pautas.map(p => (
                <tr key={p.id} className="border-b border-border hover:bg-bg-light">
                  <td className="px-4 py-3 text-sm font-medium text-gray-800">{p.name}</td>
                  <td className="px-4 py-3 text-sm text-text-muted">{p.date}</td>
                  <td className="px-4 py-3 text-sm text-text-muted">
                    <span className="px-2 py-0.5 bg-primary/10 text-primary rounded text-xs">
                      {TIPO_LABELS[p.tipo_pauta] ?? p.tipo_pauta}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-medium text-primary">{fmt(p.kcal_objetivo)} kcal</td>
                  <td className="px-4 py-3 text-sm text-right text-text-muted">{fmt(p.prot_g, 1)}g <span className="text-xs text-gray-400">({fmt(p.prot_pct)}%)</span></td>
                  <td className="px-4 py-3 text-sm text-right text-text-muted">{fmt(p.lip_g, 1)}g <span className="text-xs text-gray-400">({fmt(p.lip_pct)}%)</span></td>
                  <td className="px-4 py-3 text-sm text-right text-text-muted">{fmt(p.cho_g, 1)}g <span className="text-xs text-gray-400">({fmt(p.cho_pct)}%)</span></td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDownloadPdf(p)}
                      disabled={downloadingId === p.id}
                      className="text-xs text-terracotta hover:underline disabled:opacity-50"
                    >
                      {downloadingId === p.id ? '...' : '⬇ PDF'}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-3 text-sm">
                      <Link to={`/patients/${id}/pautas/${p.id}`} className="text-primary hover:underline">Ver</Link>
                      <Link to={`/patients/${id}/pautas/${p.id}/edit`} className="text-sage hover:underline">Editar</Link>
                      <button onClick={() => handleDelete(p.id)} className="text-red-400 hover:underline">Eliminar</button>
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
