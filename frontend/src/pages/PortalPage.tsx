import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

const API = import.meta.env.VITE_API_URL as string

interface PortalInfo {
  patient_name: string
  nutritionist_name?: string
  clinic_name?: string
}

interface Pauta {
  id: number
  name: string
  date: string
  tipo_pauta: string
  kcal_objetivo: number
  prot_pct: number
  lip_pct: number
  cho_pct: number
  menu_json?: string
}

interface Evaluation {
  id: number
  date: string
  weight_kg?: number
  fat_mass_pct?: number
  lean_mass_kg?: number
}

export default function PortalPage() {
  const { token } = useParams<{ token: string }>()
  const [info, setInfo] = useState<PortalInfo | null>(null)
  const [pautas, setPautas] = useState<Pauta[]>([])
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'pauta' | 'progreso'>('pauta')

  useEffect(() => {
    if (!token) return
    Promise.all([
      fetch(`${API}/portal/${token}`).then(r => { if (!r.ok) throw new Error('invalid'); return r.json() }),
      fetch(`${API}/portal/${token}/pautas`).then(r => r.ok ? r.json() : []),
      fetch(`${API}/portal/${token}/evaluations`).then(r => r.ok ? r.json() : []),
    ])
      .then(([inf, pau, evs]) => {
        setInfo(inf)
        setPautas(Array.isArray(pau) ? pau : [])
        setEvaluations(Array.isArray(evs) ? evs : [])
      })
      .catch(() => setError('Este enlace ha expirado o no es válido.'))
      .finally(() => setLoading(false))
  }, [token])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F7F5F2] flex items-center justify-center">
        <div className="text-[#6b7280]">Cargando...</div>
      </div>
    )
  }

  if (error || !info) {
    return (
      <div className="min-h-screen bg-[#F7F5F2] flex items-center justify-center px-4">
        <div className="text-center max-w-sm">
          <div className="text-6xl mb-4">🔗</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Enlace no válido</h2>
          <p className="text-[#6b7280]">{error ?? 'Este enlace ha expirado o no es válido. Contacta a tu nutricionista.'}</p>
        </div>
      </div>
    )
  }

  const latestPauta = pautas[0]

  return (
    <div className="min-h-screen bg-[#F7F5F2]">
      {/* Header */}
      <div className="bg-[#4b7c60] text-white px-6 py-5">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-xl font-bold">{info.clinic_name ?? 'Portal del Paciente'}</h1>
          <p className="text-white/70 text-sm mt-0.5">
            Hola, <strong>{info.patient_name}</strong>
            {info.nutritionist_name && ` · Nutricionista: ${info.nutritionist_name}`}
          </p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">
        {/* Tabs */}
        <div className="flex gap-2 mb-6 bg-white border border-[#E5EAE7] rounded-xl p-1 w-fit">
          <button
            onClick={() => setActiveTab('pauta')}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-colors ${activeTab === 'pauta' ? 'bg-[#4b7c60] text-white' : 'text-[#6b7280] hover:text-[#4b7c60]'}`}
          >
            Mi Pauta
          </button>
          <button
            onClick={() => setActiveTab('progreso')}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-colors ${activeTab === 'progreso' ? 'bg-[#4b7c60] text-white' : 'text-[#6b7280] hover:text-[#4b7c60]'}`}
          >
            Mi Progreso
          </button>
        </div>

        {activeTab === 'pauta' && (
          <>
            {!latestPauta ? (
              <div className="bg-white rounded-xl border border-[#E5EAE7] p-8 text-center text-[#6b7280]">
                Tu nutricionista aún no ha creado una pauta.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-white rounded-xl border border-[#E5EAE7] p-5">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-bold text-gray-800">{latestPauta.name}</h3>
                    <span className="text-xs bg-[#4b7c60]/10 text-[#4b7c60] px-2 py-0.5 rounded-full font-medium">{latestPauta.tipo_pauta}</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="text-center p-3 bg-[#F7F5F2] rounded-lg">
                      <div className="text-2xl font-bold text-[#4b7c60]">{latestPauta.kcal_objetivo?.toFixed(0)}</div>
                      <div className="text-xs text-[#6b7280]">kcal/día</div>
                    </div>
                    <div className="text-center p-3 bg-[#F7F5F2] rounded-lg">
                      <div className="text-2xl font-bold text-[#4b7c60]">{latestPauta.prot_pct?.toFixed(0)}%</div>
                      <div className="text-xs text-[#6b7280]">Proteínas</div>
                    </div>
                    <div className="text-center p-3 bg-[#F7F5F2] rounded-lg">
                      <div className="text-2xl font-bold text-[#4b7c60]">{latestPauta.cho_pct?.toFixed(0)}%</div>
                      <div className="text-xs text-[#6b7280]">Carbohidratos</div>
                    </div>
                    <div className="text-center p-3 bg-[#F7F5F2] rounded-lg">
                      <div className="text-2xl font-bold text-[#4b7c60]">{latestPauta.lip_pct?.toFixed(0)}%</div>
                      <div className="text-xs text-[#6b7280]">Lípidos</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {activeTab === 'progreso' && (
          <>
            {evaluations.length === 0 ? (
              <div className="bg-white rounded-xl border border-[#E5EAE7] p-8 text-center text-[#6b7280]">
                Aún no tienes evaluaciones registradas.
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-[#E5EAE7] overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[400px]">
                    <thead className="bg-[#F7F5F2] border-b border-[#E5EAE7]">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-[#6b7280] uppercase">Fecha</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-[#6b7280] uppercase">Peso</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-[#6b7280] uppercase">% Grasa</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-[#6b7280] uppercase">Masa Magra</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...evaluations].reverse().map((ev, i) => (
                        <tr key={ev.id} className={`border-b border-[#E5EAE7] ${i === 0 ? 'bg-[#4b7c60]/5 font-semibold' : ''}`}>
                          <td className="px-4 py-3 text-sm text-gray-800">{ev.date}{i === 0 && <span className="ml-2 text-xs text-[#4b7c60]">↑ última</span>}</td>
                          <td className="px-4 py-3 text-sm text-right">{ev.weight_kg != null ? `${ev.weight_kg} kg` : '—'}</td>
                          <td className="px-4 py-3 text-sm text-right">{ev.fat_mass_pct != null ? `${ev.fat_mass_pct.toFixed(1)}%` : '—'}</td>
                          <td className="px-4 py-3 text-sm text-right">{ev.lean_mass_kg != null ? `${ev.lean_mass_kg.toFixed(1)} kg` : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        <p className="text-center text-xs text-[#6b7280] mt-8">
          Información generada por tu nutricionista. Solo lectura.
        </p>
      </div>
    </div>
  )
}
