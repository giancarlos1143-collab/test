// Preview build only. Replaces fetch() so the app runs from a saved snapshot of sample data.
import data from './demo-data.json'

export function install() {
  const watch = [...data.initialWatchlist]
  const reply = (body, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } })

  const row = (tk) => {
    const t = data.tickers[tk]
    return t
      ? { ticker: tk, price: t.price, change_pct: t.change_pct, volume_multiple: t.volume_multiple,
          top_contract: t.top_contracts[0] || null, in_latest_scan: true }
      : { ticker: tk, price: null, change_pct: null, volume_multiple: null, top_contract: null, in_latest_scan: false }
  }

  window.fetch = async (input, opts = {}) => {
    const path = new URL(String(input), 'http://preview.local').pathname
    const method = (opts.method || 'GET').toUpperCase()
    if (path === '/api/session') return reply({ password_required: false, logged_in: true })
    if (path === '/api/top-plays') return reply(data.topPlays)
    if (path === '/api/sentiment') return reply(data.sentiment)
    if (path === '/api/results') return reply(data.results)
    if (path.startsWith('/api/contracts/')) {
      const c = data.contracts[decodeURIComponent(path.slice('/api/contracts/'.length))]
      return c ? reply(c) : reply({ detail: 'Not part of this preview snapshot' }, 404)
    }
    if (path.startsWith('/api/tickers/')) {
      const t = data.tickers[decodeURIComponent(path.slice('/api/tickers/'.length)).toUpperCase()]
      return t ? reply(t) : reply({ detail: 'No data for that ticker in this snapshot' }, 404)
    }
    if (path === '/api/watchlist' && method === 'GET')
      return reply({ last_updated: data.topPlays.last_updated, watchlist: watch.map(row) })
    if (path === '/api/watchlist' && method === 'POST') {
      const tk = String(JSON.parse(opts.body).ticker || '').toUpperCase().trim()
      if (!/^[A-Z0-9]{1,6}$/.test(tk)) return reply({ detail: [{ msg: 'Ticker must be 1-6 letters/digits' }] }, 422)
      if (!watch.includes(tk)) watch.push(tk)
      return reply({ ticker: tk }, 201)
    }
    if (path.startsWith('/api/watchlist/') && method === 'DELETE') {
      const tk = decodeURIComponent(path.slice('/api/watchlist/'.length)).toUpperCase()
      const i = watch.indexOf(tk); if (i >= 0) watch.splice(i, 1)
      return reply({ removed: tk })
    }
    return reply({ detail: 'Not available in the preview' }, 404)
  }
}
