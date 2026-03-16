import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { useToast } from '../context/ToastContext'
import { api } from '../api/client'

interface Appointment {
  id: number
  patient_id?: number
  patient_name?: string
  scheduled_at: string
  duration_minutes: number
  notes?: string
  status: 'scheduled' | 'completed' | 'cancelled'
  created_at: string
}

interface Patient {
  id: number
  name: string
}

const STATUS_LABELS = {
  scheduled: { label: 'Programada', color: 'bg-blue-50 text-blue-700 border-blue-200' },
  completed: { label: 'Completada', color: 'bg-green-50 text-green-700 border-green-200' },
  cancelled: { label: 'Cancelada', color: 'bg-gray-100 text-gray-500 border-gray-200' },
}

function formatDateTime(iso: string) {
  const d = new Date(iso)
  return {
    date: d.toLocaleDateString('es-CL', { weekday: 'short', day: 'numeric', month: 'short' }),
    time: d.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' }),
  }
}

function groupByDate(appointments: Appointment[]) {
  const groups: Record<string, Appointment[]> = {}
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const nextWeek = new Date(today)
  nextWeek.setDate(nextWeek.getDate() + 7)
  const nextMonth = new Date(today)
  nextMonth.setDate(nextMonth.getDate() + 30)

  for (const appt of appointments) {
    const d = new Date(appt.scheduled_at)
    d.setHours(0, 0, 0, 0)
    let key: string
    if (d.getTime() === today.getTime()) key = 'Hoy'
    else if (d < nextWeek) key = 'Esta semana'
    else if (d < nextMonth) key = 'Este mes'
    else key = 'Más adelante'
    if (!groups[key]) groups[key] = []
    groups[key].push(appt)
  }
  return groups
}

