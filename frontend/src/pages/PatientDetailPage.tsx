import { useParams } from 'react-router-dom'
import Layout from '../components/Layout'

export default function PatientDetailPage() {
  const { id } = useParams()

  return (
    <Layout title="Detalle del Paciente">
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          {/* Tabs */}
          <div className="bg-white rounded-lg shadow">
            <div className="border-b border-border">
              <div className="flex">
                <button className="px-6 py-3 border-b-2 border-primary text-primary font-medium">
                  Información
                </button>
                <button className="px-6 py-3 text-gray-600 hover:text-primary">
                  ISAK
                </button>
                <button className="px-6 py-3 text-gray-600 hover:text-primary">
                  Planes
                </button>
                <button className="px-6 py-3 text-gray-600 hover:text-primary">
                  Pautas
                </button>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nombre</label>
                  <p className="mt-1 text-gray-600">Cargando...</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <p className="mt-1 text-gray-600">Cargando...</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-bold text-primary mb-4">Acciones Rápidas</h3>
            <div className="space-y-2">
              <button className="w-full bg-primary hover:bg-primary-dark text-white py-2 rounded text-sm">
                + ISAK
              </button>
              <button className="w-full bg-terracotta hover:opacity-90 text-white py-2 rounded text-sm">
                + Plan
              </button>
              <button className="w-full bg-sage hover:opacity-90 text-white py-2 rounded text-sm">
                + Pauta
              </button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
