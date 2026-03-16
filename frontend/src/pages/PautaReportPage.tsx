import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

// ── Types ────────────────────────────────────────────────────────────────────

interface Patient {
  id: number
  name: string
  birth_date?: string
  age?: number
  sex: string
}

interface Pauta {
  id: number
  name: string
  date: string
  tipo_pauta: string
  sexo: string
  edad: number
  peso: number
  fa_key: string
  tmb: number
  get_kcal: number
  kcal_objetivo: number
  ajuste_kcal?: number
  prot_g: number
  prot_kcal: number
  prot_pct: number
  lip_g: number
  lip_kcal: number
  lip_pct: number
  cho_g: number
  cho_kcal: number
  cho_pct: number
  prot_g_kg: number
  porciones_json: string
  distribucion_json: string
  menu_json?: string
  notes?: string
}

interface MenuItem {
  nombre: string
  cantidad: number
  unidad: string
  kcal_100?: number
  prot_100?: number
  cho_100?: number
  lip_100?: number
}

// ── Constants ────────────────────────────────────────────────────────────────

const C_PRIMARY = '#4b7c60'
const C_TERRA   = '#c06c52'
const C_SAGE    = '#8da399'

const TIPO_LABELS: Record<string, string> = {
  omnivoro: 'Omnívoro', ovolacto: 'Ovo-lacto vegetariano', vegano: 'Vegano',
  vegetariano: 'Vegetariano', renal: 'Renal', diabetico: 'Diabético',
  hipocalorico: 'Hipocalórico',
}

const FA_LABELS: Record<string, string> = {
  sedentaria: 'Sedentaria', liviana: 'Liviana', moderada: 'Moderada', intensa: 'Intensa',
}

const TIEMPOS: { key: string; label: string }[] = [
  { key: 'desayuno',  label: 'Desayuno' },
  { key: 'colacion1', label: 'Colación 1' },
  { key: 'almuerzo',  label: 'Almuerzo' },
  { key: 'colacion2', label: 'Colación 2' },
  { key: 'once',      label: 'Once' },
  { key: 'cena',      label: 'Cena' },
]

const NOMBRES_GRUPOS: Record<string, string> = {
  cereales: 'Cereales', verduras_cg: 'Verduras CG', verduras_lc: 'Verduras LC',
  frutas: 'Frutas', lacteos_ag: 'Lácteos AG', lacteos_mg: 'Lácteos MG',
  lacteos_bg: 'Lácteos BG', legumbres: 'Legumbres', carnes_ag: 'Carnes AG',
  carnes_bg: 'Carnes BG', otros_proteicos: 'Otros Proteicos', aceite_grasas: 'Aceite/Grasas',
  alim_ricos_lipidos: 'Ricos en Lípidos', leches_vegetales: 'Leches Vegetales',
  lacteos_soya: 'Lácteos Soya', semillas_chia: 'Semillas Chía', azucares: 'Azúcares',
}

const SEX_LABELS: Record<string, string> = { M: 'Masculino', F: 'Femenino' }

function fmt(v?: number | null, d = 1) { return v != null ? v.toFixed(d) : '—' }

// ── Sub-components ────────────────────────────────────────────────────────────

