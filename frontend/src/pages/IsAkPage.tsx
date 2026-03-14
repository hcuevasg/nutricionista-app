import { useParams } from 'react-router-dom'
import Layout from '../components/Layout'

export default function IsAkPage() {
  const { id } = useParams()

  return (
    <Layout title="ISAK - Evaluación Antropométrica">
      <div className="bg-white rounded-lg shadow p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-lg font-bold text-primary mb-4">ISAK 1</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Edad</label>
                <input type="number" className="mt-1 w-full px-3 py-2 border border-border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Sexo</label>
                <select className="mt-1 w-full px-3 py-2 border border-border rounded-lg">
                  <option>Masculino</option>
                  <option>Femenino</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Peso (kg)</label>
                <input type="number" className="mt-1 w-full px-3 py-2 border border-border rounded-lg" />
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-bold text-primary mb-4">Pliegues (mm)</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Triceps</label>
                <input type="number" className="mt-1 w-full px-3 py-2 border border-border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Subscapular</label>
                <input type="number" className="mt-1 w-full px-3 py-2 border border-border rounded-lg" />
              </div>
            </div>
          </div>
        </div>

        <button className="mt-8 bg-primary hover:bg-primary-dark text-white px-6 py-2 rounded-lg">
          Guardar Evaluación
        </button>
      </div>
    </Layout>
  )
}
