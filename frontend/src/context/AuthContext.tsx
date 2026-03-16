import React, { createContext, useContext, useState, useEffect } from 'react'

interface User {
  id: number
  username: string
  email: string
  name?: string
  clinic_name?: string
  report_tagline?: string
  logo_base64?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  updateUser: (updated: Partial<User>) => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)

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
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
      // Refresh from server to get latest branding fields
      fetchProfile(storedToken)
        .then(profile => {
          setUser(profile)
          localStorage.setItem('user', JSON.stringify(profile))
        })
        .catch(() => { /* token expired — leave as-is, PrivateRoute will redirect */ })
    }
  }, [])

  const login = async (username: string, password: string) => {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })

    if (!response.ok) throw new Error('Login failed')

    const data = await response.json()
    const profile = await fetchProfile(data.access_token)
    setToken(data.access_token)
    setUser(profile)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(profile))
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
    <AuthContext.Provider value={{ user, token, login, register, logout, updateUser, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) throw new Error('useAuth must be used within AuthProvider')
  return context
}
