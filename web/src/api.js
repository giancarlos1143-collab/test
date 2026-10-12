export async function get(path) {
  const r = await fetch(`/api${path}`)
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `Error ${r.status}`)
  return r.json()
}
