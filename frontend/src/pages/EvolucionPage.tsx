import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Layout from '../components/Layout'
import { useToast } from '../context/ToastContext'
import { api, apiErrorMessage } from '../api/client'

interface Nota {
  id: number
  fecha: string
  motivo: string | null
  subjetivo: string | null
  objetivo: string | null
  analisis: string | null
  plan: string | null
  proximo_control: string | null
}

interface Evaluation {
  date: string
  weight_kg?: number | null
  waist_cm?: number | null
  fat_mass_pct?: number | null
  lean_mass_kg?: number | null
  sum_6_skinfolds?: number | null
}

type Draft = Omit<Nota, 'id'>

const SOAP: { key: 'subjetivo' | 'objetivo' | 'analisis' | 'plan'; letter: string; label: string; hint: string }[] = [
  { key: 'subjetivo', letter: 'S', label: 'Subjetivo', hint: 'Lo que relata el paciente: adherencia, hambre, síntomas, sueño, actividad…' },
  { key: 'objetivo', letter: 'O', label: 'Objetivo', hint: 'Mediciones y hallazgos: peso, cintura, % grasa, exámenes…' },
  { key: 'analisis', letter: 'A', label: 'Análisis', hint: 'Evaluación y diagnóstico nutricional, avance respecto a las metas.' },
  { key: 'plan', letter: 'P', label: 'Plan', hint: 'Indicaciones, cambios a la pauta y acuerdos con el paciente.' },
]

const INPUT = 'w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30'

const today = () => new Date().toLocaleDateString('en-CA')
const emptyDraft = (): Draft => ({
  fecha: today(), motivo: '', subjetivo: '', objetivo: '', analisis: '', plan: '', proximo_control: '',
})
const fmtDate = (iso: string | null) => (iso ? iso.split('-').reverse().join('-') : '')
const num = (v: number, d = 1) => v.toLocaleString('es-CL', { maximumFractionDigits: d })

/** Texto para "Objetivo" con los datos de la evaluación antropométrica más reciente. */
function evaluationSummary(e: Evaluation): string {
  const parts = [
    e.weight_kg != null && `Peso ${num(e.weight_kg)} kg`,
    e.waist_cm != null && `cintura ${num(e.waist_cm)} cm`,
    e.fat_mass_pct != null && `grasa ${num(e.fat_mass_pct)} %`,
    e.lean_mass_kg != null && `masa magra ${num(e.lean_mass_kg)} kg`,
    e.sum_6_skinfolds != null && `Σ6 pliegues ${num(e.sum_6_skinfolds)} mm`,
  ].filter(Boolean)
  return `Evaluación ISAK del ${fmtDate(e.date.slice(0, 10))}: ${parts.join(', ')}.`
}

