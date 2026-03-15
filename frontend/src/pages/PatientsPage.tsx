import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate, Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { SkeletonTableRows } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'

interface Patient {
  id: number
  name: string
  birth_date?: string
  sex?: string
  email?: string
  phone?: string
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

export default function PatientsPage() {
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const toast = useToast()

  useEffect(() => {
    if (!token) return
    fetch(`${import.meta.env.VITE_API_URL}/patients`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => {
        if (r.status === 401) { logout(); navigate('/login'); return null }
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => data && setPatients(Array.isArray(data) ? data : []))
      .catch(err => { const msg = err instanceof Error ? err.message : 'Error al cargar pacientes'; setError(msg); toast.error(msg) })
      .finally(() => setLoading(false))
  }, [token])

  const filtered = query.trim()
    ? patients.filter(p =>
        p.name.toLowerCase().includes(query.toLowerCase()) ||
        p.email?.toLowerCase().includes(query.toLowerCase()) ||
        p.phone?.includes(query)
      )
    : patients

  return (
    <Layout title="Pacientes">
      <div className="flex justify-between items-center mb-6">
        <div className="relative">
          <input
            type="text"
            placeholder="Buscar por nombre, email o teléfono..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="pl-9 pr-4 py-2 w-72 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">🔍</span>
        </div>
        <Link
          to="/patients/new"
          className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          + Nuevo Paciente
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
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
            ) : filtered.length === 0 ? (
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
              filtered.map(p => {
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

        {!loading && filtered.length > 0 && (
          <div className="px-6 py-3 border-t border-border bg-bg-light text-xs text-text-muted">
            {filtered.length} paciente{filtered.length !== 1 ? 's' : ''}
            {query && patients.length !== filtered.length ? ` de ${patients.length} total` : ''}
          </div>
        )}
      </div>
    </Layout>
  )
}
