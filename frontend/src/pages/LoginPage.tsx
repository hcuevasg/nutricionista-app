import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [challenge, setChallenge] = useState<string | null>(null)
  const [code, setCode] = useState('')
  const { login, verifyTwoFactor } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (challenge) {
        await verifyTwoFactor(challenge, code.trim())
        navigate('/dashboard')
        return
      }
      const result = await login(username, password)
      if (result?.requires2fa) {
        setChallenge(result.challenge)
        return
      }
      navigate('/dashboard')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'No se pudo iniciar sesión'
      if (challenge && msg.includes('expir')) { setChallenge(null); setCode('') }
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary to-primary-deep">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h1 className="text-3xl font-bold text-center text-primary mb-8">NutriApp</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            {challenge ? (
              <div>
                <p className="text-sm text-gray-600 mb-3">
                  Ingresa el código de 6 dígitos de tu app de autenticación, o uno de tus códigos de recuperación.
                </p>
                <label className="block text-sm font-medium text-gray-700 mb-2">Código de verificación</label>
                <input
                  type="text" inputMode="numeric" autoComplete="one-time-code" autoFocus
                  value={code} onChange={(e) => setCode(e.target.value)}
                  className="w-full px-4 py-2 border border-border rounded-lg tracking-widest text-center text-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="123456" required
                />
                <button type="button" onClick={() => { setChallenge(null); setCode(''); setError('') }}
                  className="mt-2 text-xs text-text-muted hover:text-primary">
                  ← Volver
                </button>
              </div>
            ) : (<>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Usuario
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Contraseña
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                required
              />
            </div>
            </>)}

            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary hover:bg-primary-dark text-white font-medium py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              {loading ? 'Verificando...' : challenge ? 'Verificar' : 'Ingresar'}
            </button>
          </form>

          <p className="mt-6 text-center text-gray-600">
            ¿No tienes cuenta?{' '}
            <Link to="/register" className="text-primary hover:underline font-medium">
              Registrate aquí
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
