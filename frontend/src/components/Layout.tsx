import { useState } from 'react'
import { useNavigate, NavLink, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import NetworkErrorBanner from './NetworkErrorBanner'

interface LayoutProps {
  children: React.ReactNode
  title: string
}

const menuItems = [
  { label: 'Dashboard',     path: '/dashboard', icon: '⊞' },
  { label: 'Pacientes',     path: '/patients',  icon: '◉' },
  { label: 'Agenda',        path: '/agenda',    icon: '◷' },
  { label: 'Recetas',       path: '/recetas',   icon: '🍳' },
  { label: 'Configuración', path: '/config',    icon: '⊕' },
]

export default function Layout({ children, title }: LayoutProps) {
  const { logout, user } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const initials = (user?.name || user?.username || '?').slice(0, 2).toUpperCase()

  return (
    <div className="flex h-screen bg-bg-light">
      <NetworkErrorBanner />
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:relative inset-y-0 left-0 z-30
        w-64 bg-primary text-white shadow-lg flex-shrink-0 flex flex-col
        transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="p-6 pb-4">
          <h1 className="text-xl font-bold tracking-tight">NutriApp</h1>
          <p className="text-xs mt-0.5 text-white/50 uppercase tracking-widest">Gestión Nutricional</p>
        </div>

        <nav className="flex-1 px-3 py-2 space-y-0.5">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-primary-deep text-white font-semibold'
                    : 'text-white/70 hover:bg-white/10'
                }`
              }
            >
              <span className="text-base leading-none w-5 text-center">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-white/10">
          <Link
            to="/profile"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 transition-colors mb-1"
          >
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
              {initials}
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-semibold text-white truncate">{user?.name || user?.username}</p>
              <p className="text-xs text-white/50">Nutricionista Clínica</p>
            </div>
          </Link>
          <button
            onClick={handleLogout}
            className="w-full text-center text-xs text-white/40 hover:text-white/80 py-1 transition-colors"
          >
            Cerrar sesión
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto min-w-0">
        {/* Top bar */}
        <div className="bg-white border-b border-border sticky top-0 z-10">
          <div className="px-4 md:px-8 py-4 flex items-center gap-4">
            {/* Hamburger — only on mobile */}
            <button
              className="lg:hidden flex flex-col gap-1.5 p-1 -ml-1"
              onClick={() => setSidebarOpen(true)}
              aria-label="Abrir menú"
            >
              <span className="w-5 h-0.5 bg-gray-600 rounded"></span>
              <span className="w-5 h-0.5 bg-gray-600 rounded"></span>
              <span className="w-5 h-0.5 bg-gray-600 rounded"></span>
            </button>
            <h2 className="text-xl font-bold text-gray-800">{title}</h2>
          </div>
        </div>

        {/* Page content */}
        <div className="p-4 md:p-8">
          {children}
        </div>
      </div>
    </div>
  )
}
