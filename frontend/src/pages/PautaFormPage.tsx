import { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

// ── Food group data (ported from desktop grupos_alimentos.py) ─────────────

const GRUPOS_MACROS: Record<string, { kcal: number; cho: number; lip: number; prot: number }> = {
  cereales:           { kcal: 140, cho: 30,  lip: 1,   prot: 3 },
  verduras_cg:        { kcal: 30,  cho: 5,   lip: 0,   prot: 2 },
  verduras_lc:        { kcal: 10,  cho: 2.5, lip: 0,   prot: 0 },
  frutas:             { kcal: 65,  cho: 15,  lip: 0,   prot: 1 },
  lacteos_ag:         { kcal: 110, cho: 9,   lip: 6,   prot: 5 },
  lacteos_mg:         { kcal: 85,  cho: 9,   lip: 3,   prot: 5 },
  lacteos_bg:         { kcal: 70,  cho: 10,  lip: 0,   prot: 7 },
  legumbres:          { kcal: 170, cho: 32,  lip: 1,   prot: 13 },
  carnes_ag:          { kcal: 120, cho: 1,   lip: 8,   prot: 11 },
  carnes_bg:          { kcal: 65,  cho: 1,   lip: 2,   prot: 11 },
  otros_proteicos:    { kcal: 75,  cho: 5,   lip: 3,   prot: 7 },
  aceite_grasas:      { kcal: 180, cho: 0,   lip: 20,  prot: 0 },
  alim_ricos_lipidos: { kcal: 175, cho: 5,   lip: 15,  prot: 5 },
  leches_vegetales:   { kcal: 80,  cho: 10,  lip: 2,   prot: 1 },
  lacteos_soya:       { kcal: 80,  cho: 9,   lip: 4,   prot: 6 },
  semillas_chia:      { kcal: 37,  cho: 2,   lip: 2,   prot: 1.5 },
  azucares:           { kcal: 20,  cho: 5,   lip: 0,   prot: 0 },
}

const GRUPOS_POR_PAUTA: Record<string, string[]> = {
  omnivoro:    ['cereales','verduras_cg','verduras_lc','frutas','lacteos_ag','lacteos_mg','lacteos_bg','legumbres','carnes_ag','carnes_bg','aceite_grasas','alim_ricos_lipidos','azucares'],
  ovolacto:   ['cereales','verduras_cg','verduras_lc','frutas','lacteos_ag','lacteos_mg','lacteos_bg','legumbres','otros_proteicos','aceite_grasas','alim_ricos_lipidos','leches_vegetales','lacteos_soya','semillas_chia','azucares'],
  vegano:      ['cereales','verduras_cg','verduras_lc','frutas','legumbres','otros_proteicos','aceite_grasas','alim_ricos_lipidos','leches_vegetales','lacteos_soya','semillas_chia','azucares'],
  vegetariano: ['cereales','verduras_cg','verduras_lc','frutas','lacteos_ag','lacteos_mg','lacteos_bg','legumbres','otros_proteicos','aceite_grasas','alim_ricos_lipidos','leches_vegetales','azucares'],
  renal:       ['cereales','verduras_cg','verduras_lc','frutas','lacteos_bg','carnes_bg','aceite_grasas','azucares'],
  diabetico:   ['cereales','verduras_cg','verduras_lc','frutas','lacteos_mg','lacteos_bg','legumbres','carnes_bg','otros_proteicos','aceite_grasas','alim_ricos_lipidos'],
  hipocalorico:['cereales','verduras_cg','verduras_lc','frutas','lacteos_bg','legumbres','carnes_bg','otros_proteicos','aceite_grasas'],
}

const NOMBRES_GRUPOS: Record<string, string> = {
  cereales: 'Cereales', verduras_cg: 'Verduras CG', verduras_lc: 'Verduras LC',
  frutas: 'Frutas', lacteos_ag: 'Lácteos AG', lacteos_mg: 'Lácteos MG',
  lacteos_bg: 'Lácteos BG', legumbres: 'Legumbres', carnes_ag: 'Carnes AG',
  carnes_bg: 'Carnes BG', otros_proteicos: 'Otros Proteicos', aceite_grasas: 'Aceite y Grasas',
  alim_ricos_lipidos: 'Ricos en Lípidos', leches_vegetales: 'Leches Vegetales',
  lacteos_soya: 'Lácteos de Soya', semillas_chia: 'Semillas Chía', azucares: 'Azúcares',
}

const TIEMPOS_COMIDA = [
  { key: 'desayuno',  label: 'Desayuno' },
  { key: 'colacion1', label: 'Colación 1' },
  { key: 'almuerzo',  label: 'Almuerzo' },
  { key: 'colacion2', label: 'Colación 2' },
  { key: 'once',      label: 'Once' },
  { key: 'cena',      label: 'Cena' },
]

// ── Existing constants ─────────────────────────────────────────────────────

const FA_OPTIONS = [
  { key: 'sedentaria',  label: 'Sedentaria',  factor: 1.2,   desc: 'Sin ejercicio o muy poco' },
  { key: 'liviana',     label: 'Liviana',     factor: 1.375, desc: 'Ejercicio leve 1–3 días/semana' },
  { key: 'moderada',    label: 'Moderada',    factor: 1.55,  desc: 'Ejercicio moderado 3–5 días/semana' },
  { key: 'intensa',     label: 'Intensa',     factor: 1.725, desc: 'Ejercicio intenso 6–7 días/semana' },
]

const TIPO_OPTIONS = [
  { key: 'omnivoro',    label: 'Omnívoro' },
  { key: 'ovolacto',   label: 'Ovo-lacto vegetariano' },
  { key: 'vegano',     label: 'Vegano' },
  { key: 'vegetariano', label: 'Vegetariano' },
  { key: 'renal',      label: 'Renal' },
  { key: 'diabetico',  label: 'Diabético' },
  { key: 'hipocalorico', label: 'Hipocalórico' },
]

function calcTMB(sexo: string, peso: number, talla: number, edad: number): number {
  if (sexo === 'M') return 10 * peso + 6.25 * talla - 5 * edad + 5
  return 10 * peso + 6.25 * talla - 5 * edad - 161
}

function adecuacionColor(pct: number) {
  if (pct >= 90 && pct <= 110) return 'text-green-600 bg-green-50'
  if (pct >= 80 && pct <= 120) return 'text-yellow-600 bg-yellow-50'
  return 'text-red-600 bg-red-50'
}

// ── Menu types ─────────────────────────────────────────────────────────────

interface MenuItem {
  nombre: string
  cantidad: number
  unidad: string
  kcal_100: number
  prot_100: number
  cho_100: number
  lip_100: number
}

type MenuOpcion = MenuItem[]
type MenuData = Record<string, { opcion1: MenuOpcion; opcion2: MenuOpcion }>

interface RecetaRef {
  id: number
  nombre: string
  categoria?: string
  descripcion?: string
}

interface RecetaListItem {
  id: number
  nombre: string
  categoria: string
  descripcion?: string
  porciones_rinde: number
}

function itemMacros(item: MenuItem) {
  const f = item.cantidad / 100
  return {
    kcal: +(item.kcal_100 * f).toFixed(1),
    prot: +(item.prot_100 * f).toFixed(1),
    cho:  +(item.cho_100  * f).toFixed(1),
    lip:  +(item.lip_100  * f).toFixed(1),
  }
}

function opcionTotals(items: MenuOpcion) {
  return items.reduce(
    (acc, item) => {
      const m = itemMacros(item)
      return { kcal: +(acc.kcal + m.kcal).toFixed(1), prot: +(acc.prot + m.prot).toFixed(1), cho: +(acc.cho + m.cho).toFixed(1), lip: +(acc.lip + m.lip).toFixed(1) }
    },
    { kcal: 0, prot: 0, cho: 0, lip: 0 }
  )
}

function isStructuredMenu(m: unknown): m is MenuData {
  if (!m || typeof m !== 'object') return false
  const first = Object.values(m as object)[0]
  if (!first || typeof first !== 'object') return false
  const op = (first as Record<string, unknown>).opcion1
  return Array.isArray(op)
}

function StructuredOpcion({
  items,
  colorClass,
  label,
  labelColor,
  onChange,
}: {
  items: MenuOpcion
  colorClass: string
  label: string
  labelColor: string
  onChange: (items: MenuOpcion) => void
}) {
  const totals = opcionTotals(items)
  return (
    <div className={`rounded-lg p-2 ${colorClass}`}>
      <span className={`text-xs font-bold block mb-2 ${labelColor}`}>{label}</span>
      <div className="space-y-1">
        {items.map((item, idx) => (
          <div key={idx} className="flex items-center gap-1 text-xs">
            <span className="flex-1 text-gray-700 truncate" title={item.nombre}>{item.nombre}</span>
            <input
              type="number"
              value={item.cantidad}
              min={0}
              onChange={e => {
                const next = [...items]
                next[idx] = { ...item, cantidad: +e.target.value }
                onChange(next)
              }}
              className="w-14 text-right border border-transparent focus:border-border rounded px-1 py-0.5 bg-transparent focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <span className="text-text-muted w-6 text-right">{item.unidad}</span>
          </div>
        ))}
      </div>
      <div className="mt-2 pt-1 border-t border-black/10 flex gap-2 text-xs text-text-muted flex-wrap">
        <span className="font-medium text-gray-600">{totals.kcal} kcal</span>
        <span>·</span>
        <span>P {totals.prot}g</span>
        <span>·</span>
        <span>C {totals.cho}g</span>
        <span>·</span>
        <span>G {totals.lip}g</span>
      </div>
    </div>
  )
}

// ── Small components ───────────────────────────────────────────────────────

interface PautaData {
  name: string; date: string; tipo_pauta: string; sexo: string
  edad: number; peso: number; talla: number
  fa_key: string; ajuste_kcal: number; prot_pct: number; lip_pct: number; notes: string
}

function Row({ label, value, unit = '', strong = false }: { label: string; value: string | number; unit?: string; strong?: boolean }) {
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-border last:border-0">
      <span className="text-sm text-text-muted">{label}</span>
      <span className={`text-sm ${strong ? 'font-bold text-primary text-base' : 'font-medium text-gray-800'}`}>
        {value} <span className="text-xs font-normal text-text-muted">{unit}</span>
      </span>
    </div>
  )
}

function PctBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-text-muted w-12">{label}</span>
      <div className="flex-1 bg-bg-light rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${Math.min(100, pct).toFixed(0)}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-700 w-8 text-right">{pct.toFixed(0)}%</span>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs text-text-muted mb-1">{label}</label>
      {children}
    </div>
  )
}

const INPUT = 'w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary'
const SELECT = `${INPUT} bg-white`

// ── Main component ─────────────────────────────────────────────────────────

export default function PautaFormPage() {
  const { id, pautaId } = useParams<{ id: string; pautaId: string }>()
  const location = useLocation()
  const isEdit = !!pautaId && location.pathname.endsWith('/edit')
  const isView = !!pautaId && !isEdit
  const { token } = useAuth()
  const navigate = useNavigate()

  const [patientName, setPatientName] = useState('')
  const [form, setForm] = useState<PautaData>({
    name: '', date: new Date().toISOString().split('T')[0],
    tipo_pauta: 'omnivoro', sexo: 'F', edad: 30, peso: 65, talla: 160,
    fa_key: 'moderada', ajuste_kcal: 0, prot_pct: 20, lip_pct: 30, notes: '',
  })
  const [porciones, setPorciones] = useState<Record<string, number>>({})
  const [distribucion, setDistribucion] = useState<Record<string, Record<string, number>>>({})
  const [menu, setMenu] = useState<Record<string, { opcion1: string | MenuOpcion; opcion2: string | MenuOpcion }>>({})
  const [generatingMenu, setGeneratingMenu] = useState(false)
  const [sseStatus, setSseStatus] = useState('')
  const [aiConfigured, setAiConfigured] = useState<boolean | null>(null)
  const [savingMenu, setSavingMenu] = useState(false)
  const [recetas, setRecetas] = useState<RecetaListItem[]>([])
  const [recetasLoaded, setRecetasLoaded] = useState(false)
  const [recetasLoading, setRecetasLoading] = useState(false)
  const [pickingRecetaFor, setPickingRecetaFor] = useState<string | null>(null)
  const [recetaSearch, setRecetaSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  useEffect(() => {
    if (!token || !id) return
    const patientFetch = fetch(`${API}/patients/${id}`, { headers: H }).then(r => r.json())
    const pautaFetch = (isView || isEdit)
      ? fetch(`${API}/pautas/${id}/${pautaId}`, { headers: H }).then(r => r.json())
      : Promise.resolve(null)

    Promise.all([patientFetch, pautaFetch])
      .then(([pat, pauta]) => {
        setPatientName(pat.name ?? '')
        if (pauta && (isView || isEdit)) {
          setForm({
            name: pauta.name, date: pauta.date, tipo_pauta: pauta.tipo_pauta,
            sexo: pauta.sexo, edad: pauta.edad, peso: pauta.peso,
            talla: pat.height_cm ?? 160, fa_key: pauta.fa_key,
            ajuste_kcal: pauta.ajuste_kcal ?? 0, prot_pct: pauta.prot_pct,
            lip_pct: pauta.lip_pct, notes: pauta.notes ?? '',
          })
          try { setPorciones(JSON.parse(pauta.porciones_json || '{}')) } catch {}
          try { setDistribucion(JSON.parse(pauta.distribucion_json || '{}')) } catch {}
          try { if (pauta.menu_json) setMenu(JSON.parse(pauta.menu_json)) } catch {}
        } else {
          const bd = pat.birth_date ? new Date(pat.birth_date) : null
          const age = bd ? Math.max(0, new Date().getFullYear() - bd.getFullYear()) : 30
          setForm(prev => ({
            ...prev, sexo: pat.sex === 'M' ? 'M' : 'F', edad: age,
            peso: pat.weight_kg ?? 65, talla: pat.height_cm ?? 160,
          }))
        }
      })
      .finally(() => setLoading(false))
  }, [id, pautaId, token])

  useEffect(() => {
    if (!token) return
    fetch(`${API}/pautas/ai-status`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => setAiConfigured(d.configured ?? false))
      .catch(() => setAiConfigured(false))
  }, [token])

  const setF = <K extends keyof PautaData>(k: K, v: PautaData[K]) =>
    setForm(prev => ({ ...prev, [k]: v }))

  // ── Macro calculations ───────────────────────────────────────────────────

  const calcs = useMemo(() => {
    const fa = FA_OPTIONS.find(f => f.key === form.fa_key)?.factor ?? 1.55
    const tmb = calcTMB(form.sexo, form.peso, form.talla, form.edad)
    const get_kcal = tmb * fa
    const kcal_objetivo = get_kcal + (form.ajuste_kcal || 0)
    const cho_pct = Math.max(0, 100 - form.prot_pct - form.lip_pct)
    const prot_kcal = kcal_objetivo * form.prot_pct / 100
    const prot_g = prot_kcal / 4
    const prot_g_kg = form.peso > 0 ? prot_g / form.peso : 0
    const lip_kcal = kcal_objetivo * form.lip_pct / 100
    const lip_g = lip_kcal / 9
    const cho_kcal = kcal_objetivo * cho_pct / 100
    const cho_g = cho_kcal / 4
    return { tmb, get_kcal, kcal_objetivo, cho_pct, prot_kcal, prot_g, prot_g_kg, lip_kcal, lip_g, cho_kcal, cho_g }
  }, [form])

  const macroSum = form.prot_pct + form.lip_pct
  const cho_pct = Math.max(0, 100 - macroSum)
  const macroError = macroSum > 100

  // ── Food group calculations ──────────────────────────────────────────────

  const activeGroups = GRUPOS_POR_PAUTA[form.tipo_pauta] ?? GRUPOS_POR_PAUTA['omnivoro']

  const aporteTotal = useMemo(() => {
    const t = { kcal: 0, cho: 0, lip: 0, prot: 0 }
    for (const [g, p] of Object.entries(porciones)) {
      const m = GRUPOS_MACROS[g]
      if (m && p > 0) { t.kcal += m.kcal * p; t.cho += m.cho * p; t.lip += m.lip * p; t.prot += m.prot * p }
    }
    return { kcal: Math.round(t.kcal), cho: +t.cho.toFixed(1), lip: +t.lip.toFixed(1), prot: +t.prot.toFixed(1) }
  }, [porciones])

  const portionesDistribuidas = useMemo(() => {
    const dist: Record<string, number> = {}
    for (const grupos of Object.values(distribucion)) {
      for (const [g, p] of Object.entries(grupos)) {
        dist[g] = +(((dist[g] || 0) + (p || 0)).toFixed(2))
      }
    }
    return dist
  }, [distribucion])

  const portionesRestantes = useMemo(() => {
    const rest: Record<string, number> = {}
    for (const [g, total] of Object.entries(porciones)) {
      if (total > 0) rest[g] = +((total - (portionesDistribuidas[g] || 0)).toFixed(2))
    }
    return rest
  }, [porciones, portionesDistribuidas])

  const aporteByTiempo = useMemo(() => {
    const result: Record<string, { kcal: number; pct_vct: number }> = {}
    let totalKcal = 0
    for (const t of TIEMPOS_COMIDA) {
      const grupos = distribucion[t.key] || {}
      let kcal = 0
      for (const [g, p] of Object.entries(grupos)) {
        const m = GRUPOS_MACROS[g]
        if (m && p > 0) kcal += m.kcal * p
      }
      result[t.key] = { kcal: Math.round(kcal), pct_vct: 0 }
      totalKcal += kcal
    }
    for (const t of TIEMPOS_COMIDA) {
      result[t.key].pct_vct = totalKcal > 0 ? Math.round((result[t.key].kcal / totalKcal) * 100) : 0
    }
    return result
  }, [distribucion])

  // ── Handlers ──────────────────────────────────────────────────────────────

  const setPorcion = (grupo: string, val: number) =>
    setPorciones(prev => ({ ...prev, [grupo]: Math.max(0, val) }))

  const setDistGrupo = (tiempo: string, grupo: string, val: number) =>
    setDistribucion(prev => ({
      ...prev,
      [tiempo]: { ...(prev[tiempo] || {}), [grupo]: Math.max(0, val) },
    }))

  const handleSave = async () => {
    if (!form.name.trim()) { setError('El nombre de la pauta es obligatorio'); return }
    if (macroError) { setError('La suma de proteínas + lípidos no puede superar 100%'); return }
    setSaving(true); setError(null)

    const { talla: _talla, ...rest } = form
    const payload = {
      ...rest,
      tmb: +calcs.tmb.toFixed(1), get_kcal: +calcs.get_kcal.toFixed(1),
      kcal_objetivo: +calcs.kcal_objetivo.toFixed(1),
      ajuste_kcal: form.ajuste_kcal || null,
      prot_g_kg: +calcs.prot_g_kg.toFixed(2), prot_g: +calcs.prot_g.toFixed(1),
      prot_kcal: +calcs.prot_kcal.toFixed(1), prot_pct: form.prot_pct,
      lip_pct: form.lip_pct, lip_g: +calcs.lip_g.toFixed(1), lip_kcal: +calcs.lip_kcal.toFixed(1),
      cho_pct, cho_g: +calcs.cho_g.toFixed(1), cho_kcal: +calcs.cho_kcal.toFixed(1),
      porciones_json: JSON.stringify(porciones),
      distribucion_json: JSON.stringify(distribucion),
      notes: form.notes.trim() || null,
    }

    try {
      const url = isEdit
        ? `${API}/pautas/${id}/${pautaId}`
        : `${API}/pautas?patient_id=${id}`
      const method = isEdit ? 'PUT' : 'POST'
      const res = await fetch(url, { method, headers: H, body: JSON.stringify(payload) })
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail ?? `Error ${res.status}`) }
      navigate(`/patients/${id}/pautas`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const handleGenerarMenu = () => {
    if (!pautaId || !token) return
    setGeneratingMenu(true); setError(null); setSseStatus('Conectando...')

    const url = `${API}/pautas/${id}/${pautaId}/generar-menu-stream?token=${encodeURIComponent(token)}`
    const es = new EventSource(url)

    es.addEventListener('status', (e: MessageEvent) => {
      setSseStatus(e.data)
    })

    es.addEventListener('result', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data)
        setMenu(data.menu ?? {})
      } catch {
        setError('Error al procesar la respuesta')
      }
      es.close(); setGeneratingMenu(false); setSseStatus('')
    })

    es.addEventListener('error', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data ?? '{}')
        setError(data.detail ?? 'Error al generar menú')
      } catch {
        setError('Error al generar menú')
      }
      es.close(); setGeneratingMenu(false); setSseStatus('')
    })

    es.onerror = () => {
      // Fallback al POST si SSE falla
      es.close()
      setSseStatus('Reintentando...')
      fetch(`${API}/pautas/${id}/${pautaId}/generar-menu`, { method: 'POST', headers: H })
        .then(r => r.ok ? r.json() : r.json().then(d => Promise.reject(new Error(d.detail ?? `Error ${r.status}`))))
        .then(data => setMenu(data.menu ?? {}))
        .catch(err => setError(err instanceof Error ? err.message : 'Error al generar menú'))
        .finally(() => { setGeneratingMenu(false); setSseStatus('') })
    }
  }

  const handleSaveMenu = async () => {
    if (!pautaId) return
    setSavingMenu(true); setError(null)
    try {
      const res = await fetch(`${API}/pautas/${id}/${pautaId}/menu`, {
        method: 'PATCH', headers: H, body: JSON.stringify({ menu }),
      })
      if (!res.ok) throw new Error(`Error ${res.status}`)
    } catch {
      setError('No se pudo guardar el menú')
    } finally {
      setSavingMenu(false)
    }
  }

  const handleDownloadPdf = async () => {
    if (!pautaId) return
    setDownloading(true)
    try {
      const res = await fetch(`${API}/pautas/${id}/${pautaId}/pdf`, { headers: H })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `pauta_${patientName.replace(/ /g, '_')}_${form.date}.pdf`
      a.click(); URL.revokeObjectURL(url)
    } catch {
      setError('No se pudo descargar el PDF')
    } finally {
      setDownloading(false)
    }
  }

  // ── Recipe helpers ──────────────────────────────────────────────────────────

  const loadRecetas = () => {
    if (recetasLoaded || recetasLoading) return
    setRecetasLoading(true)
    fetch(`${API}/recetas/?limit=200`, { headers: H })
      .then(r => r.json())
      .then(data => { setRecetas(Array.isArray(data) ? data : (data.items ?? [])); setRecetasLoaded(true) })
      .catch(() => {})
      .finally(() => setRecetasLoading(false))
  }

  const getRecetaForTiempo = (tiempo: string): RecetaRef | null =>
    (menu[tiempo] as Record<string, unknown> | undefined)?.receta as RecetaRef ?? null

  const selectReceta = (tiempo: string, receta: RecetaListItem) => {
    setMenu(prev => ({
      ...prev,
      [tiempo]: {
        opcion1: (prev[tiempo] as Record<string, unknown>)?.opcion1 as MenuOpcion ?? [],
        opcion2: (prev[tiempo] as Record<string, unknown>)?.opcion2 as MenuOpcion ?? [],
        ...(prev[tiempo] ?? {}),
        receta: { id: receta.id, nombre: receta.nombre, categoria: receta.categoria, descripcion: receta.descripcion },
      },
    }))
    setPickingRecetaFor(null)
    setRecetaSearch('')
  }

  const removeReceta = (tiempo: string) => {
    setMenu(prev => {
      const entry = { ...(prev[tiempo] ?? {}) } as Record<string, unknown>
      delete entry.receta
      return { ...prev, [tiempo]: entry as { opcion1: string | MenuOpcion; opcion2: string | MenuOpcion } }
    })
  }

  const filteredRecetas = recetas.filter(r =>
    !recetaSearch || r.nombre.toLowerCase().includes(recetaSearch.toLowerCase()) ||
    r.categoria.toLowerCase().includes(recetaSearch.toLowerCase())
  )

  const hasAnyReceta = TIEMPOS_COMIDA.some(({ key }) => getRecetaForTiempo(key))

  if (loading) return <Layout title="Pauta Nutricional"><div className="p-8 text-center text-text-muted">Cargando...</div></Layout>

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <Layout title={isEdit ? 'Editar Pauta' : isView ? 'Ver Pauta' : 'Nueva Pauta'}>
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <Link to={`/patients/${id}`} className="hover:text-primary">{patientName || `Paciente ${id}`}</Link>
        <span>/</span>
        <Link to={`/patients/${id}/pautas`} className="hover:text-primary">Pautas</Link>
        <span>/</span>
        <span className="text-primary font-medium">{isEdit ? 'Editar' : isView ? 'Ver' : 'Nueva'}</span>
      </div>

      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* ── Left column: form ─────────────────────────────────────────── */}
        <div className="xl:col-span-2 space-y-6">

          {/* 1. Datos básicos */}
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">Datos de la Pauta</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Field label="Nombre de la pauta *">
                  <input value={form.name} onChange={e => setF('name', e.target.value)}
                    disabled={isView} className={INPUT} placeholder="Ej: Pauta hipocalórica semana 1" />
                </Field>
              </div>
              <Field label="Fecha">
                <input type="date" value={form.date} onChange={e => setF('date', e.target.value)}
                  disabled={isView} className={INPUT} />
              </Field>
              <Field label="Tipo de pauta">
                <select value={form.tipo_pauta} onChange={e => setF('tipo_pauta', e.target.value)}
                  disabled={isView} className={SELECT}>
                  {TIPO_OPTIONS.map(t => <option key={t.key} value={t.key}>{t.label}</option>)}
                </select>
              </Field>
              <div className="col-span-2">
                <Field label="Notas">
                  <textarea value={form.notes} onChange={e => setF('notes', e.target.value)}
                    disabled={isView} rows={2} className={`${INPUT} resize-none`} placeholder="Indicaciones adicionales..." />
                </Field>
              </div>
            </div>
          </div>

          {/* 2. Datos antropométricos */}
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">Datos Antropométricos</h3>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Sexo">
                <select value={form.sexo} onChange={e => setF('sexo', e.target.value)}
                  disabled={isView} className={SELECT}>
                  <option value="F">Femenino</option>
                  <option value="M">Masculino</option>
                </select>
              </Field>
              <Field label="Edad (años)">
                <input type="number" value={form.edad} onChange={e => setF('edad', +e.target.value)}
                  disabled={isView} className={INPUT} min={1} max={120} />
              </Field>
              <Field label="Peso (kg)">
                <input type="number" step="0.1" value={form.peso} onChange={e => setF('peso', +e.target.value)}
                  disabled={isView} className={INPUT} min={1} />
              </Field>
              <Field label="Talla (cm)">
                <input type="number" value={form.talla} onChange={e => setF('talla', +e.target.value)}
                  disabled={isView} className={INPUT} min={50} max={250} />
              </Field>
            </div>
          </div>

          {/* 3. Factor de actividad */}
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">Factor de Actividad</h3>
            <div className="grid grid-cols-2 gap-3">
              {FA_OPTIONS.map(fa => (
                <label key={fa.key}
                  className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                    form.fa_key === fa.key ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/40'
                  } ${isView ? 'pointer-events-none opacity-80' : ''}`}>
                  <input type="radio" name="fa" value={fa.key} checked={form.fa_key === fa.key}
                    onChange={() => setF('fa_key', fa.key)} className="mt-0.5 accent-primary" disabled={isView} />
                  <div>
                    <p className="text-sm font-medium text-gray-800">{fa.label} <span className="text-xs text-text-muted">(×{fa.factor})</span></p>
                    <p className="text-xs text-text-muted">{fa.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 4. Calorías objetivo — GET card (Stitch style) */}
          <div className="bg-primary text-white p-8 rounded-xl shadow-lg relative overflow-hidden">
            <div className="relative z-10 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-white/30 text-xs font-black uppercase tracking-[0.2em]">Cálculo Energético</h3>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-white/80">Gasto Energético Total (GET)</p>
                <p className="text-5xl font-bold tracking-tight">
                  {calcs.get_kcal.toFixed(0)} <span className="text-xl font-normal opacity-80">kcal/día</span>
                </p>
              </div>
              <div className="pt-4 border-t border-white/10 flex gap-6 text-sm font-medium text-white/70">
                <p>TMB: <span className="text-white">{calcs.tmb.toFixed(0)} kcal</span></p>
                <p>FA: <span className="text-white">×{FA_OPTIONS.find(f => f.key === form.fa_key)?.factor ?? '—'}</span></p>
                {form.ajuste_kcal !== 0 && (
                  <p>Ajuste: <span className="text-white">{form.ajuste_kcal > 0 ? '+' : ''}{form.ajuste_kcal} kcal</span></p>
                )}
              </div>
              {form.ajuste_kcal !== 0 && (
                <div className="pt-2 text-sm font-medium text-white/70">
                  Kcal objetivo: <span className="text-white font-bold">{calcs.kcal_objetivo.toFixed(0)} kcal/día</span>
                </div>
              )}
            </div>
            {/* Abstract background */}
            <div className="absolute -right-12 -bottom-12 w-64 h-64 bg-white/10 rounded-full blur-3xl pointer-events-none"></div>
          </div>

          {/* Ajuste calórico */}
          <div className="bg-white rounded-lg shadow p-4">
            <Field label="Ajuste calórico (kcal) — negativo para déficit, positivo para superávit">
              <input type="number" value={form.ajuste_kcal} onChange={e => setF('ajuste_kcal', +e.target.value)}
                disabled={isView} className={INPUT} step="50" placeholder="0" />
            </Field>
            <p className="text-xs text-text-muted mt-2">Fórmula: Mifflin-St Jeor</p>
          </div>

          {/* 5. Distribución de macronutrientes */}
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">Distribución de Macronutrientes</h3>
            {macroError && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-3 py-2 rounded text-sm">
                La suma de proteínas + lípidos no puede superar 100%
              </div>
            )}
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <label className="text-xs text-text-muted">Proteínas</label>
                  <span className="text-xs font-medium text-primary">{form.prot_pct}%</span>
                </div>
                <input type="range" min={5} max={50} value={form.prot_pct}
                  onChange={e => setF('prot_pct', +e.target.value)}
                  disabled={isView} className="w-full accent-primary" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <label className="text-xs text-text-muted">Lípidos</label>
                  <span className="text-xs font-medium text-terracotta">{form.lip_pct}%</span>
                </div>
                <input type="range" min={10} max={50} value={form.lip_pct}
                  onChange={e => setF('lip_pct', +e.target.value)}
                  disabled={isView} className="w-full accent-orange-500" />
              </div>
              <div className="bg-bg-light rounded p-3 flex justify-between items-center">
                <span className="text-xs text-text-muted">Carbohidratos (calculado)</span>
                <span className={`text-sm font-bold ${macroError ? 'text-red-500' : 'text-blue-500'}`}>{cho_pct}%</span>
              </div>
            </div>

            {/* Macro cards — Stitch style */}
            <div className="grid grid-cols-3 gap-4 pt-2">
              {/* Proteínas */}
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Proteínas</p>
                  <span className="px-2 py-0.5 rounded-md bg-primary/10 text-primary text-[10px] font-black">{form.prot_pct}%</span>
                </div>
                <div className="space-y-0.5">
                  <p className="text-2xl font-bold">{calcs.prot_g.toFixed(1)}<span className="text-xs font-normal text-text-muted ml-1">g</span></p>
                  <p className="text-xs text-text-muted">{calcs.prot_kcal.toFixed(0)} kcal</p>
                  <p className="text-xs text-text-muted">{calcs.prot_g_kg.toFixed(2)} g/kg</p>
                </div>
                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="bg-primary h-full rounded-full" style={{ width: `${Math.min(100, form.prot_pct)}%` }} />
                </div>
              </div>
              {/* Lípidos */}
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Lípidos</p>
                  <span className="px-2 py-0.5 rounded-md bg-terracotta/10 text-terracotta text-[10px] font-black">{form.lip_pct}%</span>
                </div>
                <div className="space-y-0.5">
                  <p className="text-2xl font-bold">{calcs.lip_g.toFixed(1)}<span className="text-xs font-normal text-text-muted ml-1">g</span></p>
                  <p className="text-xs text-text-muted">{calcs.lip_kcal.toFixed(0)} kcal</p>
                </div>
                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="bg-terracotta h-full rounded-full" style={{ width: `${Math.min(100, form.lip_pct)}%` }} />
                </div>
              </div>
              {/* Carbohidratos */}
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Carbohidratos</p>
                  <span className="px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-500 text-[10px] font-black">{cho_pct}%</span>
                </div>
                <div className="space-y-0.5">
                  <p className="text-2xl font-bold">{calcs.cho_g.toFixed(1)}<span className="text-xs font-normal text-text-muted ml-1">g</span></p>
                  <p className="text-xs text-text-muted">{calcs.cho_kcal.toFixed(0)} kcal</p>
                </div>
                <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="bg-blue-500 h-full rounded-full" style={{ width: `${Math.min(100, cho_pct)}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* 6. Porciones por grupo de alimentos */}
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h3 className="text-sm font-bold text-primary uppercase tracking-wide">Porciones por Grupo de Alimentos</h3>
              {aporteTotal.kcal > 0 && (
                <span className={`text-xs px-2 py-1 rounded font-medium ${adecuacionColor(calcs.kcal_objetivo > 0 ? (aporteTotal.kcal / calcs.kcal_objetivo) * 100 : 0)}`}>
                  {aporteTotal.kcal} / {calcs.kcal_objetivo.toFixed(0)} kcal
                </span>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-bg-light text-xs text-text-muted">
                    <th className="text-left px-3 py-2">Grupo</th>
                    <th className="text-right px-3 py-2">kcal/p</th>
                    <th className="text-right px-3 py-2">prot/p</th>
                    <th className="text-center px-3 py-2 w-28">Porciones/día</th>
                    <th className="text-right px-3 py-2">Aporte kcal</th>
                    <th className="text-right px-3 py-2">Aporte prot</th>
                  </tr>
                </thead>
                <tbody>
                  {activeGroups.map((g, i) => {
                    const m = GRUPOS_MACROS[g]
                    const p = porciones[g] || 0
                    const aporte_kcal = m ? Math.round(m.kcal * p) : 0
                    const aporte_prot = m ? +(m.prot * p).toFixed(1) : 0
                    return (
                      <tr key={g} className={`border-b border-border ${i % 2 === 0 ? '' : 'bg-bg-light/40'}`}>
                        <td className="px-3 py-2 font-medium text-gray-700">{NOMBRES_GRUPOS[g] ?? g}</td>
                        <td className="px-3 py-2 text-right text-text-muted">{m?.kcal ?? '—'}</td>
                        <td className="px-3 py-2 text-right text-text-muted">{m?.prot ?? '—'}g</td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-1 justify-center">
                            <button type="button" onClick={() => setPorcion(g, +(p - 0.5).toFixed(1))}
                              disabled={isView || p <= 0}
                              className="w-6 h-6 flex items-center justify-center border border-border rounded text-text-muted hover:bg-bg-light disabled:opacity-30">−</button>
                            <input
                              type="number" step="0.5" min="0" value={p || ''}
                              onChange={e => setPorcion(g, +e.target.value)}
                              disabled={isView}
                              placeholder="0"
                              className="w-14 text-center border border-border rounded px-1 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary disabled:bg-bg-light" />
                            <button type="button" onClick={() => setPorcion(g, +(p + 0.5).toFixed(1))}
                              disabled={isView}
                              className="w-6 h-6 flex items-center justify-center border border-border rounded text-text-muted hover:bg-bg-light disabled:opacity-30">+</button>
                          </div>
                        </td>
                        <td className="px-3 py-2 text-right font-medium text-gray-700">{p > 0 ? `${aporte_kcal} kcal` : '—'}</td>
                        <td className="px-3 py-2 text-right text-gray-700">{p > 0 ? `${aporte_prot}g` : '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
                {aporteTotal.kcal > 0 && (
                  <tfoot>
                    <tr className="bg-primary/5 font-bold text-gray-800">
                      <td className="px-3 py-2" colSpan={4}>TOTAL</td>
                      <td className="px-3 py-2 text-right">
                        <div>{aporteTotal.kcal} kcal</div>
                        {calcs.kcal_objetivo > 0 && (
                          <div className={`text-xs font-normal px-1 rounded inline-block ${adecuacionColor((aporteTotal.kcal / calcs.kcal_objetivo) * 100)}`}>
                            {((aporteTotal.kcal / calcs.kcal_objetivo) * 100).toFixed(0)}%
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <div>{aporteTotal.prot}g</div>
                        {calcs.prot_g > 0 && (
                          <div className={`text-xs font-normal px-1 rounded inline-block ${adecuacionColor((aporteTotal.prot / calcs.prot_g) * 100)}`}>
                            {((aporteTotal.prot / calcs.prot_g) * 100).toFixed(0)}%
                          </div>
                        )}
                      </td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>

            {aporteTotal.kcal > 0 && (
              <div className="grid grid-cols-4 gap-3 pt-2 border-t border-border">
                {[
                  { label: 'Energía',      got: aporteTotal.kcal, target: calcs.kcal_objetivo, unit: 'kcal' },
                  { label: 'Proteínas',    got: aporteTotal.prot,  target: calcs.prot_g,         unit: 'g' },
                  { label: 'Lípidos',      got: aporteTotal.lip,   target: calcs.lip_g,          unit: 'g' },
                  { label: 'Carbohidratos',got: aporteTotal.cho,   target: calcs.cho_g,          unit: 'g' },
                ].map(({ label, got, target, unit }) => {
                  const pct = target > 0 ? (got / target) * 100 : 0
                  return (
                    <div key={label} className="text-center">
                      <p className="text-xs text-text-muted mb-1">{label}</p>
                      <p className="text-sm font-bold text-gray-800">{got} / {target.toFixed(0)}{unit}</p>
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${adecuacionColor(pct)}`}>{pct.toFixed(0)}%</span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* 7. Distribución por tiempo de comida */}
          {Object.values(porciones).some(p => p > 0) && (
            <div className="bg-white rounded-lg shadow p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-2">
                <h3 className="text-sm font-bold text-primary uppercase tracking-wide">Distribución por Tiempo de Comida</h3>
                <p className="text-xs text-text-muted">Asigna las porciones del día a cada tiempo de comida</p>
              </div>

              {/* Remaining portions summary */}
              {!isView && Object.values(portionesRestantes).some(r => r !== 0) && (
                <div className="bg-bg-light rounded-lg p-3">
                  <p className="text-xs font-medium text-text-muted mb-2">Porciones restantes por distribuir:</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(portionesRestantes).map(([g, r]) => (
                      <span key={g} className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        r === 0 ? 'bg-green-100 text-green-700' :
                        r > 0   ? 'bg-yellow-100 text-yellow-700' :
                                  'bg-red-100 text-red-600'
                      }`}>
                        {NOMBRES_GRUPOS[g] ?? g}: {r > 0 ? `+${r}` : r}p
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                {TIEMPOS_COMIDA.map(({ key, label }) => {
                  const gruposActivos = activeGroups.filter(g => (porciones[g] || 0) > 0)
                  const { kcal, pct_vct } = aporteByTiempo[key] || { kcal: 0, pct_vct: 0 }
                  return (
                    <div key={key} className="border border-border rounded-lg overflow-hidden">
                      <div className="bg-primary/5 px-3 py-2 flex items-center justify-between">
                        <span className="text-sm font-bold text-primary">{label}</span>
                        <div className="flex items-center gap-2">
                          {kcal > 0 && <span className="text-xs text-text-muted">{kcal} kcal</span>}
                          {pct_vct > 0 && <span className="text-xs font-medium bg-primary/10 text-primary px-1.5 py-0.5 rounded">{pct_vct}%</span>}
                        </div>
                      </div>
                      <div className="p-3 space-y-2">
                        {gruposActivos.length === 0 ? (
                          <p className="text-xs text-text-muted text-center py-2">Asigna porciones en la sección anterior</p>
                        ) : (
                          gruposActivos.map(g => {
                            const val = distribucion[key]?.[g] || 0
                            const restante = portionesRestantes[g] ?? 0
                            return (
                              <div key={g} className="flex items-center gap-2">
                                <span className="text-xs text-gray-600 flex-1 truncate">{NOMBRES_GRUPOS[g] ?? g}</span>
                                <div className="flex items-center gap-1">
                                  <button type="button" onClick={() => setDistGrupo(key, g, +(val - 0.5).toFixed(1))}
                                    disabled={isView || val <= 0}
                                    className="w-5 h-5 flex items-center justify-center border border-border rounded text-text-muted hover:bg-bg-light text-xs disabled:opacity-30">−</button>
                                  <input type="number" step="0.5" min="0" value={val || ''}
                                    onChange={e => setDistGrupo(key, g, +e.target.value)}
                                    disabled={isView}
                                    placeholder="0"
                                    className="w-12 text-center border border-border rounded px-1 py-0.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary disabled:bg-bg-light" />
                                  <button type="button" onClick={() => setDistGrupo(key, g, +(val + 0.5).toFixed(1))}
                                    disabled={isView}
                                    className="w-5 h-5 flex items-center justify-center border border-border rounded text-text-muted hover:bg-bg-light text-xs disabled:opacity-30">+</button>
                                </div>
                                {!isView && (
                                  <span className={`text-xs w-10 text-right font-medium ${
                                    restante === 0 ? 'text-green-600' : restante > 0 ? 'text-yellow-600' : 'text-red-500'
                                  }`}>{restante > 0 ? `+${restante}` : restante}p</span>
                                )}
                              </div>
                            )
                          })
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* 8. Menú generado con IA */}
          {isView && (Object.keys(menu).length > 0 || generatingMenu) && (
            <div className="bg-white rounded-lg shadow p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-2">
                <h3 className="text-sm font-bold text-primary uppercase tracking-wide">Ideas de Menú — IA</h3>
                <div className="flex items-center gap-3">
                  <button onClick={handleSaveMenu} disabled={savingMenu || generatingMenu}
                    className="text-xs text-white bg-primary hover:bg-primary-dark px-3 py-1 rounded disabled:opacity-50">
                    {savingMenu ? 'Guardando...' : 'Guardar cambios'}
                  </button>
                  {aiConfigured === false ? (
                    <Link to="/config" className="text-xs text-text-muted hover:underline">IA no configurada</Link>
                  ) : (
                    <button onClick={handleGenerarMenu} disabled={generatingMenu || aiConfigured === null}
                      className="text-xs text-primary hover:underline disabled:opacity-50">
                      {generatingMenu ? 'Generando...' : 'Regenerar'}
                    </button>
                  )}
                </div>
              </div>
              {generatingMenu ? (
                <div className="flex items-center gap-3 py-6 justify-center text-text-muted text-sm">
                  <svg className="animate-spin h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  {sseStatus || 'Consultando IA...'}
                </div>
              ) : isStructuredMenu(menu) ? (
                <div className="grid grid-cols-1 gap-4">
                  <p className="text-xs text-text-muted">Edita las cantidades (g/ml) directamente y guarda los cambios.</p>
                  {TIEMPOS_COMIDA.filter(({ key }) => menu[key]).map(({ key, label }) => {
                    const td = menu[key] as { opcion1: MenuOpcion; opcion2: MenuOpcion }
                    return (
                      <div key={key} className="border border-border rounded-lg overflow-hidden">
                        <div className="bg-primary/5 px-3 py-2">
                          <span className="text-sm font-bold text-primary">{label}</span>
                        </div>
                        <div className="p-3 grid grid-cols-2 gap-3">
                          <StructuredOpcion
                            items={td.opcion1}
                            colorClass="bg-primary/5 border border-primary/10"
                            label="Opción 1"
                            labelColor="text-primary"
                            onChange={items => setMenu(prev => ({
                              ...prev,
                              [key]: { ...(prev[key] as { opcion1: MenuOpcion; opcion2: MenuOpcion }), opcion1: items },
                            }))}
                          />
                          <StructuredOpcion
                            items={td.opcion2}
                            colorClass="bg-terracotta/5 border border-terracotta/10"
                            label="Opción 2"
                            labelColor="text-terracotta"
                            onChange={items => setMenu(prev => ({
                              ...prev,
                              [key]: { ...(prev[key] as { opcion1: MenuOpcion; opcion2: MenuOpcion }), opcion2: items },
                            }))}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  <p className="text-xs text-text-muted">Puedes editar las opciones directamente y luego guardar los cambios.</p>
                  {TIEMPOS_COMIDA.filter(({ key }) => menu[key]).map(({ key, label }) => (
                    <div key={key} className="border border-border rounded-lg overflow-hidden">
                      <div className="bg-primary/5 px-3 py-2">
                        <span className="text-sm font-bold text-primary">{label}</span>
                      </div>
                      <div className="p-3 grid grid-cols-2 gap-3">
                        {(['opcion1', 'opcion2'] as const).map((opt, i) => (
                          <div key={opt} className={`rounded-lg p-2 ${i === 0 ? 'bg-primary/5 border border-primary/10' : 'bg-terracotta/5 border border-terracotta/10'}`}>
                            <span className={`text-xs font-bold block mb-1 ${i === 0 ? 'text-primary' : 'text-terracotta'}`}>Opción {i + 1}</span>
                            <textarea
                              value={typeof menu[key]?.[opt] === 'string' ? menu[key][opt] as string : ''}
                              onChange={e => setMenu(prev => ({
                                ...prev,
                                [key]: { ...prev[key], [opt]: e.target.value },
                              }))}
                              rows={3}
                              className="w-full text-sm text-gray-700 bg-transparent border border-transparent focus:border-border focus:bg-white rounded p-1 resize-none focus:outline-none focus:ring-1 focus:ring-primary leading-relaxed"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── 9. Recetas del menú ─────────────────────────────────────── */}
          {isView && (
            <div className="bg-white rounded-lg shadow p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-2">
                <h3 className="text-sm font-bold text-primary uppercase tracking-wide">Recetas del Menú</h3>
                <p className="text-xs text-text-muted">Asigna una receta a cada tiempo de comida</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {TIEMPOS_COMIDA.map(({ key, label }) => {
                  const receta = getRecetaForTiempo(key)
                  return (
                    <div key={key} className="border border-border rounded-lg overflow-hidden">
                      <div className="bg-primary/5 px-3 py-2">
                        <span className="text-sm font-bold text-primary">{label}</span>
                      </div>
                      <div className="p-3 space-y-2">
                        {receta ? (
                          <div className="flex items-start justify-between bg-sage/10 border border-sage/20 rounded-lg p-2 gap-2">
                            <div className="min-w-0">
                              <p className="text-xs font-bold text-sage truncate">📋 {receta.nombre}</p>
                              {receta.categoria && <p className="text-xs text-text-muted">{receta.categoria}</p>}
                              {receta.descripcion && <p className="text-xs text-text-muted line-clamp-1">{receta.descripcion}</p>}
                            </div>
                            <button onClick={() => removeReceta(key)}
                              className="text-xs text-red-500 hover:underline flex-shrink-0">
                              Quitar
                            </button>
                          </div>
                        ) : (
                          <p className="text-xs text-text-muted text-center py-1">Sin receta asignada</p>
                        )}

                        <button
                          onClick={() => { loadRecetas(); setPickingRecetaFor(pickingRecetaFor === key ? null : key); setRecetaSearch('') }}
                          className="w-full flex items-center justify-center gap-1 text-xs text-primary border border-primary/30 hover:bg-primary/5 rounded-lg py-1.5 transition-colors"
                        >
                          <span className="material-symbols-outlined text-sm">menu_book</span>
                          {receta ? 'Cambiar receta' : 'Agregar receta'}
                        </button>

                        {pickingRecetaFor === key && (
                          <div className="border border-border rounded-lg shadow-md bg-white">
                            <input
                              autoFocus
                              value={recetaSearch}
                              onChange={e => setRecetaSearch(e.target.value)}
                              placeholder="Buscar por nombre o categoría..."
                              className="w-full px-3 py-2 text-xs border-b border-border rounded-t-lg focus:outline-none"
                            />
                            <div className="max-h-44 overflow-y-auto">
                              {recetasLoading ? (
                                <p className="text-xs text-text-muted text-center py-3">Cargando...</p>
                              ) : filteredRecetas.length === 0 ? (
                                <p className="text-xs text-text-muted text-center py-3">
                                  {recetaSearch ? 'Sin resultados' : 'No hay recetas guardadas'}
                                </p>
                              ) : (
                                filteredRecetas.map(r => (
                                  <button key={r.id} onClick={() => selectReceta(key, r)}
                                    className="w-full text-left px-3 py-2 text-xs hover:bg-bg-light flex items-center justify-between border-b border-border last:border-0">
                                    <span className="font-medium text-gray-800">{r.nombre}</span>
                                    <span className="text-text-muted ml-2 flex-shrink-0">{r.categoria}</span>
                                  </button>
                                ))
                              )}
                            </div>
                            <button onClick={() => setPickingRecetaFor(null)}
                              className="w-full text-xs text-text-muted py-1.5 hover:bg-bg-light rounded-b-lg border-t border-border">
                              Cancelar
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              {hasAnyReceta && (
                <button onClick={handleSaveMenu} disabled={savingMenu}
                  className="w-full text-sm bg-primary hover:bg-primary-dark text-white py-2 rounded-lg font-medium disabled:opacity-50">
                  {savingMenu ? 'Guardando...' : 'Guardar asignación de recetas'}
                </button>
              )}
            </div>
          )}

        </div>

        {/* ── Right column: summary + actions ──────────────────────────── */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-6 space-y-3 sticky top-24">
            <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">Resumen</h3>
            <Row label="TMB" value={calcs.tmb.toFixed(0)} unit="kcal" />
            <Row label="GET" value={calcs.get_kcal.toFixed(0)} unit="kcal" />
            {form.ajuste_kcal !== 0 && (
              <Row label="Ajuste" value={(form.ajuste_kcal > 0 ? '+' : '') + form.ajuste_kcal} unit="kcal" />
            )}
            <Row label="Kcal objetivo" value={calcs.kcal_objetivo.toFixed(0)} unit="kcal" strong />

            <div className="pt-3 border-t border-border space-y-2">
              <p className="text-xs text-text-muted font-medium">Distribución macros</p>
              <PctBar label="Prot." pct={form.prot_pct} color="bg-blue-400" />
              <PctBar label="Lip." pct={form.lip_pct} color="bg-yellow-400" />
              <PctBar label="CHO" pct={cho_pct} color="bg-orange-400" />
            </div>

            <div className="pt-3 border-t border-border space-y-1">
              <p className="text-xs text-text-muted font-medium">Gramos / día</p>
              <div className="flex justify-between text-xs">
                <span className="text-text-muted">Proteínas</span>
                <span className="font-medium">{calcs.prot_g.toFixed(1)}g · {calcs.prot_g_kg.toFixed(2)} g/kg</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-muted">Lípidos</span>
                <span className="font-medium">{calcs.lip_g.toFixed(1)}g</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-muted">CHO</span>
                <span className="font-medium">{calcs.cho_g.toFixed(1)}g</span>
              </div>
            </div>

            {aporteTotal.kcal > 0 && (
              <div className="pt-3 border-t border-border space-y-1">
                <p className="text-xs text-text-muted font-medium">Aporte por grupos</p>
                <div className="flex justify-between text-xs">
                  <span className="text-text-muted">Energía asignada</span>
                  <span className={`font-medium px-1 rounded ${adecuacionColor(calcs.kcal_objetivo > 0 ? (aporteTotal.kcal / calcs.kcal_objetivo) * 100 : 0)}`}>
                    {aporteTotal.kcal} kcal
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-text-muted">Proteína asignada</span>
                  <span className="font-medium">{aporteTotal.prot}g</span>
                </div>
              </div>
            )}

            {Object.values(aporteByTiempo).some(t => t.kcal > 0) && (
              <div className="pt-3 border-t border-border space-y-1">
                <p className="text-xs text-text-muted font-medium">Kcal por tiempo</p>
                {TIEMPOS_COMIDA.map(({ key, label }) => {
                  const { kcal, pct_vct } = aporteByTiempo[key] || { kcal: 0, pct_vct: 0 }
                  if (!kcal) return null
                  return (
                    <div key={key} className="flex justify-between text-xs">
                      <span className="text-text-muted">{label}</span>
                      <span className="font-medium text-gray-700">{kcal} kcal <span className="text-text-muted">({pct_vct}%)</span></span>
                    </div>
                  )
                })}
              </div>
            )}

            {(isEdit || !pautaId) && (
              <div className="pt-3 border-t border-border flex flex-col gap-2">
                <button onClick={handleSave} disabled={saving || macroError}
                  className="bg-primary hover:bg-primary-dark text-white py-3 rounded-lg font-medium disabled:opacity-50">
                  {saving ? 'Guardando...' : isEdit ? 'Guardar cambios' : 'Crear pauta'}
                </button>
                <Link to={isEdit ? `/patients/${id}/pautas/${pautaId}` : `/patients/${id}/pautas`}
                  className="border border-border text-text-muted hover:bg-bg-light py-3 rounded-lg font-medium text-center text-sm">
                  Cancelar
                </Link>
              </div>
            )}

            {isView && (
              <div className="pt-3 border-t border-border flex flex-col gap-2">
                <Link to={`/patients/${id}/pautas/${pautaId}/edit`}
                  className="border border-primary text-primary hover:bg-primary/5 py-3 rounded-lg font-medium text-center text-sm">
                  Editar pauta
                </Link>
                <button onClick={handleGenerarMenu}
                  disabled={generatingMenu || aiConfigured === null || aiConfigured === false}
                  title={aiConfigured === false ? 'IA no configurada. Configura GROQ_API_KEY en el servidor.' : undefined}
                  className="bg-primary hover:bg-primary-dark text-white py-3 rounded-lg font-medium disabled:opacity-50 flex items-center justify-center gap-2">
                  {generatingMenu ? (
                    <>
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                      </svg>
                      {sseStatus || 'Generando menú...'}
                    </>
                  ) : aiConfigured === false ? (
                    <>IA no configurada — ver <Link to="/config" className="underline ml-1">Config</Link></>
                  ) : (
                    <>✨ {Object.keys(menu).length > 0 ? 'Regenerar Menú IA' : 'Generar Menú con IA'}</>
                  )}
                </button>
                <button onClick={handleDownloadPdf} disabled={downloading}
                  className="bg-terracotta hover:opacity-90 text-white py-3 rounded-lg font-medium disabled:opacity-50 flex items-center justify-center gap-2">
                  {downloading ? 'Generando...' : '⬇ Descargar PDF'}
                </button>
                <Link to={`/patients/${id}/pautas`}
                  className="block border border-border text-text-muted hover:bg-bg-light py-3 rounded-lg font-medium text-center text-sm">
                  ← Volver
                </Link>
              </div>
            )}
          </div>
        </div>

      </div>
    </Layout>
  )
}
