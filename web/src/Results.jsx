import React from 'react'
import { KindPill, TierPill, Updated, useApi } from './components'
import { price, strike } from './format'

const signed = (n, d = 1) => (n == null ? '—' : `${n >= 0 ? '+' : ''}${n.toFixed(d)}%`)

export default function Results() {
  const { data: d, error, reload, loading } = useApi('/results')
  return (
    <div className="screen">
      <div className="head">
        <div>
          <h1>Results</h1>
          <div className="sub">{d ? `${d.total_flagged} plays flagged at ${d.min_score}+ (paper trades)` : ' '}</div>
          {d && <Updated iso={d.last_updated} />}
        </div>
        <button className="icon-btn" onClick={reload} aria-label="Refresh">{loading ? '…' : '↻'}</button>
      </div>
      {error && <div className="note err">{error}</div>}
      {d && (<>
        <div className="section" style={{ marginTop: 4 }}>Moved the expected way</div>
        <div className="grid3">
          {d.horizons.map((h) => (
            <div className="cell" key={h.horizon}>
              <div className="l">After {h.horizon} day{h.horizon > 1 ? 's' : ''}</div>
              <div className={`v ${h.hit_rate == null ? '' : h.hit_rate >= 0.5 ? 'up' : 'down'}`}>
                {h.hit_rate == null ? '—' : `${Math.round(h.hit_rate * 100)}%`}</div>
              <div className="l" style={{ marginTop: 4, textTransform: 'none' }}>
                {h.measured ? `${h.hits} of ${h.measured}` : 'no data yet'}</div>
              {h.measured > 0 && <div className="l" style={{ textTransform: 'none' }}>avg {signed(h.avg_move_pct, 2)}</div>}
            </div>
          ))}
        </div>
        <div className="trace" style={{ textAlign: 'left', marginTop: 10 }}>
          A hit means the stock moved the way the play bet: up for calls, down for puts. Avg is the stock's
          move in that direction. Only trading days with a stored scan are counted.
        </div>

        <div className="section">Flagged plays</div>
        {d.plays.length === 0 && <div className="note">Nothing flagged yet. Plays scoring {d.min_score}+ are logged after each scan.</div>}
        {d.plays.map((p) => (
          <div className="card" key={p.id}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <div className="row"><span className="ticker" style={{ fontSize: 22 }}>{p.underlying}</span>
                <KindPill kind={p.kind} /><TierPill tier={p.tier} /></div>
              <b style={{ color: 'var(--orange)' }}>{Math.round(p.score)}</b>
            </div>
            <div className="facts"><b>{strike(p.strike)}</b> · {price(p.contract_price)} · stock {price(p.stock_price)} · flagged {p.flag_date}</div>
            <div className="chips">
              {[1, 3, 5].map((h) => {
                const o = p.outcomes[h]
                const exp = o?.stock_move_pct == null ? null : o.stock_move_pct * (p.kind === 'call' ? 1 : -1)
                return (
                  <div key={h} className={`chip ${o ? (o.hit ? 'hit' : 'miss') : ''}`}>
                    <div className="l">{h}d</div>
                    <div className="v">{o ? signed(o.stock_move_pct, 2) : 'pending'}</div>
                    {o && <div className="l" style={{ textTransform: 'none' }}>option {signed(o.contract_change_pct, 0)}</div>}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </>)}
    </div>
  )
}
