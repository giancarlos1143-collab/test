import React, { useEffect, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import TopPlays from './TopPlays.jsx'
import Detail from './Detail.jsx'
import Login from './Login.jsx'
import Sentiment from './Sentiment.jsx'
import Results from './Results.jsx'
import Ticker from './Ticker.jsx'
import Watchlist from './Watchlist.jsx'

const I = {
  plays: <path d="M13 2 4 14h7l-1 8 9-12h-7z" />,
  sentiment: <><path d="M4 20V10M10 20V4M16 20v-8M22 20H2" /></>,
  watch: <path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" />,
  results: <><circle cx="12" cy="12" r="9" /><path d="m8 12.5 2.8 2.8L16 9.5" /></>,
}
const TABS = [
  ['/', 'Top Plays', 'plays'], ['/sentiment', 'Sentiment', 'sentiment'], ['/watchlist', 'Watchlist', 'watch'],
  ['/results', 'Results', 'results'],
]

export default function App() {
  // null = checking, false = need to log in, true = ok
  const [ok, setOk] = useState(null)
  useEffect(() => {
    fetch('/api/session').then((r) => r.json()).then((s) => setOk(!s.password_required || s.logged_in), () => setOk(true))
  }, [])
  if (ok === null) return null
  if (!ok) return <Login onDone={() => setOk(true)} />
  return (
    <>
      <Routes>
        <Route path="/" element={<TopPlays />} />
        <Route path="/play/:id" element={<Detail />} />
        <Route path="/sentiment" element={<Sentiment />} />
        <Route path="/ticker/:symbol" element={<Ticker />} />
        <Route path="/watchlist" element={<Watchlist />} />
        <Route path="/results" element={<Results />} />
        <Route path="*" element={<TopPlays />} />
      </Routes>
      <nav className="tabbar">
        {TABS.map(([to, label, icon, off]) => off
          ? <span key={to} className="tab disabled"><svg viewBox="0 0 24 24">{I[icon]}</svg>{label}</span>
          : <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `tab${isActive ? ' active' : ''}`}>
              <svg viewBox="0 0 24 24">{I[icon]}</svg>{label}</NavLink>)}
      </nav>
    </>
  )
}
