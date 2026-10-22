/** Envía al backend los errores de JavaScript no controlados (registro interno). */
const MAX_REPORTS = 10
const sent = new Set<string>()

export function reportError(message: string, stack?: string) {
  const key = `${message}|${stack?.slice(0, 200) ?? ''}`
  if (sent.has(key) || sent.size >= MAX_REPORTS) return
  sent.add(key)
  const token = localStorage.getItem('token')
  fetch(`${import.meta.env.VITE_API_URL}/errors/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify({
      message: message.slice(0, 2000),
      stack: stack?.slice(0, 8000),
      path: window.location.pathname,
    }),
    keepalive: true,
  }).catch(() => { /* sin red: no hay dónde reportarlo */ })
}

export function installErrorReporting() {
  window.addEventListener('error', e => {
    reportError(e.message || 'Error de script', e.error instanceof Error ? e.error.stack : undefined)
  })
  window.addEventListener('unhandledrejection', e => {
    const r = e.reason
    // Los errores HTTP de axios ya se muestran al usuario y los registra el backend
    if (r && typeof r === 'object' && 'isAxiosError' in r) return
    reportError(r instanceof Error ? r.message : String(r), r instanceof Error ? r.stack : undefined)
  })
}
