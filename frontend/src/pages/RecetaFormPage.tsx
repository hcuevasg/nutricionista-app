import { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Layout from '../components/Layout'

// ── Grupos alimentarios (constantes nutricionales) ────────────────────────────
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

const NOMBRES_GRUPOS: Record<string, string> = {
  cereales: 'Cereales', verduras_cg: 'Verduras CG', verduras_lc: 'Verduras LC',
  frutas: 'Frutas', lacteos_ag: 'Lácteos AG', lacteos_mg: 'Lácteos MG',
  lacteos_bg: 'Lácteos BG', legumbres: 'Legumbres', carnes_ag: 'Carnes AG',
  carnes_bg: 'Carnes BG', otros_proteicos: 'Otros Proteicos', aceite_grasas: 'Aceite y Grasas',
  alim_ricos_lipidos: 'Ricos en Lípidos', leches_vegetales: 'Leches Vegetales',
  lacteos_soya: 'Lácteos de Soya', semillas_chia: 'Semillas Chía', azucares: 'Azúcares',
}

const CATEGORIAS = ['General', 'Desayuno', 'Almuerzo', 'Cena', 'Colación', 'Postre', 'Snack', 'Bebida', 'Vegetariano', 'Vegano']

// ── Types ─────────────────────────────────────────────────────────────────────
interface Ingrediente {
  id?: number
  nombre_alimento: string
  gramos: string
  medida_casera: string
  calorias: string
  proteinas_g: string
  carbohidratos_g: string
  grasas_g: string
  fibra_g: string
}

type Equivalencias = Record<string, string>

function emptyIng(): Ingrediente {
  return { nombre_alimento: '', gramos: '100', medida_casera: '', calorias: '', proteinas_g: '', carbohidratos_g: '', grasas_g: '', fibra_g: '' }
}

function pf(v: string) { const n = parseFloat(v); return isNaN(n) ? 0 : n }

const INPUT = 'w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary'
const LABEL = 'block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1'

// ── Component ─────────────────────────────────────────────────────────────────
export default function RecetaFormPage() {
  const { recetaId } = useParams<{ recetaId: string }>()
  const isEditing = !!recetaId
  const { token } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [tab, setTab] = useState<'info' | 'nutricion' | 'equiv'>('info')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(isEditing)

  // Info fields
  const [nombre, setNombre] = useState('')
  const [categoria, setCategoria] = useState('General')
  const [porciones, setPorciones] = useState('1')
  const [descripcion, setDescripcion] = useState('')
  const [notas, setNotas] = useState('')

  // Ingredientes
  const [ingredientes, setIngredientes] = useState<Ingrediente[]>([])
  const [newIng, setNewIng] = useState<Ingrediente>(emptyIng())

  // Equivalencias
  const [equiv, setEquiv] = useState<Equivalencias>(
    Object.fromEntries(Object.keys(GRUPOS_MACROS).map(k => [k, '0']))
  )

  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  // Load if editing
  useEffect(() => {
    if (!isEditing || !token) return
    fetch(`${API}/recetas/${recetaId}`, { headers: H })
      .then(r => r.json())
      .then(data => {
        setNombre(data.nombre ?? '')
        setCategoria(data.categoria ?? 'General')
        setPorciones(String(data.porciones_rinde ?? 1))
        setDescripcion(data.descripcion ?? '')
        setNotas(data.notas ?? '')
        setIngredientes((data.ingredientes ?? []).map((i: Record<string, unknown>) => ({
          id: i.id as number,
          nombre_alimento: String(i.nombre_alimento ?? ''),
          gramos: String(i.gramos ?? 100),
          medida_casera: String(i.medida_casera ?? ''),
          calorias: String(i.calorias ?? ''),
          proteinas_g: String(i.proteinas_g ?? ''),
          carbohidratos_g: String(i.carbohidratos_g ?? ''),
          grasas_g: String(i.grasas_g ?? ''),
          fibra_g: String(i.fibra_g ?? ''),
        })))
        const eqMap: Equivalencias = Object.fromEntries(Object.keys(GRUPOS_MACROS).map(k => [k, '0']))
        for (const eq of (data.equivalencias ?? [])) {
          if (eq.grupo in eqMap) eqMap[eq.grupo] = String(eq.porciones)
        }
        setEquiv(eqMap)
      })
      .catch(() => toast.error('Error al cargar receta'))
      .finally(() => setLoading(false))
  }, [recetaId, token])

  // Totales por porción
  const totales = useMemo(() => {
    const t = { kcal: 0, prot: 0, cho: 0, fat: 0, fib: 0 }
    for (const i of ingredientes) {
      t.kcal += pf(i.calorias)
      t.prot += pf(i.proteinas_g)
      t.cho  += pf(i.carbohidratos_g)
      t.fat  += pf(i.grasas_g)
      t.fib  += pf(i.fibra_g)
    }
    return t
  }, [ingredientes])

  const n = Math.max(1, pf(porciones))
  const porPorcion = { kcal: totales.kcal / n, prot: totales.prot / n, cho: totales.cho / n, fat: totales.fat / n, fib: totales.fib / n }

  // Totales desde equivalencias
  const equivTotales = useMemo(() => {
    let kcal = 0, prot = 0, cho = 0, fat = 0
    for (const [grupo, val] of Object.entries(equiv)) {
      const p = pf(val)
      const m = GRUPOS_MACROS[grupo]
      kcal += p * m.kcal; prot += p * m.prot; cho += p * m.cho; fat += p * m.lip
    }
    return { kcal, prot, cho, fat }
  }, [equiv])

  // Add ingrediente
  const addIngrediente = () => {
    if (!newIng.nombre_alimento.trim()) return
    setIngredientes(prev => [...prev, { ...newIng }])
    setNewIng(emptyIng())
  }

  const removeIngrediente = (idx: number) =>
    setIngredientes(prev => prev.filter((_, i) => i !== idx))

  // Save
  const handleSave = async () => {
    if (!nombre.trim()) { toast.error('El nombre es obligatorio'); return }
    setSaving(true)
    const body = {
      nombre, descripcion: descripcion || null, categoria,
      porciones_rinde: Math.max(1, pf(porciones)),
      notas: notas || null,
      ingredientes: ingredientes.map(i => ({
        nombre_alimento: i.nombre_alimento,
        gramos: pf(i.gramos),
        medida_casera: i.medida_casera || null,
        calorias: pf(i.calorias),
        proteinas_g: pf(i.proteinas_g),
        carbohidratos_g: pf(i.carbohidratos_g),
        grasas_g: pf(i.grasas_g),
        fibra_g: pf(i.fibra_g),
      })),
      equivalencias: Object.entries(equiv)
        .filter(([, v]) => pf(v) > 0)
        .map(([grupo, v]) => ({ grupo, porciones: pf(v) })),
    }
    try {
      const url = isEditing ? `${API}/recetas/${recetaId}` : `${API}/recetas/`
      const method = isEditing ? 'PUT' : 'POST'
      const res = await fetch(url, { method, headers: H, body: JSON.stringify(body) })
      if (!res.ok) throw new Error()
      toast.success(isEditing ? 'Receta actualizada' : 'Receta creada')
      navigate('/recetas')
    } catch {
      toast.error('Error al guardar receta')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Layout title="Receta"><div className="text-center py-16 text-gray-400">Cargando…</div></Layout>

  const tabs = [
    { key: 'info',    label: 'Información e Ingredientes' },
    { key: 'nutricion', label: 'Aporte Nutricional' },
    { key: 'equiv',   label: 'Equivalencias' },
  ] as const

  return (
    <Layout title={isEditing ? 'Editar Receta' : 'Nueva Receta'}>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/recetas" className="hover:text-primary">Recetas</Link>
        <span>/</span>
        <span className="text-gray-800 font-medium">{isEditing ? nombre || 'Editar' : 'Nueva'}</span>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl w-fit">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              tab === t.key ? 'bg-white text-primary shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Información e Ingredientes ─────────────────────────────── */}
      {tab === 'info' && (
        <div className="space-y-6">
          {/* Info básica */}
          <div className="bg-white border border-border rounded-xl p-6">
            <h3 className="font-semibold text-gray-700 mb-4">Información básica</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className={LABEL}>Nombre de la receta *</label>
                <input value={nombre} onChange={e => setNombre(e.target.value)}
                  placeholder="Ej: Queque de zanahoria" className={INPUT} />
              </div>
              <div>
                <label className={LABEL}>Categoría</label>
                <select value={categoria} onChange={e => setCategoria(e.target.value)} className={INPUT}>
                  {CATEGORIAS.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className={LABEL}>Porciones que rinde</label>
                <input type="number" min="1" value={porciones} onChange={e => setPorciones(e.target.value)} className={INPUT} />
              </div>
              <div className="sm:col-span-2">
                <label className={LABEL}>Descripción corta</label>
                <input value={descripcion} onChange={e => setDescripcion(e.target.value)}
                  placeholder="Ej: Postre húmedo y esponjoso, sin azúcar refinada" className={INPUT} />
              </div>
              <div className="sm:col-span-2">
                <label className={LABEL}>Preparación / Notas</label>
                <textarea value={notas} onChange={e => setNotas(e.target.value)} rows={4}
                  placeholder="Pasos de preparación, temperatura, tiempo de cocción…" className={INPUT} />
              </div>
            </div>
          </div>

          {/* Ingredientes */}
          <div className="bg-white border border-border rounded-xl p-6">
            <h3 className="font-semibold text-gray-700 mb-4">Ingredientes</h3>

            {/* Formulario agregar */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">Agregar ingrediente</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
                <div className="col-span-2">
                  <label className={LABEL}>Alimento</label>
                  <input value={newIng.nombre_alimento}
                    onChange={e => setNewIng(p => ({ ...p, nombre_alimento: e.target.value }))}
                    placeholder="Ej: Harina integral" className={INPUT} />
                </div>
                <div>
                  <label className={LABEL}>Gramos</label>
                  <input type="number" value={newIng.gramos}
                    onChange={e => setNewIng(p => ({ ...p, gramos: e.target.value }))} className={INPUT} />
                </div>
                <div>
                  <label className={LABEL}>Medida casera</label>
                  <input value={newIng.medida_casera}
                    onChange={e => setNewIng(p => ({ ...p, medida_casera: e.target.value }))}
                    placeholder="Ej: 2 tazas" className={INPUT} />
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-3">
                {([['calorias','Kcal'],['proteinas_g','Prot (g)'],['carbohidratos_g','CHO (g)'],['grasas_g','Grasas (g)'],['fibra_g','Fibra (g)']] as [keyof Ingrediente, string][]).map(([field, lbl]) => (
                  <div key={field}>
                    <label className={LABEL}>{lbl}</label>
                    <input type="number" value={newIng[field] as string}
                      onChange={e => setNewIng(p => ({ ...p, [field]: e.target.value }))}
                      placeholder="0" className={INPUT} />
                  </div>
                ))}
              </div>
              <button onClick={addIngrediente}
                className="px-4 py-2 bg-primary text-white text-sm font-semibold rounded-lg hover:bg-primary-dark transition-colors">
                + Agregar
              </button>
            </div>

            {/* Lista ingredientes */}
            {ingredientes.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-6">Sin ingredientes. Agrega el primero arriba.</p>
            ) : (
              <div className="space-y-2">
                {ingredientes.map((ing, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-3 gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800">
                        {ing.nombre_alimento}
                        {ing.medida_casera && <span className="text-gray-400 font-normal"> ({ing.medida_casera})</span>}
                        <span className="text-gray-500 font-normal"> · {ing.gramos}g</span>
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {pf(ing.calorias).toFixed(0)} kcal · {pf(ing.proteinas_g).toFixed(1)}g prot · {pf(ing.carbohidratos_g).toFixed(1)}g CHO · {pf(ing.grasas_g).toFixed(1)}g grasas
                      </p>
                    </div>
                    <button onClick={() => removeIngrediente(idx)}
                      className="text-terracotta hover:text-red-600 text-lg leading-none flex-shrink-0">×</button>
                  </div>
                ))}
                {/* Total receta */}
                <div className="flex justify-end px-4 py-2 bg-primary/5 rounded-lg">
                  <p className="text-xs font-semibold text-primary">
                    Total: {totales.kcal.toFixed(0)} kcal · {totales.prot.toFixed(1)}g prot · {totales.cho.toFixed(1)}g CHO · {totales.fat.toFixed(1)}g grasas · {totales.fib.toFixed(1)}g fibra
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Tab: Aporte Nutricional ───────────────────────────────────────── */}
      {tab === 'nutricion' && (
        <div className="bg-white border border-border rounded-xl p-6">
          <h3 className="font-semibold text-gray-700 mb-1">Por porción <span className="text-gray-400 font-normal">(÷ {n} porciones)</span></h3>
          <p className="text-xs text-gray-400 mb-6">Calculado automáticamente según los ingredientes.</p>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-8">
            {([
              ['Calorías', porPorcion.kcal, 'kcal', 'bg-amber-50 text-amber-700'],
              ['Proteínas', porPorcion.prot, 'g', 'bg-green-50 text-green-700'],
              ['Carbohidratos', porPorcion.cho, 'g', 'bg-blue-50 text-blue-700'],
              ['Grasas', porPorcion.fat, 'g', 'bg-pink-50 text-pink-700'],
              ['Fibra', porPorcion.fib, 'g', 'bg-purple-50 text-purple-700'],
            ] as [string, number, string, string][]).map(([lbl, val, unit, cls]) => (
              <div key={lbl} className={`rounded-xl p-4 ${cls}`}>
                <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{lbl}</p>
                <p className="text-2xl font-bold mt-1">{val.toFixed(lbl === 'Calorías' ? 0 : 1)}</p>
                <p className="text-xs opacity-60">{unit}</p>
              </div>
            ))}
          </div>
          <div className="border-t border-border pt-4">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Total receta completa</p>
            <p className="text-sm text-gray-600">
              {totales.kcal.toFixed(0)} kcal · {totales.prot.toFixed(1)}g prot · {totales.cho.toFixed(1)}g CHO · {totales.fat.toFixed(1)}g grasas · {totales.fib.toFixed(1)}g fibra
              <span className="text-gray-400"> (para {n} porción{n !== 1 ? 'es' : ''})</span>
            </p>
          </div>
        </div>
      )}

      {/* ── Tab: Equivalencias ────────────────────────────────────────────── */}
      {tab === 'equiv' && (
        <div className="bg-white border border-border rounded-xl p-6">
          <h3 className="font-semibold text-gray-700 mb-1">Equivalencias por porción</h3>
          <p className="text-sm text-gray-500 mb-2">
            Indica cuántas porciones de cada grupo alimentario equivale <strong>1 porción</strong> de la receta.
          </p>

          {/* Referencia receta */}
          <div className="bg-primary/5 rounded-lg px-4 py-3 mb-2 text-xs text-primary font-medium">
            Receta: {porPorcion.kcal.toFixed(0)} kcal · {porPorcion.prot.toFixed(1)}g prot · {porPorcion.cho.toFixed(1)}g CHO · {porPorcion.fat.toFixed(1)}g grasas por porción
          </div>
          <div className="bg-sage/10 rounded-lg px-4 py-3 mb-6 text-xs text-gray-600">
            Desde equivalencias: {equivTotales.kcal.toFixed(0)} kcal · {equivTotales.prot.toFixed(1)}g prot · {equivTotales.cho.toFixed(1)}g CHO · {equivTotales.fat.toFixed(1)}g grasas
          </div>

          {/* Tabla grupos */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                  <th className="text-left px-3 py-2 rounded-l">Grupo</th>
                  <th className="px-3 py-2 text-center">Porciones</th>
                  <th className="px-3 py-2 text-center">Ref. kcal</th>
                  <th className="px-3 py-2 text-center">Ref. prot</th>
                  <th className="px-3 py-2 text-center">Ref. CHO</th>
                  <th className="px-3 py-2 text-center rounded-r">Ref. grasas</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(NOMBRES_GRUPOS).map(([key, nombre], idx) => {
                  const m = GRUPOS_MACROS[key]
                  return (
                    <tr key={key} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-3 py-2 font-medium text-gray-700">{nombre}</td>
                      <td className="px-3 py-2 text-center">
                        <input
                          type="number" min="0" step="0.5"
                          value={equiv[key] ?? '0'}
                          onChange={e => setEquiv(p => ({ ...p, [key]: e.target.value }))}
                          className="w-20 text-center border border-border rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                        />
                      </td>
                      <td className="px-3 py-2 text-center text-gray-400 text-xs">{m.kcal}</td>
                      <td className="px-3 py-2 text-center text-gray-400 text-xs">{m.prot}</td>
                      <td className="px-3 py-2 text-center text-gray-400 text-xs">{m.cho}</td>
                      <td className="px-3 py-2 text-center text-gray-400 text-xs">{m.lip}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Botón guardar fijo */}
      <div className="flex justify-end gap-3 mt-6">
        <Link to="/recetas" className="px-4 py-2 border border-border text-sm rounded-lg hover:bg-gray-50 transition-colors">
          Cancelar
        </Link>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-primary text-white text-sm font-semibold rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-60"
        >
          {saving ? 'Guardando…' : isEditing ? 'Guardar cambios' : 'Crear receta'}
        </button>
      </div>
    </Layout>
  )
}
