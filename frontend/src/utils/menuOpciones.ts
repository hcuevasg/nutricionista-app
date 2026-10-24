/**
 * Formatos de menú por tiempo de comida que conviven en menu_json:
 *  - Antiguo:     { opcion1: "texto", opcion2: "texto" }
 *  - IA:          { opcion1: MenuItem[], opcion2: MenuItem[] }      (gramos y nutrientes)
 *  - Planilla:    { opciones: [{ plato, lineas: [{ porcion, texto }] }] }
 *    (pautas importadas de las planillas Excel de la nutricionista: N opciones,
 *     nombre del plato y alimentos en texto con medida casera)
 */

export interface LineaPlanilla {
  porcion?: string   // "1 Cereal", "3 A. Proteicos"
  texto: string      // "2 Reb pan molde Castaños"
}

export interface OpcionPlanilla {
  plato?: string
  lineas: LineaPlanilla[]
}

/** Una opción lista para mostrar, venga del formato que venga. */
export interface OpcionVista {
  titulo?: string
  lineas: { izquierda: string; derecha?: string }[]
}

export function isPlanillaEntry(entry: unknown): entry is { opciones: OpcionPlanilla[] } {
  return !!entry && typeof entry === 'object' && Array.isArray((entry as { opciones?: unknown }).opciones)
}

/** true si el menú completo usa el formato de planilla. */
export function isPlanillaMenu(menu: unknown): boolean {
  if (!menu || typeof menu !== 'object') return false
  const entries = Object.values(menu as object)
  return entries.length > 0 && entries.some(isPlanillaEntry)
}

export function opcionesParaMostrar(entry: unknown): OpcionVista[] {
  if (!entry || typeof entry !== 'object') return []
  if (isPlanillaEntry(entry)) {
    return entry.opciones.map((o) => ({
      titulo: o.plato || undefined,
      lineas: o.lineas.filter((l) => l.texto?.trim()).map((l) => ({ izquierda: l.texto, derecha: l.porcion })),
    }))
  }
  const e = entry as Record<string, unknown>
  return (['opcion1', 'opcion2'] as const)
    .map((k) => e[k])
    .filter((op) => op && (typeof op === 'string' ? op.trim() : Array.isArray(op) && op.length))
    .map((op) =>
      typeof op === 'string'
        ? { lineas: op.split('\n').filter(Boolean).map((t) => ({ izquierda: t })) }
        : {
            lineas: (op as Record<string, unknown>[]).map((it) => ({
              izquierda: String(it.nombre ?? it.alimento ?? ''),
              derecha: `${it.cantidad ?? ''}${it.unidad ?? it.medida ?? ''}`.trim() || undefined,
            })),
          },
    )
}
