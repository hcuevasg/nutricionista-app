import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

// ── Types ──────────────────────────────────────────────────────────────────────

interface Patient {
  id: number
  name: string
  birth_date?: string
  age?: number
  sex: string
}

interface Evaluation {
  id: number
  date: string
  isak_level: string
  weight_kg?: number
  height_cm?: number
  waist_cm?: number
  fat_mass_pct?: number
  fat_mass_kg?: number
  lean_mass_kg?: number
  body_density?: number
  sum_6_skinfolds?: number
  tmb?: number
  get_kcal?: number
  // Skinfolds
  triceps_mm?: number
  subscapular_mm?: number
  biceps_mm?: number
  iliac_crest_mm?: number
  supraspinal_mm?: number
  abdominal_mm?: number
  medial_thigh_mm?: number
  max_calf_mm?: number
  pectoral_mm?: number
  axillary_mm?: number
  front_thigh_mm?: number
  // Perimeters
  arm_relaxed_cm?: number
  arm_contracted_cm?: number
  hip_glute_cm?: number
  thigh_max_cm?: number
  thigh_mid_cm?: number
  calf_cm?: number
  neck_cm?: number
  chest_cm?: number
  // Somatotype
  somatotype_endo?: number
  somatotype_meso?: number
  somatotype_ecto?: number
}

// ── Helpers ────────────────────────────────────────────────────────────────────

const fmt = (v: number | undefined | null, d = 1): string =>
  v != null ? Number(v).toFixed(d) : '—'

const bmiCategory = (bmi: number): string => {
  if (bmi < 18.5) return 'Bajo peso'
  if (bmi < 25) return 'Normal'
  if (bmi < 30) return 'Sobrepeso'
  return 'Obesidad'
}

const bmiInsight = (bmi: number | null): string => {
  if (!bmi) return 'Evaluación antropométrica completa. Revisar resultados con el profesional.'
  if (bmi < 18.5) return 'Se recomienda plan de aumento de masa muscular y revisión de la ingesta calórica.'
  if (bmi < 25) return 'Composición corporal en rangos normales. Continuar con los hábitos actuales.'
  if (bmi < 30) return 'Se detecta sobrepeso. Orientar hacia reducción de masa grasa con plan adecuado.'
  return 'Se registra obesidad. Plan nutricional intensivo y seguimiento periódico recomendados.'
}

// Harris-Benedict BMR
const calcBMR = (patient: Patient, ev: Evaluation): number | null => {
  const age = patient.age ?? (patient.birth_date
    ? Math.floor((Date.now() - new Date(patient.birth_date).getTime()) / (365.25 * 86400000))
    : null)
  if (!ev.weight_kg || !ev.height_cm || !age) return null
  const w = ev.weight_kg, h = ev.height_cm
  return patient.sex === 'M'
    ? 88.362 + 13.397 * w + 4.799 * h - 5.677 * age
    : 447.593 + 9.247 * w + 3.098 * h - 4.330 * age
}

// ── Metric card ────────────────────────────────────────────────────────────────

interface MetricCardProps {
  label: string
  value: string
  unit: string
  note?: string
  border: string   // Tailwind border-color class e.g. 'border-primary'
  icon: string
  iconColor: string
}

function MetricCard({ label, value, unit, note, border, icon, iconColor }: MetricCardProps) {
  return (
    <div className={`bg-bg-light rounded-xl p-5 border-l-4 ${border} flex-1`}>
      <div className="flex justify-between items-start mb-3">
        <p className="text-text-muted text-xs font-bold uppercase tracking-wider">{label}</p>
        <span className={`material-symbols-outlined text-lg ${iconColor}`}>{icon}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <p className="text-3xl font-black text-slate-900">{value}</p>
        <span className="text-text-muted text-sm ml-1">{unit}</span>
      </div>
      {note && <p className="text-xs text-text-muted mt-1 italic">{note}</p>}
    </div>
  )
}

// ── Progress bar ───────────────────────────────────────────────────────────────

