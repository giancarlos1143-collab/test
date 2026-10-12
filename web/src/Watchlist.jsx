import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { ScoreRing, Updated, useApi } from './components'
import { chg, chgClass, price, strike, x1 } from './format'

export default function Watchlist() {
  const { data, error, reload } = useApi('/watchlist')
  const [text, setText] = useState('')
  const [msg, setMsg] = useState(null)

  async function add(e) {
    e.preventDefault()
    const r = await fetch('/api/watchlist', { method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ ticker: text }) })
    if (!r.ok) { setMsg((await r.json()).detail?.[0]?.msg || 'Could not add that ticker'); return }
    setText(''); setMsg('Added. Fetching its options data…'); reload()
    setTimeout(reload, 2500); setTimeout(() => setMsg(null), 3000)
  }
  async function remove(t) {
    await fetch(`/api/watchlist/${t}`, { method: 'DELETE' }); reload()
  }
  return (
    <div className="screen">
      <div className="head"><div><h1>Watchlist</h1>
        <div className="sub">Added tickers are scanned automatically</div>
        {data && <Updated iso={data.last_updated} />}</div></div>
      <form className="add" onSubmit={add}>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Add ticker (e.g. DRAM)"
          maxLength={6} autoCapitalize="characters" autoCorrect="off" />
        <button type="submit" disabled={!text.trim()}>Add</button>
      </form>
      {msg && <div className="bk-text" style={{ marginBottom: 10 }}>{msg}</div>}
      {error && <div className="note err">{error}</div>}
      {data && data.watchlist.length === 0 && <div className="note">Your watchlist is empty. Add a ticker above.</div>}
      {data?.watchlist.map((w) => (
        <div className="card" key={w.ticker}>
          <div className="play">
            <Link to={`/ticker/${w.ticker}`} style={{ color: 'inherit', textDecoration: 'none', flex: 1 }}>
              <div className="ticker">{w.ticker}</div>
              {w.in_latest_scan ? (
                <div className="facts"><b>{price(w.price)}</b> <span className={chgClass(w.change_pct)}>{chg(w.change_pct)}</span>
                  {' · '}options volume <b>{w.volume_multiple == null ? 'building history' : `${x1(w.volume_multiple)} avg`}</b></div>
              ) : <div className="facts">Waiting for the next scan…</div>}
            </Link>
            <button className="rm" onClick={() => remove(w.ticker)} aria-label={`Remove ${w.ticker}`}>✕</button>
          </div>
          {w.top_contract && (
            <Link className="top-line play" style={{ color: 'inherit', textDecoration: 'none', display: 'flex' }}
              to={`/play/${encodeURIComponent(w.top_contract.contract)}`}>
              <span>Top contract: <b>{w.top_contract.kind.toUpperCase()} {strike(w.top_contract.strike)}</b> · {w.top_contract.dte}d · {price(w.top_contract.price)}</span>
              <ScoreRing score={w.top_contract.score} tier={w.top_contract.tier} size={40} stroke={4} />
            </Link>
          )}
        </div>
      ))}
    </div>
  )
}
