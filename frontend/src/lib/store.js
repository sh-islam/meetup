// Hash router + the new-meetup draft (kept in sessionStorage so a reload doesn't lose it).
// Routes:  #/            home
//          #/new/1..6    wizard steps, #/new/done
//          #/open        paste a link
//          #/m/<token>   meetup; planner tabs: #/m/<token>/best | /people | /settings
export function parseHash() {
  const h = (location.hash || '#/').replace(/^#/, '')
  const parts = h.split('/').filter(Boolean)
  if (parts.length === 0) return { page: 'home' }
  if (parts[0] === 'new') return { page: 'new', step: parts[1] || '1' }
  if (parts[0] === 'open') return { page: 'open' }
  if (parts[0] === 'm' && parts[1]) return { page: 'meetup', token: parts[1], tab: parts[2] || 'times' }
  return { page: 'home' }
}

export function go(path, replace = false) {
  const h = path.startsWith('#') ? path : '#' + path
  if (replace) history.replaceState(null, '', h)
  else location.hash = h
  if (replace) window.dispatchEvent(new HashChangeEvent('hashchange'))
}

export function back(fallback = '/') {
  if (history.length > 1) history.back()
  else go(fallback)
}

// Accepts a full link or a bare token, returns the token or null
export function tokenFromInput(s) {
  s = (s || '').trim()
  const m = s.match(/#\/m\/([A-Za-z0-9_-]+)/)
  if (m) return m[1]
  if (/^[A-Za-z0-9_-]{8,}$/.test(s)) return s
  return null
}

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    let ok = false
    try { ok = document.execCommand('copy') } catch { /* ignore */ }
    ta.remove()
    return ok
  }
}

// ---- new-meetup draft ----
const KEY = 'meetup.draft.v1'
export const emptyDraft = () => ({
  dates: [], hourStart: 8, hourEnd: 24, mySlots: [],
  title: '', description: '', location: '',
  plannerName: '', plannerEmail: '',
  invitees: [], paintMode: 'free',
})
export function loadDraft() {
  try { const s = sessionStorage.getItem(KEY); if (s) return { ...emptyDraft(), ...JSON.parse(s) } } catch { /* ignore */ }
  return emptyDraft()
}
export function saveDraft(d) {
  try { sessionStorage.setItem(KEY, JSON.stringify(d)) } catch { /* ignore */ }
}
export function clearDraft() {
  try { sessionStorage.removeItem(KEY) } catch { /* ignore */ }
}

export const isWide = () => window.matchMedia('(min-width: 900px)').matches
