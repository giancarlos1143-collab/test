import React from 'react'
import { Link } from 'react-router-dom'
import { KindPill, ScoreRing, TierPill, Updated, useApi } from './components'
import { money, price, strike, x1 } from './format'

export default function TopPlays() {
  const { data, error, loading, reload } = useApi('/top-plays')
  return (
    <div className="screen">
      <div className="head">
        <div>
          <h1>Top Plays</h1>
          <div className="sub">{data ? `${data.count} high-conviction signals detected` : ' '}</div>
          {data && <Updated iso={data.last_updated} />}
        </div>
        <button className="icon-btn" onClick={reload} aria-label="Refresh">{loading ? '…' : '↻'}</button>
      </div>
      {error && <div className="note err">Couldn't load plays: {error}</div>}
      {data && data.count === 0 && <div className="note">No contracts scored 60+ in the latest scan.</div>}
      {data?.plays.map((p) => (
        <Link key={p.contract} className="card play" to={`/play/${encodeURIComponent(p.contract)}`}>
          <div>
            <div className="row">
              <span className="ticker">{p.ticker}</span><KindPill kind={p.kind} /><TierPill tier={p.tier} />
            </div>
            <div className="facts"><b>{strike(p.strike)}</b> · {price(p.price)} · <b>{p.dte}d</b> to expiry</div>
            <div className="stats">
              <div className="stat"><div className="v">{money(p.premium)}</div><div className="l">Premium</div></div>
              <div className="stat"><div className="v">{x1(p.vol_oi)}</div><div className="l">V/OI</div></div>
              <div className="stat"><div className="v">{p.iv == null ? '—' : `${Math.round(p.iv * 100)}%`}</div><div className="l">IV</div></div>
            </div>
          </div>
          <ScoreRing score={p.score} tier={p.tier} />
        </Link>
      ))}
    </div>
  )
}
