import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { isChunkLoadError, reloadForNewVersion } from './lazyPage'

describe('recarga tras publicar una versión nueva', () => {
  const reload = vi.fn()

  beforeEach(() => {
    sessionStorage.clear()
    reload.mockClear()
    vi.stubGlobal('location', { ...window.location, reload })
  })
  afterEach(() => vi.unstubAllGlobals())

  it('reconoce los errores de carga de archivos de la app', () => {
    expect(isChunkLoadError(new TypeError(
      'Failed to fetch dynamically imported module: https://x.vercel.app/assets/DashboardPage-Bw.js'))).toBe(true)
    expect(isChunkLoadError(new TypeError('Importing a module script failed.'))).toBe(true)
    expect(isChunkLoadError(new Error('Cannot read properties of undefined'))).toBe(false)
  })

  it('recarga una sola vez y no entra en bucle', () => {
    expect(reloadForNewVersion()).toBe(true)
    expect(reloadForNewVersion()).toBe(false)
    expect(reload).toHaveBeenCalledTimes(1)
  })
})
