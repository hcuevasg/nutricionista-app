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

const INPUT = 'w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary'
const LABEL = 'block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1'

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
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Información Personal */}
        <section className="bg-white rounded-xl shadow-sm border border-border p-6 space-y-4">
          <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest border-b border-border pb-3">
            Información Personal
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className={LABEL}>
                Nombre completo <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => set('name', e.target.value)}
                className={INPUT}
                placeholder="Ej: Maria Gonzalez"
                required
              />
            </div>
            <div>
              <label className={LABEL}>Fecha de nacimiento</label>
              <input
                type="date"
                value={form.birth_date}
                onChange={(e) => set('birth_date', e.target.value)}
                className={INPUT}
              />
            </div>
            <div>
              <label className={LABEL}>Edad (calculada)</label>
              <input
                type="text"
                readOnly
                value={age != null ? `${age} anos` : '--'}
                className={`${INPUT} bg-bg-light text-text-muted cursor-not-allowed`}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={LABEL}>Sexo</label>
              <select
                value={form.sex}
                onChange={(e) => set('sex', e.target.value)}
                className={`${INPUT} bg-white`}
              >
                <option value="Masculino">Masculino</option>
                <option value="Femenino">Femenino</option>
              </select>
            </div>
            <div>
              <label className={LABEL}>Ocupacion</label>
              <input
                type="text"
                value={form.occupation}
                onChange={(e) => set('occupation', e.target.value)}
                className={INPUT}
                placeholder="Ej: Profesor"
              />
            </div>
          </div>
        </section>

        {/* Datos Fisicos */}
        <section className="bg-white rounded-xl shadow-sm border border-border p-6 space-y-4">
          <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest border-b border-border pb-3">
            Datos Fisicos
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={LABEL}>Talla (cm)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={form.height_cm}
                onChange={(e) => set('height_cm', e.target.value)}
                className={INPUT}
                placeholder="170.0"
              />
            </div>
            <div>
              <label className={LABEL}>Peso (kg)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={form.weight_kg}
                onChange={(e) => set('weight_kg', e.target.value)}
                className={INPUT}
                placeholder="70.0"
              />
            </div>
          </div>
        </section>

        {/* Contacto */}
        <section className="bg-white rounded-xl shadow-sm border border-border p-6 space-y-4">
          <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest border-b border-border pb-3">
            Contacto
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={LABEL}>Telefono</label>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => set('phone', e.target.value)}
                className={INPUT}
                placeholder="+56 9 1234 5678"
              />
            </div>
            <div>
              <label className={LABEL}>Correo electronico</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => set('email', e.target.value)}
                className={INPUT}
                placeholder="paciente@email.com"
              />
            </div>
          </div>
          <div>
            <label className={LABEL}>Direccion</label>
            <input
              type="text"
              value={form.address}
              onChange={(e) => set('address', e.target.value)}
              className={INPUT}
              placeholder="Calle, numero, ciudad"
            />
          </div>
        </section>

        {/* Notas */}
        <section className="bg-white rounded-xl shadow-sm border border-border p-6 space-y-4">
          <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest border-b border-border pb-3">
            Notas / Antecedentes
          </h3>
          <textarea
            value={form.notes}
            onChange={(e) => set('notes', e.target.value)}
            rows={4}
            className={`${INPUT} resize-none`}
            placeholder="Antecedentes medicos, alergias, restricciones alimentarias..."
          />
        </section>

        {/* Acciones */}
        <div className="flex items-center justify-between pb-8">
          <button
            type="button"
            onClick={() => navigate('/patients')}
            className="border border-border hover:bg-bg-light text-gray-700 px-4 py-2 rounded-lg font-medium"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={saving}
            className="bg-primary hover:bg-primary-dark text-white px-6 py-2 rounded-lg font-medium disabled:opacity-60"
          >
            {saving ? 'Guardando...' : isEditing ? 'Guardar cambios' : 'Crear paciente'}
          </button>
        </div>
      </form>
    </Layout>
  )
}
