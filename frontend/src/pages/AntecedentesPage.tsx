import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'

const TABS = [
  'Identificación',
  'Historial Peso',
  'Anamnesis Remota',
  'Antecedentes Sociales',
  'Anamnesis Alimentaria',
  'Recordatorio 24hrs',
  'Metas y Signos',
]

interface RecordatorioRow {
  tiempo: string
  horario: string
  preparaciones: string
  observaciones: string
}

interface FormData {
  identidad_genero: string
  estado_civil: string
  prevision: string
  horario_trabajo: string
  tipo_traslado: string
  nutricionista_previo: string
  motivo_consulta: string
  tipo_alimentacion: string
  peso_habitual: string
  peso_maximo: string
  peso_minimo: string
  peso_oscilaciones: string
  enfermedades_preexistentes: string
  antecedentes_familiares: string
  farmacos_suplementos: string
  suplementacion_b12: string
  cirugias: string
  dietas_moda: string
  tabaco_alcohol: string
  ejercicio_frecuencia: string
  ejercicio_duracion: string
  ejercicio_intensidad: string
  ejercicio_objetivo: string
  con_quien_vive: string
  mascotas: string
  relacion_familiar: string
  quien_cocina: string
  gusta_cocinar: string
  sale_fines_semana: string
  transito_intestinal: string
  sintomas_gi: string
  evento_traumatico: string
  intolerancias: string
  aversiones: string
  alimentos_gustados: string
  comida_emocional: string
  tiempo_comidas: string
  come_distracciones: string
  calificacion_alimentacion: string
  metas_corto_plazo: string
  metas_largo_plazo: string
  signos_carenciales: string
}

const EMPTY_FORM: FormData = {
  identidad_genero: '',
  estado_civil: '',
  prevision: '',
  horario_trabajo: '',
  tipo_traslado: '',
  nutricionista_previo: '',
  motivo_consulta: '',
  tipo_alimentacion: '',
  peso_habitual: '',
  peso_maximo: '',
  peso_minimo: '',
  peso_oscilaciones: '',
  enfermedades_preexistentes: '',
  antecedentes_familiares: '',
  farmacos_suplementos: '',
  suplementacion_b12: '',
  cirugias: '',
  dietas_moda: '',
  tabaco_alcohol: '',
  ejercicio_frecuencia: '',
  ejercicio_duracion: '',
  ejercicio_intensidad: '',
  ejercicio_objetivo: '',
  con_quien_vive: '',
  mascotas: '',
  relacion_familiar: '',
  quien_cocina: '',
  gusta_cocinar: '',
  sale_fines_semana: '',
  transito_intestinal: '',
  sintomas_gi: '',
  evento_traumatico: '',
  intolerancias: '',
  aversiones: '',
  alimentos_gustados: '',
  comida_emocional: '',
  tiempo_comidas: '',
  come_distracciones: '',
  calificacion_alimentacion: '',
  metas_corto_plazo: '',
  metas_largo_plazo: '',
  signos_carenciales: '',
}

const inputClass = 'w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary'
const labelClass = 'block text-xs font-semibold text-text-muted uppercase tracking-wide mb-1'
const sectionClass = 'bg-white rounded-xl border border-border p-6 mb-4'

function Label({ children }: { children: React.ReactNode }) {
  return <label className={labelClass}>{children}</label>
}

function BoolSelect({ value, onChange, name }: { value: string; onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void; name: string }) {
  return (
    <select name={name} value={value} onChange={onChange} className={inputClass}>
      <option value="">Sin información</option>
      <option value="true">Sí</option>
      <option value="false">No</option>
    </select>
  )
}

