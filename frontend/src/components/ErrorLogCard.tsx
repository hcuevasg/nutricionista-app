import { useEffect, useState } from 'react'
import { api } from '../api/client'

interface ErrorEntry {
  id: number
  source: 'backend' | 'frontend'
  method: string | null
  path: string | null
  error_type: string | null
  message: string | null
  stack: string | null
  created_at: string
}

/** Errores registrados en la cuenta (backend y navegador), últimos 90 días. */
export default function ErrorLogCard() {
  const [errors, setErrors] = useState<ErrorEntry[] | null>(null)
  const [open, setOpen] = useState<number | null>(null)

  useEffect(() => {
    api.get<{ errors: ErrorEntry[] }>('/settings/error-logs', { limit: 50 })
      .then(d => setErrors(d.errors))
      .catch(() => setErrors([]))
  }, [])

  return (
    <div className="bg-white rounded-xl shadow-sm border border-border overflow-hidden">
      <div className="px-6 py-4 border-b border-border">
        <h2 className="text-xs font-bold text-text-muted uppercase tracking-widest">Errores registrados</h2>
        <p className="text-sm text-text-muted mt-1">Fallos de la aplicación en tu cuenta (se guardan 90 días).</p>
      </div>
      {errors === null ? (
        <div className="px-6 py-8 text-center text-text-muted text-sm">Cargando...</div>
      ) : errors.length === 0 ? (
        <div className="px-6 py-8 text-center text-text-muted text-sm">Sin errores registrados. 🎉</div>
      ) : (
        <ul className="divide-y divide-gray-100">
          {errors.map(e => (
            <li key={e.id} className="px-6 py-3">
              <button onClick={() => setOpen(open === e.id ? null : e.id)} className="w-full text-left flex gap-3 items-start">
                <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full mt-0.5 ${e.source === 'backend'
                  ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
                  {e.source === 'backend' ? 'Servidor' : 'Navegador'}
                </span>
                <span className="flex-1 min-w-0">
                  <span className="block text-sm text-gray-800 truncate">{e.message ?? e.error_type}</span>
                  <span className="block text-xs text-text-muted">
                    #{e.id} · {[e.method, e.path].filter(Boolean).join(' ')} · {new Date(e.created_at + 'Z').toLocaleString('es-CL')}
                  </span>
                </span>
              </button>
              {open === e.id && e.stack && (
                <pre className="mt-2 text-[11px] bg-gray-50 border border-gray-100 rounded p-3 overflow-x-auto max-h-64">{e.stack}</pre>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
