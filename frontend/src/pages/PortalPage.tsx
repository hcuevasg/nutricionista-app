import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

interface PortalInfo {
  patient_name: string
  nutritionist_name?: string
  clinic_name?: string
  consent_at?: string | null
  consent_version?: string | null
  current_consent_version: string
}

/** El paciente acepta la política de privacidad vigente desde su portal. */
function ConsentCard({ token, info, onAccepted }: { token: string; info: PortalInfo; onAccepted: (i: PortalInfo) => void }) {
  const [checked, setChecked] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const renewal = !!info.consent_at

  const accept = async () => {
    setBusy(true); setError(null)
    try {
      onAccepted(await api.post<PortalInfo>(`/portal/${token}/consent`, { accepted: true }))
    } catch {
      setError('No se pudo registrar tu aceptación. Intenta de nuevo.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="bg-white border-2 border-[#4b7c60]/30 rounded-xl p-5 mb-6 space-y-3">
      <h2 className="font-bold text-gray-900">
        {renewal ? 'Actualizamos la política de privacidad' : 'Autorización para tratar tus datos de salud'}
      </h2>
      <p className="text-sm text-gray-600">
        {info.nutritionist_name ?? 'Tu nutricionista'} registra tus datos personales y de salud (mediciones,
        antecedentes y pautas) para tu atención nutricional. Puedes pedir acceder a ellos, corregirlos, recibir una
        copia o que se eliminen cuando la ley lo permita.
      </p>
      <label className="flex items-start gap-2 text-sm text-gray-800 cursor-pointer">
        <input type="checkbox" checked={checked} onChange={e => setChecked(e.target.checked)} className="mt-0.5 accent-[#4b7c60]" />
        <span>
          Leí la{' '}
          <a href="/privacidad" target="_blank" rel="noopener noreferrer" className="text-[#4b7c60] font-semibold underline">política de privacidad</a>
          {' '}y autorizo el tratamiento de mis datos de salud para mi atención nutricional.
        </span>
      </label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button onClick={accept} disabled={!checked || busy}
        className="bg-[#4b7c60] text-white px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50">
        {busy ? 'Registrando…' : 'Acepto'}
      </button>
    </div>
  )
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
  weight_kg?: number | null
  fat_mass_pct?: number | null
  lean_mass_kg?: number | null
  sum_6_skinfolds?: number | null
  waist_cm?: number | null
  goals_text?: string | null
  next_eval_date?: string | null
}

const fmtNum = (v: number, d = 1) => v.toLocaleString('es-CL', { minimumFractionDigits: d, maximumFractionDigits: d })
const fmtDate = (iso: string) => { const [y, m, d] = iso.slice(0, 10).split('-'); return `${d}-${m}-${y}` }

type MetricKey = 'weight_kg' | 'fat_mass_pct' | 'sum_6_skinfolds' | 'waist_cm'
const METRICS: { key: MetricKey; label: string; unit: string; lowerIsBetter: boolean }[] = [
  { key: 'weight_kg', label: 'Peso', unit: 'kg', lowerIsBetter: false },
  { key: 'fat_mass_pct', label: 'Grasa corporal', unit: '%', lowerIsBetter: true },
  { key: 'sum_6_skinfolds', label: 'Σ 6 pliegues', unit: 'mm', lowerIsBetter: true },
  { key: 'waist_cm', label: 'Cintura', unit: 'cm', lowerIsBetter: true },
]

function ProgressView({ evaluations }: { evaluations: Evaluation[] }) {
  const last = evaluations[evaluations.length - 1]
  const goals = (last.goals_text ?? '').split('\n').map(g => g.trim()).filter(Boolean)
  const series = METRICS.map(m => {
    const pts = evaluations.filter(e => e[m.key] != null).map(e => ({ date: fmtDate(e.date), value: e[m.key] as number }))
    return { ...m, pts }
  }).filter(m => m.pts.length > 0)
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {series.map(m => {
          const first = m.pts[0].value, cur = m.pts[m.pts.length - 1].value, diff = cur - first
          const good = m.lowerIsBetter ? diff < 0 : null
          return (
            <div key={m.key} className="bg-white rounded-xl border border-[#E5EAE7] p-4">
              <p className="text-xs text-[#6b7280]">{m.label}</p>
              <p className="text-2xl font-bold text-gray-800">{fmtNum(cur)} <span className="text-sm font-normal text-[#6b7280]">{m.unit}</span></p>
              {m.pts.length > 1 && Math.abs(diff) >= 0.05 && (
                <p className={`text-xs font-semibold mt-1 ${good === null ? 'text-[#6b7280]' : good ? 'text-[#4b7c60]' : 'text-[#c06c52]'}`}>
                  {diff > 0 ? '+' : '−'}{fmtNum(Math.abs(diff))} {m.unit} desde el inicio
                </p>
              )}
            </div>
          )
        })}
      </div>

      {series.filter(m => m.pts.length > 1).map(m => (
        <div key={m.key} className="bg-white rounded-xl border border-[#E5EAE7] p-4">
          <h4 className="text-sm font-bold text-gray-800 mb-2">{m.label} ({m.unit})</h4>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={m.pts} margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5EAE7" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} />
                <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} domain={['auto', 'auto']} tickFormatter={(v: number) => fmtNum(v)} />
                <Tooltip formatter={(v) => [`${fmtNum(Number(v))} ${m.unit}`, m.label]} />
                <Line type="monotone" dataKey="value" stroke="#4b7c60" strokeWidth={2.5} dot={{ r: 4, fill: '#4b7c60' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ))}

      {goals.length > 0 && (
        <div className="bg-white rounded-xl border border-[#E5EAE7] overflow-hidden">
          <div className="bg-[#F7F5F2] px-4 py-3 flex justify-between items-center border-b border-[#E5EAE7]">
            <h4 className="text-sm font-bold text-gray-800">Metas para tu próxima evaluación</h4>
            {last.next_eval_date && <span className="text-xs font-semibold text-[#4b7c60]">{fmtDate(last.next_eval_date)}</span>}
          </div>
          <ul className="px-4 py-3 space-y-2">
            {goals.map(g => (
              <li key={g} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="mt-1 h-3 w-3 shrink-0 rounded border-2 border-[#4b7c60]" />{g}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default function PortalPage() {
  const { token } = useParams<{ token: string }>()
  const [info, setInfo] = useState<PortalInfo | null>(null)
  const [pautas, setPautas] = useState<Pauta[]>([])
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'pauta' | 'menu' | 'progreso'>('pauta')

  useEffect(() => {
    if (!token) return
    Promise.all([
      api.get<PortalInfo>(`/portal/${token}`),
      api.get<Pauta[]>(`/portal/${token}/pautas`).catch(() => []),
      api.get<Evaluation[]>(`/portal/${token}/evaluations`).catch(() => []),
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
        {info.consent_version !== info.current_consent_version && token && (
          <ConsentCard token={token} info={info} onAccepted={setInfo} />
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6 bg-white border border-[#E5EAE7] rounded-xl p-1 w-fit">
          <button
            onClick={() => setActiveTab('pauta')}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-colors ${activeTab === 'pauta' ? 'bg-[#4b7c60] text-white' : 'text-[#6b7280] hover:text-[#4b7c60]'}`}
          >
            Mi Pauta
          </button>
          <button
            onClick={() => setActiveTab('menu')}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-colors ${activeTab === 'menu' ? 'bg-[#4b7c60] text-white' : 'text-[#6b7280] hover:text-[#4b7c60]'}`}
          >
            Mi Menú
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

        {activeTab === 'menu' && (() => {
          const menuRaw = latestPauta?.menu_json
          let menuData: Record<string, { opcion1?: string; opcion2?: string }> = {}
          try { if (menuRaw) menuData = JSON.parse(menuRaw) } catch {}
          const tiempos = ['desayuno','colacion1','almuerzo','colacion2','once','cena']
          const labels: Record<string, string> = { desayuno:'Desayuno', colacion1:'Colación 1', almuerzo:'Almuerzo', colacion2:'Colación 2', once:'Once', cena:'Cena' }
          const entries = tiempos.filter(t => menuData[t])
          return !latestPauta ? (
            <div className="bg-white rounded-xl border border-[#E5EAE7] p-8 text-center text-[#6b7280]">Tu nutricionista aún no ha creado una pauta.</div>
          ) : entries.length === 0 ? (
            <div className="bg-white rounded-xl border border-[#E5EAE7] p-8 text-center text-[#6b7280]">El menú aún no ha sido generado.</div>
          ) : (
            <div className="space-y-3">
              {entries.map(t => {
                const entry = menuData[t] as Record<string, unknown>
                const fmt = (op: unknown) => {
                  if (!op || op === '') return null
                  if (typeof op === 'string') return op
                  if (Array.isArray(op)) return op.map((item: Record<string, unknown>) => `${item.nombre ?? item.alimento ?? ''} ${item.cantidad ?? ''}${item.unidad ? ' (' + item.unidad + ')' : item.medida ? ' (' + item.medida + ')' : ''}`).filter(Boolean).join(', ')
                  return null
                }
                return (
                  <div key={t} className="bg-white rounded-xl border border-[#E5EAE7] p-4">
                    <h4 className="font-bold text-[#4b7c60] mb-2">{labels[t]}</h4>
                    {fmt(entry.opcion1) && <p className="text-sm text-gray-700 mb-1"><span className="font-semibold text-[#6b7280] text-xs uppercase mr-1">Opción 1:</span>{fmt(entry.opcion1)}</p>}
                    {fmt(entry.opcion2) && <p className="text-sm text-gray-700"><span className="font-semibold text-[#6b7280] text-xs uppercase mr-1">Opción 2:</span>{fmt(entry.opcion2)}</p>}
                    {!!entry.receta && <p className="text-sm text-[#c06c52] mt-1">🍳 {(entry.receta as Record<string, unknown>).nombre as string}</p>}
                  </div>
                )
              })}
            </div>
          )
        })()}

        {activeTab === 'progreso' && (
          <>
            {evaluations.length === 0 ? (
              <div className="bg-white rounded-xl border border-[#E5EAE7] p-8 text-center text-[#6b7280]">
                Aún no tienes evaluaciones registradas.
              </div>
            ) : (
              <>
              <ProgressView evaluations={evaluations} />
              <div className="bg-white rounded-xl border border-[#E5EAE7] overflow-hidden mt-4">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[400px]">
                    <thead className="bg-[#F7F5F2] border-b border-[#E5EAE7]">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-[#6b7280] uppercase">Fecha</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-[#6b7280] uppercase">Peso</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-[#6b7280] uppercase">% Grasa</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-[#6b7280] uppercase">Masa magra</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-[#6b7280] uppercase">Σ 6 pliegues</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...evaluations].reverse().map((ev, i) => (
                        <tr key={ev.id} className={`border-b border-[#E5EAE7] ${i === 0 ? 'bg-[#4b7c60]/5 font-semibold' : ''}`}>
                          <td className="px-4 py-3 text-sm text-gray-800">{fmtDate(ev.date)}{i === 0 && <span className="ml-2 text-xs text-[#4b7c60]">↑ última</span>}</td>
                          <td className="px-4 py-3 text-sm text-right">{ev.weight_kg != null ? `${fmtNum(ev.weight_kg)} kg` : '—'}</td>
                          <td className="px-4 py-3 text-sm text-right">{ev.fat_mass_pct != null ? `${fmtNum(ev.fat_mass_pct)}%` : '—'}</td>
                          <td className="px-4 py-3 text-sm text-right">{ev.lean_mass_kg != null ? `${fmtNum(ev.lean_mass_kg)} kg` : '—'}</td>
                          <td className="px-4 py-3 text-sm text-right">{ev.sum_6_skinfolds != null ? `${fmtNum(ev.sum_6_skinfolds)} mm` : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              </>
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
