import { describe, expect, it } from 'vitest'

import { formatDateTime } from '@/utils/format'

describe('formatDateTime', () => {
  it('returns dash for empty value', () => {
    expect(formatDateTime(null)).toBe('—')
    expect(formatDateTime(undefined)).toBe('—')
    expect(formatDateTime('')).toBe('—')
  })

  it('returns the original string for an invalid date', () => {
    expect(formatDateTime('not-a-date')).toBe('not-a-date')
  })

  it('formats a valid ISO date to YYYY-MM-DD HH:mm', () => {
    expect(formatDateTime('2026-11-24T10:30:00Z')).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/)
  })
})
