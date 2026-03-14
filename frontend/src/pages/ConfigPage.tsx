import Layout from '../components/Layout'

export default function ConfigPage() {
  return (
    <Layout title="Configuración">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-primary mb-4">Perfil</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Usuario</label>
              <input type="text" disabled className="mt-1 w-full px-4 py-2 border border-border rounded-lg bg-gray-100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input type="email" disabled className="mt-1 w-full px-4 py-2 border border-border rounded-lg bg-gray-100" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-primary mb-4">Cambiar Contraseña</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Contraseña Actual</label>
              <input type="password" className="mt-1 w-full px-4 py-2 border border-border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Nueva Contraseña</label>
              <input type="password" className="mt-1 w-full px-4 py-2 border border-border rounded-lg" />
            </div>
            <button className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg">
              Actualizar
            </button>
          </div>
        </div>
      </div>
    </Layout>
  )
}