/** Notas de evolución por consulta (SOAP) del paciente. */
export default function EvolucionPage() {
  const { id } = useParams<{ id: string }>()
  const toast = useToast()
  const [patientName, setPatientName] = useState('')
  const [notas, setNotas] = useState<Nota[] | null>(null)
  const [lastEval, setLastEval] = useState<Evaluation | null>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get<{ name: string }>(`/patients/${id}`).then(p => setPatientName(p.name)).catch(() => {})
    api.get<Nota[]>(`/notas/${id}`).then(setNotas).catch(err => {
      setNotas([])
      toast.error(apiErrorMessage(err, 'No se pudieron cargar las notas'))
    })
    api.get<Evaluation[]>(`/anthropometrics/${id}`)
      .then(evals => setLastEval([...evals].sort((a, b) => b.date.localeCompare(a.date))[0] ?? null))
      .catch(() => {})
  }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  const startNew = () => {
    setEditingId(null)
    setDraft(emptyDraft())
  }

  const startEdit = (n: Nota) => {
    setEditingId(n.id)
    const { id: _id, ...rest } = n
    setDraft({ ...rest, motivo: rest.motivo ?? '', proximo_control: rest.proximo_control ?? '' })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const set = (key: keyof Draft, value: string) => setDraft(d => (d ? { ...d, [key]: value } : d))

  const save = async () => {
    if (!draft) return
    setSaving(true)
    try {
      if (editingId) {
        const updated = await api.put<Nota>(`/notas/${id}/${editingId}`, draft)
        setNotas(ns => (ns ?? []).map(n => (n.id === editingId ? updated : n)))
      } else {
        const created = await api.post<Nota>(`/notas/${id}`, draft)
        setNotas(ns => [created, ...(ns ?? [])].sort((a, b) => b.fecha.localeCompare(a.fecha) || b.id - a.id))
      }
      toast.success('Nota guardada')
      setDraft(null)
      setEditingId(null)
    } catch (err) {
      toast.error(apiErrorMessage(err, 'No se pudo guardar la nota'))
    } finally {
      setSaving(false)
    }
  }

  const remove = async (n: Nota) => {
    if (!window.confirm(`¿Eliminar la nota del ${fmtDate(n.fecha)}? No se puede deshacer.`)) return
    try {
      await api.delete(`/notas/${id}/${n.id}`)
      setNotas(ns => (ns ?? []).filter(x => x.id !== n.id))
    } catch (err) {
      toast.error(apiErrorMessage(err, 'No se pudo eliminar la nota'))
    }
  }

  const empty = (d: Draft) => !d.motivo && SOAP.every(s => !d[s.key])

  return (
    <Layout title="Evolución">
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <Link to={`/patients/${id}`} className="hover:text-primary">{patientName || 'Paciente'}</Link>
        <span>/</span>
        <span className="text-primary font-medium">Evolución</span>
      </div>

      <div className="max-w-3xl space-y-6">
        {!draft ? (
          <button onClick={startNew}
            className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-semibold">
            + Nueva nota de consulta
          </button>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-border p-6 space-y-4">
            <h2 className="text-xs font-bold text-text-muted uppercase tracking-widest border-b border-border pb-3">
              {editingId ? 'Editar nota' : 'Nueva nota de consulta'}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-[160px_1fr] gap-3">
              <label className="text-sm">
                <span className="block text-xs font-semibold text-text-muted mb-1">Fecha</span>
                <input type="date" value={draft.fecha} onChange={e => set('fecha', e.target.value)} className={INPUT} />
              </label>
              <label className="text-sm">
                <span className="block text-xs font-semibold text-text-muted mb-1">Motivo de la consulta</span>
                <input value={draft.motivo ?? ''} onChange={e => set('motivo', e.target.value)}
                  placeholder="Control mensual, primera consulta…" className={INPUT} />
              </label>
            </div>
            {SOAP.map(s => (
              <label key={s.key} className="block">
                <span className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-text-muted">
                    <span className="inline-flex w-5 h-5 items-center justify-center rounded bg-primary/10 text-primary font-bold mr-1.5">{s.letter}</span>
                    {s.label}
                  </span>
                  {s.key === 'objetivo' && lastEval && (
                    <button type="button" onClick={() => set('objetivo', [draft.objetivo, evaluationSummary(lastEval)].filter(Boolean).join('\n'))}
                      className="text-xs text-primary font-semibold hover:underline">
                      + Insertar última evaluación
                    </button>
                  )}
                </span>
                <textarea rows={3} value={draft[s.key] ?? ''} onChange={e => set(s.key, e.target.value)}
                  placeholder={s.hint} className={`${INPUT} resize-y`} />
              </label>
            ))}
            <label className="block sm:w-60">
              <span className="block text-xs font-semibold text-text-muted mb-1">Próximo control</span>
              <input type="date" value={draft.proximo_control ?? ''} onChange={e => set('proximo_control', e.target.value)} className={INPUT} />
            </label>
            <div className="flex gap-2 justify-end">
              <button onClick={() => { setDraft(null); setEditingId(null) }}
                className="px-4 py-2 border border-gray-200 rounded-lg text-sm font-semibold hover:bg-bg-light">Cancelar</button>
              <button onClick={save} disabled={saving || !draft.fecha || empty(draft)}
                className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50">
                {saving ? 'Guardando…' : 'Guardar nota'}
              </button>
            </div>
          </div>
        )}

        {notas === null ? (
          <p className="text-sm text-text-muted">Cargando…</p>
        ) : notas.length === 0 ? (
          <div className="bg-white rounded-xl border border-border p-10 text-center text-sm text-text-muted">
            Aún no hay notas de evolución. Registra cada consulta para dejar constancia en la ficha clínica.
          </div>
        ) : (
          <ol className="relative border-l-2 border-primary/20 ml-2 space-y-5">
            {notas.map(n => (
              <li key={n.id} className="ml-5">
                <span className="absolute -left-[7px] mt-5 w-3 h-3 rounded-full bg-primary" />
                <div className="bg-white rounded-xl shadow-sm border border-border p-5 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-bold text-gray-900">{fmtDate(n.fecha)}</p>
                      {n.motivo && <p className="text-sm text-text-muted">{n.motivo}</p>}
                    </div>
                    <div className="flex gap-3 text-xs font-semibold">
                      <button onClick={() => startEdit(n)} className="text-primary hover:underline">Editar</button>
                      <button onClick={() => remove(n)} className="text-red-600 hover:underline">Eliminar</button>
                    </div>
                  </div>
                  <dl className="space-y-2">
                    {SOAP.filter(s => n[s.key]).map(s => (
                      <div key={s.key} className="flex gap-3">
                        <dt className="flex-shrink-0 w-5 h-5 rounded bg-primary/10 text-primary text-xs font-bold flex items-center justify-center" title={s.label}>{s.letter}</dt>
                        <dd className="text-sm text-gray-700 whitespace-pre-line">{n[s.key]}</dd>
                      </div>
                    ))}
                  </dl>
                  {n.proximo_control && (
                    <p className="text-xs text-text-muted">Próximo control: <span className="font-semibold">{fmtDate(n.proximo_control)}</span></p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        )}
      </div>
    </Layout>
  )
}
