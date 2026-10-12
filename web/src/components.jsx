import React, { useCallback, useEffect, useState } from 'react'
import { get } from './api'
import { tierClass, tierColor, when } from './format'

export function ScoreRing({ score, tier, size = 64, stroke = 6 }) {
  const r = (size - stroke) / 2, c = 2 * Math.PI * r
  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={tierColor(tier)} strokeWidth={stroke}
          strokeLinecap="round" strokeDasharray={`${(c * score) / 100} ${c}`} />
      </svg>
      <span style={{ fontSize: size * 0.33 }}>{Math.round(score)}</span>
    </div>
  )
}

export const KindPill = ({ kind }) => <span className={`pill ${kind}`}>{kind.toUpperCase()}</span>
export const TierPill = ({ tier }) => <span className={`pill ${tierClass(tier)}`}>{tier}</span>

export function Updated({ iso }) {
  return <div className="updated">Last updated {when(iso)}</div>
}

// Loads `path` from the API; returns state plus a reload function.
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const load = useCallback(() => {
    setState((s) => ({ ...s, loading: true }))
    get(path).then((data) => setState({ data, error: null, loading: false }),
      (error) => setState({ data: null, error: error.message, loading: false }))
  }, [path])
  useEffect(load, [load])
  return { ...state, reload: load }
}
