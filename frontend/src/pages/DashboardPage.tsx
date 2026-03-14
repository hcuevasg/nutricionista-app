import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

interface Stats {
  total_patients: number
  total_evaluations: number
  total_plans: number
  total_pautas: number
}

interface RecentPatient {
  id: number
  name: string
  sex: string
  birth_date?: string
  created_at?: string
  last_evaluation?: string
  last_plan?: string
}

function calcAge(bd?: string): number | null {
  if (!bd) return null
  const d = new Date(bd)
  if (isNaN(d.getTime())) return null
  const t = new Date()
  let age = t.getFullYear() - d.getFullYear()
  if (t.getMonth() < d.getMonth() || (t.getMonth() === d.getMonth() && t.getDate() < d.getDate())) age--
  return age >= 0 ? age : null
}

function StatCard({ label, value, color }: { label: string; value: number | null; color: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-text-muted text-sm font-medium">{label}</h3>
      <p className={`text-3xl font-bold mt-2 ${color}`}>
        {value == null ? '—' : value}
      </p>
    </div>
  )
}

export default function DashboardPage() {
  const { token, user } = useAuth()
  const [stats, setStats] = useState<Stats | null>(null)
  const [recent, setRecent] = useState<RecentPatient[]>([])
  const [loading, setLoading] = useState(true)

  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    if (!token) return
    Promise.all([
      fetch(`${API}/dashboard/stats`, { headers: H }).then(r => r.json()),
      fetch(`${API}/dashboard/recent-patients`, { headers: H }).then(r => r.json()),
    ])
      .then(([s, r]) => {
        setStats(s)
        setRecent(Array.isArray(r) ? r : [])
      })
      .finally(() => setLoading(false))
  }, [token])

  return (
    <Layout title="Dashboard">
      {/* Greeting */}
      <p className="text-text-muted mb-6">
        Bienvenido, <span className="font-semibold text-primary">{user?.username}</span>
      </p>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard label="Total Pacientes"       value={loading ? null : stats?.total_patients ?? 0}    color="text-primary" />
        <StatCard label="Evaluaciones ISAK"     value={loading ? null : stats?.total_evaluations ?? 0} color="text-terracotta" />
        <StatCard label="Planes Alimenticios"   value={loading ? null : stats?.total_plans ?? 0}       color="text-sage" />
        <StatCard label="Pautas Nutricionales"  value={loading ? null : stats?.total_pautas ?? 0}      color="text-primary-dark" />
      </div>

      {/* Recent patients */}
      <div className="mt-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-primary">Pacientes recientes</h2>
          <Link to="/patients" className="text-sm text-primary hover:underline">
            Ver todos →
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loading ? (
            <div className="p-6 text-center text-text-muted text-sm">Cargando...</div>
          ) : recent.length === 0 ? (
            <div className="p-8 text-center text-text-muted text-sm space-y-3">
              <p>No hay pacientes registrados aún.</p>
              <Link
                to="/patients/new"
                className="inline-block bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm"
              >
                + Agregar primer paciente
              </Link>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-bg-light border-b border-border">
                <tr>
                  {['Paciente', 'Edad / Sexo', 'Última evaluación', 'Último plan', 'Acciones'].map(h => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recent.map(p => {
                  const age = calcAge(p.birth_date)
                  return (
                    <tr key={p.id} className="border-b border-border hover:bg-bg-light">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-bold">
                            {p.name.slice(0, 2).toUpperCase()}
                          </div>
                          <span className="text-sm font-medium text-gray-800">{p.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-text-muted">
                        {age != null ? `${age} años` : '—'} · {p.sex}
                      </td>
                      <td className="px-6 py-4 text-sm text-text-muted">
                        {p.last_evaluation ?? <span className="text-gray-400 italic">Sin evaluación</span>}
                      </td>
                      <td className="px-6 py-4 text-sm text-text-muted">
                        {p.last_plan ?? <span className="text-gray-400 italic">Sin plan</span>}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-3 text-sm">
                          <Link to={`/patients/${p.id}`} className="text-primary hover:underline">Ver</Link>
                          <Link to={`/patients/${p.id}/isak`} className="text-text-muted hover:underline">ISAK</Link>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/patients/new"
          className="bg-white rounded-lg shadow p-5 hover:shadow-md transition-shadow flex items-center gap-4 group">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary text-lg group-hover:bg-primary group-hover:text-white transition-colors">+</div>
          <div>
            <p className="font-medium text-gray-800 text-sm">Nuevo Paciente</p>
            <p className="text-xs text-text-muted">Registrar datos personales</p>
          </div>
        </Link>

        <Link to="/patients"
          className="bg-white rounded-lg shadow p-5 hover:shadow-md transition-shadow flex items-center gap-4 group">
          <div className="w-10 h-10 rounded-lg bg-terracotta/10 flex items-center justify-center text-terracotta text-lg group-hover:bg-terracotta group-hover:text-white transition-colors">📋</div>
          <div>
            <p className="font-medium text-gray-800 text-sm">Ver Pacientes</p>
            <p className="text-xs text-text-muted">Lista completa</p>
          </div>
        </Link>

        <Link to="/patients"
          className="bg-white rounded-lg shadow p-5 hover:shadow-md transition-shadow flex items-center gap-4 group">
          <div className="w-10 h-10 rounded-lg bg-sage/20 flex items-center justify-center text-gray-600 text-lg group-hover:bg-sage group-hover:text-white transition-colors">📊</div>
          <div>
            <p className="font-medium text-gray-800 text-sm">Nueva Evaluación ISAK</p>
            <p className="text-xs text-text-muted">Selecciona un paciente</p>
          </div>
        </Link>
      </div>
    </Layout>
  )
}
