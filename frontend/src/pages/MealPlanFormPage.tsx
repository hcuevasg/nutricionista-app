import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

const MEAL_TYPES = ['Desayuno', 'Media mañana', 'Almuerzo', 'Merienda', 'Cena', 'Colación']
const UNITS = ['g', 'ml', 'taza', 'cdta', 'cda', 'unidad', 'porción', 'rebanada']

interface Item {
  id?: number
  meal_type: string
  food_name: string
  quantity: string
  unit: string
  calories: string
  protein_g: string
  carbs_g: string
  fat_g: string
  fiber_g: string
}

interface PlanForm {
  name: string
  date: string
  goal: string
  notes: string
}

function emptyItem(meal_type = MEAL_TYPES[0]): Item {
  return { meal_type, food_name: '', quantity: '', unit: 'g', calories: '', protein_g: '', carbs_g: '', fat_g: '', fiber_g: '' }
}

function pf(v: string) { const n = parseFloat(v); return isNaN(n) ? null : n }
function sum(items: Item[], field: keyof Item) {
  return items.reduce((acc, it) => acc + (pf(it[field] as string) ?? 0), 0)
}

export default function MealPlanFormPage() {
  const { id, planId } = useParams<{ id: string; planId: string }>()
  const isEditing = !!planId
  const { token } = useAuth()
  const navigate = useNavigate()

  const [patientName, setPatientName] = useState('')
  const [form, setForm] = useState<PlanForm>({ name: '', date: new Date().toISOString().split('T')[0], goal: '', notes: '' })
  const [items, setItems] = useState<Item[]>([])
  const [addMealType, setAddMealType] = useState(MEAL_TYPES[0])
  const [loading, setLoading] = useState(isEditing)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  useEffect(() => {
    if (!token || !id) return
    fetch(`${API}/patients/${id}`, { headers: H })
      .then(r => r.json()).then(p => setPatientName(p.name ?? ''))
    if (isEditing) {
      fetch(`${API}/meal-plans/${id}/${planId}`, { headers: H })
        .then(r => r.json())
        .then(plan => {
          setForm({ name: plan.name, date: plan.date, goal: plan.goal ?? '', notes: plan.notes ?? '' })
          setItems((plan.items ?? []).map((it: Record<string, unknown>) => ({
            id: it.id as number,
            meal_type: it.meal_type as string,
            food_name: it.food_name as string,
            quantity: it.quantity != null ? String(it.quantity) : '',
            unit: it.unit as string ?? 'g',
            calories: it.calories != null ? String(it.calories) : '',
            protein_g: it.protein_g != null ? String(it.protein_g) : '',
            carbs_g: it.carbs_g != null ? String(it.carbs_g) : '',
            fat_g: it.fat_g != null ? String(it.fat_g) : '',
            fiber_g: it.fiber_g != null ? String(it.fiber_g) : '',
          })))
        })
        .finally(() => setLoading(false))
    }
  }, [id, planId, token])

  const setF = (k: keyof PlanForm, v: string) => setForm(p => ({ ...p, [k]: v }))

  const addItem = () => setItems(prev => [...prev, emptyItem(addMealType)])

  const updateItem = (idx: number, field: keyof Item, val: string) =>
    setItems(prev => prev.map((it, i) => i === idx ? { ...it, [field]: val } : it))

  const removeItem = (idx: number) => setItems(prev => prev.filter((_, i) => i !== idx))

  const totalKcal = sum(items, 'calories')
  const totalProt = sum(items, 'protein_g')
  const totalCarbs = sum(items, 'carbs_g')
  const totalFat = sum(items, 'fat_g')

  const handleSave = async () => {
    if (!form.name.trim()) { setError('El nombre del plan es obligatorio'); return }
    setSaving(true); setError(null)

    const payload = {
      name: form.name.trim(),
      date: form.date,
      goal: form.goal.trim() || null,
      notes: form.notes.trim() || null,
      calories: totalKcal || null,
      protein_g: totalProt || null,
      carbs_g: totalCarbs || null,
      fat_g: totalFat || null,
      items: items.filter(it => it.food_name.trim()).map(it => ({
        meal_type: it.meal_type,
        food_name: it.food_name.trim(),
        quantity: pf(it.quantity),
        unit: it.unit || null,
        calories: pf(it.calories),
        protein_g: pf(it.protein_g),
        carbs_g: pf(it.carbs_g),
        fat_g: pf(it.fat_g),
        fiber_g: pf(it.fiber_g),
      })),
    }

    const url = isEditing ? `${API}/meal-plans/${id}/${planId}` : `${API}/meal-plans?patient_id=${id}`
    const method = isEditing ? 'PUT' : 'POST'

    try {
      const res = await fetch(url, { method, headers: H, body: JSON.stringify(payload) })
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail ?? `Error ${res.status}`) }
      navigate(`/patients/${id}/plans`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Layout title="Plan Alimenticio"><div className="p-8 text-center text-text-muted">Cargando...</div></Layout>

  // Group items by meal type preserving order
  const grouped = MEAL_TYPES.map(mt => ({ mt, items: items.map((it, idx) => ({ it, idx })).filter(({ it }) => it.meal_type === mt) }))

  return (
    <Layout title={isEditing ? 'Editar Plan' : 'Nuevo Plan'}>
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/patients" className="hover:text-primary">Pacientes</Link>
        <span>/</span>
        <Link to={`/patients/${id}`} className="hover:text-primary">{patientName || `Paciente ${id}`}</Link>
        <span>/</span>
        <Link to={`/patients/${id}/plans`} className="hover:text-primary">Planes</Link>
        <span>/</span>
        <span className="text-primary font-medium">{isEditing ? 'Editar' : 'Nuevo'}</span>
      </div>

      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left: form + items */}
        <div className="xl:col-span-2 space-y-6">

          {/* Plan metadata */}
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">Datos del Plan</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-xs text-text-muted mb-1">Nombre del plan *</label>
                <input value={form.name} onChange={e => setF('name', e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Ej: Plan hipocalórico semana 1" />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1">Fecha</label>
                <input type="date" value={form.date} onChange={e => setF('date', e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1">Objetivo</label>
                <input value={form.goal} onChange={e => setF('goal', e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Ej: Bajar de peso" />
              </div>
              <div className="col-span-2">
                <label className="block text-xs text-text-muted mb-1">Notas</label>
                <textarea value={form.notes} onChange={e => setF('notes', e.target.value)} rows={2}
                  className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  placeholder="Indicaciones adicionales..." />
              </div>
            </div>
          </div>

          {/* Items grouped by meal type */}
          <div className="bg-white rounded-lg shadow p-6 space-y-6">
            <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">Alimentos por Tiempo de Comida</h3>

            {grouped.map(({ mt, items: group }) => group.length > 0 && (
              <div key={mt}>
                <div className="bg-primary/10 rounded px-3 py-1.5 mb-2">
                  <span className="text-xs font-bold text-primary uppercase tracking-wide">{mt}</span>
                </div>
                <div className="space-y-2">
                  {/* Header */}
                  <div className="grid grid-cols-12 gap-1 px-1 text-xs text-text-muted font-medium">
                    <span className="col-span-3">Alimento</span>
                    <span className="col-span-1">Cant.</span>
                    <span className="col-span-1">Unidad</span>
                    <span className="col-span-1">Kcal</span>
                    <span className="col-span-1">Prot.</span>
                    <span className="col-span-1">Carb.</span>
                    <span className="col-span-1">Gras.</span>
                    <span className="col-span-1">Fibra</span>
                    <span className="col-span-2"></span>
                  </div>
                  {group.map(({ it, idx }) => (
                    <div key={idx} className="grid grid-cols-12 gap-1 items-center">
                      <input value={it.food_name} onChange={e => updateItem(idx, 'food_name', e.target.value)}
                        className="col-span-3 px-2 py-1.5 border border-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="Nombre alimento" />
                      <input type="number" value={it.quantity} onChange={e => updateItem(idx, 'quantity', e.target.value)}
                        className="col-span-1 px-2 py-1.5 border border-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-primary" placeholder="0" />
                      <select value={it.unit} onChange={e => updateItem(idx, 'unit', e.target.value)}
                        className="col-span-1 px-1 py-1.5 border border-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-primary bg-white">
                        {UNITS.map(u => <option key={u}>{u}</option>)}
                      </select>
                      {(['calories','protein_g','carbs_g','fat_g','fiber_g'] as (keyof Item)[]).map(field => (
                        <input key={field} type="number" value={it[field] as string}
                          onChange={e => updateItem(idx, field, e.target.value)}
                          className="col-span-1 px-2 py-1.5 border border-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-primary" placeholder="0" />
                      ))}
                      <button onClick={() => removeItem(idx)}
                        className="col-span-2 text-red-400 hover:text-red-600 text-xs text-right pr-1">✕ Quitar</button>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {items.filter(it => it.food_name.trim()).length === 0 && (
              <p className="text-sm text-text-muted italic text-center py-4">
                Aún no hay alimentos. Usa el botón de abajo para agregar.
              </p>
            )}

            {/* Add item row */}
            <div className="flex items-center gap-3 pt-4 border-t border-border">
              <select value={addMealType} onChange={e => setAddMealType(e.target.value)}
                className="px-3 py-2 border border-border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary">
                {MEAL_TYPES.map(mt => <option key={mt}>{mt}</option>)}
              </select>
              <button onClick={addItem}
                className="bg-primary/10 hover:bg-primary/20 text-primary px-4 py-2 rounded-lg text-sm font-medium">
                + Agregar alimento
              </button>
            </div>
          </div>
        </div>

        {/* Right: macros summary + save */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">Resumen Nutricional</h3>
            <div className="space-y-3">
              <MacroCard label="Calorías totales" value={totalKcal.toFixed(0)} unit="kcal" color="text-primary" big />
              <MacroCard label="Proteínas" value={totalProt.toFixed(1)} unit="g" color="text-blue-500" />
              <MacroCard label="Carbohidratos" value={totalCarbs.toFixed(1)} unit="g" color="text-orange-500" />
              <MacroCard label="Grasas" value={totalFat.toFixed(1)} unit="g" color="text-yellow-500" />
            </div>
            {totalKcal > 0 && (
              <div className="pt-3 border-t border-border space-y-1">
                <p className="text-xs text-text-muted font-medium">Distribución</p>
                <MacroPct label="Proteínas" pct={totalKcal ? (totalProt * 4 / totalKcal) * 100 : 0} color="bg-blue-400" />
                <MacroPct label="Carbos" pct={totalKcal ? (totalCarbs * 4 / totalKcal) * 100 : 0} color="bg-orange-400" />
                <MacroPct label="Grasas" pct={totalKcal ? (totalFat * 9 / totalKcal) * 100 : 0} color="bg-yellow-400" />
              </div>
            )}
          </div>

          <div className="flex flex-col gap-2">
            <button onClick={handleSave} disabled={saving}
              className="bg-primary hover:bg-primary-dark text-white py-3 rounded-lg font-medium disabled:opacity-50">
              {saving ? 'Guardando...' : isEditing ? 'Guardar cambios' : 'Crear plan'}
            </button>
            <Link to={`/patients/${id}/plans`}
              className="border border-border text-text-muted hover:bg-bg-light py-3 rounded-lg font-medium text-center text-sm">
              Cancelar
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  )
}

function MacroCard({ label, value, unit, color, big }: { label: string; value: string; unit: string; color: string; big?: boolean }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-text-muted">{label}</span>
      <span className={`font-bold ${color} ${big ? 'text-xl' : 'text-sm'}`}>{value} <span className="text-xs font-normal">{unit}</span></span>
    </div>
  )
}

function MacroPct({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-text-muted w-16">{label}</span>
      <div className="flex-1 bg-bg-light rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${Math.min(100, pct).toFixed(0)}%` }} />
      </div>
      <span className="text-xs text-text-muted w-8 text-right">{pct.toFixed(0)}%</span>
    </div>
  )
}
