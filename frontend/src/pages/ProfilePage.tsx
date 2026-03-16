import { useState, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'

const INPUT = 'w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary'

export default function ProfilePage() {
  const { token, user, updateUser } = useAuth()
  const API = import.meta.env.VITE_API_URL
  const H = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  const [name, setName] = useState(user?.name ?? user?.username ?? '')
  const [email, setEmail] = useState(user?.email ?? '')
  const [profileMsg, setProfileMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [savingProfile, setSavingProfile] = useState(false)

  // Branding
  const [clinicName, setClinicName] = useState(user?.clinic_name ?? '')
  const [reportTagline, setReportTagline] = useState(user?.report_tagline ?? '')
  const [logoBase64, setLogoBase64] = useState<string>(user?.logo_base64 ?? '')
  const [brandMsg, setBrandMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [savingBrand, setSavingBrand] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 500 * 1024) {
      setBrandMsg({ ok: false, text: 'El logo no puede superar 500 KB' })
      return
    }
    const reader = new FileReader()
    reader.onload = () => setLogoBase64(reader.result as string)
    reader.readAsDataURL(file)
  }

  const handleBrand = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingBrand(true); setBrandMsg(null)
    try {
      const body: Record<string, string | null> = {
        clinic_name: clinicName || null,
        report_tagline: reportTagline || null,
        logo_base64: logoBase64 || null,
      }
      const res = await fetch(`${API}/auth/profile`, {
        method: 'PUT', headers: H, body: JSON.stringify(body),
      })
      const d = await res.json()
      if (!res.ok) throw new Error(d.detail ?? `Error ${res.status}`)
      updateUser({ clinic_name: d.clinic_name, report_tagline: d.report_tagline, logo_base64: d.logo_base64 })
      setBrandMsg({ ok: true, text: 'Marca actualizada correctamente' })
    } catch (err) {
      setBrandMsg({ ok: false, text: err instanceof Error ? err.message : 'Error al guardar' })
    } finally {
      setSavingBrand(false)
    }
  }

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
      <div className="max-w-lg mx-auto space-y-6">

        {/* Datos del perfil */}
        <form onSubmit={handleProfile} className="bg-white rounded-xl shadow-sm border border-border p-6 space-y-4">
          <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest border-b border-border pb-3">Datos del Perfil</h3>

          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Usuario</label>
            <input value={user?.username ?? ''} disabled className={`${INPUT} bg-bg-light text-text-muted`} />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Nombre</label>
            <input value={name} onChange={e => setName(e.target.value)} className={INPUT} placeholder="Tu nombre completo" />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} className={INPUT} />
          </div>

          {profileMsg && (
            <p className={`text-sm px-3 py-2 rounded-lg ${profileMsg.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
              {profileMsg.text}
            </p>
          )}
          <button type="submit" disabled={savingProfile}
            className="w-full bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium disabled:opacity-50">
            {savingProfile ? 'Guardando...' : 'Guardar cambios'}
          </button>
        </form>

        {/* Marca del consultorio */}
        <form onSubmit={handleBrand} className="bg-white rounded-xl shadow-sm border border-border p-6 space-y-4">
          <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest border-b border-border pb-3">Marca del Consultorio</h3>
          <p className="text-xs text-text-muted">Esta información aparecerá en el encabezado de los informes exportados.</p>

          {/* Logo upload */}
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Logo</label>
            <div className="flex items-center gap-4">
              {logoBase64 ? (
                <img src={logoBase64} alt="Logo" className="h-16 w-auto max-w-[160px] object-contain rounded-lg border border-border" />
              ) : (
                <div className="h-16 w-16 rounded-lg border-2 border-dashed border-border flex items-center justify-center text-text-muted">
                  <span className="material-symbols-outlined text-2xl">add_photo_alternate</span>
                </div>
              )}
              <div className="flex flex-col gap-2">
                <button type="button" onClick={() => fileInputRef.current?.click()}
                  className="text-sm text-primary font-medium hover:underline text-left">
                  {logoBase64 ? 'Cambiar logo' : 'Subir logo'}
                </button>
                {logoBase64 && (
                  <button type="button" onClick={() => setLogoBase64('')}
                    className="text-sm text-red-500 hover:underline text-left">
                    Eliminar logo
                  </button>
                )}
                <span className="text-xs text-text-muted">PNG, JPG. Máx. 500 KB</span>
              </div>
            </div>
            <input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/webp"
              className="hidden" onChange={handleLogoChange} />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Nombre del consultorio</label>
            <input value={clinicName} onChange={e => setClinicName(e.target.value)}
              className={INPUT} placeholder="Ej: Consultorio Nutrición Integral" />
            <p className="text-xs text-text-muted mt-1">Si no hay logo, este nombre aparecerá en el informe.</p>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Eslogan / Frase</label>
            <input value={reportTagline} onChange={e => setReportTagline(e.target.value)}
              className={INPUT} placeholder="Ej: Nutricionista — RUT 12.345.678-9" />
            <p className="text-xs text-text-muted mt-1">Aparecerá como subtítulo en el encabezado del informe.</p>
          </div>

          {/* Preview */}
          {(logoBase64 || clinicName || reportTagline) && (
            <div className="rounded-lg overflow-hidden border border-primary/20">
              <div className="text-xs font-bold text-text-muted uppercase tracking-widest px-3 py-2 bg-bg-light border-b border-border">
                Vista previa del encabezado
              </div>
              <div className="bg-primary px-5 py-4 flex items-center gap-3">
                {logoBase64 ? (
                  <img src={logoBase64} alt="Logo" className="h-12 w-auto max-w-[120px] object-contain rounded-lg bg-white/10 p-1" />
                ) : (
                  <div className="bg-white/20 p-2 rounded-lg">
                    <span className="material-symbols-outlined text-white text-3xl">monitoring</span>
                  </div>
                )}
                <div>
                  <p className="text-white font-black text-xl tracking-tight">
                    {clinicName || user?.name || user?.username}
                  </p>
                  {reportTagline && (
                    <p className="text-white/80 text-xs font-semibold uppercase tracking-widest mt-0.5">
                      {reportTagline}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {brandMsg && (
            <p className={`text-sm px-3 py-2 rounded-lg ${brandMsg.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
              {brandMsg.text}
            </p>
          )}
          <button type="submit" disabled={savingBrand}
            className="w-full bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium disabled:opacity-50">
            {savingBrand ? 'Guardando...' : 'Guardar marca'}
          </button>
        </form>

        {/* Divider */}
        <div className="border-t border-border my-4" />

        {/* Cambiar contraseña */}
        <form onSubmit={handlePassword} className="bg-white rounded-xl shadow-sm border border-border p-6 space-y-4">
          <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest border-b border-border pb-3">Cambiar Contraseña</h3>

          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Contraseña actual</label>
            <input type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)}
              required className={INPUT} />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Nueva contraseña</label>
            <input type="password" value={newPw} onChange={e => setNewPw(e.target.value)}
              required minLength={6} className={INPUT} />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Confirmar nueva contraseña</label>
            <input type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)}
              required className={INPUT} />
          </div>

          {pwMsg && (
            <p className={`text-sm px-3 py-2 rounded-lg ${pwMsg.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
              {pwMsg.text}
            </p>
          )}
          <button type="submit" disabled={savingPw}
            className="w-full bg-terracotta hover:opacity-90 text-white px-4 py-2 rounded-lg font-medium disabled:opacity-50">
            {savingPw ? 'Guardando...' : 'Cambiar contraseña'}
          </button>
        </form>

      </div>
    </Layout>
  )
}
