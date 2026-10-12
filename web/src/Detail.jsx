import React from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { KindPill, ScoreRing, Updated, useApi } from './components'
import { money, num, ordinal, price, strike, tierColor, when, x1 } from './format'

const Cell = ({ l, v }) => <div className="cell"><div className="l">{l}</div><div className="v">{v}</div></div>

const LABELS = { vol_oi: 'Volume / Open Interest', premium: 'Premium (dollar flow)',
  vol_multiple: 'Volume multiple', expiry_iv: 'Expiry + IV' }

export default function Detail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { data: d, error } = useApi(`/contracts/${encodeURIComponent(id)}`)
  return (
    <div className="screen">
      <button className="back" onClick={() => nav(-1)} aria-label="Back">‹</button>
      {error && <div className="note err">{error}</div>}
      {d && (<>
        <div className="hero">
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <ScoreRing score={d.score} tier={d.tier} size={130} stroke={10} />
          </div>
          <div className="tier" style={{ color: tierColor(d.tier) }}>{d.tier}</div>
          <div className="title"><span className="ticker">{d.ticker}</span><KindPill kind={d.kind} /></div>
          <Updated iso={d.last_updated} />
        </div>

        <div className="section">Contract Details</div>
        <div className="grid">
          <Cell l="Strike" v={strike(d.strike)} />
          <Cell l="Premium" v={price(d.price)} />
          <Cell l="Days to expiry" v={d.dte} />
          <Cell l="IV percentile" v={d.iv_percentile == null ? 'Building' : ordinal(Math.round(d.iv_percentile))} />
          <Cell l="Expiration" v={d.expiration} />
          <Cell l="Implied vol" v={d.iv == null ? '—' : `${Math.round(d.iv * 100)}%`} />
        </div>

        <div className="section">Flow &amp; Volume</div>
        <div className="grid">
          <Cell l="Dollar flow" v={money(d.premium)} />
          <Cell l="Volume multiple" v={d.volume_multiple == null ? 'Building' : x1(d.volume_multiple)} />
          <Cell l="Open interest" v={num(d.open_interest)} />
          <Cell l="Volume" v={num(d.volume)} />
          <Cell l="Scored at" v={when(d.scored_at)} />
          <Cell l="Side" v={d.side || 'n/a'} />
        </div>

        <div className="section">Score Breakdown</div>
        {Object.entries(d.breakdown).map(([k, b]) => (
          <div className="card" key={k}>
            <div className="bk-head"><span>{LABELS[k]}</span><em>{b.score.toFixed(1)} / {b.max}</em></div>
            <div className="bar"><i style={{ width: `${(b.score / b.max) * 100}%` }} /></div>
            <div className="bk-text">{b.explanation}</div>
          </div>
        ))}
        <div className="trace">{d.contract}<br />Traced to scan #{d.scan_id}, snapshot #{d.snapshot_id}</div>
      </>)}
    </div>
  )
}
