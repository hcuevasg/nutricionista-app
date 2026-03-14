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
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{error}</div>
        )}

        {/* Backup */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h2 className="text-lg font-bold text-primary">Backup de datos</h2>
              <p className="text-sm text-text-muted mt-1">
                Descarga todos tus datos (pacientes, evaluaciones, planes, pautas) en formato JSON.
              </p>
            </div>
            <button
              onClick={handleBackup}
              disabled={downloading}
              className="bg-terracotta hover:opacity-90 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2"
            >
              {downloading ? 'Generando...' : '⬇ Descargar backup'}
            </button>
          </div>
          <p className="text-xs text-text-muted mt-3 border-t border-border pt-3">
            Guarda el archivo en un lugar seguro (Google Drive, iCloud, etc.). Se recomienda hacer backup mensualmente.
          </p>
        </div>

        {/* Audit logs */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-border flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-primary">Registro de actividad</h2>
              <p className="text-sm text-text-muted">{total} registros en total</p>
            </div>
          </div>

          {loadingLogs ? (
            <div className="px-6 py-8 text-center text-text-muted text-sm">Cargando...</div>
          ) : logs.length === 0 ? (
            <div className="px-6 py-8 text-center text-text-muted text-sm">Sin actividad registrada.</div>
          ) : (
            <div className="divide-y divide-border">
              {logs.map(log => (
                <div key={log.id} className="px-6 py-3 flex items-start gap-4">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 mt-0.5 ${ACTION_COLOR[log.action] ?? 'bg-gray-100 text-gray-600'}`}>
                    {ACTION_LABEL[log.action] ?? log.action}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700 truncate">
                      <span className="text-text-muted capitalize">{log.resource}</span>
                      {log.detail && <span> — {log.detail}</span>}
                    </p>
                  </div>
                  <span className="text-xs text-text-muted shrink-0">{fmtDate(log.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </Layout>
  )
}
