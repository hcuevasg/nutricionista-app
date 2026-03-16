import { useEffect, useState } from 'react'

export default function NetworkErrorBanner() {
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<string>).detail
      setMessage(detail)
      // Auto-dismiss after 5 seconds
      setTimeout(() => setMessage(null), 5000)
    }
    window.addEventListener('api-network-error', handler)
    return () => window.removeEventListener('api-network-error', handler)
  }, [])

  if (!message) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between gap-3 bg-red-600 text-white px-4 py-2.5 text-sm shadow-lg">
      <span>⚠ {message}</span>
      <button
        onClick={() => setMessage(null)}
        className="text-white/80 hover:text-white font-bold text-lg leading-none"
        aria-label="Cerrar"
      >
        ×
      </button>
    </div>
  )
}
