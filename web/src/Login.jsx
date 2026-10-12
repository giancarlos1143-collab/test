import React, { useState } from 'react'

export default function Login({ onDone }) {
  const [pw, setPw] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  async function submit(e) {
    e.preventDefault(); setBusy(true); setErr(null)
    const r = await fetch('/api/login', { method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ password: pw }) })
    setBusy(false)
    if (r.ok) onDone()
    else setErr((await r.json().catch(() => ({}))).detail || 'Could not log in')
  }
  return (
    <div className="screen" style={{ paddingTop: 120 }}>
      <h1>Options Flow</h1>
      <div className="sub">Private. Enter your password.</div>
      <form className="add" style={{ marginTop: 24 }} onSubmit={submit}>
        <input type="password" value={pw} onChange={(e) => setPw(e.target.value)} placeholder="Password"
          autoFocus autoComplete="current-password" style={{ textTransform: 'none' }} />
        <button type="submit" disabled={!pw || busy}>{busy ? '…' : 'Go'}</button>
      </form>
      {err && <div className="note err" style={{ padding: 0, textAlign: 'left' }}>{err}</div>}
    </div>
  )
}
