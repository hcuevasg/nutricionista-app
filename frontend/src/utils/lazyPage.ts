import { lazy, type ComponentType } from 'react'

const RELOAD_KEY = 'nutriapp:chunk-reload-at'

/** Error de carga de un archivo de la app (normalmente tras publicar una versión nueva). */
export function isChunkLoadError(err: unknown): boolean {
  const msg = err instanceof Error ? err.message : String(err)
  return /dynamically imported module|Importing a module script failed|error loading dynamically imported module|Unable to preload CSS/i.test(msg)
}

/**
 * Recarga la página una vez para tomar la versión nueva. Si ya se recargó hace
 * menos de 30 s no lo repite (evita un bucle si el problema es otro, p. ej. sin red).
 * Devuelve true si va a recargar.
 */
export function reloadForNewVersion(): boolean {
  try {
    const last = Number(sessionStorage.getItem(RELOAD_KEY) || 0)
    if (Date.now() - last < 30_000) return false
    sessionStorage.setItem(RELOAD_KEY, String(Date.now()))
  } catch {
    return false
  }
  window.location.reload()
  return true
}

/**
 * Como React.lazy, pero si el archivo de la página ya no existe porque se
 * publicó una versión nueva mientras la app estaba abierta, recarga la página
 * en vez de mostrar un error.
 */
export function lazyPage<T extends ComponentType<any>>(factory: () => Promise<{ default: T }>) {
  return lazy(() =>
    factory().catch((err) => {
      if (isChunkLoadError(err) && reloadForNewVersion()) {
        return new Promise<{ default: T }>(() => {})   // la página se está recargando
      }
      throw err
    }),
  )
}
