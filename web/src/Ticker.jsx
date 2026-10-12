import React from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { KindPill, ScoreRing, TierPill, Updated, useApi } from './components'
import { BiasPill, SplitBar } from './Sentiment.jsx'
import { chg, chgClass, compact, money, price, strike, x1 } from './format'

export default function Ticker() {
  const { symbol } = useParams()
  const nav = useNavigate()
  const { data: t, error } = useApi(`/tickers/${symbol}`)
  return (
    <div className="screen">
      <button className="back" onClick={() => nav(-1)} aria-label="Back">‹</button>
      {error && <div className="note err">{error}</div>}
      {t && (<>
        <div className="head">
          <div>
            <h1>{t.ticker}</h1>
            <div className="big-price">{price(t.price)}</div>
            <div className={chgClass(t.change_pct)} style={{ fontWeight: 700 }}>{chg(t.change_pct)}</div>
            <Updated iso={t.last_updated} />
          </div>
          <BiasPill bias={t.bias} />
        </div>
        <div className="say">{t.summary}</div>

        <div className="section">Calls vs Puts</div>
        <div className="card">
          <SplitBar call={t.call_volume} put={t.put_volume} label="by volume" />
          <div className="bk-text" style={{ marginTop: 10 }}>{t.read}</div>
        </div>

        <div className="grid" style={{ marginTop: 10 }}>
          <div className="cell"><div className="l">Call premium</div><div className="v up">{money(t.call_premium)}</div></div>
          <div className="cell"><div className="l">Put premium</div><div className="v down">{money(t.put_premium)}</div></div>
          <div className="cell"><div className="l">Today's volume</div><div className="v">{compact(t.volume)}</div></div>
          <div className="cell"><div className="l">30-day average</div><div className="v">{t.avg_volume_30d ? compact(t.avg_volume_30d) : 'Building'}</div></div>
        </div>

        {t.top_contracts.length > 0 && <div className="section">Top Contracts</div>}
        {t.top_contracts.map((p) => (
          <Link key={p.contract} className="card play" to={`/play/${encodeURIComponent(p.contract)}`}>
            <div>
              <div className="row"><KindPill kind={p.kind} />{p.tier && <TierPill tier={p.tier} />}</div>
              <div className="facts"><b>{strike(p.strike)}</b> · {price(p.price)} · <b>{p.dte}d</b> · {money(p.premium)} · {x1(p.vol_oi)} V/OI</div>
            </div>
            <ScoreRing score={p.score} tier={p.tier} size={52} stroke={5} />
          </Link>
        ))}
      </>)}
    </div>
  )
}
