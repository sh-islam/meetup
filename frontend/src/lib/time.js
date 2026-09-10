// Slot math. A slot is 'YYYY-MM-DDTHH:MM' in the meetup's timezone, 10-minute aligned.
export const SLOT_MIN = 15

const pad = (n) => String(n).padStart(2, '0')

export function slotKey(date, minutes) {
  return `${date}T${pad(Math.floor(minutes / 60))}:${pad(minutes % 60)}`
}

export function slotMinutes(slot) {
  const [h, m] = slot.slice(11, 16).split(':').map(Number)
  return h * 60 + m
}

export function slotDate(slot) {
  return slot.slice(0, 10)
}

export function rowsFor(hourStart, hourEnd) {
  return ((hourEnd - hourStart) * 60) / SLOT_MIN
}

// minutes from midnight -> '7:00 PM'; 1440 -> '12:00 AM'
export function fmtTime(minutes, short = false) {
  const mm = ((minutes % 1440) + 1440) % 1440
  let h = Math.floor(mm / 60)
  const m = mm % 60
  const ampm = h < 12 ? 'AM' : 'PM'
  h = h % 12 || 12
  if (short && m === 0) return `${h} ${ampm}`
  return `${h}:${pad(m)} ${ampm}`
}

export function fmtDate(iso, opts = { weekday: 'short', month: 'short', day: 'numeric' }) {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString(undefined, opts)
}

export function fmtDateLong(iso) {
  return fmtDate(iso, { weekday: 'long', month: 'long', day: 'numeric' })
}

export function fmtBlock(start, end) {
  return `${fmtDate(slotDate(start))}, ${fmtTime(slotMinutes(start))} to ${fmtTime(endMinutes(start, end))}`
}

// end is exclusive and may be midnight of the next day; report it as 1440 on the start date
export function endMinutes(start, end) {
  if (slotDate(end) === slotDate(start)) return slotMinutes(end)
  return 1440
}

export function addMinutes(slot, minutes) {
  const [y, mo, d] = slotDate(slot).split('-').map(Number)
  const dt = new Date(y, mo - 1, d, 0, slotMinutes(slot) + minutes)
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`
}

export function localTimezone() {
  try { return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC' } catch { return 'UTC' }
}

// 'America/Toronto' + a date -> 'Toronto · Eastern Daylight Time (UTC−4)'
export function tzLabel(tz, dateISO) {
  if (!tz) return ''
  const city = tz.split('/').pop().replace(/_/g, ' ')
  const [y, m, d] = (dateISO || todayISO()).split('-').map(Number)
  const at = new Date(Date.UTC(y, m - 1, d, 12))
  let long = '', off = ''
  try {
    long = new Intl.DateTimeFormat('en', { timeZone: tz, timeZoneName: 'long' }).formatToParts(at).find((p) => p.type === 'timeZoneName')?.value || ''
    off = new Intl.DateTimeFormat('en', { timeZone: tz, timeZoneName: 'shortOffset' }).formatToParts(at).find((p) => p.type === 'timeZoneName')?.value || ''
  } catch { return tz }
  off = off.replace('GMT', 'UTC').replace('-', '−')
  if (off === 'UTC') off = 'UTC±0'
  return `${city} · ${long} (${off})`
}

export function todayISO() {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// Group sorted slot keys into [{start, end}] contiguous blocks (end exclusive)
export function slotsToBlocks(slots) {
  const out = []
  const sorted = [...slots].sort()
  let start = null, prev = null
  for (const s of sorted) {
    if (prev !== null && s === addMinutes(prev, SLOT_MIN)) { prev = s; continue }
    if (start !== null) out.push({ start, end: addMinutes(prev, SLOT_MIN) })
    start = prev = s
  }
  if (start !== null) out.push({ start, end: addMinutes(prev, SLOT_MIN) })
  return out
}
