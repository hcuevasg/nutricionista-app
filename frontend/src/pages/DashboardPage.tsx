import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'
import { SkeletonStatCards, SkeletonTableRows } from '../components/Skeleton'
import { api } from '../api/client'

interface Stats {
  total_patients: number
  total_evaluations: number
  total_plans: number
  total_pautas: number
}

interface UpcomingAppointment {
  id: number
  patient_name?: string
  scheduled_at: string
  duration_minutes: number
  status: string
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

function getGreeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Buenos días'
  if (h < 18) return 'Buenas tardes'
  return 'Buenas noches'
}

function getDateEs(): string {
  return new Date().toLocaleDateString('es-CL', { day: 'numeric', month: 'long' })
}

interface StatCardProps {
  label: string
  value: number | null
  borderColor: string
  badge: string
  badgeColor: string
  icon: string
}

function StatCard({ label, value, borderColor, badge, badgeColor, icon }: StatCardProps) {
  return (
    <div className={`bg-white rounded-xl shadow-sm ring-1 ring-gray-200 p-6 border-l-4 ${borderColor}`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-lg leading-none">{icon}</span>
        <span className={`text-xs font-bold px-2 py-1 rounded-full ${badgeColor}`}>{badge}</span>
      </div>
      <p className="text-text-muted text-sm font-medium">{label}</p>
      <p className="text-3xl font-bold text-gray-800 mt-1">
        {value == null ? '—' : value}
      </p>
    </div>
  )
}

export default function DashboardPage() {
  const { token, user } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState<Stats | null>(null)
  const [recent, setRecent] = useState<RecentPatient[]>([])
  const [loading, setLoading] = useState(true)

  const [upcomingAppts, setUpcomingAppts] = useState<UpcomingAppointment[]>([])
  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    if (!token) return
    Promise.all([
      fetch(`${API}/dashboard/stats`, { headers: H }).then(r => r.json()),
      fetch(`${API}/dashboard/recent-patients`, { headers: H }).then(r => r.json()),
      api.get<UpcomingAppointment[]>('/appointments', { limit: 5 }).catch(() => []),
    ])
      .then(([s, r, appts]) => {
        setStats(s)
        setRecent(Array.isArray(r) ? r : [])
        setUpcomingAppts(Array.isArray(appts) ? appts : [])
      })
      .finally(() => setLoading(false))
  }, [token])

  return (
    <Layout title="Dashboard">
      {/* Greeting header */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800">
          {getGreeting()} — {getDateEs()}
        </h2>
        <p className="text-text-muted mt-1 font-medium italic">
          {stats != null
            ? `Tienes ${stats.total_patients} paciente${stats.total_patients !== 1 ? 's' : ''} registrado${stats.total_patients !== 1 ? 's' : ''}`
            : 'Cargando estadísticas...'}
        </p>
      </div>

      {/* Stats */}
      {loading ? <SkeletonStatCards /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            label="Total Pacientes"
            value={stats?.total_patients ?? 0}
            borderColor="border-primary"
            badge="Pacientes"
            badgeColor="text-primary bg-primary/10"
            icon="◉"
          />
          <StatCard
            label="Evaluaciones ISAK"
            value={stats?.total_evaluations ?? 0}
            borderColor="border-terracotta"
            badge="ISAK 1+2"
            badgeColor="text-terracotta bg-terracotta/10"
            icon="⊙"
          />
          <StatCard
            label="Planes Alimenticios"
            value={stats?.total_plans ?? 0}
            borderColor="border-[#d9a441]"
            badge="Planes"
            badgeColor="text-amber-600 bg-amber-100"
            icon="⊛"
          />
          <StatCard
            label="Pautas Nutricionales"
            value={stats?.total_pautas ?? 0}
            borderColor="border-sage"
            badge="Pautas IA"
            badgeColor="text-green-600 bg-green-100"
            icon="⊡"
          />
        </div>
      )}

      {/* Main grid: table + sidebar */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-10 gap-6 lg:gap-8">

        {/* Left: Recent patients table */}
        <section className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-800">Últimos pacientes atendidos</h3>
            <Link to="/patients" className="text-sm text-primary font-semibold hover:underline">
              Ver todos →
            </Link>
          </div>

          <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-200 overflow-hidden overflow-x-auto">
            {loading ? (
              <table className="w-full min-w-[520px]"><tbody><SkeletonTableRows cols={5} rows={4} /></tbody></table>
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
              <table className="w-full min-w-[520px] text-left">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    {['Paciente', 'Edad / Sexo', 'Última evaluación', 'Estado', ''].map(h => (
                      <th key={h} className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {recent.map(p => {
                    const age = calcAge(p.birth_date)
                    const hasEval = !!p.last_evaluation
                    return (
                      <tr
                        key={p.id}
                        className="hover:bg-bg-light/50 transition-colors cursor-pointer group"
                        onClick={() => navigate(`/patients/${p.id}`)}
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-primary/10 border-2 border-primary/20 flex items-center justify-center text-primary text-xs font-bold">
                              {p.name.slice(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-gray-800">{p.name}</p>
                              {age != null && <p className="text-xs text-text-muted">{age} años</p>}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-text-muted">
                          {age != null ? `${age} años` : '—'} · {p.sex}
                        </td>
                        <td className="px-6 py-4 text-sm text-text-muted">
                          {p.last_evaluation ?? <span className="italic text-gray-400">Sin evaluación</span>}
                        </td>
                        <td className="px-6 py-4">
                          {hasEval ? (
                            <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-green-100 text-green-700 uppercase tracking-wider">
                              En seguimiento
                            </span>
                          ) : (
                            <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-amber-100 text-amber-600 uppercase tracking-wider">
                              Sin pauta
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <span className="text-gray-300 group-hover:text-primary transition-colors text-lg">›</span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </section>

        {/* Right: Quick actions sidebar */}
        <aside className="lg:col-span-3 space-y-6">
          {/* Quick access buttons */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-gray-800">Accesos Rápidos</h3>
            <div className="grid grid-cols-1 gap-3">
              <Link
                to="/patients/new"
                className="flex items-center gap-3 p-4 bg-primary text-white rounded-xl hover:bg-primary-dark transition-all shadow-md"
              >
                <span className="bg-white/20 p-2 rounded-lg text-base leading-none">◉</span>
                <span className="font-medium">Nuevo paciente</span>
              </Link>
              <Link
                to="/patients"
                className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-primary/40 hover:bg-bg-light transition-all shadow-sm group"
              >
                <span className="text-primary bg-primary/10 p-2 rounded-lg group-hover:bg-primary group-hover:text-white transition-colors text-base leading-none">⊙</span>
                <span className="font-medium text-gray-700">Nueva evaluación ISAK</span>
              </Link>
              <Link
                to="/patients"
                className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-primary/40 hover:bg-bg-light transition-all shadow-sm group"
              >
                <span className="text-primary bg-primary/10 p-2 rounded-lg group-hover:bg-primary group-hover:text-white transition-colors text-base leading-none">⊡</span>
                <span className="font-medium text-gray-700">Nueva pauta nutricional</span>
              </Link>
            </div>
          </div>

          {/* Proximas consultas */}
          <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-200 p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-800">Proximas consultas</h3>
              <Link to="/agenda" className="text-xs text-primary font-semibold hover:underline">Ver agenda →</Link>
            </div>
            {upcomingAppts.length === 0 ? (
              <p className="text-sm text-text-muted text-center py-3">Sin consultas proximas.</p>
            ) : (
              <ul className="space-y-3">
                {upcomingAppts.map(appt => {
                  const d = new Date(appt.scheduled_at)
                  const dateStr = d.toLocaleDateString('es-CL', { weekday: 'short', day: 'numeric', month: 'short' })
                  const timeStr = d.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' })
                  return (
                    <li key={appt.id} className="flex items-start gap-3">
                      <div className="mt-0.5 w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0 mt-2"></div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">
                          {appt.patient_name ?? <span className="italic text-gray-400">Sin paciente</span>}
                        </p>
                        <p className="text-xs text-text-muted">{dateStr} · {timeStr}</p>
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
            <Link
              to="/agenda"
              className="mt-4 w-full block py-2 bg-primary/5 text-primary text-xs font-bold rounded-lg border border-primary/20 hover:bg-primary hover:text-white transition-all text-center"
            >
              + Nueva cita
            </Link>
          </div>

          {/* Resumen de actividad */}
          <div className="bg-primary/5 rounded-xl p-6 border border-primary/10 relative overflow-hidden">
            <div className="relative z-10">
              <h3 className="text-lg font-bold text-primary mb-4">Resumen</h3>
              {stats == null ? (
                <p className="text-sm text-text-muted">Cargando...</p>
              ) : (
                <div className="space-y-3">
                  {[
                    { label: 'Pacientes activos', value: stats.total_patients, color: 'bg-primary' },
                    { label: 'Evaluaciones totales', value: stats.total_evaluations, color: 'bg-terracotta' },
                    { label: 'Planes alimenticios', value: stats.total_plans, color: 'bg-[#d9a441]' },
                    { label: 'Pautas con IA', value: stats.total_pautas, color: 'bg-sage' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full ${color}`}></div>
                        <span className="text-sm text-gray-700">{label}</span>
                      </div>
                      <span className="text-sm font-bold text-gray-800">{value}</span>
                    </div>
                  ))}
                </div>
              )}
              <Link
                to="/patients"
                className="mt-6 w-full block py-2 bg-white text-primary text-xs font-bold rounded-lg border border-primary/20 hover:bg-primary hover:text-white transition-all text-center"
              >
                Ver todos los pacientes
              </Link>
            </div>
            <div className="absolute -bottom-4 -right-4 text-primary/5 select-none text-[120px] leading-none">
              ✦
            </div>
          </div>
        </aside>
      </div>
    </Layout>
  )
}
