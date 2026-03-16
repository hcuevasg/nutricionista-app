import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useToast } from '../context/ToastContext'
import Layout from '../components/Layout'
import { api } from '../api/client'

interface Receta {
  id: number
  nombre: string
  categoria: string
  porciones_rinde: number
  descripcion?: string
  created_at: string
}

interface PaginatedRecetas {
  items: Receta[]
  total: number
  skip: number
  limit: number
}

const CATEGORIAS = ['Todas', 'General', 'Desayuno', 'Almuerzo', 'Cena', 'Colación', 'Postre', 'Snack', 'Bebida', 'Vegetariano', 'Vegano']
const PAGE_SIZE = 50

export default function RecetasPage() {
  const toast = useToast()
  const navigate = useNavigate()
  const [recetas, setRecetas] = useState<Receta[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [q, setQ] = useState('')
  const [catFiltro, setCatFiltro] = useState('Todas')
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const load = async (skip = 0, search = '') => {
    try {
      const params: Record<string, string | number> = { skip, limit: PAGE_SIZE }
      if (search.trim()) params.q = search.trim()
      const data = await api.get<PaginatedRecetas>('/recetas/', params)
      if (skip === 0) {
        setRecetas(data.items)
      } else {
        setRecetas(prev => [...prev, ...data.items])
      }
      setTotal(data.total)
    } catch {
      toast.error('Error al cargar recetas')
    }
  }

  useEffect(() => {
    setLoading(true)
    load(0, q).finally(() => setLoading(false))
  }, [q]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleLoadMore = async () => {
    setLoadingMore(true)
    await load(recetas.length, q)
    setLoadingMore(false)
  }

  const handleDelete = async (id: number, nombre: string) => {
    if (!confirm(`¿Eliminar la receta "${nombre}"? Esta acción no se puede deshacer.`)) return
    setDeletingId(id)
    try {
      await api.delete(`/recetas/${id}`)
      toast.success('Receta eliminada')
      setRecetas(prev => prev.filter(r => r.id !== id))
      setTotal(prev => prev - 1)
    } catch {
      toast.error('Error al eliminar receta')
    } finally {
      setDeletingId(null)
    }
  }

  const filtered = catFiltro === 'Todas' ? recetas : recetas.filter(r => r.categoria === catFiltro)
  const hasMore = recetas.length < total

  return (
    <Layout title="Recetas">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-6">
        <div className="flex-1">
          <p className="text-sm text-gray-500 mt-1">
            Crea y gestiona tus recetas con ingredientes, aporte nutricional y equivalencias por porción.
          </p>
        </div>
        <Link
          to="/recetas/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white text-sm font-semibold rounded-lg hover:bg-primary-dark transition-colors"
        >
          + Nueva Receta
        </Link>
      </div>

      {/* Filtros */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <input
          type="text"
          placeholder="Buscar receta…"
          value={q}
          onChange={e => setQ(e.target.value)}
          className="flex-1 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <select
          value={catFiltro}
          onChange={e => setCatFiltro(e.target.value)}
          className="border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {CATEGORIAS.map(c => <option key={c}>{c}</option>)}
        </select>
      </div>

      {/* Lista */}
      {loading ? (
        <div className="text-center py-16 text-gray-400">Cargando recetas…</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-5xl mb-4">🍳</div>
          <p className="text-gray-500 font-medium">
            {q || catFiltro !== 'Todas' ? 'Sin resultados para tu búsqueda.' : 'Aún no tienes recetas guardadas.'}
          </p>
          {!q && catFiltro === 'Todas' && (
            <Link to="/recetas/new" className="mt-4 inline-block text-primary text-sm font-semibold hover:underline">
              Crear primera receta →
            </Link>
          )}
        </div>
      ) : (
        <>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(r => (
            <div
              key={r.id}
              className="bg-white border border-border rounded-xl p-5 hover:shadow-md transition-shadow flex flex-col gap-3"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-gray-800 leading-tight">{r.nombre}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                      {r.categoria}
                    </span>
                    <span className="text-xs text-gray-400">
                      {r.porciones_rinde} porción{r.porciones_rinde !== 1 ? 'es' : ''}
                    </span>
                  </div>
                </div>
              </div>
              {r.descripcion && (
                <p className="text-sm text-gray-500 line-clamp-2">{r.descripcion}</p>
              )}
              <div className="flex gap-2 mt-auto pt-2 border-t border-border">
                <button
                  onClick={() => navigate(`/recetas/${r.id}/edit`)}
                  className="flex-1 text-sm text-primary font-medium hover:underline text-left"
                >
                  Ver / Editar
                </button>
                <button
                  onClick={() => handleDelete(r.id, r.nombre)}
                  disabled={deletingId === r.id}
                  className="text-sm text-terracotta hover:underline disabled:opacity-50"
                >
                  {deletingId === r.id ? '…' : 'Eliminar'}
                </button>
              </div>
            </div>
          ))}
        </div>
        {hasMore && catFiltro === 'Todas' && (
          <div className="mt-6 text-center">
            <button
              onClick={handleLoadMore}
              disabled={loadingMore}
              className="px-5 py-2 border border-primary text-primary rounded-lg text-sm font-medium hover:bg-primary/5 disabled:opacity-50"
            >
              {loadingMore ? 'Cargando...' : `Cargar más (${total - recetas.length} restantes)`}
            </button>
          </div>
        )}
        </>
      )}
    </Layout>
  )
}
