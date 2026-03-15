import { useNavigate, NavLink, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface LayoutProps {
  children: React.ReactNode
  title: string
}

const menuItems = [
  { label: 'Dashboard',     path: '/dashboard', icon: '⊞' },
  { label: 'Pacientes',     path: '/patients',  icon: '👥' },
  { label: 'Evaluaciones',  path: '/isak',      icon: '📏' },
  { label: 'Planes',        path: '/plans',     icon: '🥗' },
  { label: 'Pautas',        path: '/pautas',    icon: '📋' },
  { label: 'Configuración', path: '/config',    icon: '⚙️'  },
]

export default function Layout({ children, title }: LayoutProps) {
  const { logout, user } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-bg-light">
      {/* Sidebar */}
      <div className="relative w-60 bg-primary text-white shadow-lg flex-shrink-0 flex flex-col">
        <div className="p-6 pb-4">
          <h1 className="text-xl font-bold tracking-tight">NutriApp</h1>
          <p className="text-xs mt-0.5 opacity-60">Gestión Nutricional</p>
        </div>

        <nav className="flex-1 px-3 py-2 space-y-0.5">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-white/20 font-semibold text-white'
                    : 'text-white/75 hover:bg-white/10 hover:text-white'
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
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-white/75 hover:bg-white/10 hover:text-white transition-colors mb-2"
          >
            <div className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center text-xs font-bold">
              {(user?.name || user?.username || '?').slice(0, 1).toUpperCase()}
            </div>
            <span className="truncate">{user?.name || user?.username}</span>
          </Link>
          <button
            onClick={handleLogout}
            className="w-full text-center text-xs text-white/50 hover:text-white/90 py-1 transition-colors"
          >
            Cerrar sesión
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        {/* Top bar */}
        <div className="bg-white border-b border-border sticky top-0 z-10">
          <div className="px-8 py-4">
            <h2 className="text-xl font-bold text-gray-800">{title}</h2>
          </div>
        </div>

        {/* Page content */}
        <div className="p-8">
          {children}
        </div>
      </div>
    </div>
  )
}
