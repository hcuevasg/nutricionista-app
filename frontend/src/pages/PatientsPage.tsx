import Layout from '../components/Layout'

export default function PatientsPage() {
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
            <tr className="border-b border-border hover:bg-bg-light">
              <td className="px-6 py-4 text-sm text-gray-700">Cargando...</td>
              <td className="px-6 py-4 text-sm text-gray-700"></td>
              <td className="px-6 py-4 text-sm text-gray-700"></td>
              <td className="px-6 py-4 text-sm">
                <button className="text-primary hover:underline">Ver</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
