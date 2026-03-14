import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

interface PatientFormData {
  name: string
  birth_date: string
  sex: string
  height_cm: string
  weight_kg: string
  phone: string
  email: string
  address: string
  occupation: string
  notes: string
}

const EMPTY_FORM: PatientFormData = {
  name: '',
  birth_date: '',
  sex: 'Masculino',
  height_cm: '',
  weight_kg: '',
  phone: '',
  email: '',
  address: '',
  occupation: '',
  notes: '',
}

function calcAge(birthDateStr: string): number | null {
  try {
    const bd = new Date(birthDateStr)
    if (isNaN(bd.getTime())) return null
    const today = new Date()
    let age = today.getFullYear() - bd.getFullYear()
    const m = today.getMonth() - bd.getMonth()
    if (m < 0 || (m === 0 && today.getDate() < bd.getDate())) age--
    return age >= 0 ? age : null
  } catch {
    return null
  }
}

export default function PatientFormPage() {
  const { id } = useParams<{ id: string }>()
  const isEditing = !!id
  const { token } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState<PatientFormData>(EMPTY_FORM)
  const [age, setAge] = useState<number | null>(null)
  const [loading, setLoading] = useState(isEditing)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load patient data when editing
  useEffect(() => {
    if (!isEditing || !token) return
    fetch(`${import.meta.env.VITE_API_URL}/patients/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => {
        setForm({
          name: data.name ?? '',
          birth_date: data.birth_date ?? '',
          sex: data.sex ?? 'Masculino',
          height_cm: data.height_cm != null ? String(data.height_cm) : '',
          weight_kg: data.weight_kg != null ? String(data.weight_kg) : '',
          phone: data.phone ?? '',
          email: data.email ?? '',
          address: data.address ?? '',
          occupation: data.occupation ?? '',
          notes: data.notes ?? '',
        })
      })
      .catch(() => setError('Error al cargar el paciente'))
      .finally(() => setLoading(false))
  }, [id, isEditing, token])

  // Auto-calculate age
  useEffect(() => {
    setAge(calcAge(form.birth_date))
  }, [form.birth_date])

  const set = (field: keyof PatientFormData, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) {
      setError('El nombre es obligatorio')
      return
    }
    setSaving(true)
    setError(null)

    const payload = {
      name: form.name.trim(),
      birth_date: form.birth_date || null,
      sex: form.sex,
      height_cm: form.height_cm ? parseFloat(form.height_cm) : null,
      weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      address: form.address.trim() || null,
      occupation: form.occupation.trim() || null,
      notes: form.notes.trim() || null,
    }

    const url = isEditing
      ? `${import.meta.env.VITE_API_URL}/patients/${id}`
      : `${import.meta.env.VITE_API_URL}/patients`

    try {
      const response = await fetch(url, {
        method: isEditing ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail ?? `Error ${response.status}`)
      }

      navigate('/patients')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Layout title={isEditing ? 'Editar Paciente' : 'Nuevo Paciente'}>
        <div className="text-center py-12 text-text-muted">Cargando...</div>
      </Layout>
    )
  }

  return (
    <Layout title={isEditing ? 'Editar Paciente' : 'Nuevo Paciente'}>
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto space-y-6">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Datos personales */}
        <section className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">
            Datos Personales
          </h3>

          <div>
            <label className="block text-sm text-text-muted mb-1">
              Nombre completo <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Ej: María González"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm text-text-muted mb-1">
                Fecha de nacimiento
              </label>
              <input
                type="date"
                value={form.birth_date}
                onChange={(e) => set('birth_date', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1">
                Edad (calculada)
              </label>
              <input
                type="text"
                readOnly
                value={age != null ? `${age} años` : '—'}
                className="w-full px-3 py-2 border border-border rounded-lg bg-bg-light text-text-muted cursor-not-allowed"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-text-muted mb-1">Sexo</label>
              <select
                value={form.sex}
                onChange={(e) => set('sex', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              >
                <option value="Masculino">Masculino</option>
                <option value="Femenino">Femenino</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1">
                Ocupación
              </label>
              <input
                type="text"
                value={form.occupation}
                onChange={(e) => set('occupation', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Ej: Profesor"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-text-muted mb-1">
                Teléfono
              </label>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => set('phone', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="+56 9 1234 5678"
              />
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1">
                Correo electrónico
              </label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => set('email', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="paciente@email.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-text-muted mb-1">
              Dirección
            </label>
            <input
              type="text"
              value={form.address}
              onChange={(e) => set('address', e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Calle, número, ciudad"
            />
          </div>
        </section>

        {/* Medidas */}
        <section className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">
            Medidas Iniciales
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-text-muted mb-1">
                Talla (cm)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={form.height_cm}
                onChange={(e) => set('height_cm', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="170.0"
              />
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1">
                Peso (kg)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={form.weight_kg}
                onChange={(e) => set('weight_kg', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="70.0"
              />
            </div>
          </div>
        </section>

        {/* Notas */}
        <section className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">
            Notas / Antecedentes
          </h3>
          <textarea
            value={form.notes}
            onChange={(e) => set('notes', e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            placeholder="Antecedentes médicos, alergias, restricciones alimentarias..."
          />
        </section>

        {/* Acciones */}
        <div className="flex gap-3 pb-8">
          <button
            type="submit"
            disabled={saving}
            className="flex-1 bg-primary hover:bg-primary-dark text-white py-3 rounded-lg font-medium disabled:opacity-60"
          >
            {saving ? 'Guardando...' : isEditing ? 'Guardar cambios' : 'Crear paciente'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/patients')}
            className="flex-1 border border-border text-text-muted hover:bg-bg-light py-3 rounded-lg font-medium"
          >
            Cancelar
          </button>
        </div>
      </form>
    </Layout>
  )
}
