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
  if (parts[0] === 'm' && parts[1]) return { page: 'meetup', token: parts[1], tab: parts[2] || 'times', action: parts[3] || '' }
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
  title: '', description: '', location: '', icon: '',
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

// ---- meetups opened on this device (the in-app "bookmark") ----
const RECENT = 'meetup.recent.v1'
export function loadRecent() {
  try { return JSON.parse(localStorage.getItem(RECENT) || '[]') } catch { return [] }
}
export function rememberMeetup({ token, title, role, icon = '' }) {
  try {
    const list = loadRecent().filter((m) => m.token !== token)
    list.unshift({ token, title, role, icon, at: Date.now() })
    localStorage.setItem(RECENT, JSON.stringify(list.slice(0, 12)))
  } catch { /* ignore */ }
}
export function forgetMeetup(token) {
  try {
    localStorage.setItem(RECENT, JSON.stringify(loadRecent().filter((m) => m.token !== token)))
    localStorage.setItem(HIDDEN, JSON.stringify(loadHidden().filter((m) => m.token !== token)))
  } catch { /* ignore */ }
}
// hidden = taken off the home list but kept, so it can be restored
const HIDDEN = 'meetup.hidden.v1'
export function loadHidden() {
  try { return JSON.parse(localStorage.getItem(HIDDEN) || '[]') } catch { return [] }
}
export function hideMeetup(token) {
  try {
    const entry = loadRecent().find((m) => m.token === token)
    localStorage.setItem(RECENT, JSON.stringify(loadRecent().filter((m) => m.token !== token)))
    if (entry) localStorage.setItem(HIDDEN, JSON.stringify([entry, ...loadHidden().filter((m) => m.token !== token)].slice(0, 30)))
  } catch { /* ignore */ }
}
export function restoreMeetup(token) {
  try {
    const entry = loadHidden().find((m) => m.token === token)
    localStorage.setItem(HIDDEN, JSON.stringify(loadHidden().filter((m) => m.token !== token)))
    if (entry) rememberMeetup(entry)
  } catch { /* ignore */ }
}

// ---- PWA install prompt (Chrome on Android / desktop) ----
let _installEvent = null
if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); _installEvent = e })
}
export const installPrompt = { get: () => _installEvent, clear: () => { _installEvent = null } }
