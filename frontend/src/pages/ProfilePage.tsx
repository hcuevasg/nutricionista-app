import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

const INPUT = 'w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary'

export default function ProfilePage() {
  const { token, user } = useAuth()
  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  const [name, setName] = useState(user?.name ?? user?.username ?? '')
  const [email, setEmail] = useState(user?.email ?? '')
  const [profileMsg, setProfileMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [savingProfile, setSavingProfile] = useState(false)

  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [pwMsg, setPwMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [savingPw, setSavingPw] = useState(false)

  const handleProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingProfile(true); setProfileMsg(null)
    try {
      const res = await fetch(`${API}/auth/profile`, {
        method: 'PUT', headers: H, body: JSON.stringify({ name, email }),
      })
      const d = await res.json()
      if (!res.ok) throw new Error(d.detail ?? `Error ${res.status}`)
      setProfileMsg({ ok: true, text: 'Perfil actualizado correctamente' })
    } catch (err) {
      setProfileMsg({ ok: false, text: err instanceof Error ? err.message : 'Error al guardar' })
    } finally {
      setSavingProfile(false)
    }
  }

  const handlePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (newPw !== confirmPw) { setPwMsg({ ok: false, text: 'Las contraseñas no coinciden' }); return }
    setSavingPw(true); setPwMsg(null)
    try {
      const res = await fetch(`${API}/auth/password`, {
        method: 'PUT', headers: H,
        body: JSON.stringify({ current_password: currentPw, new_password: newPw }),
      })
      const d = await res.json()
      if (!res.ok) throw new Error(d.detail ?? `Error ${res.status}`)
      setPwMsg({ ok: true, text: 'Contraseña actualizada correctamente' })
      setCurrentPw(''); setNewPw(''); setConfirmPw('')
    } catch (err) {
      setPwMsg({ ok: false, text: err instanceof Error ? err.message : 'Error al cambiar contraseña' })
    } finally {
      setSavingPw(false)
    }
  }

  return (
    <Layout title="Mi Perfil">
      <div className="max-w-lg space-y-6">

        {/* Datos del perfil */}
        <form onSubmit={handleProfile} className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">Datos del Perfil</h3>

          <div>
            <label className="block text-xs text-text-muted mb-1">Usuario</label>
            <input value={user?.username ?? ''} disabled className={`${INPUT} bg-bg-light text-text-muted`} />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">Nombre</label>
            <input value={name} onChange={e => setName(e.target.value)} className={INPUT} placeholder="Tu nombre completo" />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} className={INPUT} />
          </div>

          {profileMsg && (
            <p className={`text-sm px-3 py-2 rounded ${profileMsg.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
              {profileMsg.text}
            </p>
          )}
          <button type="submit" disabled={savingProfile}
            className="w-full bg-primary hover:bg-primary-dark text-white py-2 rounded-lg text-sm font-medium disabled:opacity-50">
            {savingProfile ? 'Guardando...' : 'Guardar cambios'}
          </button>
        </form>

        {/* Cambiar contraseña */}
        <form onSubmit={handlePassword} className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-sm font-bold text-primary uppercase tracking-wide border-b border-border pb-2">Cambiar Contraseña</h3>

          <div>
            <label className="block text-xs text-text-muted mb-1">Contraseña actual</label>
            <input type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)}
              required className={INPUT} />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">Nueva contraseña</label>
            <input type="password" value={newPw} onChange={e => setNewPw(e.target.value)}
              required minLength={6} className={INPUT} />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">Confirmar nueva contraseña</label>
            <input type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)}
              required className={INPUT} />
          </div>

          {pwMsg && (
            <p className={`text-sm px-3 py-2 rounded ${pwMsg.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
              {pwMsg.text}
            </p>
          )}
          <button type="submit" disabled={savingPw}
            className="w-full bg-terracotta hover:opacity-90 text-white py-2 rounded-lg text-sm font-medium disabled:opacity-50">
            {savingPw ? 'Guardando...' : 'Cambiar contraseña'}
          </button>
        </form>

      </div>
    </Layout>
  )
}