export default function AntecedentesPage() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()
  const API = import.meta.env.VITE_API_URL
  const [activeTab, setActiveTab] = useState(0)
  const [form, setForm] = useState<FormData>(EMPTY_FORM)
  const [recordatorioSemana, setRecordatorioSemana] = useState<RecordatorioRow[]>([])
  const [recordatorioFinde, setRecordatorioFinde] = useState<RecordatorioRow[]>([])
  const [patientName, setPatientName] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

  const showToast = (msg: string, type: 'success' | 'error') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  useEffect(() => {
    if (!token || !id) return
    const H = { Authorization: `Bearer ${token}` }
    const load = async () => {
      try {
        const res = await fetch(`${API}/patients/${id}`, { headers: H })
        if (res.ok) {
          const patient = await res.json()
          setPatientName(patient.name)
        }
      } catch {
        // ignore
      }
      try {
        const res = await fetch(`${API}/antecedentes/${id}`, { headers: H })
        if (res.ok) {
          const data = await res.json()
          const mapped: Partial<FormData> = {}
          for (const key of Object.keys(EMPTY_FORM) as (keyof FormData)[]) {
            const val = (data as Record<string, unknown>)[key]
            if (val === null || val === undefined) {
              mapped[key] = ''
            } else if (typeof val === 'boolean') {
              mapped[key] = val ? 'true' : 'false'
            } else {
              mapped[key] = String(val)
            }
          }
          setForm({ ...EMPTY_FORM, ...mapped })
          if (data.recordatorio_semana) {
            try { setRecordatorioSemana(JSON.parse(data.recordatorio_semana)) } catch { /* noop */ }
          }
          if (data.recordatorio_finde) {
            try { setRecordatorioFinde(JSON.parse(data.recordatorio_finde)) } catch { /* noop */ }
          }
        }
        // 404 = new record, stay with empty form
      } catch {
        // network error, stay with empty form
      }
      setLoading(false)
    }
    load()
  }, [id, token, API])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const buildPayload = () => {
    const payload: Record<string, unknown> = {}
    for (const key of Object.keys(form) as (keyof FormData)[]) {
      const boolKeys = ['nutricionista_previo', 'gusta_cocinar', 'sale_fines_semana', 'come_distracciones']
      const floatKeys = ['peso_habitual', 'peso_maximo', 'peso_minimo']
      const intKeys = ['calificacion_alimentacion']
      if (boolKeys.includes(key)) {
        payload[key] = form[key] === '' ? null : form[key] === 'true'
      } else if (floatKeys.includes(key)) {
        payload[key] = form[key] === '' ? null : parseFloat(form[key])
      } else if (intKeys.includes(key)) {
        payload[key] = form[key] === '' ? null : parseInt(form[key])
      } else {
        payload[key] = form[key] === '' ? null : form[key]
      }
    }
    payload.recordatorio_semana = recordatorioSemana.length > 0 ? JSON.stringify(recordatorioSemana) : null
    payload.recordatorio_finde = recordatorioFinde.length > 0 ? JSON.stringify(recordatorioFinde) : null
    return payload
  }

  const handleSave = async () => {
    if (!token || !id) return
    setSaving(true)
    try {
      const res = await fetch(`${API}/antecedentes/${id}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(buildPayload()),
      })
      if (res.ok) {
        showToast('Antecedentes guardados correctamente', 'success')
      } else {
        showToast('Error al guardar antecedentes', 'error')
      }
    } catch {
      showToast('Error al guardar antecedentes', 'error')
    } finally {
      setSaving(false)
    }
  }

  const addRecordatorioRow = (type: 'semana' | 'finde') => {
    const row: RecordatorioRow = { tiempo: '', horario: '', preparaciones: '', observaciones: '' }
    if (type === 'semana') setRecordatorioSemana(prev => [...prev, row])
    else setRecordatorioFinde(prev => [...prev, row])
  }

  const updateRecordatorioRow = (type: 'semana' | 'finde', idx: number, field: keyof RecordatorioRow, value: string) => {
    if (type === 'semana') {
      setRecordatorioSemana(prev => prev.map((r, i) => i === idx ? { ...r, [field]: value } : r))
    } else {
      setRecordatorioFinde(prev => prev.map((r, i) => i === idx ? { ...r, [field]: value } : r))
    }
  }

  const removeRecordatorioRow = (type: 'semana' | 'finde', idx: number) => {
    if (type === 'semana') setRecordatorioSemana(prev => prev.filter((_, i) => i !== idx))
    else setRecordatorioFinde(prev => prev.filter((_, i) => i !== idx))
  }

  const RecordatorioTable = ({ type, rows }: { type: 'semana' | 'finde'; rows: RecordatorioRow[] }) => (
    <div>
      <table className="w-full text-sm border border-border rounded-lg overflow-hidden mb-3">
        <thead className="bg-bg-light">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-semibold text-text-muted uppercase">Tiempo</th>
            <th className="px-3 py-2 text-left text-xs font-semibold text-text-muted uppercase">Horario</th>
            <th className="px-3 py-2 text-left text-xs font-semibold text-text-muted uppercase">Preparaciones</th>
            <th className="px-3 py-2 text-left text-xs font-semibold text-text-muted uppercase">Observaciones</th>
            <th className="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx} className="border-t border-border">
              {(['tiempo', 'horario', 'preparaciones', 'observaciones'] as const).map(field => (
                <td key={field} className="px-2 py-1">
                  <input
                    className="w-full border-0 bg-transparent text-sm focus:outline-none focus:ring-1 focus:ring-primary rounded px-1"
                    value={row[field]}
                    onChange={e => updateRecordatorioRow(type, idx, field, e.target.value)}
                  />
                </td>
              ))}
              <td className="px-2 py-1">
                <button
                  type="button"
                  onClick={() => removeRecordatorioRow(type, idx)}
                  className="text-red-400 hover:text-red-600 text-xs"
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={5} className="px-3 py-4 text-center text-xs text-text-muted italic">Sin registros</td>
            </tr>
          )}
        </tbody>
      </table>
      <button
        type="button"
        onClick={() => addRecordatorioRow(type)}
        className="text-sm text-primary font-semibold hover:underline"
      >
        + Agregar tiempo
      </button>
    </div>
  )

  if (loading) {
    return (
      <Layout title="Antecedentes">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout title="Antecedentes">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg text-white text-sm font-semibold shadow-lg ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}>
          {toast.msg}
        </div>
      )}

      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <Link to={`/patients/${id}`} className="hover:text-primary">{patientName || `Paciente #${id}`}</Link>
        <span>/</span>
        <span className="text-primary font-medium">Antecedentes</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Antecedentes Clínicos</h1>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-5 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-dark transition-colors disabled:opacity-50"
        >
          {saving ? 'Guardando...' : 'Guardar'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 flex-wrap mb-6 border-b border-border">
        {TABS.map((tab, idx) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(idx)}
            className={`px-4 py-2 text-sm font-semibold rounded-t-lg transition-colors ${
              activeTab === idx
                ? 'bg-primary text-white'
                : 'text-gray-600 hover:text-primary'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab 0 - Identificación */}
      {activeTab === 0 && (
        <div className="space-y-4">
          <div className={sectionClass}>
            <h3 className="text-sm font-bold text-gray-700 mb-4">Datos de Identificación</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Identidad de Género</Label>
                <input name="identidad_genero" value={form.identidad_genero} onChange={handleChange} className={inputClass} placeholder="Ej: Femenina, Masculina, No binaria..." />
              </div>
              <div>
                <Label>Estado Civil</Label>
                <select name="estado_civil" value={form.estado_civil} onChange={handleChange} className={inputClass}>
                  <option value="">Seleccionar...</option>
                  <option>Soltero/a</option>
                  <option>Casado/a</option>
                  <option>Conviviente</option>
                  <option>Divorciado/a</option>
                  <option>Viudo/a</option>
                </select>
              </div>
              <div>
                <Label>Previsión</Label>
                <select name="prevision" value={form.prevision} onChange={handleChange} className={inputClass}>
                  <option value="">Seleccionar...</option>
                  <option>FONASA</option>
                  <option>ISAPRE</option>
                  <option>Particular</option>
                  <option>Otro</option>
                </select>
              </div>
              <div>
                <Label>Horario de Trabajo</Label>
                <input name="horario_trabajo" value={form.horario_trabajo} onChange={handleChange} className={inputClass} placeholder="Ej: Diurno, Nocturno, Mixto..." />
              </div>
              <div>
                <Label>Tipo de Traslado</Label>
                <input name="tipo_traslado" value={form.tipo_traslado} onChange={handleChange} className={inputClass} placeholder="Ej: Auto, Transporte público, Caminando..." />
              </div>
              <div>
                <Label>¿Ha visto nutricionista antes?</Label>
                <BoolSelect name="nutricionista_previo" value={form.nutricionista_previo} onChange={handleChange} />
              </div>
              <div>
                <Label>Tipo de Alimentación</Label>
                <select name="tipo_alimentacion" value={form.tipo_alimentacion} onChange={handleChange} className={inputClass}>
                  <option value="">Seleccionar...</option>
                  <option>Omnívoro</option>
                  <option>Vegetariano</option>
                  <option>Vegano</option>
                  <option>Ovolactovegetariano</option>
                  <option>Otro</option>
                </select>
              </div>
            </div>
            <div className="mt-4">
              <Label>Motivo de Consulta</Label>
              <textarea name="motivo_consulta" value={form.motivo_consulta} onChange={handleChange} rows={3} className={inputClass} placeholder="Describa el motivo de consulta..." />
            </div>
          </div>
        </div>
      )}

      {/* Tab 1 - Historial Peso */}
      {activeTab === 1 && (
        <div className={sectionClass}>
          <h3 className="text-sm font-bold text-gray-700 mb-4">Historial de Peso</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Peso Habitual (kg)</Label>
              <input type="number" step="0.1" name="peso_habitual" value={form.peso_habitual} onChange={handleChange} className={inputClass} placeholder="0.0" />
            </div>
            <div>
              <Label>Peso Máximo (kg)</Label>
              <input type="number" step="0.1" name="peso_maximo" value={form.peso_maximo} onChange={handleChange} className={inputClass} placeholder="0.0" />
            </div>
            <div>
              <Label>Peso Mínimo (kg)</Label>
              <input type="number" step="0.1" name="peso_minimo" value={form.peso_minimo} onChange={handleChange} className={inputClass} placeholder="0.0" />
            </div>
          </div>
          <div className="mt-4">
            <Label>Oscilaciones de Peso</Label>
            <textarea name="peso_oscilaciones" value={form.peso_oscilaciones} onChange={handleChange} rows={3} className={inputClass} placeholder="Describa fluctuaciones de peso, intentos de baja de peso, etc." />
          </div>
        </div>
      )}

      {/* Tab 2 - Anamnesis Remota */}
      {activeTab === 2 && (
        <div className="space-y-4">
          <div className={sectionClass}>
            <h3 className="text-sm font-bold text-gray-700 mb-4">Patologías y Medicamentos</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Enfermedades Preexistentes</Label>
                <textarea name="enfermedades_preexistentes" value={form.enfermedades_preexistentes} onChange={handleChange} rows={3} className={inputClass} placeholder="DM2, HTA, dislipidemia, etc." />
              </div>
              <div>
                <Label>Antecedentes Familiares</Label>
                <textarea name="antecedentes_familiares" value={form.antecedentes_familiares} onChange={handleChange} rows={3} className={inputClass} placeholder="Enfermedades hereditarias, antecedentes familiares relevantes..." />
              </div>
              <div>
                <Label>Fármacos y Suplementos</Label>
                <textarea name="farmacos_suplementos" value={form.farmacos_suplementos} onChange={handleChange} rows={3} className={inputClass} placeholder="Medicamentos actuales, dosis, frecuencia..." />
              </div>
              <div>
                <Label>Suplementación B12</Label>
                <textarea name="suplementacion_b12" value={form.suplementacion_b12} onChange={handleChange} rows={3} className={inputClass} placeholder="Indicar dosis y frecuencia si aplica..." />
              </div>
              <div>
                <Label>Cirugías</Label>
                <textarea name="cirugias" value={form.cirugias} onChange={handleChange} rows={2} className={inputClass} placeholder="Cirugías previas relevantes..." />
              </div>
              <div>
                <Label>Dietas de Moda</Label>
                <textarea name="dietas_moda" value={form.dietas_moda} onChange={handleChange} rows={2} className={inputClass} placeholder="Keto, ayuno intermitente, etc." />
              </div>
              <div>
                <Label>Tabaco / Alcohol</Label>
                <textarea name="tabaco_alcohol" value={form.tabaco_alcohol} onChange={handleChange} rows={2} className={inputClass} placeholder="Frecuencia y cantidad..." />
              </div>
            </div>
          </div>
          <div className={sectionClass}>
            <h3 className="text-sm font-bold text-gray-700 mb-4">Actividad Física</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Frecuencia</Label>
                <input name="ejercicio_frecuencia" value={form.ejercicio_frecuencia} onChange={handleChange} className={inputClass} placeholder="Ej: 3 veces por semana" />
              </div>
              <div>
                <Label>Duración</Label>
                <input name="ejercicio_duracion" value={form.ejercicio_duracion} onChange={handleChange} className={inputClass} placeholder="Ej: 45 minutos" />
              </div>
              <div>
                <Label>Intensidad</Label>
                <select name="ejercicio_intensidad" value={form.ejercicio_intensidad} onChange={handleChange} className={inputClass}>
                  <option value="">Seleccionar...</option>
                  <option>Baja</option>
                  <option>Moderada</option>
                  <option>Alta</option>
                </select>
              </div>
              <div>
                <Label>Objetivo del Ejercicio</Label>
                <input name="ejercicio_objetivo" value={form.ejercicio_objetivo} onChange={handleChange} className={inputClass} placeholder="Pérdida de peso, rendimiento, salud..." />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3 - Antecedentes Sociales */}
      {activeTab === 3 && (
        <div className={sectionClass}>
          <h3 className="text-sm font-bold text-gray-700 mb-4">Contexto Social</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>¿Con quién vive?</Label>
              <input name="con_quien_vive" value={form.con_quien_vive} onChange={handleChange} className={inputClass} placeholder="Solo/a, pareja, familia, etc." />
            </div>
            <div>
              <Label>Mascotas</Label>
              <input name="mascotas" value={form.mascotas} onChange={handleChange} className={inputClass} placeholder="Tipo y cantidad de mascotas..." />
            </div>
            <div>
              <Label>Relación Familiar</Label>
              <textarea name="relacion_familiar" value={form.relacion_familiar} onChange={handleChange} rows={2} className={inputClass} placeholder="Descripción del entorno familiar..." />
            </div>
            <div>
              <Label>¿Quién cocina en casa?</Label>
              <input name="quien_cocina" value={form.quien_cocina} onChange={handleChange} className={inputClass} placeholder="El/la paciente, pareja, familiar, nadie..." />
            </div>
            <div>
              <Label>¿Le gusta cocinar?</Label>
              <BoolSelect name="gusta_cocinar" value={form.gusta_cocinar} onChange={handleChange} />
            </div>
            <div>
              <Label>¿Sale los fines de semana?</Label>
              <BoolSelect name="sale_fines_semana" value={form.sale_fines_semana} onChange={handleChange} />
            </div>
          </div>
        </div>
      )}

      {/* Tab 4 - Anamnesis Alimentaria */}
      {activeTab === 4 && (
        <div className={sectionClass}>
          <h3 className="text-sm font-bold text-gray-700 mb-4">Hábitos Alimentarios</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Tránsito Intestinal</Label>
              <textarea name="transito_intestinal" value={form.transito_intestinal} onChange={handleChange} rows={2} className={inputClass} placeholder="Frecuencia, consistencia, síntomas..." />
            </div>
            <div>
              <Label>Síntomas Gastrointestinales</Label>
              <textarea name="sintomas_gi" value={form.sintomas_gi} onChange={handleChange} rows={2} className={inputClass} placeholder="Distensión, reflujo, náuseas..." />
            </div>
            <div>
              <Label>Evento Traumático con Comida</Label>
              <textarea name="evento_traumatico" value={form.evento_traumatico} onChange={handleChange} rows={2} className={inputClass} placeholder="Atragantamiento, alergias graves, etc." />
            </div>
            <div>
              <Label>Intolerancias</Label>
              <textarea name="intolerancias" value={form.intolerancias} onChange={handleChange} rows={2} className={inputClass} placeholder="Lactosa, gluten, fructosa, etc." />
            </div>
            <div>
              <Label>Aversiones Alimentarias</Label>
              <textarea name="aversiones" value={form.aversiones} onChange={handleChange} rows={2} className={inputClass} placeholder="Alimentos que no tolera o rechaza..." />
            </div>
            <div>
              <Label>Alimentos Gustados</Label>
              <textarea name="alimentos_gustados" value={form.alimentos_gustados} onChange={handleChange} rows={2} className={inputClass} placeholder="Alimentos que le gustan mucho..." />
            </div>
            <div>
              <Label>Comida Emocional</Label>
              <textarea name="comida_emocional" value={form.comida_emocional} onChange={handleChange} rows={2} className={inputClass} placeholder="¿Come por ansiedad, estrés, tristeza?..." />
            </div>
            <div>
              <Label>Tiempo de Comidas</Label>
              <input name="tiempo_comidas" value={form.tiempo_comidas} onChange={handleChange} className={inputClass} placeholder="Cuántos tiempos de comida al día..." />
            </div>
            <div>
              <Label>¿Come con distracciones?</Label>
              <BoolSelect name="come_distracciones" value={form.come_distracciones} onChange={handleChange} />
            </div>
            <div>
              <Label>Calificación de su Alimentación (1-10)</Label>
              <input type="number" min="1" max="10" name="calificacion_alimentacion" value={form.calificacion_alimentacion} onChange={handleChange} className={inputClass} placeholder="1-10" />
            </div>
          </div>
        </div>
      )}

      {/* Tab 5 - Recordatorio 24hrs */}
      {activeTab === 5 && (
        <div className="space-y-6">
          <div className={sectionClass}>
            <h3 className="text-sm font-bold text-gray-700 mb-4">Dia de Semana</h3>
            <RecordatorioTable type="semana" rows={recordatorioSemana} />
          </div>
          <div className={sectionClass}>
            <h3 className="text-sm font-bold text-gray-700 mb-4">Fin de Semana</h3>
            <RecordatorioTable type="finde" rows={recordatorioFinde} />
          </div>
        </div>
      )}

      {/* Tab 6 - Metas y Signos */}
      {activeTab === 6 && (
        <div className={sectionClass}>
          <h3 className="text-sm font-bold text-gray-700 mb-4">Metas y Signos Carenciales</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Metas a Corto Plazo</Label>
              <textarea name="metas_corto_plazo" value={form.metas_corto_plazo} onChange={handleChange} rows={4} className={inputClass} placeholder="Objetivos para las próximas semanas/meses..." />
            </div>
            <div>
              <Label>Metas a Largo Plazo</Label>
              <textarea name="metas_largo_plazo" value={form.metas_largo_plazo} onChange={handleChange} rows={4} className={inputClass} placeholder="Objetivos a 6-12 meses..." />
            </div>
            <div className="md:col-span-2">
              <Label>Signos Carenciales</Label>
              <textarea name="signos_carenciales" value={form.signos_carenciales} onChange={handleChange} rows={4} className={inputClass} placeholder="Caída de cabello, uñas quebradizas, palidez, etc." />
            </div>
          </div>
        </div>
      )}

      {/* Bottom save button */}
      <div className="flex justify-end mt-6 gap-3">
        <Link
          to={`/patients/${id}`}
          className="px-5 py-2 border border-gray-200 rounded-lg text-sm font-semibold hover:bg-bg-light transition-colors"
        >
          Volver
        </Link>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-5 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-dark transition-colors disabled:opacity-50"
        >
          {saving ? 'Guardando...' : 'Guardar Antecedentes'}
        </button>
      </div>
    </Layout>
  )
}
