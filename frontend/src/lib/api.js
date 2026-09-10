// Thin fetch wrapper. The token identifies the person; the role comes from the server.
export const API = (import.meta.env.VITE_API_URL || 'https://shad-server.elf-tarpon.ts.net/meetup-api').replace(/\/$/, '')

let token = null
export function setToken(t) { token = t }
export function getToken() { return token }

async function req(method, path, body) {
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['X-Meetup-Token'] = token
  let r
  try {
    r = await fetch(API + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  } catch (e) {
    throw new Error("Can't reach the server. Check your connection and try again.")
  }
  let data = null
  try { data = await r.json() } catch { /* non-JSON */ }
  if (!r.ok) throw new Error((data && data.error) || `Something went wrong (${r.status}).`)
  return data
}

export const api = {
  health: () => req('GET', '/health'),
  createMeetup: (body) => req('POST', '/meetups', body),
  getMeetup: () => req('GET', '/meetups/me'),
  updateMeetup: (patch) => req('PATCH', '/meetups/me', patch),
  setName: (name) => req('PUT', '/meetups/me/name', { name }),
  saveAvailability: (slots) => req('PUT', '/meetups/me/availability', { slots }),
  heatmap: () => req('GET', '/meetups/me/heatmap'),
  stats: () => req('GET', '/meetups/me/stats'),
  addInvitees: (invitees) => req('POST', '/meetups/me/invitees', { invitees }),
  removeInvitee: (id) => req('DELETE', `/meetups/me/invitees/${id}`),
  confirm: (start, end) => req('POST', '/meetups/me/confirm', { start, end }),
  reopen: () => req('POST', '/meetups/me/reopen'),
  nudge: (participant_id, start, end) => req('POST', '/meetups/me/nudge', { participant_id, start, end }),
}
