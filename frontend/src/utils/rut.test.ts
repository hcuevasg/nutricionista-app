import { describe, expect, it } from 'vitest'
import { computeDv, formatRut, isValidRut } from './rut'

describe('rut (módulo 11)', () => {
  it('calcula el dígito verificador', () => {
    expect(computeDv('12345678')).toBe('5')
    expect(computeDv('7775315')).toBe('K')
    expect(computeDv('5126663')).toBe('3')
  })

  it('valida RUT con o sin formato', () => {
    expect(isValidRut('12.345.678-5')).toBe(true)
    expect(isValidRut('123456785')).toBe(true)
    expect(isValidRut('7.775.315-k')).toBe(true)
    expect(isValidRut('12.345.678-6')).toBe(false)
    expect(isValidRut('1-9')).toBe(false)
    expect(isValidRut('')).toBe(false)
  })

  it('formatea mientras se escribe', () => {
    expect(formatRut('123456785')).toBe('12.345.678-5')
    expect(formatRut('7775315k')).toBe('7.775.315-K')
    expect(formatRut('1')).toBe('1')
  })
})