function MacroCard({ label, g, kcal, pct, color }: { label: string; g: number; kcal: number; pct: number; color: string }) {
  return (
    <div className="bg-white rounded-xl border border-slate-100 p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{label}</span>
        <span className="text-xs font-black px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: color }}>{pct}%</span>
      </div>
      <p className="text-2xl font-bold text-slate-800">{fmt(g)}<span className="text-sm font-normal text-slate-400 ml-1">g</span></p>
      <p className="text-xs text-slate-400">{fmt(kcal, 0)} kcal</p>
      <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${Math.min(100, pct)}%`, backgroundColor: color }} />
      </div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function PautaReportPage() {
  const { id, pautaId } = useParams<{ id: string; pautaId: string }>()
  const { token, user } = useAuth()
  const reportRef = useRef<HTMLDivElement>(null)
  const API = import.meta.env.VITE_API_URL

  const [patient, setPatient] = useState<Patient | null>(null)
  const [pauta, setPauta] = useState<Pauta | null>(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    if (!id || !pautaId || !token) return
    const H = { Authorization: `Bearer ${token}` }
    Promise.all([
      fetch(`${API}/patients/${id}`, { headers: H }).then(r => r.json()),
      fetch(`${API}/pautas/${id}/${pautaId}`, { headers: H }).then(r => r.json()),
    ]).then(([p, pa]) => {
      setPatient(p)
      setPauta(pa)
      setLoading(false)
    })
  }, [id, pautaId, token, API])

  const captureCanvas = async () => {
    if (!reportRef.current) return null
    await document.fonts.ready
    await new Promise(r => setTimeout(r, 200))
    return html2canvas(reportRef.current, {
      scale: 2, useCORS: true, allowTaint: true,
      backgroundColor: '#F7F5F2', logging: false,
    })
  }

  const handleExportPNG = async () => {
    setExporting(true)
    try {
      const canvas = await captureCanvas()
      if (!canvas) return
      const a = document.createElement('a')
      a.download = `pauta_${patient?.name.replace(/ /g, '_')}_${pauta?.date}.png`
      a.href = canvas.toDataURL('image/png')
      a.click()
    } finally { setExporting(false) }
  }

  const handleExportPDF = async () => {
    setExporting(true)
    try {
      const canvas = await captureCanvas()
      if (!canvas) return
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
      const pdfW = pdf.internal.pageSize.getWidth()
      const pdfH = (canvas.height * pdfW) / canvas.width
      let y = 0
      const pageH = pdf.internal.pageSize.getHeight()
      while (y < pdfH) {
        if (y > 0) pdf.addPage()
        pdf.addImage(imgData, 'PNG', 0, -y, pdfW, pdfH)
        y += pageH
      }
      pdf.save(`pauta_${patient?.name.replace(/ /g, '_')}_${pauta?.date}.pdf`)
    } finally { setExporting(false) }
  }

  if (loading || !patient || !pauta) {
    return (
      <div className="min-h-screen bg-bg-light flex items-center justify-center">
        <p className="text-text-muted text-sm">Cargando informe...</p>
      </div>
    )
  }

  // ── Parse JSON fields ────────────────────────────────────────────────────────
  let porciones: Record<string, number> = {}
  let distribucion: Record<string, Record<string, number>> = {}
  let menu: Record<string, unknown> = {}
  try { porciones = JSON.parse(pauta.porciones_json || '{}') } catch {}
  try { distribucion = JSON.parse(pauta.distribucion_json || '{}') } catch {}
  try { if (pauta.menu_json) menu = JSON.parse(pauta.menu_json) } catch {}

  const activeGroups = Object.entries(porciones).filter(([, v]) => v > 0)

  const initials = patient.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()

  const brandName = user?.clinic_name || user?.name || user?.username || 'Consultorio'
  const brandTagline = user?.report_tagline || 'Pauta Nutricional'

  // Kcal por tiempo
  const GRUPOS_MACROS: Record<string, number> = {
    cereales: 140, verduras_cg: 30, verduras_lc: 10, frutas: 65,
    lacteos_ag: 110, lacteos_mg: 85, lacteos_bg: 70, legumbres: 170,
    carnes_ag: 120, carnes_bg: 65, otros_proteicos: 75, aceite_grasas: 180,
    alim_ricos_lipidos: 175, leches_vegetales: 80, lacteos_soya: 80,
    semillas_chia: 37, azucares: 20,
  }
  const kcalPorTiempo: Record<string, number> = {}
  let totalKcalDistribuida = 0
  for (const { key } of TIEMPOS) {
    const grupos = distribucion[key] || {}
    const kcal = Object.entries(grupos).reduce((s, [g, p]) => s + (GRUPOS_MACROS[g] ?? 0) * p, 0)
    kcalPorTiempo[key] = Math.round(kcal)
    totalKcalDistribuida += kcal
  }

  return (
    <div className="min-h-screen bg-bg-light font-sans">

      {/* ── Toolbar (not exported) ── */}
      <div className="no-export sticky top-0 z-50 bg-white border-b border-border px-6 py-3 flex items-center justify-between shadow-sm">
        <Link to={`/patients/${id}/pautas/${pautaId}`}
          className="flex items-center gap-2 text-text-muted hover:text-primary text-sm transition-colors">
          <span className="material-symbols-outlined text-lg">arrow_back</span>
          Volver a Pauta
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-text-muted text-sm">Informe — {patient.name}</span>
          <button onClick={handleExportPNG} disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-border rounded-lg text-sm font-medium text-slate-700 hover:bg-bg-light transition-colors disabled:opacity-50">
            <span className="material-symbols-outlined text-lg">image</span>
            {exporting ? 'Exportando...' : 'Exportar PNG'}
          </button>
          <button onClick={handleExportPDF} disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold text-white transition-colors disabled:opacity-50"
            style={{ backgroundColor: C_PRIMARY }}>
            <span className="material-symbols-outlined text-lg">download</span>
            {exporting ? 'Exportando...' : 'Exportar PDF'}
          </button>
        </div>
      </div>

      {/* ── Report ── */}
      <div className="py-8 px-4 flex justify-center">
        <div ref={reportRef} className="w-full max-w-4xl bg-bg-light" style={{ fontFamily: 'Inter, sans-serif' }}>

          {/* 1. Header */}
          <header className="w-full py-8 px-8 text-white flex justify-between items-center" style={{ backgroundColor: C_PRIMARY }}>
            <div className="flex items-center gap-4">
              {user?.logo_base64 ? (
                <img src={user.logo_base64} alt="Logo" className="h-14 w-auto max-w-[160px] object-contain rounded-xl bg-white/10 p-1" />
              ) : (
                <div className="bg-white/20 p-3 rounded-xl">
                  <span className="material-symbols-outlined text-4xl">restaurant_menu</span>
                </div>
              )}
              <div>
                <h1 className="text-3xl font-black tracking-tight">{brandName}</h1>
                <p className="text-white/80 text-xs font-semibold uppercase tracking-widest mt-0.5">{brandTagline}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-bold text-lg">Paciente: {patient.name}</p>
              <p className="text-white/70 text-sm mt-0.5">Fecha: {pauta.date}</p>
            </div>
          </header>

          {/* Main card */}
          <div className="bg-white rounded-b-xl shadow-xl overflow-hidden border border-primary/10">

            {/* 2. Hero */}
            <div className="p-8 border-b border-slate-100 flex gap-6 items-center"
              style={{ background: 'linear-gradient(135deg, rgba(75,124,96,0.07) 0%, transparent 100%)' }}>
              <div className="w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl font-black flex-shrink-0 border-4 border-white shadow-md"
                style={{ backgroundColor: C_PRIMARY }}>
                {initials}
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-slate-900">{pauta.name}</h2>
                <p className="text-text-muted text-sm mt-1">
                  {SEX_LABELS[pauta.sexo] ?? pauta.sexo} · {pauta.edad} años · {fmt(pauta.peso, 1)} kg
                </p>
              </div>
              <div className="flex-shrink-0 px-4 py-2 rounded-full text-sm font-bold text-white"
                style={{ backgroundColor: C_SAGE }}>
                {TIPO_LABELS[pauta.tipo_pauta] ?? pauta.tipo_pauta}
              </div>
            </div>

            {/* 3. Datos energéticos */}
            <div className="p-8 border-b border-slate-100">
              <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.15em] mb-5">Datos Energéticos</h3>
              <div className="grid grid-cols-4 gap-4 mb-6">
                {[
                  { label: 'TMB', value: fmt(pauta.tmb, 0), unit: 'kcal' },
                  { label: 'GET', value: fmt(pauta.get_kcal, 0), unit: 'kcal' },
                  { label: 'Ajuste', value: pauta.ajuste_kcal ? (pauta.ajuste_kcal > 0 ? '+' : '') + pauta.ajuste_kcal : '0', unit: 'kcal' },
                  { label: 'Kcal Objetivo', value: fmt(pauta.kcal_objetivo, 0), unit: 'kcal', highlight: true },
                ].map(({ label, value, unit, highlight }) => (
                  <div key={label} className={`rounded-xl p-4 text-center ${highlight ? 'text-white' : 'bg-slate-50'}`}
                    style={highlight ? { backgroundColor: C_PRIMARY } : {}}>
                    <p className={`text-xs font-bold uppercase tracking-wide mb-1 ${highlight ? 'text-white/70' : 'text-slate-400'}`}>{label}</p>
                    <p className={`text-2xl font-black ${highlight ? 'text-white' : 'text-slate-800'}`}>{value}</p>
                    <p className={`text-xs mt-0.5 ${highlight ? 'text-white/60' : 'text-slate-400'}`}>{unit}</p>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400 mb-4">Factor actividad: <span className="font-semibold text-slate-600">{FA_LABELS[pauta.fa_key] ?? pauta.fa_key}</span> · Fórmula: Mifflin-St Jeor</p>

              {/* Macros */}
              <div className="grid grid-cols-3 gap-4">
                <MacroCard label="Proteínas" g={pauta.prot_g} kcal={pauta.prot_kcal} pct={pauta.prot_pct} color={C_PRIMARY} />
                <MacroCard label="Lípidos"   g={pauta.lip_g}  kcal={pauta.lip_kcal}  pct={pauta.lip_pct}  color={C_TERRA} />
                <MacroCard label="Carbohidratos" g={pauta.cho_g} kcal={pauta.cho_kcal} pct={pauta.cho_pct} color="#3b82f6" />
              </div>
              <p className="text-xs text-slate-400 mt-3">Proteínas: <span className="font-semibold text-slate-600">{fmt(pauta.prot_g_kg, 2)} g/kg peso corporal</span></p>
            </div>

            {/* 4. Porciones por grupo */}
            {activeGroups.length > 0 && (
              <div className="p-8 border-b border-slate-100">
                <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.15em] mb-5">Porciones por Grupo de Alimentos</h3>
                <div className="grid grid-cols-2 gap-x-8 gap-y-2">
                  {activeGroups.map(([grupo, porciones_val]) => (
                    <div key={grupo} className="flex items-center justify-between py-1.5 border-b border-slate-100">
                      <span className="text-sm text-slate-700">{NOMBRES_GRUPOS[grupo] ?? grupo}</span>
                      <span className="text-sm font-bold text-slate-800 bg-slate-50 px-2 py-0.5 rounded">
                        {porciones_val} {porciones_val === 1 ? 'porción' : 'porciones'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 5. Distribución por tiempo de comida */}
            {totalKcalDistribuida > 0 && (
              <div className="p-8 border-b border-slate-100">
                <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.15em] mb-5">Distribución por Tiempo de Comida</h3>
                <div className="grid grid-cols-2 gap-4">
                  {TIEMPOS.filter(({ key }) => kcalPorTiempo[key] > 0).map(({ key, label }) => {
                    const grupos = Object.entries(distribucion[key] || {}).filter(([, v]) => v > 0)
                    const pct = totalKcalDistribuida > 0 ? Math.round((kcalPorTiempo[key] / totalKcalDistribuida) * 100) : 0
                    return (
                      <div key={key} className="border border-slate-100 rounded-xl overflow-hidden">
                        <div className="px-4 py-2 flex items-center justify-between" style={{ backgroundColor: `${C_PRIMARY}10` }}>
                          <span className="text-sm font-bold" style={{ color: C_PRIMARY }}>{label}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-400">{kcalPorTiempo[key]} kcal</span>
                            <span className="text-xs font-bold px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: C_PRIMARY }}>{pct}%</span>
                          </div>
                        </div>
                        <div className="px-4 py-3 space-y-1">
                          {grupos.map(([g, p]) => (
                            <div key={g} className="flex items-center justify-between text-xs">
                              <span className="text-slate-600">{NOMBRES_GRUPOS[g] ?? g}</span>
                              <span className="font-semibold text-slate-700">{p}p</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* 6. Menú */}
            {Object.keys(menu).length > 0 && (
              <div className="p-8 border-b border-slate-100">
                <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.15em] mb-5">Ideas de Menú</h3>
                <div className="space-y-4">
                  {TIEMPOS.filter(({ key }) => menu[key]).map(({ key, label }) => {
                    const entry = menu[key] as Record<string, unknown>
                    const op1 = entry?.opcion1
                    const op2 = entry?.opcion2
                    const receta = entry?.receta as { nombre: string; categoria?: string } | undefined
                    return (
                      <div key={key} className="border border-slate-100 rounded-xl overflow-hidden">
                        <div className="px-4 py-2" style={{ backgroundColor: `${C_PRIMARY}10` }}>
                          <span className="text-sm font-bold" style={{ color: C_PRIMARY }}>{label}</span>
                        </div>
                        <div className="p-4 grid grid-cols-2 gap-4">
                          {/* Opción 1 */}
                          <div className="rounded-lg p-3" style={{ backgroundColor: `${C_PRIMARY}08`, border: `1px solid ${C_PRIMARY}20` }}>
                            <p className="text-xs font-bold mb-2" style={{ color: C_PRIMARY }}>Opción 1</p>
                            {Array.isArray(op1) ? (
                              <div className="space-y-1">
                                {(op1 as MenuItem[]).map((item, i) => (
                                  <div key={i} className="flex items-center justify-between text-xs">
                                    <span className="text-slate-700 truncate flex-1">{item.nombre}</span>
                                    <span className="text-slate-400 ml-2 flex-shrink-0">{item.cantidad}{item.unidad}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-wrap">{String(op1 ?? '')}</p>
                            )}
                          </div>
                          {/* Opción 2 */}
                          <div className="rounded-lg p-3" style={{ backgroundColor: `${C_TERRA}08`, border: `1px solid ${C_TERRA}20` }}>
                            <p className="text-xs font-bold mb-2" style={{ color: C_TERRA }}>Opción 2</p>
                            {Array.isArray(op2) ? (
                              <div className="space-y-1">
                                {(op2 as MenuItem[]).map((item, i) => (
                                  <div key={i} className="flex items-center justify-between text-xs">
                                    <span className="text-slate-700 truncate flex-1">{item.nombre}</span>
                                    <span className="text-slate-400 ml-2 flex-shrink-0">{item.cantidad}{item.unidad}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-wrap">{String(op2 ?? '')}</p>
                            )}
                          </div>
                        </div>
                        {/* Receta asignada */}
                        {receta && (
                          <div className="px-4 pb-4">
                            <div className="rounded-lg p-3 flex items-center gap-2" style={{ backgroundColor: `${C_SAGE}15`, border: `1px solid ${C_SAGE}30` }}>
                              <span className="material-symbols-outlined text-sm" style={{ color: C_SAGE }}>menu_book</span>
                              <div>
                                <p className="text-xs font-bold" style={{ color: C_SAGE }}>Receta: {receta.nombre}</p>
                                {receta.categoria && <p className="text-xs text-slate-400">{receta.categoria}</p>}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* 7. Notas */}
            {pauta.notes && (
              <div className="p-8 border-b border-slate-100">
                <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.15em] mb-3">Notas / Indicaciones</h3>
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap bg-slate-50 rounded-xl p-4">{pauta.notes}</p>
              </div>
            )}

            {/* Footer */}
            <div className="px-8 py-5 flex items-center justify-between" style={{ backgroundColor: C_PRIMARY }}>
              <p className="text-white font-bold text-sm">{brandName}</p>
              <p className="text-white/60 text-xs">
                © {new Date().getFullYear()} {brandName} · Generado {new Date().toLocaleDateString('es-CL')}
              </p>
            </div>

          </div>
        </div>
      </div>
    </div>
  )
}