export default function AgendaPage() {
  const toast = useToast()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingAppt, setEditingAppt] = useState<Appointment | null>(null)
  const [form, setForm] = useState({
    patient_id: '',
    scheduled_at: '',
    duration_minutes: '45',
    notes: '',
    status: 'scheduled',
  })
  const [saving, setSaving] = useState(false)

  const load = async () => {
    try {
      const [appts, pats] = await Promise.all([
        api.get<Appointment[]>('/appointments'),
        api.get<{ items: Patient[] }>('/patients', { limit: 200 }),
      ])
      setAppointments(appts)
      setPatients(pats.items)
    } catch {
      toast.error('Error al cargar la agenda')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const openCreate = () => {
    setEditingAppt(null)
    const now = new Date()
    now.setMinutes(0, 0, 0)
    now.setHours(now.getHours() + 1)
    setForm({ patient_id: '', scheduled_at: now.toISOString().slice(0, 16), duration_minutes: '45', notes: '', status: 'scheduled' })
    setShowModal(true)
  }

  const openEdit = (appt: Appointment) => {
    setEditingAppt(appt)
    setForm({
      patient_id: String(appt.patient_id ?? ''),
      scheduled_at: new Date(appt.scheduled_at).toISOString().slice(0, 16),
      duration_minutes: String(appt.duration_minutes),
      notes: appt.notes ?? '',
      status: appt.status,
    })
    setShowModal(true)
  }

  const handleSave = async () => {
    if (!form.scheduled_at) { toast.error('Selecciona fecha y hora'); return }
    setSaving(true)
    try {
      const payload = {
        patient_id: form.patient_id ? Number(form.patient_id) : null,
        scheduled_at: new Date(form.scheduled_at).toISOString(),
        duration_minutes: Number(form.duration_minutes),
        notes: form.notes || null,
        status: form.status,
      }
      if (editingAppt) {
        const updated = await api.put<Appointment>(`/appointments/${editingAppt.id}`, payload)
        setAppointments(prev => prev.map(a => a.id === updated.id ? updated : a))
        toast.success('Cita actualizada')
      } else {
        const created = await api.post<Appointment>('/appointments', payload)
        setAppointments(prev => [...prev, created].sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()))
        toast.success('Cita creada')
      }
      setShowModal(false)
    } catch {
      toast.error('Error al guardar la cita')
    } finally {
      setSaving(false)
    }
  }

  const handleStatusChange = async (appt: Appointment, status: string) => {
    try {
      const updated = await api.patch<Appointment>(`/appointments/${appt.id}/status?status=${status}`)
      setAppointments(prev => prev.map(a => a.id === updated.id ? updated : a))
      toast.success(status === 'completed' ? 'Marcada como completada' : 'Cita cancelada')
    } catch {
      toast.error('Error al actualizar estado')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('¿Eliminar esta cita?')) return
    try {
      await api.delete(`/appointments/${id}`)
      setAppointments(prev => prev.filter(a => a.id !== id))
      toast.success('Cita eliminada')
    } catch {
      toast.error('Error al eliminar')
    }
  }

  const groups = groupByDate(appointments)
  const ORDER = ['Hoy', 'Esta semana', 'Este mes', 'Más adelante']

  return (
    <Layout title="Agenda">
      <div className="flex justify-between items-center mb-6">
        <p className="text-sm text-text-muted">Gestiona tus consultas y citas programadas.</p>
        <button
          onClick={openCreate}
          className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          + Nueva Cita
        </button>
      </div>

      {loading ? (
        <div className="text-center py-16 text-text-muted">Cargando agenda...</div>
      ) : appointments.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-5xl mb-4">📅</div>
          <p className="text-text-muted font-medium">Sin citas programadas.</p>
          <button onClick={openCreate} className="mt-4 text-primary text-sm font-semibold hover:underline">
            Crear primera cita →
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          {ORDER.filter(k => groups[k]).map(group => (
            <div key={group}>
              <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-3">{group}</h3>
              <div className="space-y-3">
                {groups[group].map(appt => {
                  const { date, time } = formatDateTime(appt.scheduled_at)
                  const statusInfo = STATUS_LABELS[appt.status] ?? STATUS_LABELS.scheduled
                  return (
                    <div key={appt.id} className="bg-white border border-border rounded-xl p-4 flex items-start gap-4 hover:shadow-sm transition-shadow">
                      <div className="text-center min-w-[52px]">
                        <div className="text-xs text-text-muted">{date}</div>
                        <div className="text-lg font-bold text-primary">{time}</div>
                        <div className="text-xs text-text-muted">{appt.duration_minutes}min</div>
                      </div>
                      <div className="flex-1 min-w-0">
                        {appt.patient_name ? (
                          <Link to={`/patients/${appt.patient_id}`} className="font-semibold text-gray-800 hover:text-primary">
                            {appt.patient_name}
                          </Link>
                        ) : (
                          <span className="font-semibold text-gray-500 italic">Sin paciente asignado</span>
                        )}
                        {appt.notes && <p className="text-sm text-text-muted mt-0.5 truncate">{appt.notes}</p>}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0 flex-wrap justify-end">
                        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                        {appt.status === 'scheduled' && (
                          <>
                            <button
                              onClick={() => handleStatusChange(appt, 'completed')}
                              className="text-xs text-green-600 hover:underline font-medium"
                            >
                              Completar
                            </button>
                            <button
                              onClick={() => handleStatusChange(appt, 'cancelled')}
                              className="text-xs text-text-muted hover:underline"
                            >
                              Cancelar
                            </button>
                          </>
                        )}
                        <button onClick={() => openEdit(appt)} className="text-xs text-primary hover:underline">
                          Editar
                        </button>
                        <button onClick={() => handleDelete(appt.id)} className="text-xs text-terracotta hover:underline">
                          Eliminar
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-lg font-bold">{editingAppt ? 'Editar Cita' : 'Nueva Cita'}</h3>

            <div>
              <label className="block text-xs font-semibold text-text-muted uppercase mb-1">Paciente</label>
              <select
                value={form.patient_id}
                onChange={e => setForm(f => ({ ...f, patient_id: e.target.value }))}
                className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Sin paciente asignado</option>
                {patients.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-muted uppercase mb-1">Fecha y Hora *</label>
              <input
                type="datetime-local"
                value={form.scheduled_at}
                onChange={e => setForm(f => ({ ...f, scheduled_at: e.target.value }))}
                className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-muted uppercase mb-1">Duración</label>
              <select
                value={form.duration_minutes}
                onChange={e => setForm(f => ({ ...f, duration_minutes: e.target.value }))}
                className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {[30, 45, 60, 90].map(m => <option key={m} value={m}>{m} minutos</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-muted uppercase mb-1">Notas</label>
              <textarea
                value={form.notes}
                onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
                rows={2}
                placeholder="Motivo de consulta, observaciones..."
                className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 border border-border text-gray-700 py-2 rounded-lg text-sm font-medium hover:bg-bg-light"
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 bg-primary text-white py-2 rounded-lg text-sm font-medium hover:bg-primary-dark disabled:opacity-50"
              >
                {saving ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
