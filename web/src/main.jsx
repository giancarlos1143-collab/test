import React from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, MemoryRouter } from 'react-router-dom'
import App from './App.jsx'
import './styles.css'

const demo = import.meta.env.VITE_DEMO === '1'
const Router = demo ? MemoryRouter : HashRouter

async function start() {
  if (demo) (await import('./demoApi.js')).install()   // preview build only: serve a saved snapshot
  createRoot(document.getElementById('root')).render(
    <Router>
      {demo && <div className="demo-banner">Preview with sample data. A saved snapshot, not live.</div>}
      <App />
    </Router>,
  )
}
start()
