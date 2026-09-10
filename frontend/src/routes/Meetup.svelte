<script>
  // The shared meetup screen. Invitees paint and send. The planner gets tabs (phone) / a sidebar (wide) and the decision sheet.
  import { tick } from 'svelte'
  import TimeGrid from '../components/TimeGrid.svelte'
  import Stats from '../components/Stats.svelte'
  import ConfirmDialog from '../components/ConfirmDialog.svelte'
  import NudgeDialog from '../components/NudgeDialog.svelte'
  import DatePicker from '../components/DatePicker.svelte'
  import HourRange from '../components/HourRange.svelte'
  import InviteeList from '../components/InviteeList.svelte'
  import MapPicker from '../components/MapPicker.svelte'
  import Sheet from '../components/Sheet.svelte'
  import SaveSheet from '../components/SaveSheet.svelte'
  import IconPicker from '../components/IconPicker.svelte'
  import { iconSvg } from '../lib/icons.js'
  import { api, setToken } from '../lib/api.js'
  import { SLOT_MIN, addMinutes, fmtBlock, fmtDate, fmtTime, localTimezone, slotDate, slotKey, slotMinutes } from '../lib/time.js'
  import { copyText, go, isWide, rememberMeetup, forgetMeetup } from '../lib/store.js'

  let { token, tab = 'times' } = $props()

  let data = $state(null)
  let loading = $state(true)
  let error = $state('')
  let toast = $state('')
  let toastTimer = null
  let mySlots = $state([])
  let dirty = $state(false)
  let busy = $state(false)
  let nameInput = $state('')
  let stats = $state(null)
  let copied = $state('')
  let grid = $state(null)

  // sheets
  let detailsOpen = $state(false)
  let saveOpen = $state(false)
  let deleteOpen = $state(false)
  let decideOpen = $state(false)
  let selection = $state(null)
  let editing = $state(null)        // null | about | location | days | hours | mode
  let inviteOpen = $state(false)
  let person = $state(null)
  let newInvitees = $state([])
  let info = $state(null)
  let infoTimer = null
  let wide = $state(isWide())
  $effect(() => {
    const mq = window.matchMedia('(min-width: 900px)')
    const on = () => { wide = mq.matches }
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  })

  // settings form
  let fIcon = $state('')
  let fTitle = $state(''), fDesc = $state(''), fLoc = $state(''), fDates = $state([]), fHs = $state(8), fHe = $state(24), fMode = $state('free')

  const meetup = $derived(data ? data.meetup : null)
  const me = $derived(data ? data.me : null)
  const isPlanner = $derived(!!me && me.role === 'planner')
  const confirmed = $derived(!!meetup && meetup.status === 'confirmed')
  const people = $derived(data ? data.participants : [])
  const planner = $derived(people.find((p) => p.role === 'planner'))
  const allowed = $derived(meetup && meetup.paint_mode === 'restricted' && !isPlanner ? data.planner_slots : null)
  const tzNote = $derived(meetup && localTimezone() !== meetup.timezone ? `Times are in ${meetup.timezone}.` : '')
  const activeTab = $derived(isPlanner ? tab : 'times')

  // heatmap that reflects my unsaved painting
  const liveHeat = $derived.by(() => {
    if (!data) return {}
    const out = {}
    for (const [k, ids] of Object.entries(data.heatmap)) {
      const rest = ids.filter((id) => id !== me.id)
      if (rest.length) out[k] = rest
    }
    for (const k of mySlots) out[k] = [...(out[k] || []), me.id]
    return out
  })
  function idsFor(block, heat) {
    if (!block) return []
    let k = block.start, ids = null
    for (let n = 0; n < 400 && k < block.end; n++) {
      const here = new Set(heat[k] || [])
      ids = ids === null ? here : new Set([...ids].filter((id) => here.has(id)))
      k = addMinutes(k, SLOT_MIN)
    }
    return ids ? [...ids] : []
  }
  const selectionIds = $derived(idsFor(selection, liveHeat))
  const confirmedBlock = $derived(confirmed ? { start: meetup.confirmed_start, end: meetup.confirmed_end } : null)
  const confirmedNames = $derived.by(() => {
    if (!data || !confirmedBlock) return []
    const ids = new Set(idsFor(confirmedBlock, data.heatmap))
    return people.filter((p) => ids.has(p.id)).map((p) => p.name)
  })

  function apply(view) {
    data = view
    mySlots = view.my_slots
    dirty = false
    fTitle = view.meetup.title; fDesc = view.meetup.description; fLoc = view.meetup.location; fIcon = view.meetup.icon || ''
    fDates = [...view.meetup.dates]; fHs = view.meetup.hour_start; fHe = view.meetup.hour_end; fMode = view.meetup.paint_mode
  }
  async function load() {
    loading = true; error = ''
    setToken(token)
    try {
      apply(await api.getMeetup())
      rememberMeetup({ token, title: data.meetup.title, role: data.me.role, icon: data.meetup.icon })
    } catch (e) { error = e.message } finally { loading = false }
  }
  $effect(() => { token; load() })
  $effect(() => { if (isPlanner && activeTab === 'best') loadStats() })

  function say(msg) { toast = msg; clearTimeout(toastTimer); toastTimer = setTimeout(() => (toast = ''), 3200) }
  function openTab(t) { go(t === 'times' ? `/m/${token}` : `/m/${token}/${t}`) }

  async function saveName() {
    if (!nameInput.trim()) return
    busy = true; error = ''
    try { apply(await api.setName(nameInput.trim())) } catch (e) { error = e.message } finally { busy = false }
  }
  async function saveAvailability() {
    busy = true; error = ''
    try {
      apply(await api.saveAvailability(mySlots))
      say(isPlanner ? 'Saved.' : (data.mail_configured ? `Sent. ${planner.name} got an email.` : `Saved. ${planner.name} can see your times.`))
    } catch (e) { error = e.message } finally { busy = false }
  }
  async function loadStats() { try { stats = await api.stats() } catch (e) { error = e.message } }

  // ----- tapping the grid -----
  function runAt(k) {
    const hs = meetup.hour_start * 60, he = meetup.hour_end * 60
    const date = slotDate(k)
    const keyAt = (m) => (m >= 1440 ? addMinutes(slotKey(date, 1440 - SLOT_MIN), SLOT_MIN) : slotKey(date, m))
    const sig = (m) => (liveHeat[slotKey(date, m)] || []).slice().sort().join(',')
    const m = slotMinutes(k)
    const here = sig(m)
    if (!here) return { start: keyAt(m), end: keyAt(Math.min(he, m + 60)) }
    let a = m, b = m + SLOT_MIN
    while (a - SLOT_MIN >= hs && sig(a - SLOT_MIN) === here) a -= SLOT_MIN
    while (b < he && sig(b) === here) b += SLOT_MIN
    return { start: keyAt(a), end: keyAt(b) }
  }
  function showInfo(k) {
    const ids = liveHeat[k] || []
    info = { when: `${fmtDate(slotDate(k))} · ${fmtTime(slotMinutes(k))}`, who: people.filter((p) => ids.includes(p.id)).map((p) => p.name), mine: ids.includes(me.id), n: ids.length }
    clearTimeout(infoTimer); infoTimer = setTimeout(() => (info = null), 3500)
  }
  function onTap(k) {
    if (isPlanner && !confirmed && (decideOpen || !isWide())) { selection = runAt(k); decideOpen = true }
    else showInfo(k)
  }
  function openDecide() {
    if (!selection && stats && stats.windows.length) selection = { start: stats.windows[0].start, end: stats.windows[0].end }
    if (!selection && !stats) loadStats().then(() => { if (!selection && stats && stats.windows.length) selection = { start: stats.windows[0].start, end: stats.windows[0].end } })
    decideOpen = true
  }
  function closeDecide() { decideOpen = false }
  async function pickFromStats(sel) {
    selection = sel
    openTab('times')
    decideOpen = true
    await tick()
    setTimeout(() => grid && grid.scrollToSlot(sel.start), 50)
  }
  async function doConfirm(sel) {
    busy = true; error = ''
    try { apply(await api.confirm(sel.start, sel.end)); decideOpen = false; selection = null; say('Confirmed. Everyone has been told.') }
    catch (e) { error = e.message } finally { busy = false }
  }
  async function doNudge(p, sel) {
    busy = true; error = ''
    try {
      const v = await api.nudge(p.id, sel.start, sel.end)
      apply(v); decideOpen = false; selection = null
      say(v.mail_configured ? `Nudge sent to ${p.name}.` : `Nudge recorded for ${p.name}. Email isn't set up yet.`)
    } catch (e) { error = e.message } finally { busy = false }
  }
  async function doReopen() {
    if (!confirm('Undo the confirmation? People can paint again. Nobody is emailed.')) return
    busy = true; error = ''
    try { apply(await api.reopen()); editing = null; say('Reopened.') } catch (e) { error = e.message } finally { busy = false }
  }
  async function doDelete() {
    busy = true; error = ''
    try {
      await api.deleteMeetup()
      forgetMeetup(token)
      deleteOpen = false
      go('/')
    } catch (e) { error = e.message; deleteOpen = false } finally { busy = false }
  }
  async function saveSettings(patch) {
    busy = true; error = ''
    try {
      const v = await api.updateMeetup(patch)
      apply(v); editing = null
      say(v.changes.length ? 'Saved. Invitees were told.' : 'Saved.')
    } catch (e) { error = e.message } finally { busy = false }
  }
  async function sendInvites() {
    if (!newInvitees.length) return
    busy = true; error = ''
    try { apply(await api.addInvitees(newInvitees)); newInvitees = []; inviteOpen = false; say(data.mail_configured ? 'Invites sent.' : 'Added. Share their links from the People list.') }
    catch (e) { error = e.message } finally { busy = false }
  }
  async function removePerson(p) {
    if (!confirm(`Remove ${p.name} from this meetup?`)) return
    busy = true; error = ''
    try { apply(await api.removeInvitee(p.id)); person = null; say(`${p.name} removed.`) } catch (e) { error = e.message } finally { busy = false }
  }
  async function copy(text, key) {
    if (await copyText(text)) { copied = key; say('Link copied.'); setTimeout(() => { if (copied === key) copied = '' }, 1500) }
  }
  function nudgeLabel(n) {
    if (!n) return ''
    const when = fmtBlock(n.block_start, n.block_end)
    if (n.answer === 'yes') return `said yes to ${when}`
    if (n.answer === 'no') return `said no to ${when}`
    return `nudged for ${when}, waiting`
  }
  const hoursLabel = $derived(meetup ? `${fmtTime(meetup.hour_start * 60, true)} to ${meetup.hour_end === 24 ? 'midnight' : fmtTime(meetup.hour_end * 60, true)}` : '')
  const responded = $derived(people.filter((p) => p.responded).length)
  const answeredLine = $derived(`${responded} of ${people.length} have answered`)
  const myUrl = $derived(`${location.origin}${location.pathname}#/m/${token}`)
  const sheetOpen = $derived(detailsOpen || saveOpen || deleteOpen || (decideOpen && !wide) || !!person || inviteOpen || !!editing)
