import { Fragment, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { CartesianGrid, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import Layout from '../components/Layout'
import { useToast } from '../context/ToastContext'
import { api, apiErrorMessage } from '../api/client'

interface CatalogItem {
  key: string
  nombre: string
  grupo: string
  unidad: string
  ref_min: number | null
  ref_max: number | null
}

interface Examen {
  id: number
  fecha: string
  analito: string
  nombre: string
  grupo: string
  valor: number
  unidad: string | null
  ref_min: number | null
  ref_max: number | null
  estado: 'bajo' | 'normal' | 'alto'
}

interface RowInput { valor: string; min: string; max: string }

const INPUT = 'px-2 py-1.5 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30'
const ESTADO: Record<Examen['estado'], { label: string; cls: string }> = {
  bajo: { label: 'Bajo', cls: 'bg-amber-50 text-amber-700 border-amber-200' },
  normal: { label: 'Normal', cls: 'bg-green-50 text-green-700 border-green-100' },
  alto: { label: 'Alto', cls: 'bg-red-50 text-red-700 border-red-200' },
}
const HOMA_LIMIT = 2.5

const num = (v: number) => v.toLocaleString('es-CL', { maximumFractionDigits: 2 })
const fmtDate = (iso: string) => iso.split('-').reverse().join('-')
/** Acepta coma o punto decimal ("5,6" o "5.6"); vacío o inválido → null. */
const parseDecimal = (s: string): number | null => {
  const t = s.trim().replace(',', '.')
  return /^-?\d+(\.\d+)?$/.test(t) ? parseFloat(t) : null
}

function rangeText(min: number | null, max: number | null, unidad?: string | null) {
  const u = unidad ? ` ${unidad}` : ''
  if (min != null && max != null) return `${num(min)}–${num(max)}${u}`
  if (max != null) return `≤ ${num(max)}${u}`
  if (min != null) return `≥ ${num(min)}${u}`
  return '—'
}

/** Exámenes de laboratorio del paciente: último valor por examen, historial y HOMA-IR. */
export default function LaboratorioPage() {
  const { id } = useParams<{ id: string }>()
  const toast = useToast()
  const [patientName, setPatientName] = useState('')
  const [catalog, setCatalog] = useState<CatalogItem[]>([])
  const [examenes, setExamenes] = useState<Examen[] | null>(null)
  const [open, setOpen] = useState<string | null>(null)
  const [form, setForm] = useState<{ fecha: string; rows: Record<string, RowInput> } | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get<{ name: string }>(`/patients/${id}`).then(p => setPatientName(p.name)).catch(() => {})
    api.get<CatalogItem[]>(`/laboratorio/${id}/catalogo`).then(setCatalog).catch(() => {})
    api.get<Examen[]>(`/laboratorio/${id}`).then(setExamenes).catch(err => {
      setExamenes([])
      toast.error(apiErrorMessage(err, 'No se pudieron cargar los exámenes'))
    })
  }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  // Por examen: resultados del más reciente al más antiguo
  const byAnalito = useMemo(() => {
    const map = new Map<string, Examen[]>()
    for (const e of [...(examenes ?? [])].sort((a, b) => b.fecha.localeCompare(a.fecha) || b.id - a.id)) {
      map.set(e.analito, [...(map.get(e.analito) ?? []), e])
    }
    return map
  }, [examenes])

  const groups = useMemo(() => {
    const out = new Map<string, CatalogItem[]>()
    for (const c of catalog) out.set(c.grupo, [...(out.get(c.grupo) ?? []), c])
    return [...out.entries()]
  }, [catalog])

  // HOMA-IR = glicemia (mg/dL) × insulina (µUI/mL) / 405, con ambos del mismo día
  const homa = useMemo(() => {
    const ins = new Map((byAnalito.get('insulina') ?? []).map(e => [e.fecha, e.valor]))
    return (byAnalito.get('glicemia') ?? [])
      .filter(g => ins.has(g.fecha))
      .map(g => ({ fecha: g.fecha, valor: (g.valor * ins.get(g.fecha)!) / 405 }))
  }, [byAnalito])

  const outOfRange = [...byAnalito.values()].filter(list => list[0].estado !== 'normal').length

  const startForm = () => setForm({
    fecha: new Date().toLocaleDateString('en-CA'),
    rows: Object.fromEntries(catalog.map(c => [c.key, {
      valor: '', min: c.ref_min != null ? num(c.ref_min) : '', max: c.ref_max != null ? num(c.ref_max) : '',
    }])),
  })

  const setRow = (key: string, field: keyof RowInput, value: string) =>
    setForm(f => (f ? { ...f, rows: { ...f.rows, [key]: { ...f.rows[key], [field]: value } } } : f))

  const filled = form ? Object.entries(form.rows).filter(([, r]) => r.valor.trim() !== '') : []
  const invalid = filled.some(([, r]) => parseDecimal(r.valor) == null)

  const save = async () => {
    if (!form || !filled.length || invalid) return
    setSaving(true)
    try {
      const created = await api.post<Examen[]>(`/laboratorio/${id}`, {
        fecha: form.fecha,
        resultados: filled.map(([analito, r]) => ({
          analito, valor: parseDecimal(r.valor), ref_min: parseDecimal(r.min), ref_max: parseDecimal(r.max),
        })),
      })
      setExamenes(prev => [...(prev ?? []), ...created])
      setForm(null)
      toast.success(`${created.length} resultado${created.length === 1 ? '' : 's'} guardado${created.length === 1 ? '' : 's'}`)
    } catch (err) {
      toast.error(apiErrorMessage(err, 'No se pudieron guardar los resultados'))
    } finally {
      setSaving(false)
    }
  }

  const remove = async (e: Examen) => {
    if (!window.confirm(`¿Eliminar ${e.nombre} del ${fmtDate(e.fecha)}?`)) return
    try {
      await api.delete(`/laboratorio/${id}/${e.id}`)
      setExamenes(prev => (prev ?? []).filter(x => x.id !== e.id))
    } catch (err) {
      toast.error(apiErrorMessage(err, 'No se pudo eliminar el resultado'))
    }
  }

  return (
    <Layout title="Laboratorio">
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <Link to={`/patients/${id}`} className="hover:text-primary">{patientName || 'Paciente'}</Link>
        <span>/</span>
        <span className="text-primary font-medium">Laboratorio</span>
      </div>

      <div className="max-w-4xl space-y-6">
        <div className="flex flex-wrap items-center gap-3">
          {!form && (
            <button onClick={startForm} disabled={!catalog.length}
              className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50">
              + Ingresar resultados
            </button>
          )}
          {examenes && examenes.length > 0 && (
            <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${outOfRange
              ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-green-50 text-green-700 border-green-100'}`}>
              {outOfRange ? `${outOfRange} examen${outOfRange === 1 ? '' : 'es'} fuera de rango en el último control` : 'Últimos resultados dentro de rango'}
            </span>
          )}
        </div>

        {form && (
          <div className="bg-white rounded-xl shadow-sm border border-border p-6 space-y-4">
            <div className="flex flex-wrap items-end justify-between gap-3 border-b border-border pb-3">
              <h2 className="text-xs font-bold text-text-muted uppercase tracking-widest">Resultados de la toma de muestra</h2>
              <label className="text-sm">
                <span className="block text-xs font-semibold text-text-muted mb-1">Fecha del examen</span>
                <input type="date" value={form.fecha} onChange={e => setForm({ ...form, fecha: e.target.value })} className={INPUT} />
              </label>
            </div>
            <p className="text-xs text-text-muted">
              Completa solo los exámenes que trae el informe. Los rangos son referenciales: ajústalos a los del laboratorio si difieren.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-text-muted text-left">
                    <th className="py-2 pr-3 font-semibold">Examen</th>
                    <th className="py-2 pr-3 font-semibold">Resultado</th>
                    <th className="py-2 pr-3 font-semibold">Mín.</th>
                    <th className="py-2 font-semibold">Máx.</th>
                  </tr>
                </thead>
                <tbody>
                  {groups.map(([grupo, items]) => (
                    <Fragment key={grupo}>
                      <tr><td colSpan={4} className="pt-4 pb-1 text-xs font-bold text-primary uppercase tracking-wider">{grupo}</td></tr>
                      {items.map(c => {
                        const r = form.rows[c.key]
                        const bad = r.valor.trim() !== '' && parseDecimal(r.valor) == null
                        return (
                          <tr key={c.key} className="border-t border-gray-50">
                            <td className="py-1.5 pr-3 text-gray-800">{c.nombre}</td>
                            <td className="py-1.5 pr-3">
                              <div className="flex items-center gap-1.5">
                                <input value={r.valor} onChange={e => setRow(c.key, 'valor', e.target.value)} inputMode="decimal"
                                  className={`${INPUT} w-24 ${bad ? 'border-red-400' : ''}`} aria-label={`Resultado ${c.nombre}`} />
                                <span className="text-xs text-text-muted whitespace-nowrap">{c.unidad}</span>
                              </div>
                            </td>
                            <td className="py-1.5 pr-3"><input value={r.min} onChange={e => setRow(c.key, 'min', e.target.value)} inputMode="decimal" className={`${INPUT} w-20`} aria-label={`Mínimo ${c.nombre}`} /></td>
                            <td className="py-1.5"><input value={r.max} onChange={e => setRow(c.key, 'max', e.target.value)} inputMode="decimal" className={`${INPUT} w-20`} aria-label={`Máximo ${c.nombre}`} /></td>
                          </tr>
                        )
                      })}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setForm(null)} className="px-4 py-2 border border-gray-200 rounded-lg text-sm font-semibold hover:bg-bg-light">Cancelar</button>
              <button onClick={save} disabled={saving || !filled.length || invalid || !form.fecha}
                className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50">
                {saving ? 'Guardando…' : `Guardar ${filled.length || ''} resultado${filled.length === 1 ? '' : 's'}`}
              </button>
            </div>
          </div>
        )}

        {homa.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-border p-5 flex flex-wrap items-center gap-4">
            <div>
              <p className="text-xs font-bold text-text-muted uppercase tracking-widest">HOMA-IR</p>
              <p className="text-2xl font-bold text-gray-900">{num(homa[0].valor)}</p>
            </div>
            <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${homa[0].valor >= HOMA_LIMIT ? ESTADO.alto.cls : ESTADO.normal.cls}`}>
              {homa[0].valor >= HOMA_LIMIT ? 'Sugiere resistencia a la insulina' : 'Sin resistencia a la insulina'}
            </span>
            <p className="text-xs text-text-muted flex-1 min-w-[200px]">
              Glicemia × insulina / 405 del {fmtDate(homa[0].fecha)}. Referencia: &lt; {num(HOMA_LIMIT)}.
              {homa[1] && ` Anterior: ${num(homa[1].valor)} (${fmtDate(homa[1].fecha)}).`}
            </p>
          </div>
        )}

        {examenes === null ? (
          <p className="text-sm text-text-muted">Cargando…</p>
        ) : examenes.length === 0 ? (
          !form && (
            <div className="bg-white rounded-xl border border-border p-10 text-center text-sm text-text-muted">
              Aún no hay exámenes registrados.
            </div>
          )
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr className="text-xs font-bold text-gray-400 uppercase tracking-wider text-left">
                  <th className="px-4 py-3">Examen</th>
                  <th className="px-4 py-3">Último</th>
                  <th className="px-4 py-3 hidden sm:table-cell">Anterior</th>
                  <th className="px-4 py-3 hidden md:table-cell">Referencia</th>
                  <th className="px-4 py-3 text-right">Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {catalog.filter(c => byAnalito.has(c.key)).map(c => {
                  const list = byAnalito.get(c.key)!
                  const last = list[0]
                  const prev = list[1]
                  const isOpen = open === c.key
                  return (
                    <Fragment key={c.key}>
                      <tr onClick={() => setOpen(isOpen ? null : c.key)} className="cursor-pointer hover:bg-bg-light/50">
                        <td className="px-4 py-3 text-gray-800 font-medium">{isOpen ? '▾' : '▸'} {c.nombre}</td>
                        <td className="px-4 py-3">
                          <span className="font-semibold text-gray-900">{num(last.valor)}</span>
                          <span className="text-xs text-text-muted"> {last.unidad}</span>
                          <span className={`ml-2 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${ESTADO[last.estado].cls}`}>{ESTADO[last.estado].label}</span>
                        </td>
                        <td className="px-4 py-3 text-text-muted hidden sm:table-cell">
                          {prev ? `${num(prev.valor)} ${last.valor > prev.valor ? '↑' : last.valor < prev.valor ? '↓' : '='}` : '—'}
                        </td>
                        <td className="px-4 py-3 text-text-muted hidden md:table-cell">{rangeText(last.ref_min, last.ref_max, last.unidad)}</td>
                        <td className="px-4 py-3 text-right text-xs text-text-muted whitespace-nowrap">{fmtDate(last.fecha)}</td>
                      </tr>
                      {isOpen && (
                        <tr>
                          <td colSpan={5} className="px-4 pb-4 bg-bg-light/30">
                            {list.length > 1 && (
                              <div className="h-44 mt-2">
                                <ResponsiveContainer width="100%" height="100%">
                                  <LineChart data={[...list].reverse().map(e => ({ fecha: fmtDate(e.fecha), valor: e.valor }))}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#E5EAE7" />
                                    {(last.ref_min != null || last.ref_max != null) && (
                                      <ReferenceArea y1={last.ref_min ?? undefined} y2={last.ref_max ?? undefined} fill="#4b7c60" fillOpacity={0.1} ifOverflow="extendDomain" />
                                    )}
                                    <XAxis dataKey="fecha" tick={{ fontSize: 11 }} padding={{ left: 24, right: 24 }} />
                                    <YAxis tick={{ fontSize: 11 }} tickFormatter={num} width={44} domain={['auto', 'auto']} />
                                    <Tooltip formatter={v => [`${num(Number(v))} ${last.unidad ?? ''}`, c.nombre]} />
                                    <Line type="monotone" dataKey="valor" stroke="#4b7c60" strokeWidth={2} dot={{ r: 3 }} />
                                  </LineChart>
                                </ResponsiveContainer>
                              </div>
                            )}
                            <ul className="mt-2 space-y-1">
                              {list.map(e => (
                                <li key={e.id} className="flex items-center gap-3 text-xs text-gray-700">
                                  <span className="w-20 text-text-muted">{fmtDate(e.fecha)}</span>
                                  <span className="w-24 font-semibold">{num(e.valor)} {e.unidad}</span>
                                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${ESTADO[e.estado].cls}`}>{ESTADO[e.estado].label}</span>
                                  <span className="text-text-muted">ref. {rangeText(e.ref_min, e.ref_max)}</span>
                                  <button onClick={() => remove(e)} className="ml-auto text-red-600 hover:underline">Eliminar</button>
                                </li>
                              ))}
                            </ul>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  )
}
