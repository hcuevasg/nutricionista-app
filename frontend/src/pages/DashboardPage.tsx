import Layout from '../components/Layout'

export default function DashboardPage() {
  return (
    <Layout title="Dashboard">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Stats Cards */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium">Total Pacientes</h3>
          <p className="text-3xl font-bold text-primary mt-2">--</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium">Evaluaciones Recientes</h3>
          <p className="text-3xl font-bold text-terracotta mt-2">--</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium">Planes Activos</h3>
          <p className="text-3xl font-bold text-sage mt-2">--</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium">Pautas</h3>
          <p className="text-3xl font-bold text-primary-dark mt-2">--</p>
        </div>
      </div>

      <div className="mt-12">
        <h2 className="text-2xl font-bold text-primary mb-6">Actividad Reciente</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-6 text-center text-gray-500">
            <p>No hay actividad registrada</p>
          </div>
        </div>
      </div>
    </Layout>
  )
}
