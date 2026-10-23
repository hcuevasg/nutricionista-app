import { useState } from 'react'
import { api, apiErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'

const INPUT = 'w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30'

/** Activar / desactivar la verificación en dos pasos (TOTP) del profesional. */
export default function TwoFactorCard() {
  const { user, updateUser, setSessionToken } = useAuth()
  const enabled = !!user?.totp_enabled
  const [setup, setSetup] = useState<{ secret: string; qr_svg: string } | null>(null)
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')
  const [recovery, setRecovery] = useState<string[] | null>(null)
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [busy, setBusy] = useState(false)

  const run = async (fn: () => Promise<void>) => {
    setBusy(true); setMsg(null)
    try { await fn() } catch (err) { setMsg({ ok: false, text: apiErrorMessage(err, 'No se pudo completar') }) }
    finally { setBusy(false) }
  }

  const start = () => run(async () => {
    setSetup(await api.post<{ secret: string; qr_svg: string }>('/auth/2fa/setup'))
    setCode('')
  })

  const enable = () => run(async () => {
    const res = await api.post<{ recovery_codes: string[]; access_token: string }>('/auth/2fa/enable', { code: code.trim() })
    setSessionToken(res.access_token)  // las demás sesiones quedaron cerradas
    setRecovery(res.recovery_codes)
    setSetup(null); setCode('')
    updateUser({ totp_enabled: true })
    setMsg({ ok: true, text: 'Verificación en dos pasos activada.' })
  })

  const disable = () => run(async () => {
    const res = await api.post<{ access_token: string }>('/auth/2fa/disable', { password, code: code.trim() })
    setSessionToken(res.access_token)
    setPassword(''); setCode(''); setRecovery(null)
    updateUser({ totp_enabled: false })
    setMsg({ ok: true, text: 'Verificación en dos pasos desactivada.' })
  })

  return (
    <div className="bg-white rounded-xl shadow-sm border border-border p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest">Verificación en dos pasos</h3>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${enabled ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
          {enabled ? 'Activa' : 'Inactiva'}
        </span>
      </div>
      <p className="text-sm text-gray-600">
        Además de tu contraseña, al iniciar sesión se pedirá un código de 6 dígitos de una app de autenticación
        (Google Authenticator, Microsoft Authenticator, 1Password…). Recomendado: manejas datos de salud.
      </p>

      {recovery && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-amber-800 mb-2">Guarda tus códigos de recuperación</p>
          <p className="text-xs text-amber-700 mb-3">
            Sirven para entrar si pierdes el teléfono. Cada uno funciona una sola vez y no se volverán a mostrar.
          </p>
          <div className="grid grid-cols-2 gap-1 font-mono text-sm text-gray-800">
            {recovery.map(c => <span key={c}>{c}</span>)}
          </div>
          <button onClick={() => navigator.clipboard.writeText(recovery.join('\n'))}
            className="mt-3 text-xs font-semibold text-amber-800 hover:underline">Copiar códigos</button>
        </div>
      )}

      {!enabled && !setup && (
        <button onClick={start} disabled={busy}
          className="w-full bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium disabled:opacity-50">
          Activar verificación en dos pasos
        </button>
      )}

      {!enabled && setup && (
        <div className="space-y-3">
          <p className="text-sm text-gray-700">1. Escanea este código con tu app de autenticación:</p>
          <img alt="Código QR para la app de autenticación" className="mx-auto w-44 h-44"
            src={`data:image/svg+xml;base64,${btoa(setup.qr_svg)}`} />
          <p className="text-xs text-text-muted text-center">
            ¿No puedes escanear? Ingresa esta clave: <span className="font-mono text-gray-700 select-all">{setup.secret}</span>
          </p>
          <p className="text-sm text-gray-700">2. Escribe el código que muestra la app:</p>
          <div className="flex gap-2">
            <input value={code} onChange={e => setCode(e.target.value)} inputMode="numeric" placeholder="123456"
              className={`${INPUT} tracking-widest text-center`} />
            <button onClick={enable} disabled={busy || code.trim().length < 6}
              className="bg-primary text-white px-4 rounded-lg text-sm font-medium disabled:opacity-50">Activar</button>
          </div>
        </div>
      )}

      {enabled && (
        <div className="space-y-2">
          <p className="text-sm text-gray-700">Para desactivarla, confirma tu contraseña y un código vigente (o de recuperación):</p>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder="Contraseña" className={INPUT} />
          <input value={code} onChange={e => setCode(e.target.value)} placeholder="Código" className={INPUT} />
          <button onClick={disable} disabled={busy || !password || !code.trim()}
            className="w-full border border-red-200 text-red-600 hover:bg-red-50 px-4 py-2 rounded-lg font-medium disabled:opacity-50">
            Desactivar
          </button>
        </div>
      )}

      {msg && (
        <p className={`text-sm px-3 py-2 rounded-lg ${msg.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>{msg.text}</p>
      )}
    </div>
  )
}
