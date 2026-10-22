import React, { createContext, useContext, useState, useEffect } from 'react'

interface User {
  id: number
  username: string
  email: string
  name?: string
  clinic_name?: string
  report_tagline?: string
  logo_base64?: string
  totp_enabled?: boolean
}

/** Resultado del primer paso del login cuando la cuenta tiene verificación en dos pasos. */
export interface TwoFactorChallenge { requires2fa: true; challenge: string }

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<TwoFactorChallenge | void>
  verifyTwoFactor: (challenge: string, code: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  updateUser: (updated: Partial<User>) => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Hidratar de forma síncrona: si se lee en useEffect, PrivateRoute ve token=null
  // en el primer render y redirige a /login al recargar cualquier página privada.
  const [user, setUser] = useState<User | null>(() => {
    const storedUser = localStorage.getItem('user')
    return storedUser && localStorage.getItem('token') ? JSON.parse(storedUser) : null
  })
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem('user') ? localStorage.getItem('token') : null
  )

  const fetchProfile = async (accessToken: string): Promise<User> => {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    if (!res.ok) throw new Error('Failed to fetch profile')
    return res.json()
  }

  // Load token from localStorage on mount and refresh profile from server
  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    if (storedToken && storedUser) {
      // Refresh from server to get latest branding fields
      fetchProfile(storedToken)
        .then(profile => {
          setUser(profile)
          localStorage.setItem('user', JSON.stringify(profile))
        })
        .catch(() => { /* token expired — leave as-is, PrivateRoute will redirect */ })
    }
  }, [])

  const login = async (username: string, password: string): Promise<TwoFactorChallenge | void> => {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })

    if (!response.ok) throw new Error(await errorDetail(response, 'Usuario o contraseña incorrectos'))

    const data = await response.json()
    if (data.requires_2fa) return { requires2fa: true, challenge: data.challenge_token }
    await startSession(data.access_token)
    return undefined
  }

  const verifyTwoFactor = async (challenge: string, code: string) => {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/2fa/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ challenge_token: challenge, code })
    })
    if (!response.ok) throw new Error(await errorDetail(response, 'Código incorrecto'))
    const data = await response.json()
    await startSession(data.access_token)
  }

  const startSession = async (accessToken: string) => {
    const profile = await fetchProfile(accessToken)
    setToken(accessToken)
    setUser(profile)
    localStorage.setItem('token', accessToken)
    localStorage.setItem('user', JSON.stringify(profile))
  }

  const errorDetail = async (response: Response, fallback: string) => {
    if (response.status === 401) return fallback
    const body = await response.json().catch(() => ({}))
    return typeof body.detail === 'string' ? body.detail : fallback
  }

  const register = async (username: string, email: string, password: string) => {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password })
    })

    if (!response.ok) throw new Error('Registration failed')

    const data = await response.json()
    const profile = await fetchProfile(data.access_token)
    setToken(data.access_token)
    setUser(profile)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(profile))
  }

  const updateUser = (updated: Partial<User>) => {
    setUser(prev => {
      if (!prev) return prev
      const next = { ...prev, ...updated }
      localStorage.setItem('user', JSON.stringify(next))
      return next
    })
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, verifyTwoFactor, register, logout, updateUser, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) throw new Error('useAuth must be used within AuthProvider')
  return context
}
