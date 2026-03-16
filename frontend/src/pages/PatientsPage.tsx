import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { SkeletonTableRows } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'
import { api } from '../api/client'

interface Patient {
  id: number
  name: string
  birth_date?: string
  sex?: string
  email?: string
  phone?: string
}

interface PaginatedPatients {
  items: Patient[]
  total: number
  skip: number
  limit: number
}

function calcAge(bd?: string): number | null {
  if (!bd) return null
  const d = new Date(bd)
  if (isNaN(d.getTime())) return null
  const today = new Date()
  let age = today.getFullYear() - d.getFullYear()
  if (today.getMonth() < d.getMonth() || (today.getMonth() === d.getMonth() && today.getDate() < d.getDate())) age--
  return age >= 0 ? age : null
}

const PAGE_SIZE = 50

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const toast = useToast()

  const loadPatients = useCallback(async (skip = 0, search = '') => {
    try {
      const params: Record<string, string | number> = { skip, limit: PAGE_SIZE }
      if (search.trim()) params.q = search.trim()
      const data = await api.get<PaginatedPatients>('/patients', params)
      if (skip === 0) {
        setPatients(data.items)
      } else {
        setPatients(prev => [...prev, ...data.items])
      }
      setTotal(data.total)
    } catch {
      const msg = 'Error al cargar pacientes'
      setError(msg)
      toast.error(msg)
    }
  }, [toast])

  // Initial load
  useEffect(() => {
    setLoading(true)
    setError(null)
    loadPatients(0, query).finally(() => setLoading(false))
  }, [query]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleLoadMore = async () => {
    setLoadingMore(true)
    await loadPatients(patients.length, query)
    setLoadingMore(false)
  }

  const hasMore = patients.length < total

  return (
    <Layout title="Pacientes">
      <div className="flex flex-col sm:flex-row gap-3 justify-between items-start sm:items-center mb-6">
        <div className="relative w-full sm:w-72">
          <input
            type="text"
            placeholder="Buscar por nombre, email o teléfono..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="pl-9 pr-4 py-2 w-full border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">🔍</span>
        </div>
        <Link
          to="/patients/new"
          className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-medium flex-shrink-0"
        >
          + Nuevo Paciente
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden overflow-x-auto">
        <table className="w-full min-w-[480px]">
          <thead className="bg-bg-light border-b border-border">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Paciente</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Edad / Sexo</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Contacto</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <SkeletonTableRows cols={4} rows={5} />
            ) : patients.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-12 text-center">
                  {query ? (
                    <p className="text-text-muted text-sm">Sin resultados para "<strong>{query}</strong>"</p>
                  ) : (
                    <div className="space-y-3">
                      <p className="text-text-muted text-sm">No hay pacientes registrados aún.</p>
                      <Link
                        to="/patients/new"
                        className="inline-block bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm"
                      >
                        + Agregar primer paciente
                      </Link>
                    </div>
                  )}
                </td>
              </tr>
            ) : (
              patients.map(p => {
                const age = calcAge(p.birth_date)
                return (
                  <tr key={p.id} className="border-b border-border hover:bg-bg-light transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-bold flex-shrink-0">
                          {p.name.slice(0, 2).toUpperCase()}
                        </div>
                        <span className="text-sm font-medium text-gray-800">{p.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-text-muted">
                      {age != null ? `${age} años` : '—'}
                      {p.sex ? ` · ${p.sex}` : ''}
                    </td>
                    <td className="px-6 py-4 text-sm text-text-muted">
                      <div>{p.email || <span className="italic text-gray-300">sin email</span>}</div>
                      <div>{p.phone || ''}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-3 text-sm">
                        <Link to={`/patients/${p.id}`} className="text-primary hover:underline font-medium">Ver</Link>
                        <Link to={`/patients/${p.id}/edit`} className="text-text-muted hover:text-gray-700 hover:underline">Editar</Link>
                        <Link to={`/patients/${p.id}/isak`} className="text-text-muted hover:text-gray-700 hover:underline">ISAK</Link>
                      </div>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>

        {!loading && (
          <div className="px-6 py-3 border-t border-border bg-bg-light flex items-center justify-between text-xs text-text-muted">
            <span>
              {patients.length} de {total} paciente{total !== 1 ? 's' : ''}
            </span>
            {hasMore && (
              <button
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="text-primary hover:underline font-medium disabled:opacity-50"
              >
                {loadingMore ? 'Cargando...' : `Cargar más (${total - patients.length} restantes)`}
              </button>
            )}
          </div>
        )}
      </div>
    </Layout>
  )
}
