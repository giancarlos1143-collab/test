import React from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import TopPlays from './TopPlays.jsx'
import Detail from './Detail.jsx'

const Soon = ({ name }) => <div className="screen"><h1>{name}</h1><div className="note">Coming in the next stage.</div></div>

const I = {
  plays: <path d="M13 2 4 14h7l-1 8 9-12h-7z" />,
  sentiment: <><path d="M4 20V10M10 20V4M16 20v-8M22 20H2" /></>,
  watch: <path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" />,
  news: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M7 9h10M7 13h10M7 17h6" /></>,
  profile: <><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-6 8-6s8 2 8 6" /></>,
}
const TABS = [
  ['/', 'Top Plays', 'plays'], ['/sentiment', 'Sentiment', 'sentiment'], ['/watchlist', 'Watchlist', 'watch'],
  ['/news', 'Hot News', 'news', true], ['/profile', 'Profile', 'profile', true],
]

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<TopPlays />} />
        <Route path="/play/:id" element={<Detail />} />
        <Route path="/sentiment" element={<Soon name="Options Momentum" />} />
        <Route path="/watchlist" element={<Soon name="Watchlist" />} />
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
