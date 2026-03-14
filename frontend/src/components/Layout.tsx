import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface LayoutProps {
  children: React.ReactNode
  title: string
}

export default function Layout({ children, title }: LayoutProps) {
  const { logout, user } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const menuItems = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Pacientes', path: '/patients' },
    { label: 'ISAK', path: '/isak' },
    { label: 'Planes', path: '/plans' },
    { label: 'Pautas', path: '/pautas' },
    { label: 'Reportes', path: '/reports' },
  ]

  return (
    <div className="flex h-screen bg-bg-light">
      {/* Sidebar */}
      <div className="w-64 bg-primary text-white shadow-lg">
        <div className="p-6">
          <h1 className="text-2xl font-bold">NutriApp</h1>
          <p className="text-sm text-primary-dark mt-1">Gestión Nutricional</p>
        </div>

        <nav className="mt-8">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className="block px-6 py-3 hover:bg-primary-dark transition-colors text-sm"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-primary-dark">
          <button
            onClick={handleLogout}
            className="w-full bg-terracotta hover:bg-opacity-90 text-white py-2 rounded text-sm"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        {/* Top navbar */}
        <div className="bg-white shadow sticky top-0 z-10">
          <div className="px-8 py-4 flex justify-between items-center">
            <h2 className="text-2xl font-bold text-primary">{title}</h2>
            <div className="text-sm text-gray-600">
              {user?.username}
            </div>
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
