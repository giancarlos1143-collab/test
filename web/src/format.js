export function money(n) {
  if (n == null) return '—'
  const a = Math.abs(n)
  if (a >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (a >= 1e6) return `$${(n / 1e6).toFixed(a >= 1e7 ? 1 : 2)}M`
  if (a >= 1e3) return `$${Math.round(n / 1e3)}K`
  return `$${n.toFixed(0)}`
}
export const num = (n) => (n == null ? '—' : Math.round(n).toLocaleString())
export const x1 = (n) => (n == null ? '—' : `${n.toFixed(1)}x`)
export const pct = (n) => (n == null ? '—' : `${Math.round(n * 100)}%`)
export const price = (n) => (n == null ? '—' : `$${n.toFixed(2)}`)
export const strike = (n) => (Number.isInteger(n) ? `$${n}` : `$${n.toFixed(2)}`)

export function ordinal(n) {
  const s = ['th', 'st', 'nd', 'rd'], v = n % 100
  return n + (s[(v - 20) % 10] || s[v] || s[0])
}
export function when(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}
export function tierClass(tier) {
  return { ROBBERY: 'robbery', 'STRONG STICKUP': 'strong', CASING: 'casing' }[tier] || 'casing'
}
export function tierColor(tier) {
  return { ROBBERY: 'var(--red)', 'STRONG STICKUP': 'var(--orange)', CASING: '#C7803A' }[tier] || 'var(--muted)'
}
