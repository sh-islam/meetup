<script>
  // The decision sheet body: a selected block with steppers, who's free, and the actions.
  // Modes: 'pick' (steppers + Confirm / Nudge), 'confirm' (review), 'nudge' (preview for one person).
  import { SLOT_MIN, addMinutes, fmtDate, fmtTime, slotDate, slotMinutes, endMinutes } from '../lib/time.js'

  let {
    selection = $bindable(null),   // {start, end}
    participants = [],             // [{id, name, role}]
    availableIds = [],             // ids free for the whole selection
    hourStart = 8,
    hourEnd = 24,
    mailConfigured = false,
    busy = false,
    onconfirm = () => {},          // (selection)
    onnudge = () => {},            // (person, selection)
    oncancel = () => {},
  } = $props()

  let mode = $state('pick')        // pick | confirm | nudge
  let nudgeTarget = $state(null)

  const availSet = $derived(new Set(availableIds))
  const free = $derived(participants.filter((p) => availSet.has(p.id)))
  const missing = $derived(participants.filter((p) => !availSet.has(p.id)))
  const missingInvitees = $derived(missing.filter((p) => p.role === 'invitee'))
  const initial = (n) => (n || '?').trim().charAt(0).toUpperCase()

  const startMin = $derived(selection ? slotMinutes(selection.start) : 0)
  const endMin = $derived(selection ? endMinutes(selection.start, selection.end) : 0)
  const dayLabel = $derived(selection ? fmtDate(slotDate(selection.start), { weekday: 'long', month: 'short', day: 'numeric' }) : '')

  function step(which, d) {
    if (!selection) return
    const date = slotDate(selection.start)
    let s = startMin, e = endMin
    if (which === 'start') s += d; else e += d
    if (s < hourStart * 60 || e > hourEnd * 60 || e - s < SLOT_MIN) return
    const pad = (n) => String(n).padStart(2, '0')
    const key = (m) => `${date}T${pad(Math.floor(m / 60))}:${pad(m % 60)}`
    selection = { start: key(s), end: e === 1440 ? addMinutes(key(1440 - SLOT_MIN), SLOT_MIN) : key(e) }
  }
  function names(list) { return list.map((p) => p.name).join(', ') }
  function startNudge(p) { nudgeTarget = p; mode = 'nudge' }
</script>

{#if !selection}
  <div class="center">
    <h2>Pick a time</h2>
    <p class="lead">Tap a time on the grid, or choose one from Best times.</p>
    <button type="button" class="btn ghost sm" onclick={oncancel}>Close</button>
  </div>
{:else if mode === 'pick'}
  <div class="center">
    <span class="label">{dayLabel}</span>
    <h2 style="margin-top:6px">{fmtTime(startMin)} to {fmtTime(endMin)}</h2>
  </div>
  <div class="range">
    <div class="stepper">
      <button type="button" onclick={() => step('start', -SLOT_MIN)} aria-label="Start earlier">−</button>
      <b>{fmtTime(startMin)}</b>
      <button type="button" onclick={() => step('start', SLOT_MIN)} aria-label="Start later">+</button>
    </div>
    <div class="to">to</div>
    <div class="stepper">
      <button type="button" onclick={() => step('end', -SLOT_MIN)} aria-label="End earlier">−</button>
      <b>{fmtTime(endMin)}</b>
      <button type="button" onclick={() => step('end', SLOT_MIN)} aria-label="End later">+</button>
    </div>
  </div>
  <div class="who">
    <div class="faces">
      {#each participants as p (p.id)}<span class="face" class:off={!availSet.has(p.id)}>{initial(p.name)}</span>{/each}
    </div>
    <div><b>{free.length} of {participants.length} free</b>{#if missing.length} <span class="muted">· missing {names(missing)}</span>{/if}</div>
  </div>
  <div class="actions">
    <button type="button" class="btn sm" onclick={() => (mode = 'confirm')}>Confirm this time</button>
    {#if missingInvitees.length === 1}
      <button type="button" class="btn ghost sm" onclick={() => startNudge(missingInvitees[0])}>Nudge {missingInvitees[0].name}</button>
    {:else if missingInvitees.length > 1}
      <div class="nudge-list">
        {#each missingInvitees as p (p.id)}
          <button type="button" class="btn ghost sm" onclick={() => startNudge(p)}>Nudge {p.name}</button>
        {/each}
      </div>
    {/if}
    <button type="button" class="link" onclick={oncancel}>Cancel</button>
  </div>
{:else if mode === 'confirm'}
  <div class="center">
    <span class="label">Confirm</span>
    <h2 style="margin-top:6px">{dayLabel}<br />{fmtTime(startMin)} to {fmtTime(endMin)}</h2>
  </div>
  <div class="glass card" style="padding:16px">
    <div class="row between" style="margin-bottom:8px"><span class="caption">Coming</span><b>{free.length ? names(free) : 'nobody marked this time'}</b></div>
    {#if missing.length}<div class="row between"><span class="caption">Not free</span><span class="muted">{names(missing)}</span></div>{/if}
  </div>
  <p class="caption" style="text-align:center">{mailConfigured ? 'Everyone gets an email with the details and a calendar file.' : 'Email is not set up yet, so nobody is emailed. The meetup is marked confirmed.'} Nobody can change their times after this.</p>
  <div class="actions">
    <button type="button" class="btn sm" disabled={busy} onclick={() => onconfirm(selection)}>{busy ? 'Confirming…' : 'Send confirmation'}</button>
    <button type="button" class="link" onclick={() => (mode = 'pick')}>Back</button>
  </div>
{:else if mode === 'nudge' && nudgeTarget}
  <div class="center">
    <span class="label">Nudge {nudgeTarget.name}</span>
    <h2 style="margin-top:6px">{dayLabel}<br />{fmtTime(startMin)} to {fmtTime(endMin)}</h2>
  </div>
  <p class="muted" style="text-align:center;font-size:15px">{nudgeTarget.name} gets an email saying {free.length ? names(free) : 'nobody yet'} {free.length === 1 ? 'is' : 'are'} free then, with a Yes and a No button.</p>
  <div class="actions">
    <button type="button" class="btn sm" disabled={busy} onclick={() => onnudge(nudgeTarget, selection)}>{busy ? 'Sending…' : `Send nudge to ${nudgeTarget.name}`}</button>
    <button type="button" class="link" onclick={() => (mode = 'pick')}>Back</button>
  </div>
{/if}

<style>
  .center { text-align: center; }
  .who { display: flex; align-items: center; justify-content: center; gap: 12px; font-size: 15px; font-weight: 500; color: var(--text-2); flex-wrap: wrap; text-align: center; }
  .who b { color: var(--text); font-weight: 700; }
  .actions { display: flex; flex-direction: column; gap: 8px; align-items: center; }
  .actions .btn { width: 100%; }
  .nudge-list { display: flex; flex-direction: column; gap: 8px; width: 100%; }
</style>
