import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

interface AuditEntry {
  id: number
  action: string
  resource: string
  resource_id: number | null
  detail: string | null
  created_at: string
}

const ACTION_LABEL: Record<string, string> = {
  login: 'Inicio de sesión',
  login_failed: 'Login fallido',
  register: 'Registro',
  create: 'Crear',
  update: 'Editar',
  delete: 'Eliminar',
  export: 'Exportar',
}

const ACTION_COLOR: Record<string, string> = {
  login: 'bg-green-100 text-green-700',
  login_failed: 'bg-red-100 text-red-700',
  register: 'bg-blue-100 text-blue-700',
  create: 'bg-primary/10 text-primary',
  update: 'bg-yellow-100 text-yellow-700',
  delete: 'bg-red-100 text-red-600',
  export: 'bg-terracotta/10 text-terracotta',
}

export default function ConfigPage() {
  const { token } = useAuth()
  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  const [logs, setLogs] = useState<AuditEntry[]>([])
  const [total, setTotal] = useState(0)
  const [loadingLogs, setLoadingLogs] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API}/settings/audit-logs?limit=50`, { headers: H })
      .then(r => r.json())
      .then(d => { setLogs(d.logs ?? []); setTotal(d.total ?? 0) })
      .catch(() => setError('No se pudieron cargar los registros'))
      .finally(() => setLoadingLogs(false))
  }, [])

  const handleBackup = async () => {
    setDownloading(true)
    try {
      const res = await fetch(`${API}/settings/backup`, { headers: H })
      if (!res.ok) throw new Error()
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
      a.download = `nutriapp_backup_${date}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('No se pudo descargar el backup')
    } finally {
      setDownloading(false)
    }
  }

  const fmtDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('es-CL', { dateStyle: 'short', timeStyle: 'short' })
    } catch { return iso }
  }

  return (
    <Layout title="Configuración">
      <div className="max-w-3xl mx-auto space-y-6">

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
        )}

        {/* Backup */}
        <div className="bg-white rounded-xl shadow-sm border border-border border-l-4 border-l-terracotta p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-start gap-4">
              <span className="text-2xl mt-0.5">&#11015;</span>
              <div>
                <h2 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-2">Backup de datos</h2>
                <p className="text-sm text-gray-600">
                  Descarga todos tus datos (pacientes, evaluaciones, planes, pautas) en formato JSON.
                </p>
              </div>
            </div>
            <button
              onClick={handleBackup}
              disabled={downloading}
              className="bg-terracotta hover:opacity-90 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2 shrink-0"
            >
              {downloading ? 'Generando...' : 'Descargar backup'}
            </button>
          </div>
          <div className="border-t border-border my-4" />
          <p className="text-xs text-text-muted">
            Guarda el archivo en un lugar seguro (Google Drive, iCloud, etc.). Se recomienda hacer backup mensualmente.
          </p>
        </div>

        {/* Audit logs */}
        <div className="bg-white rounded-xl shadow-sm border border-border overflow-hidden">
          <div className="px-6 py-4 border-b border-border flex items-center justify-between">
            <div>
              <h2 className="text-xs font-bold text-text-muted uppercase tracking-widest">Registro de actividad</h2>
              <p className="text-sm text-text-muted mt-1">{total} registros en total</p>
            </div>
          </div>

          {loadingLogs ? (
            <div className="px-6 py-8 text-center text-text-muted text-sm">Cargando...</div>
          ) : logs.length === 0 ? (
            <div className="p-10 text-center text-text-muted text-sm space-y-4">
              <div className="text-4xl mb-2">&#128203;</div>
              <p className="font-medium">Sin actividad registrada.</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-4 py-3 text-xs font-bold text-gray-400 uppercase tracking-wider text-left">Acción</th>
                  <th className="px-4 py-3 text-xs font-bold text-gray-400 uppercase tracking-wider text-left">Recurso</th>
                  <th className="px-4 py-3 text-xs font-bold text-gray-400 uppercase tracking-wider text-left">Detalle</th>
                  <th className="px-4 py-3 text-xs font-bold text-gray-400 uppercase tracking-wider text-right">Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {logs.map(log => (
                  <tr key={log.id} className="hover:bg-bg-light/50 transition-colors">
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-bold inline-block ${ACTION_COLOR[log.action] ?? 'bg-gray-100 text-gray-600'}`}>
                        {ACTION_LABEL[log.action] ?? log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 capitalize">{log.resource}</td>
                    <td className="px-4 py-3 text-sm text-text-muted truncate max-w-xs">{log.detail ?? '—'}</td>
                    <td className="px-4 py-3 text-xs text-text-muted text-right whitespace-nowrap">{fmtDate(log.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

      </div>
    </Layout>
  )
}
