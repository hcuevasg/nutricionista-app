/** RUT chileno: dígito verificador por módulo 11 (mismo algoritmo que el backend, rut.py). */

/** Deja solo dígitos y K: "12.345.678-k" → "12345678K". */
export function cleanRut(value: string): string {
  return value.replace(/[^0-9kK]/g, '').toUpperCase()
}

/** Dígito verificador del cuerpo del RUT (serie 2..7 de derecha a izquierda). */
export function computeDv(body: string): string {
  let total = 0
  let factor = 2
  for (let i = body.length - 1; i >= 0; i--) {
    total += Number(body[i]) * factor
    factor = factor === 7 ? 2 : factor + 1
  }
  const dv = 11 - (total % 11)
  return dv === 11 ? '0' : dv === 10 ? 'K' : String(dv)
}

/** true si el RUT tiene un dígito verificador correcto y un largo razonable. */
export function isValidRut(value: string): boolean {
  const raw = cleanRut(value)
  if (raw.length < 2) return false
  const body = raw.slice(0, -1)
  if (!/^\d+$/.test(body)) return false
  const n = Number(body)
  return n >= 100_000 && n <= 99_999_999 && computeDv(String(n)) === raw.slice(-1)
}

/** Formato con puntos y guion mientras se escribe: "123456785" → "12.345.678-5". */
export function formatRut(value: string): string {
  const raw = cleanRut(value).slice(0, 9)
  if (raw.length < 2) return raw
  const body = raw.slice(0, -1).replace(/^0+/, '')
  return `${body.replace(/\B(?=(\d{3})+(?!\d))/g, '.')}-${raw.slice(-1)}`
}