</script>

{#snippet icon(name)}
  {#if name === 'times'}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="4" width="18" height="17" rx="3"/><path d="M3 10h18M9 4v4M15 4v4"/></svg>
  {:else if name === 'best'}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/></svg>
  {:else if name === 'people'}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.5c3 0 6 2 6 5.5"/></svg>
  {:else}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/><circle cx="9" cy="7" r="2" fill="var(--ground-a)"/><circle cx="15" cy="12" r="2" fill="var(--ground-a)"/><circle cx="8" cy="17" r="2" fill="var(--ground-a)"/></svg>{/if}
{/snippet}

{#snippet legend()}
  <div class="legend">
    <span><i class="some"></i>some free</span>
    <span><i class="all"></i>everyone</span>
    <span><i class="you"></i>you</span>
    {#if allowed}<span><i class="off"></i>not offered</span>{/if}
  </div>
{/snippet}

{#if loading}
  <div class="center-screen"><p class="muted">Loading…</p></div>
{:else if !data}
  <div class="screen column">
    <div class="body" style="justify-content:center">
      <div><h1>Can't open this meetup</h1><p class="lead">{error}</p></div>
      <a class="btn ghost" href="#/open">Try another link</a>
    </div>
  </div>
{:else if me.name === null}
  <div class="screen column">
    <div class="top"><span></span></div>
    <div class="body">
      <div><span class="label">You're invited</span><h1 style="margin-top:8px">{meetup.title}</h1><p class="lead">{planner.name} wants to know when you're free. First, what should we call you?</p></div>
      {#if error}<div class="msg error">{error}</div>{/if}
      <div class="field"><label for="nm">Your name</label><input id="nm" type="text" bind:value={nameInput} onkeydown={(e) => e.key === 'Enter' && saveName()} autocomplete="given-name" /></div>
    </div>
    <div class="bottom"><button type="button" class="btn" disabled={busy || !nameInput.trim()} onclick={saveName}>Continue</button></div>
  </div>
{:else}
  <div class="shell" class:planner={isPlanner} class:invitee={!isPlanner} class:sheet-open={sheetOpen}>
    <!-- sidebar (wide screens) -->
    <aside class="side">
      <a class="brand" href="#/">Meet<b>up</b></a>
      <div>
        <h2>{#if meetup.icon}<span class="h-icon">{@html iconSvg(meetup.icon, 22)}</span>{/if}{meetup.title}</h2>
        <div class="sub">Planned by {isPlanner ? 'you' : planner.name} · {people.length} people{meetup.location ? ` · ${meetup.location}` : ''}</div>
        <div class="sub" style="margin-top:2px">{answeredLine}</div>
        <button type="button" class="link" onclick={() => (detailsOpen = true)}>Details</button>
      </div>
      {#if isPlanner}
        <nav class="nav">
          {#each [['times', 'Times'], ['best', 'Best times'], ['people', 'People'], ['settings', 'Settings']] as [t, l] (t)}
            <button type="button" class:on={activeTab === t} onclick={() => openTab(t)}>{@render icon(t)}{l}</button>
          {/each}
        </nav>
      {/if}
      {#if tzNote}<div class="caption" style="margin-top:auto">{tzNote}</div>{/if}
    </aside>

    <div class="main">
      <!-- phone header -->
      <header class="mhead">
        <div class="title-row">
          <div class="min0">
            {#if activeTab === 'times'}
              <h2>{#if meetup.icon}<span class="h-icon">{@html iconSvg(meetup.icon, 22)}</span>{/if}{meetup.title}</h2>
              <div class="sub">Planned by {isPlanner ? 'you' : planner.name} · {people.length} people{meetup.location ? ` · ${meetup.location}` : ''}</div>
              <div class="sub" style="margin-top:2px">{answeredLine}</div>
            {:else if activeTab === 'best'}
              <h2>Best times</h2><div class="sub">{answeredLine}</div>
            {:else if activeTab === 'people'}
              <h2>People</h2><div class="sub">{answeredLine}</div>
            {:else}
              <h2>Settings</h2><div class="sub">{meetup.title}</div>
            {/if}
          </div>
          <div class="row" style="gap:8px">
            {#if activeTab === 'times'}<button type="button" class="disclose phone-only" onclick={() => (detailsOpen = true)} aria-label="Details"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg></button>{/if}
          </div>
        </div>
        {#if confirmed && activeTab === 'times'}
          <div class="msg ok"><b>Confirmed:</b> {fmtBlock(meetup.confirmed_start, meetup.confirmed_end)}<br /><span style="font-size:13px">Coming: {confirmedNames.length ? confirmedNames.join(', ') : 'nobody marked this time'}</span></div>
        {/if}
        {#if error}<div class="msg error">{error}</div>{/if}
        {#if activeTab === 'times'}
          <div class="row between">
            {@render legend()}
            {#if isPlanner && !confirmed}<button type="button" class="btn ghost sm auto confirm-btn" onclick={openDecide}>Confirm</button>{/if}
          </div>
        {/if}
      </header>

      {#if activeTab === 'times'}
        <div class="times-area">
          <div class="gridbox">
            <TimeGrid bind:this={grid} dates={meetup.dates} hourStart={meetup.hour_start} hourEnd={meetup.hour_end} bind:mySlots
              heatmap={liveHeat} total={people.length} {allowed} readonly={confirmed} selection={decideOpen ? selection : null}
              highlight={confirmedBlock} fill onchange={() => { dirty = true }} ontap={onTap} />
          </div>
          {#if decideOpen && wide}
            <aside class="glass panel">
              <ConfirmDialog bind:selection participants={people} availableIds={selectionIds} hourStart={meetup.hour_start} hourEnd={meetup.hour_end}
                mailConfigured={data.mail_configured} {busy} onconfirm={doConfirm} onnudge={doNudge} oncancel={closeDecide} />
            </aside>
          {/if}
        </div>
      {:else if activeTab === 'best'}
        <div class="page"><Stats {stats} participants={people} onpick={pickFromStats} /></div>
      {:else if activeTab === 'people'}
        <div class="page">
          <div class="glass" style="padding:4px 20px">
            {#each people as p (p.id)}
              <button type="button" class="list-row" onclick={() => (person = p)}>
                <div class="main"><div class="t">{p.name} {#if p.role === 'planner'}<span class="badge">planner</span>{/if}</div>
                  <div class="s">{#if p.responded}<span class="mint-text">answered</span>{:else}not yet{/if}{#if p.nudge} · {nudgeLabel(p.nudge)}{/if}</div></div>
                <span class="chev">›</span>
              </button>
            {/each}
          </div>
          {#if !confirmed}<button type="button" class="btn ghost" onclick={() => (inviteOpen = true)}>Invite more people</button>{/if}
        </div>
      {:else}
        <div class="page">
          <div class="glass" style="padding:4px 20px">
            <button type="button" class="list-row" disabled={confirmed} onclick={() => (editing = 'about')}><div class="main"><div class="t">Title and description</div><div class="s">{meetup.title}</div></div><span class="chev">›</span></button>
            <button type="button" class="list-row" disabled={confirmed} onclick={() => (editing = 'location')}><div class="main"><div class="t">Location</div><div class="s">{meetup.location || 'Not set'}</div></div><span class="chev">›</span></button>
            <button type="button" class="list-row" disabled={confirmed} onclick={() => (editing = 'days')}><div class="main"><div class="t">Days</div><div class="s">{meetup.dates.map((x) => fmtDate(x)).join(', ')}</div></div><span class="chev">›</span></button>
            <button type="button" class="list-row" disabled={confirmed} onclick={() => (editing = 'hours')}><div class="main"><div class="t">Hours to show</div><div class="s">{hoursLabel}</div></div><span class="chev">›</span></button>
            <button type="button" class="list-row" disabled={confirmed} onclick={() => (editing = 'mode')}><div class="main"><div class="t">Time selection</div><div class="s">{meetup.paint_mode === 'free' ? 'Anyone can select any time' : 'Only the times I picked'}</div></div><span class="chev">›</span></button>
          </div>
          {#if confirmed}
            <p class="caption">This meetup is confirmed, so settings are locked.</p>
            <button type="button" class="btn danger" disabled={busy} onclick={doReopen}>Undo confirmation</button>
          {:else}
            <p class="caption">Changing days or hours emails everyone, and drops selected times that no longer fit.</p>
          {/if}
          <div class="glass" style="padding:4px 20px;margin-top:8px">
            <button type="button" class="list-row" onclick={() => (deleteOpen = true)}><div class="main"><div class="t danger-text">Delete this meetup</div><div class="s">For everyone. Links stop working.</div></div><span class="chev">›</span></button>
          </div>
        </div>
      {/if}
    </div>

    {#if isPlanner}
      <nav class="tabbar tabbar-sheen">
        {#each [['times', 'Times'], ['best', 'Best'], ['people', 'People'], ['settings', 'Settings']] as [t, l] (t)}
          <button type="button" class="tab" class:on={activeTab === t} onclick={() => openTab(t)}>{@render icon(t)}{l}</button>
        {/each}
      </nav>
    {/if}

    {#if activeTab === 'times' && dirty && !confirmed && !decideOpen}
      <div class="float">
        <button type="button" class="btn mint" disabled={busy} onclick={saveAvailability}>{busy ? 'Saving…' : (isPlanner ? 'Save my times' : 'Send my availability')}</button>
        {#if !isPlanner}<div class="hint" style="text-align:center">{planner.name} gets one email with your picks.</div>{/if}
      </div>
    {/if}
    {#if info && activeTab === 'times' && !decideOpen}
      <div class="pill">{info.when} · {info.who.length ? info.who.join(', ') : 'nobody yet'}{#if info.mine} · <span class="mint-text">you're free</span>{/if}</div>
    {/if}
  </div>

  {#if toast}<div class="toast">{toast}</div>{/if}

  <Sheet open={detailsOpen} onclose={() => (detailsOpen = false)} title="Details">
    <NudgeDialog {meetup} {planner} {people} {confirmedNames} {responded} best={data.best} {isPlanner} onclose={() => (detailsOpen = false)} onsave={() => { detailsOpen = false; saveOpen = true }} />
  </Sheet>

  <Sheet open={saveOpen} onclose={() => (saveOpen = false)} title="Save">
    <SaveSheet url={myUrl} title={meetup.title} onclose={() => (saveOpen = false)} />
  </Sheet>

  <Sheet open={decideOpen && !wide} onclose={closeDecide} title="Decide">
    <ConfirmDialog bind:selection participants={people} availableIds={selectionIds} hourStart={meetup.hour_start} hourEnd={meetup.hour_end}
      mailConfigured={data.mail_configured} {busy} onconfirm={doConfirm} onnudge={doNudge} oncancel={closeDecide} />
  </Sheet>

  <Sheet open={!!person} onclose={() => (person = null)} title="Person">
    {#if person}
      <h2 style="text-align:center">{person.name}</h2>
      <p class="caption" style="text-align:center">{person.email || ''}{person.role === 'planner' ? ' · planner' : ''}<br />{person.responded ? 'Has answered' : 'Has not answered yet'}{person.nudge ? ` · ${nudgeLabel(person.nudge)}` : ''}</p>
      {#if person.url}<button type="button" class="btn ghost sm" onclick={() => copy(person.url, person.id)}>{copied === person.id ? 'Copied' : 'Copy their link'}</button>{/if}
      {#if person.role === 'invitee' && !confirmed}<button type="button" class="btn danger sm" disabled={busy} onclick={() => removePerson(person)}>Remove from meetup</button>{/if}
      <button type="button" class="link" onclick={() => (person = null)}>Close</button>
    {/if}
  </Sheet>

  <Sheet open={inviteOpen} onclose={() => (inviteOpen = false)} title="Invite">
    <h2 style="text-align:center">Invite more people</h2>
    <InviteeList bind:invitees={newInvitees} exclude={me.email} />
    <button type="button" class="btn sm" disabled={busy || !newInvitees.length} onclick={sendInvites}>{busy ? 'Sending…' : 'Send invites'}</button>
  </Sheet>

  <Sheet open={editing === 'about'} onclose={() => (editing = null)} title="Title">
    <h2 style="text-align:center">Title and description</h2>
    <div class="field"><label for="st">Title</label><input id="st" type="text" bind:value={fTitle} /></div>
    <div class="field"><label>Icon</label><IconPicker bind:value={fIcon} /></div>
    <div class="field"><label for="sd">Description</label><textarea id="sd" bind:value={fDesc}></textarea></div>
    <button type="button" class="btn sm" disabled={busy || !fTitle.trim()} onclick={() => saveSettings({ title: fTitle, description: fDesc, icon: fIcon })}>Save</button>
  </Sheet>
  <Sheet open={deleteOpen} onclose={() => (deleteOpen = false)} title="Delete">
    <h2 style="text-align:center">Delete “{meetup.title}”?</h2>
    <p class="muted" style="text-align:center;font-size:15px">This removes it for everyone. All {people.length} links stop working and everyone's selected times are gone. {data.mail_configured ? 'Invitees get a short email saying it\'s off.' : ''} This can't be undone.</p>
    <button type="button" class="btn danger sm" disabled={busy} onclick={doDelete}>{busy ? 'Deleting…' : 'Delete for everyone'}</button>
    <button type="button" class="btn ghost sm" onclick={() => (deleteOpen = false)}>Keep it</button>
  </Sheet>
  <Sheet open={editing === 'location'} onclose={() => (editing = null)} title="Location">
    <h2 style="text-align:center">Location</h2>
    <MapPicker bind:location={fLoc} />
    <button type="button" class="btn sm" disabled={busy} onclick={() => saveSettings({ location: fLoc })}>Save</button>
  </Sheet>
  <Sheet open={editing === 'days'} onclose={() => (editing = null)} title="Days">
    <h2 style="text-align:center">Days</h2>
    <DatePicker bind:dates={fDates} />
    <button type="button" class="btn sm" disabled={busy || !fDates.length} onclick={() => saveSettings({ dates: fDates })}>Save</button>
  </Sheet>
  <Sheet open={editing === 'hours'} onclose={() => (editing = null)} title="Hours">
    <h2 style="text-align:center">Hours to show</h2>
    <HourRange bind:hourStart={fHs} bind:hourEnd={fHe} />
    <button type="button" class="btn sm" disabled={busy} onclick={() => saveSettings({ hour_start: fHs, hour_end: fHe })}>Save</button>
  </Sheet>
  <Sheet open={editing === 'mode'} onclose={() => (editing = null)} title="Time selection">
    <h2 style="text-align:center">Time selection</h2>
    <button type="button" class="choice" class:on={fMode === 'free'} onclick={() => (fMode = 'free')}><span class="dot"></span><span><div class="t">Anyone can select any time</div><div class="s">Best for finding out when everyone is free.</div></span></button>
    <button type="button" class="choice" class:on={fMode === 'restricted'} onclick={() => (fMode = 'restricted')}><span class="dot"></span><span><div class="t">Only the times I picked</div><div class="s">Invitees can only choose within the times you selected.</div></span></button>
    <button type="button" class="btn sm" disabled={busy} onclick={() => saveSettings({ paint_mode: fMode })}>Save</button>
  </Sheet>
{/if}

<style>
  .center-screen { min-height: 100dvh; display: grid; place-items: center; }
  .h-icon { display: inline-block; vertical-align: -4px; margin-right: 8px; color: var(--accent); }
  .shell { height: 100dvh; display: flex; flex-direction: column; position: relative; }
  .side { display: none; }
  .main { flex: 1; min-height: 0; display: flex; flex-direction: column; }
  .mhead { padding: calc(12px + env(safe-area-inset-top)) var(--pad) 16px; display: flex; flex-direction: column; gap: 16px; flex: none; }
  .title-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
  .min0 { min-width: 0; }
  .sub { color: var(--text-2); font-size: 15px; font-weight: 500; margin-top: 4px; }
  .disclose { flex: none; width: 44px; height: 44px; border-radius: 14px; display: grid; place-items: center; background: var(--glass); border: 1px solid var(--edge); color: var(--text-2); }
  .confirm-btn { height: 40px; padding: 0 16px; flex: none; }
  .times-area { flex: 1; min-height: 0; display: flex; flex-direction: column; }
  .gridbox { flex: 1; min-height: 0; display: flex; flex-direction: column; }
  .panel { display: none; }
  .page { flex: 1; min-height: 0; overflow: auto; padding: 4px var(--pad) 120px; display: flex; flex-direction: column; gap: 24px; }
  .tabbar { position: relative; display: grid; grid-template-columns: repeat(4, 1fr); padding: 8px 8px calc(8px + env(safe-area-inset-bottom)); background: var(--bar-bg); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border-top: 1px solid var(--edge); flex: none; }
  .tab { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 0 6px; border-radius: 14px; color: var(--text-3); font-size: 12px; font-weight: 700; min-height: 52px; }
  .tab.on { color: var(--accent); }
  .sheet-open .tabbar, .sheet-open .float, .sheet-open .pill { visibility: hidden; }
  .tab :global(svg) { width: 24px; height: 24px; }
  .float { position: absolute; left: var(--pad); right: var(--pad); bottom: calc(20px + env(safe-area-inset-bottom)); z-index: 5; }
  .planner .float { bottom: calc(96px + env(safe-area-inset-bottom)); }
  .pill { position: absolute; left: 50%; transform: translateX(-50%); bottom: calc(96px + env(safe-area-inset-bottom)); z-index: 4; padding: 10px 14px; border-radius: 999px; background: oklch(0.15 0.03 265 / .85); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid var(--edge-2); font-size: 13px; font-weight: 600; white-space: nowrap; max-width: calc(100vw - 48px); overflow: hidden; text-overflow: ellipsis; box-shadow: 0 10px 30px oklch(0 0 0 / .4); }
  .planner .pill { bottom: calc(172px + env(safe-area-inset-bottom)); }
  .invitee .pill { bottom: calc(96px + env(safe-area-inset-bottom)); }
  .brand { font-size: 20px; font-weight: 800; letter-spacing: -0.02em; color: var(--text); }
  .brand b { color: var(--accent); }
  .nav { display: flex; flex-direction: column; gap: 4px; }
  .nav button { display: flex; align-items: center; gap: 12px; height: 48px; padding: 0 14px; border-radius: 14px; color: var(--text-2); font-size: 15px; font-weight: 700; border: 1px solid transparent; text-align: left; }
  .nav button.on { background: var(--glass-2); color: var(--text); border-color: var(--edge); }
  .nav button :global(svg) { width: 22px; height: 22px; }
  @media (min-width: 900px) {
    .shell { flex-direction: row; }
    .side { display: flex; flex-direction: column; gap: 32px; width: 264px; flex: none; padding: 28px 24px; border-right: 1px solid var(--edge); background: oklch(1 0 0 / .03); }
    .side .sub { font-size: 14px; }
    .mhead { padding: 24px 32px 16px; }
    .mhead .title-row .min0 h2 { font-size: 22px; }
    .phone-only { display: none !important; }
    .times-area { flex-direction: row; gap: 24px; margin: 0 32px 32px; min-height: 0; }
    .gridbox { margin: 0; border: 1px solid var(--edge); border-radius: 16px; overflow: hidden; }
    .panel { display: flex; flex-direction: column; gap: 16px; width: 360px; flex: none; padding: 24px; align-self: flex-start; max-height: 100%; overflow: auto; }
    .page { padding: 4px 32px 32px; max-width: 760px; }
    .tabbar { display: none; }
    .float { left: auto; right: 32px; bottom: 56px; width: 320px; }
    .planner .float { bottom: 56px; }
    .pill, .planner .pill, .invitee .pill { bottom: 56px; }
  }
</style>
