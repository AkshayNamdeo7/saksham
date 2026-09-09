export function formatINR(value: number | null | undefined, decimals = 0): string {
  if (value === null || value === undefined || isNaN(value)) return '₹0'
  return (
    '₹' +
    value.toLocaleString('en-IN', {
      maximumFractionDigits: decimals,
      minimumFractionDigits: 0,
    })
  )
}

export function formatLakh(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return '—'
  if (value >= 10000000) return `₹${(value / 10000000).toFixed(1).replace(/\.0$/, '')} crore`
  if (value >= 100000) return `₹${(value / 100000).toFixed(1).replace(/\.0$/, '')} lakh`
  return formatINR(value)
}

export function slugify(s: string): string {
  return s
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export function parseCurrencyInput(value: string): number | undefined {
  const cleaned = value.replace(/[₹,\s]/g, '')
  if (!/^\d+(\.\d+)?$/.test(cleaned)) return undefined
  return parseFloat(cleaned)
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1).replace(/\.0$/, '')}%`
}

export function tenureLabel(months: number): string {
  if (months >= 12 && months % 12 === 0) {
    const y = months / 12
    return `${y} ${y === 1 ? 'year' : 'years'}`
  }
  return `${months} months`
}

export function cls(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(' ')
}