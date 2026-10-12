import React from 'react'
import { Link } from 'react-router-dom'
import { Updated, useApi } from './components'
import { chg, chgClass, compact, money, price, x1 } from './format'

export const BiasPill = ({ bias }) => <span className={`pill ${bias.toLowerCase()}`}>{bias.toUpperCase()}</span>

export function SplitBar({ call, put, label }) {
  const total = call + put || 1, c = (call / total) * 100
  return (
    <>
      <div className="split"><div className="c" style={{ width: `${c}%` }} /><div className="p" style={{ width: `${100 - c}%` }} /></div>
      <div className="split-l"><span><b className="c">{c.toFixed(0)}%</b> calls</span><span>{label}</span><span><b className="p">{(100 - c).toFixed(0)}%</b> puts</span></div>
    </>
  )
}

export default function Sentiment() {
  const { data: d, error, reload, loading } = useApi('/sentiment')
  const max = d ? Math.max(1, ...d.activity.map((a) => a.volume_multiple || 0)) : 1
  return (
    <div className="screen">
      <div className="head">
        <div><h1>Options Momentum</h1>{d && <Updated iso={d.last_updated} />}</div>
        <button className="icon-btn" onClick={reload} aria-label="Refresh">{loading ? '…' : '↻'}</button>
      </div>
      {error && <div className="note err">{error}</div>}
      {d && (<>
        <div className="grid">
          <div className="cell"><div className="l">Total options traded</div><div className="v">{compact(d.total_volume)}</div></div>
          <div className="cell"><div className="l">Total premium</div><div className="v">{money(d.total_premium)}</div></div>
        </div>
        <div className="card" style={{ marginTop: 10 }}>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <div className="cell" style={{ border: 0, padding: 0, background: 'none' }}>
              <div className="l">Market direction</div>
              <div className={`v ${d.direction === 'Bullish' ? 'up' : d.direction === 'Bearish' ? 'down' : ''}`}>{d.direction}</div>
            </div>
            <BiasPill bias={d.direction} />
          </div>
          <SplitBar call={d.call_volume} put={d.put_volume} label="by volume" />
        </div>

        <div className="section">Activity Intensity</div>
        <div className="card">
          {d.building_history && <div className="bk-text" style={{ marginBottom: 6 }}>Some tickers are still building 30-day history.</div>}
          {d.activity.map((a) => (
            <Link key={a.ticker} to={`/ticker/${a.ticker}`} style={{ color: 'inherit', textDecoration: 'none' }}>
              <div className="hbar"><span className="t">{a.ticker}</span>
                <span className="tr"><i style={{ width: `${((a.volume_multiple || 0) / max) * 100}%` }} /></span>
                <span className="m">{x1(a.volume_multiple)}</span></div>
            </Link>
          ))}
        </div>

        <div className="section">Momentum Leaders</div>
        {d.leaders.map((t, i) => (
          <Link key={t.ticker} to={`/ticker/${t.ticker}`} className="card">
            <div className="leader">
              <span className="rank">{i + 1}</span>
              <div className="mid">
                <div className="row"><span className="ticker" style={{ fontSize: 22 }}>{t.ticker}</span>
                  {t.intensity && <span className={`pill ${t.intensity.toLowerCase()}`}>{t.intensity.toUpperCase()}</span>}</div>
                <div className="px">{price(t.price)} <span className={chgClass(t.change_pct)}>{chg(t.change_pct)}</span> · {x1(t.volume_multiple)} avg volume</div>
              </div>
              <div className="end"><BiasPill bias={t.bias} /></div>
            </div>
          </Link>
        ))}
      </>)}
    </div>
  )
}