function ProgressBar({ label, pct, color }: { label: string; pct: number | null; color: string }) {
  if (!pct || pct <= 0) return null
  const clamped = Math.min(pct, 100)
  return (
    <div>
      <div className="flex justify-between text-sm mb-1 font-bold">
        <span className="text-slate-700">{label}</span>
        <span style={{ color }}>{clamped.toFixed(1)}%</span>
      </div>
      <div className="h-3 w-full bg-slate-200 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${clamped}%`, backgroundColor: color }} />
      </div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function IsAkReportPage() {
  const { id, evalId } = useParams<{ id: string; evalId: string }>()
  const { token } = useAuth()
  const reportRef = useRef<HTMLDivElement>(null)
  const API = import.meta.env.VITE_API_URL

  const [patient, setPatient] = useState<Patient | null>(null)
  const [ev, setEv] = useState<Evaluation | null>(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    if (!id || !evalId || !token) return
    const headers = { Authorization: `Bearer ${token}` }
    Promise.all([
      fetch(`${API}/patients/${id}`, { headers }).then(r => r.json()),
      fetch(`${API}/anthropometrics/${id}/${evalId}`, { headers }).then(r => r.json()),
    ]).then(([p, e]) => {
      setPatient(p)
      setEv(e)
      setLoading(false)
    })
  }, [id, evalId, token, API])

  const handleExportPNG = async () => {
    if (!reportRef.current) return
    setExporting(true)
    await new Promise(r => setTimeout(r, 100))
    const canvas = await html2canvas(reportRef.current, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#F7F5F2',
    })
    const link = document.createElement('a')
    link.download = `ISAK_${patient?.name?.replace(/\s+/g, '_')}_${ev?.date}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    setExporting(false)
  }

  const handleExportPDF = async () => {
    if (!reportRef.current) return
    setExporting(true)
    await new Promise(r => setTimeout(r, 100))
    const canvas = await html2canvas(reportRef.current, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#F7F5F2',
    })
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    const pdfW = pdf.internal.pageSize.getWidth()
    const pdfH = (canvas.height * pdfW) / canvas.width
    pdf.addImage(imgData, 'PNG', 0, 0, pdfW, pdfH)
    pdf.save(`ISAK_${patient?.name?.replace(/\s+/g, '_')}_${ev?.date}.pdf`)
    setExporting(false)
  }

  if (loading || !patient || !ev) {
    return (
      <div className="min-h-screen bg-bg-light flex items-center justify-center">
        <div className="text-text-muted text-sm">Cargando informe...</div>
      </div>
    )
  }

  // ── Computed values ──────────────────────────────────────────────────────────
  const bmi = ev.weight_kg && ev.height_cm
    ? ev.weight_kg / Math.pow(ev.height_cm / 100, 2)
    : null

  const leanPct = ev.lean_mass_kg && ev.weight_kg && ev.weight_kg > 0
    ? Math.min((ev.lean_mass_kg / ev.weight_kg) * 100, 99.9)
    : null

  const tmb = ev.tmb ?? calcBMR(patient, ev)

  const sigma4 = [ev.biceps_mm, ev.triceps_mm, ev.subscapular_mm, ev.iliac_crest_mm]
  const sigma4Sum = sigma4.every(v => v != null) ? sigma4.reduce((a, b) => a! + b!, 0)! : null

  const isak2 = ev.isak_level === 'ISAK 2'
  const isBadgeGreen = isak2

  const initials = patient.name.split(' ').slice(0, 2).map(w => w[0]?.toUpperCase()).join('')
  const sexLabel = patient.sex === 'M' ? 'Masculino' : 'Femenino'
  const ageStr = patient.age ? `${patient.age} años · ` : ''

  // Key perimeters for the anthropometry table
  const perimRows: [string, number | undefined][] = [
    ['Cintura', ev.waist_cm],
    ['Cadera / Glúteo', ev.hip_glute_cm],
    ['Brazo contraído', ev.arm_contracted_cm],
    ['Brazo relajado', ev.arm_relaxed_cm],
    ['Muslo máximo', ev.thigh_max_cm],
    ['Pantorrilla', ev.calf_cm],
  ]
  const filteredPerims = perimRows.filter(([, v]) => v != null)

  // Skinfolds
  const sfList: [string, number | undefined][] = [
    ['Tríceps', ev.triceps_mm],
    ['Subescapular', ev.subscapular_mm],
    ['Bíceps', ev.biceps_mm],
    ['Cresta Iliaca', ev.iliac_crest_mm],
    ['Supraespinal', ev.supraspinal_mm],
    ['Abdominal', ev.abdominal_mm],
    ['Muslo Medial', ev.medial_thigh_mm],
    ['Pantorrilla Máx.', ev.max_calf_mm],
    ...(isak2 ? [
      ['Pectoral', ev.pectoral_mm] as [string, number | undefined],
      ['Axilar Medio', ev.axillary_mm] as [string, number | undefined],
      ['Muslo Anterior', ev.front_thigh_mm] as [string, number | undefined],
    ] : []),
  ]
  const filteredSf = sfList.filter(([, v]) => v != null)

  // Colors
  const C_PRIMARY = '#4b7c60'
  const C_TERRA = '#c06c52'
  const C_AMBER = '#d9a441'
  const C_SAGE = '#8da399'

  return (
    <div className="min-h-screen bg-bg-light font-sans">
      {/* ── Toolbar (not exported) ── */}
      <div className="no-export sticky top-0 z-50 bg-white border-b border-border px-6 py-3 flex items-center justify-between shadow-sm">
        <Link
          to={`/patients/${id}/isak`}
          className="flex items-center gap-2 text-text-muted hover:text-primary text-sm transition-colors"
        >
          <span className="material-symbols-outlined text-lg">arrow_back</span>
          Volver a ISAK
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-text-muted text-sm">Informe ISAK — {patient.name}</span>
          <button
            onClick={handleExportPNG}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-border rounded-lg text-sm font-medium text-slate-700 hover:bg-bg-light transition-colors disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-lg">image</span>
            {exporting ? 'Exportando...' : 'Exportar PNG'}
          </button>
          <button
            onClick={handleExportPDF}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold text-white transition-colors disabled:opacity-50"
            style={{ backgroundColor: C_PRIMARY }}
          >
            <span className="material-symbols-outlined text-lg">download</span>
            {exporting ? 'Exportando...' : 'Exportar PDF'}
          </button>
        </div>
      </div>

      {/* ── Report (exported) ── */}
      <div className="py-8 px-4 flex justify-center">
        <div
          ref={reportRef}
          className="w-full max-w-4xl bg-bg-light"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >

          {/* ── 1. Header band ── */}
          <header className="w-full py-8 px-8 text-white flex justify-between items-center" style={{ backgroundColor: C_PRIMARY }}>
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-3 rounded-xl">
                <span className="material-symbols-outlined text-4xl">monitoring</span>
              </div>
              <div>
                <h1 className="text-3xl font-black tracking-tight">NutriApp</h1>
                <p className="text-white/80 text-xs font-semibold uppercase tracking-widest mt-0.5">
                  Informe Antropométrico
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-bold text-lg">Paciente: {patient.name}</p>
              <p className="text-white/70 text-sm mt-0.5">Evaluación: {ev.date}</p>
            </div>
          </header>

          {/* ── Main white card ── */}
          <div className="bg-white rounded-b-xl shadow-xl overflow-hidden border border-primary/10">

            {/* ── 2. Hero section ── */}
            <div
              className="p-8 border-b border-slate-100 flex gap-6 items-center"
              style={{ background: 'linear-gradient(135deg, rgba(75,124,96,0.07) 0%, transparent 100%)' }}
            >
              {/* Avatar */}
              <div
                className="w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl font-black flex-shrink-0 border-4 border-white shadow-md"
                style={{ backgroundColor: C_PRIMARY }}
              >
                {initials}
              </div>

              {/* Info */}
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-slate-900">
                  Informe ISAK — {patient.name}
                </h2>
                <p className="text-text-muted text-sm mt-1">
                  {ageStr}{sexLabel}
                </p>
                <p className="text-slate-600 mt-2 text-sm leading-relaxed">
                  {bmiInsight(bmi)}
                </p>
              </div>

              {/* ISAK badge */}
              <div
                className="flex-shrink-0 px-4 py-2 rounded-full text-sm font-bold text-white flex items-center gap-1"
                style={{ backgroundColor: isBadgeGreen ? C_PRIMARY : C_SAGE }}
              >
                <span className="material-symbols-outlined text-base">verified</span>
                {ev.isak_level}
              </div>
            </div>

            {/* ── 3. Metric cards ── */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-5 p-8">
              <MetricCard
                label="IMC (BMI)"
                value={bmi ? fmt(bmi) : '—'}
                unit="kg/m²"
                note={bmi ? `${bmiCategory(bmi)} · Rango: 18.5–24.9` : undefined}
                border="border-terracotta"
                icon="speed"
                iconColor="text-terracotta"
              />
              <MetricCard
                label="% Masa Grasa"
                value={ev.fat_mass_pct && ev.fat_mass_pct > 0 ? fmt(ev.fat_mass_pct) : '—'}
                unit="%"
                note={ev.fat_mass_kg ? `${fmt(ev.fat_mass_kg)} kg masa grasa` : undefined}
                border="border-terracotta"
                icon="opacity"
                iconColor="text-terracotta"
              />
              <MetricCard
                label="Masa Magra"
                value={ev.lean_mass_kg ? fmt(ev.lean_mass_kg) : '—'}
                unit="kg"
                note={leanPct ? `${leanPct.toFixed(1)}% del peso total` : undefined}
                border="border-primary"
                icon="fitness_center"
                iconColor="text-primary"
              />
              <MetricCard
                label="Tasa Metabólica Basal"
                value={tmb ? String(Math.round(tmb)) : '—'}
                unit="kcal"
                note="Requerimiento energético diario"
                border="border-amber-500"
                icon="bolt"
                iconColor="text-amber-500"
              />
            </div>

            {/* ── 4. Two-column: Anthropometry + Body Distribution ── */}
            <div className="px-8 pb-8 grid grid-cols-1 lg:grid-cols-3 gap-8" style={{ backgroundColor: '#f8faf9' }}>

              {/* Left: Anthropometry table */}
              <div className="lg:col-span-2">
                <h3 className="text-base font-bold mb-4 flex items-center gap-2" style={{ color: C_PRIMARY }}>
                  <span className="material-symbols-outlined text-lg" style={{ color: C_PRIMARY }}>straighten</span>
                  Medidas Antropométricas
                </h3>
                {filteredPerims.length > 0 ? (
                  <div className="overflow-hidden rounded-lg border border-slate-200">
                    <table className="w-full text-left text-sm">
                      <thead className="text-xs uppercase font-bold text-slate-500" style={{ backgroundColor: C_PRIMARY }}>
                        <tr>
                          <th className="px-5 py-3 text-white">Medida</th>
                          <th className="px-5 py-3 text-white text-right">Actual (cm)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {filteredPerims.map(([label, val], i) => (
                          <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-bg-light'}>
                            <td className="px-5 py-3 font-medium text-slate-700">{label}</td>
                            <td className="px-5 py-3 text-right font-bold" style={{ color: C_PRIMARY }}>
                              {fmt(val)} cm
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-text-muted text-sm">Sin perímetros registrados.</p>
                )}

                {/* Extra stats below table */}
                <div className="mt-4 grid grid-cols-3 gap-3">
                  {ev.weight_kg && (
                    <div className="bg-white rounded-lg p-3 border border-slate-200 text-center">
                      <p className="text-xs text-text-muted uppercase font-bold">Peso</p>
                      <p className="text-lg font-black text-slate-900 mt-1">{fmt(ev.weight_kg)} <span className="text-sm font-normal text-text-muted">kg</span></p>
                    </div>
                  )}
                  {ev.height_cm && (
                    <div className="bg-white rounded-lg p-3 border border-slate-200 text-center">
                      <p className="text-xs text-text-muted uppercase font-bold">Talla</p>
                      <p className="text-lg font-black text-slate-900 mt-1">{fmt(ev.height_cm)} <span className="text-sm font-normal text-text-muted">cm</span></p>
                    </div>
                  )}
                  {sigma4Sum != null && (
                    <div className="bg-white rounded-lg p-3 border border-slate-200 text-center">
                      <p className="text-xs text-text-muted uppercase font-bold">Σ4 Pliegues</p>
                      <p className="text-lg font-black text-slate-900 mt-1">{sigma4Sum.toFixed(1)} <span className="text-sm font-normal text-text-muted">mm</span></p>
                    </div>
                  )}
                </div>
              </div>

              {/* Right: Body Distribution */}
              <div className="flex flex-col">
                <h3 className="text-base font-bold mb-4 flex items-center gap-2" style={{ color: C_PRIMARY }}>
                  <span className="material-symbols-outlined text-lg" style={{ color: C_PRIMARY }}>pie_chart</span>
                  Distribución Corporal
                </h3>
                <div className="flex-1 flex flex-col gap-4 bg-white rounded-lg p-5 border border-slate-200">
                  <ProgressBar label="Masa Magra" pct={leanPct} color={C_PRIMARY} />
                  <ProgressBar label="Masa Grasa" pct={ev.fat_mass_pct ?? null} color={C_TERRA} />
                  {ev.body_density != null && (
                    <div className="mt-2 pt-3 border-t border-slate-100">
                      <div className="flex justify-between text-xs">
                        <span className="text-text-muted font-medium">Densidad corporal</span>
                        <span className="font-bold text-slate-700">{fmt(ev.body_density, 4)} g/mL</span>
                      </div>
                    </div>
                  )}
                  {bmi && (
                    <div className="mt-2 p-3 rounded-lg border text-xs italic text-slate-600 leading-relaxed"
                         style={{ backgroundColor: 'rgba(75,124,96,0.05)', borderColor: 'rgba(75,124,96,0.15)' }}>
                      "{bmiInsight(bmi).replace('.', '.')}"
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ── 5. Skinfolds section (replaces "Recommended Portions") ── */}
            {filteredSf.length > 0 && (
              <div className="p-8 border-t border-slate-100">
                <h3 className="text-base font-bold mb-6 flex items-center gap-2" style={{ color: C_PRIMARY }}>
                  <span className="material-symbols-outlined text-lg" style={{ color: C_PRIMARY }}>point_scan</span>
                  Pliegues Cutáneos (mm)
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {filteredSf.map(([label, val], i) => (
                    <div
                      key={i}
                      className="flex flex-col items-center p-4 rounded-2xl text-center"
                      style={{ backgroundColor: '#f0f4f1' }}
                    >
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center mb-2 text-white text-xs font-black"
                        style={{ backgroundColor: i % 2 === 0 ? C_PRIMARY : C_SAGE }}
                      >
                        {String(val!.toFixed(1))}
                      </div>
                      <p className="text-xs font-bold uppercase text-text-muted leading-tight">{label}</p>
                      <span className="text-base font-black text-slate-800 mt-1">{fmt(val, 1)} mm</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── 6. ISAK 2: Somatotype (if available) ── */}
            {isak2 && ev.somatotype_endo != null && (
              <div className="p-8 border-t border-slate-100">
                <h3 className="text-base font-bold mb-6 flex items-center gap-2" style={{ color: C_TERRA }}>
                  <span className="material-symbols-outlined text-lg" style={{ color: C_TERRA }}>scatter_plot</span>
                  Somatotipo — Heath &amp; Carter (1990)
                </h3>
                <div className="grid grid-cols-3 gap-5">
                  {[
                    { label: 'Endomorfia', value: ev.somatotype_endo, color: C_TERRA },
                    { label: 'Mesomorfia', value: ev.somatotype_meso, color: C_PRIMARY },
                    { label: 'Ectomorfia', value: ev.somatotype_ecto, color: C_SAGE },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-bg-light rounded-xl p-5 border-l-4" style={{ borderLeftColor: color }}>
                      <p className="text-xs text-text-muted font-bold uppercase tracking-wider mb-2">{label}</p>
                      <p className="text-4xl font-black text-slate-900">{fmt(value)}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── 7. Footer bar ── */}
            <div className="p-6 text-white flex flex-col sm:flex-row items-center justify-between gap-4"
                 style={{ backgroundColor: C_PRIMARY }}>
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-3xl">assignment</span>
                <div>
                  <p className="font-bold text-base leading-tight">Informe Oficial ISAK</p>
                  <p className="text-white/75 text-sm">
                    {ev.isak_level} · Evaluación {ev.date} · Documento de uso profesional
                  </p>
                </div>
              </div>
              <p className="text-white/60 text-xs">
                © {new Date().getFullYear()} NutriApp · Generado {new Date().toLocaleDateString('es-CL')}
              </p>
            </div>

          </div>
        </div>
      </div>
    </div>
  )
}
