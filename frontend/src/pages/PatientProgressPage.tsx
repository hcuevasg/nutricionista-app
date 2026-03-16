import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Patient {
  id: number
  name: string
  sex: string
  birth_date?: string
}

interface Eval {
  id: number
  date: string
  weight_kg?: number
  fat_mass_pct?: number
  lean_mass_kg?: number
  fat_mass_kg?: number
  isak_level?: string
}

// ── Constants ─────────────────────────────────────────────────────────────────

const C_PRIMARY = '#4b7c60'
const C_TERRA   = '#c06c52'
const C_SAGE    = '#8da399'

function fmt(v?: number | null, d = 1) { return v != null ? v.toFixed(d) : '—' }

function delta(first?: number | null, last?: number | null) {
  if (first == null || last == null) return null
  return last - first
}

function DeltaBadge({ value, unit = '', inverse = false }: { value: number | null; unit?: string; inverse?: boolean }) {
  if (value == null) return <span className="text-slate-300 text-xs">—</span>
  const positive = inverse ? value < 0 : value > 0
  const neutral = Math.abs(value) < 0.05
  return (
    <span className={`text-xs font-bold px-1.5 py-0.5 rounded-full ${
      neutral ? 'bg-slate-100 text-slate-400'
      : positive ? 'bg-green-100 text-green-700'
      : 'bg-red-100 text-red-600'
    }`}>
      {value > 0 ? '+' : ''}{value.toFixed(1)}{unit}
    </span>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────

export default function PatientProgressPage() {
  const { id } = useParams<{ id: string }>()
  const { token, user } = useAuth()
  const reportRef = useRef<HTMLDivElement>(null)
  const API = import.meta.env.VITE_API_URL

  const [patient, setPatient] = useState<Patient | null>(null)
  const [evals, setEvals]     = useState<Eval[]>([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    if (!id || !token) return
    const H = { Authorization: `Bearer ${token}` }
    Promise.all([
      fetch(`${API}/patients/${id}`, { headers: H }).then(r => r.json()),
      fetch(`${API}/anthropometrics/${id}`, { headers: H }).then(r => r.json()),
    ]).then(([p, ev]) => {
      setPatient(p)
      const list: Eval[] = Array.isArray(ev) ? ev : []
      setEvals(list.sort((a, b) => a.date.localeCompare(b.date)))
      setLoading(false)
    })
  }, [id, token, API])

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
      a.download = `progreso_${patient?.name.replace(/ /g, '_')}.png`
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
      pdf.save(`progreso_${patient?.name.replace(/ /g, '_')}.pdf`)
    } finally { setExporting(false) }
  }

  if (loading || !patient) {
    return (
      <div className="min-h-screen bg-[#F7F5F2] flex items-center justify-center">
        <p className="text-[#6b7280] text-sm">Cargando informe de progreso...</p>
      </div>
    )
  }

  // Derived data
  const first = evals[0]
  const last  = evals[evals.length - 1]
  const hasData = evals.length > 0

  const brandName    = user?.clinic_name || user?.name || user?.username || 'Consultorio'
  const brandTagline = user?.report_tagline || 'Informe de Progreso'
  const initials     = patient.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()

  // Chart data — only entries with at least weight
  const chartData = evals
    .filter(e => e.weight_kg != null)
    .map(e => ({
      fecha: e.date,
      'Peso (kg)': e.weight_kg,
      '% Grasa': e.fat_mass_pct ?? null,
      'Masa Magra (kg)': e.lean_mass_kg ?? null,
    }))

  const hasWeightChart = chartData.length >= 2
  const hasFatChart    = chartData.some(d => d['% Grasa'] != null) && chartData.filter(d => d['% Grasa'] != null).length >= 2

  const dWeight = delta(first?.weight_kg, last?.weight_kg)
  const dFat    = delta(first?.fat_mass_pct, last?.fat_mass_pct)
  const dLean   = delta(first?.lean_mass_kg, last?.lean_mass_kg)

  return (
    <div className="min-h-screen bg-[#F7F5F2] font-sans">

      {/* Toolbar (no export) */}
      <div className="no-export sticky top-0 z-50 bg-white border-b border-[#E5EAE7] px-6 py-3 flex items-center justify-between shadow-sm">
        <Link to={`/patients/${id}`}
          className="flex items-center gap-2 text-[#6b7280] hover:text-[#4b7c60] text-sm transition-colors">
          ← Volver al Paciente
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-[#6b7280] text-sm">Informe de Progreso — {patient.name}</span>
          <button onClick={handleExportPNG} disabled={exporting}
            className="px-4 py-2 bg-white border border-[#E5EAE7] rounded-lg text-sm font-medium text-slate-700 hover:bg-[#F7F5F2] transition-colors disabled:opacity-50">
            {exporting ? 'Exportando...' : '↓ PNG'}
          </button>
          <button onClick={handleExportPDF} disabled={exporting}
            className="px-4 py-2 rounded-lg text-sm font-bold text-white disabled:opacity-50"
            style={{ backgroundColor: C_PRIMARY }}>
            {exporting ? 'Exportando...' : '↓ PDF'}
          </button>
        </div>
      </div>

      {/* Report */}
      <div className="py-8 px-4 flex justify-center">
        <div ref={reportRef} className="w-full max-w-4xl bg-[#F7F5F2]" style={{ fontFamily: 'Inter, sans-serif' }}>

          {/* 1. Header */}
          <header className="w-full py-8 px-8 text-white flex justify-between items-center"
            style={{ backgroundColor: C_PRIMARY }}>
            <div className="flex items-center gap-4">
              {user?.logo_base64 ? (
                <img src={user.logo_base64} alt="Logo" className="h-14 w-auto max-w-[160px] object-contain rounded-xl bg-white/10 p-1" />
              ) : (
                <div className="bg-white/20 p-3 rounded-xl">
                  <span className="text-3xl">📈</span>
                </div>
              )}
              <div>
                <h1 className="text-3xl font-black tracking-tight">{brandName}</h1>
                <p className="text-white/80 text-xs font-semibold uppercase tracking-widest mt-0.5">{brandTagline}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-bold text-lg">Paciente: {patient.name}</p>
              <p className="text-white/70 text-sm mt-0.5">
                {evals.length} evaluación{evals.length !== 1 ? 'es' : ''} registrada{evals.length !== 1 ? 's' : ''}
              </p>
            </div>
          </header>

          <div className="bg-white rounded-b-xl shadow-xl overflow-hidden border border-[#4b7c60]/10">

            {/* 2. Hero — paciente + variaciones */}
            <div className="p-8 border-b border-slate-100 flex gap-6 items-center"
              style={{ background: 'linear-gradient(135deg, rgba(75,124,96,0.07) 0%, transparent 100%)' }}>
              <div className="w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl font-black flex-shrink-0 border-4 border-white shadow-md"
                style={{ backgroundColor: C_PRIMARY }}>
                {initials}
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-slate-900">{patient.name}</h2>
                <p className="text-[#6b7280] text-sm mt-1">
                  {patient.sex === 'M' ? 'Masculino' : patient.sex === 'F' ? 'Femenino' : patient.sex}
                  {first && ` · Primera eval: ${first.date}`}
                  {last && evals.length > 1 && ` · Última: ${last.date}`}
                </p>
              </div>
              {evals.length > 1 && (
                <div className="flex gap-6 flex-shrink-0">
                  <div className="text-center">
                    <p className="text-xs text-slate-400 mb-1">Peso</p>
                    <DeltaBadge value={dWeight} unit=" kg" inverse />
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-slate-400 mb-1">% Grasa</p>
                    <DeltaBadge value={dFat} unit="%" inverse />
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-slate-400 mb-1">Masa Magra</p>
                    <DeltaBadge value={dLean} unit=" kg" />
                  </div>
                </div>
              )}
            </div>

            {!hasData ? (
              <div className="p-16 text-center text-slate-400">
                <p className="text-4xl mb-4">📋</p>
                <p className="font-medium">No hay evaluaciones antropométricas registradas para este paciente.</p>
              </div>
            ) : (
              <>
                {/* 3. Resumen primera vs última evaluación */}
                {evals.length > 1 && (
                  <div className="p-8 border-b border-slate-100">
                    <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.15em] mb-5">
                      Comparativa: Primera vs Última Evaluación
                    </h3>
                    <div className="grid grid-cols-2 gap-6">
                      {/* Primera */}
                      <div className="border border-slate-100 rounded-xl overflow-hidden">
                        <div className="px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-slate-500 bg-slate-50">
                          Primera evaluación — {first?.date}
                        </div>
                        <div className="p-4 space-y-2">
                          {[
                            { label: 'Peso', value: fmt(first?.weight_kg), unit: 'kg' },
                            { label: '% Grasa', value: fmt(first?.fat_mass_pct), unit: '%' },
                            { label: 'Masa magra', value: fmt(first?.lean_mass_kg), unit: 'kg' },
                            { label: 'Masa grasa', value: fmt(first?.fat_mass_kg), unit: 'kg' },
                          ].map(r => (
                            <div key={r.label} className="flex justify-between text-sm">
                              <span className="text-slate-500">{r.label}</span>
                              <span className="font-semibold text-slate-800">{r.value} {r.value !== '—' ? r.unit : ''}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      {/* Última */}
                      <div className="border rounded-xl overflow-hidden" style={{ borderColor: `${C_PRIMARY}30` }}>
                        <div className="px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-white"
                          style={{ backgroundColor: C_PRIMARY }}>
                          Última evaluación — {last?.date}
                        </div>
                        <div className="p-4 space-y-2">
                          {[
                            { label: 'Peso', value: fmt(last?.weight_kg), unit: 'kg', delta: dWeight, inv: true },
                            { label: '% Grasa', value: fmt(last?.fat_mass_pct), unit: '%', delta: dFat, inv: true },
                            { label: 'Masa magra', value: fmt(last?.lean_mass_kg), unit: 'kg', delta: dLean, inv: false },
                            { label: 'Masa grasa', value: fmt(last?.fat_mass_kg), unit: 'kg', delta: delta(first?.fat_mass_kg, last?.fat_mass_kg), inv: true },
                          ].map(r => (
                            <div key={r.label} className="flex justify-between items-center text-sm">
                              <span className="text-slate-500">{r.label}</span>
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-slate-800">{r.value} {r.value !== '—' ? r.unit : ''}</span>
                                <DeltaBadge value={r.delta ?? null} unit={r.unit === '%' ? '%' : ` ${r.unit}`} inverse={r.inv} />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 4. Gráfico de peso */}
                {hasWeightChart && (
                  <div className="p-8 border-b border-slate-100">
                    <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.15em] mb-5">
                      Evolución del Peso
                    </h3>
                    <ResponsiveContainer width="100%" height={220}>
                      <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="fecha" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={['auto', 'auto']} />
                        <Tooltip
                          contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }}
                          formatter={(v) => [`${(v as number).toFixed(1)} kg`, 'Peso']}
                        />
                        <Line
                          type="monotone" dataKey="Peso (kg)"
                          stroke={C_PRIMARY} strokeWidth={2.5}
                          dot={{ fill: C_PRIMARY, r: 4 }} activeDot={{ r: 6 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* 5. Gráfico composición corporal */}
                {hasFatChart && (
                  <div className="p-8 border-b border-slate-100">
                    <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.15em] mb-5">
                      Composición Corporal
                    </h3>
                    <ResponsiveContainer width="100%" height={220}>
                      <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="fecha" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={['auto', 'auto']} />
                        <Tooltip
                          contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }}
                        />
                        <Legend wrapperStyle={{ fontSize: 12 }} />
                        <Line
                          type="monotone" dataKey="% Grasa"
                          stroke={C_TERRA} strokeWidth={2}
                          dot={{ fill: C_TERRA, r: 3 }} activeDot={{ r: 5 }}
                          connectNulls
                        />
                        <Line
                          type="monotone" dataKey="Masa Magra (kg)"
                          stroke={C_SAGE} strokeWidth={2}
                          dot={{ fill: C_SAGE, r: 3 }} activeDot={{ r: 5 }}
                          connectNulls
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* 6. Tabla completa de evaluaciones */}
                <div className="p-8">
                  <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.15em] mb-5">
                    Historial Completo de Evaluaciones
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100">
                          {['Fecha', 'Nivel', 'Peso (kg)', '% Grasa', 'Masa Magra (kg)', 'Masa Grasa (kg)'].map(h => (
                            <th key={h} className="py-2 px-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {[...evals].reverse().map((e, i) => (
                          <tr key={e.id} className={`border-b border-slate-50 ${i === 0 ? 'font-semibold' : ''}`}>
                            <td className="py-2.5 px-3 text-slate-800">
                              {e.date}
                              {i === 0 && <span className="ml-2 text-xs text-[#4b7c60] font-bold">↑ última</span>}
                            </td>
                            <td className="py-2.5 px-3">
                              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 font-medium">
                                {e.isak_level ?? 'ISAK 1'}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-slate-700">{fmt(e.weight_kg)}</td>
                            <td className="py-2.5 px-3 text-slate-700">{e.fat_mass_pct != null ? `${fmt(e.fat_mass_pct)}%` : '—'}</td>
                            <td className="py-2.5 px-3 text-slate-700">{fmt(e.lean_mass_kg)}</td>
                            <td className="py-2.5 px-3 text-slate-700">{fmt(e.fat_mass_kg)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
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
