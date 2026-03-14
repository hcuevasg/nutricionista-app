import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'

interface Patient {
  id: number
  name: string
  email?: string
  phone?: string
}

export default function PatientsPage() {
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/patients`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.status === 401) {
          logout()
          navigate('/login')
          return
        }

        if (!response.ok) {
          throw new Error(`Error ${response.status}`)
        }

        const data = await response.json()
        setPatients(Array.isArray(data) ? data : [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al cargar pacientes')
      } finally {
        setLoading(false)
      }
    }

    if (token) {
      fetchPatients()
    }
  }, [token, logout, navigate])

  return (
    <Layout title="Pacientes">
      <div className="flex justify-between items-center mb-6">
        <div>
          <input
            type="text"
            placeholder="Buscar pacientes..."
            className="px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <button className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg">
          + Nuevo Paciente
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-bg-light border-b border-border">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Nombre</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Email</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Teléfono</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr className="border-b border-border hover:bg-bg-light">
                <td colSpan={4} className="px-6 py-4 text-sm text-gray-700 text-center">
                  Cargando...
                </td>
              </tr>
            ) : patients.length === 0 ? (
              <tr className="border-b border-border hover:bg-bg-light">
                <td colSpan={4} className="px-6 py-4 text-sm text-gray-700 text-center">
                  No hay pacientes registrados
                </td>
              </tr>
            ) : (
              patients.map((patient) => (
                <tr key={patient.id} className="border-b border-border hover:bg-bg-light">
                  <td className="px-6 py-4 text-sm text-gray-700">{patient.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{patient.email || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{patient.phone || '-'}</td>
                  <td className="px-6 py-4 text-sm">
                    <button className="text-primary hover:underline">Ver</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
