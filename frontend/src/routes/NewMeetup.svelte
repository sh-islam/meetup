<script>
  // New meetup wizard: one job per screen. Steps live in the hash (#/new/1 … #/new/6, #/new/done).
  import DatePicker from '../components/DatePicker.svelte'
  import HourRange from '../components/HourRange.svelte'
  import TimeGrid from '../components/TimeGrid.svelte'
  import InviteeList from '../components/InviteeList.svelte'
  import MapPicker from '../components/MapPicker.svelte'
  import IconPicker from '../components/IconPicker.svelte'
  import { iconSvg } from '../lib/icons.js'
  import Sheet from '../components/Sheet.svelte'
  import SaveSheet from '../components/SaveSheet.svelte'
  import { api } from '../lib/api.js'
  import { localTimezone, slotDate, slotMinutes, fmtDate, fmtTime, tzLabel } from '../lib/time.js'
  import { go, back, copyText, loadDraft, saveDraft, clearDraft, rememberMeetup } from '../lib/store.js'

  let { step = '1' } = $props()

  let d = $state(loadDraft())
  $effect(() => { saveDraft($state.snapshot(d)) })

  let hoursOpen = $state(false)
  let optionsOpen = $state(false)
  let saveOpen = $state(false)
  let busy = $state(false)
  let error = $state('')
  let created = $state(null)
  let copied = $state('')
  const timezone = localTimezone()
  const tzText = $derived(tzLabel(timezone, d.dates[0]))
  const TOTAL = 6
  const n = $derived(parseInt(step, 10) || 1)

  // drop painted slots that fall outside the current dates / hours
  $effect(() => {
    const ds = new Set(d.dates)
    const lo = d.hourStart * 60, hi = d.hourEnd * 60
    const keep = d.mySlots.filter((s) => ds.has(slotDate(s)) && slotMinutes(s) >= lo && slotMinutes(s) < hi)
    if (keep.length !== d.mySlots.length) d.mySlots = keep
  })
  // guard: can't be on a later step without the earlier ones, or on done without a result
  $effect(() => {
    if (step === 'done' && !created) go('/new/1', true)
    else if (n >= 2 && !d.dates.length) go('/new/1', true)
    else if (n >= 4 && !d.title.trim()) go('/new/3', true)
    else if (n >= 5 && !(d.plannerName.trim() && d.plannerEmail.trim())) go('/new/4', true)
  })

  const hoursLabel = $derived(`${fmtTime(d.hourStart * 60, true)} to ${d.hourEnd === 24 ? 'midnight' : fmtTime(d.hourEnd * 60, true)}`)
  const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

  function next() { go(`/new/${n + 1}`); window.scrollTo(0, 0) }
  function prev() { if (n > 1) go(`/new/${n - 1}`); else back('/') }

  async function create() {
    error = ''
    busy = true
    try {
      created = await api.createMeetup({
        title: d.title, description: d.description, location: d.location, icon: d.icon, timezone,
        hour_start: d.hourStart, hour_end: d.hourEnd, dates: d.dates, paint_mode: d.paintMode,
        planner: { name: d.plannerName, email: d.plannerEmail }, invitees: d.invitees, availability: d.mySlots,
      })
      clearDraft()
      rememberMeetup({ token: created.planner_token, title: created.meetup.title, role: 'planner', icon: created.meetup.icon })
      go('/new/done')
      window.scrollTo(0, 0)
    } catch (e) { error = e.message } finally { busy = false }
  }
  async function copy(text, key) {
    if (await copyText(text)) { copied = key; setTimeout(() => { if (copied === key) copied = '' }, 1500) }
  }
  function finish() { d = loadDraft(); go(`/m/${created.planner_token}`) }
</script>

{#snippet top(label)}
  <div class="top">
    <button type="button" class="icon-btn" onclick={prev} aria-label="Back"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg></button>
    <span class="label">{label}</span>
  </div>
{/snippet}

{#if step === 'done' && created}
  <div class="screen column">
    <div class="top"><span></span><span class="label">Done</span></div>
    <div class="body">
      <div>
        {#if created.meetup.icon}<div class="tile">{@html iconSvg(created.meetup.icon, 34)}</div>{/if}
        <h1>“{created.meetup.title}” is ready</h1>
        <p class="lead">{created.mail_configured ? 'Invites are on their way. Your planner link was emailed to you too.' : 'Email isn’t set up on the server yet, so nothing was sent. Share the links below yourself.'}</p>
      </div>
      <div class="msg info">Meetups you create or open are saved on this device and listed on the Meetup home screen. <button type="button" class="inline-link" onclick={() => (saveOpen = true)}>Bookmark or install</button> to get back even faster.</div>
      <div>
        <div class="label" style="margin-bottom:12px">Your planner link</div>
        <div class="glass linkcard">
          <div class="who">You <span class="badge">planner</span></div>
          <code>{created.participants.find((p) => p.role === 'planner').url}</code>
          <button type="button" class="btn ghost sm" onclick={() => copy(created.participants.find((p) => p.role === 'planner').url, 'planner')}>{copied === 'planner' ? 'Copied' : 'Copy link'}</button>
          <div class="hint" style="margin:0">Keep it to yourself, anyone with it can change the meetup.</div>
        </div>
      </div>
      {#if created.participants.some((p) => p.role === 'invitee')}
        <div>
          <div class="label" style="margin-bottom:12px">Invitee links, one per person</div>
          <div class="stack" style="gap:12px">
            {#each created.participants.filter((p) => p.role === 'invitee') as p (p.id)}
              <div class="glass linkcard">
                <div class="who">{p.name} <span class="caption">{p.email}</span></div>
                <code>{p.url}</code>
                <button type="button" class="btn ghost sm" onclick={() => copy(p.url, p.id)}>{copied === p.id ? 'Copied' : 'Copy link'}</button>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
    <div class="bottom"><button type="button" class="btn" onclick={finish}>Open my dashboard</button></div>
  </div>
  <Sheet open={saveOpen} onclose={() => (saveOpen = false)} title="Save">
    <SaveSheet url={created.participants.find((p) => p.role === 'planner').url} title={created.meetup.title} onclose={() => (saveOpen = false)} />
  </Sheet>

{:else if n === 1}
  <div class="screen column">
    {@render top(`Step 1 of ${TOTAL}`)}
    <div class="body">
      <div><h1>Which days?</h1><p class="lead">Pick every day that could work. You'll select your free times next.</p></div>
      <DatePicker bind:dates={d.dates} />
    </div>
    <div class="bottom"><button type="button" class="btn" disabled={!d.dates.length} onclick={next}>Next<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg></button></div>
  </div>

{:else if n === 2}
  <div class="screen column wide fixed">
    {@render top(`Step 2 of ${TOTAL}`)}
    <div class="body tight" style="padding-bottom:0">
      <div class="row between">
        <div><h1>When are you free?</h1><p class="lead">Press and hold, then drag to select the times you're free. Do the same over a selected time to clear it.</p></div>
      </div>
      <div class="row between">
        <button type="button" class="chip" onclick={() => (hoursOpen = true)}><span class="txt">Hours: {hoursLabel}</span><span class="x" aria-hidden="true">›</span></button>
        <span class="caption">{d.mySlots.length ? `${d.mySlots.length * 15 / 60}h selected` : ''}</span>
      </div>
      <div class="gridbox">
        <TimeGrid dates={d.dates} hourStart={d.hourStart} hourEnd={d.hourEnd} bind:mySlots={d.mySlots} fill />
      </div>
    </div>
    <div class="bottom">
      <button type="button" class="btn" onclick={next}>{d.mySlots.length ? 'Next' : 'Skip for now'}<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg></button>
    </div>
  </div>
  <Sheet open={hoursOpen} onclose={() => (hoursOpen = false)} title="Hours to show">
    <h2 style="text-align:center">Hours to show</h2>
    <p class="caption" style="text-align:center">Everyone sees this range on the grid. Times are in {tzText}.</p>
    <HourRange bind:hourStart={d.hourStart} bind:hourEnd={d.hourEnd} />
    <button type="button" class="btn sm" onclick={() => (hoursOpen = false)}>Done</button>
  </Sheet>

{:else if n === 3}
  <div class="screen column">
    {@render top(`Step 3 of ${TOTAL}`)}
    <div class="body">
      <div><h1>What is it?</h1><p class="lead">A name people will recognise in their inbox.</p></div>
      <div class="field"><label for="title">Title</label><input id="title" type="text" placeholder="Board game night" bind:value={d.title} autocomplete="off" /></div>
      <div class="field"><label>Icon</label><IconPicker bind:value={d.icon} /></div>
      <div class="field"><label for="desc">Description <span class="muted">(optional)</span></label><textarea id="desc" placeholder="Anything people should know" bind:value={d.description}></textarea></div>
    </div>
    <div class="bottom"><button type="button" class="btn" disabled={!d.title.trim()} onclick={next}>Next<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg></button></div>
  </div>

{:else if n === 4}
  <div class="screen column">
    {@render top(`Step 4 of ${TOTAL}`)}
    <div class="body">
      <div><h1>Who are you?</h1><p class="lead">Your planner link goes to this email.</p></div>
      <div class="field"><label for="pname">Your name</label><input id="pname" type="text" bind:value={d.plannerName} autocomplete="name" /></div>
      <div class="field"><label for="pemail">Your email</label><input id="pemail" type="email" bind:value={d.plannerEmail} autocomplete="email" /></div>
    </div>
    <div class="bottom"><button type="button" class="btn" disabled={!d.plannerName.trim() || !EMAIL_RE.test(d.plannerEmail.trim())} onclick={next}>Next<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg></button></div>
  </div>

{:else if n === 5}
  <div class="screen column">
    {@render top(`Step 5 of ${TOTAL}`)}
    <div class="body">
      <div><h1>Who's invited?</h1><p class="lead">Each person gets their own link. You can add more later.</p></div>
      <InviteeList bind:invitees={d.invitees} exclude={d.plannerEmail} />
    </div>
    <div class="bottom"><button type="button" class="btn" onclick={next}>{d.invitees.length ? 'Next' : 'Skip for now'}<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg></button></div>
  </div>

{:else}
  <div class="screen column">
    {@render top(`Step 6 of ${TOTAL}`)}
    <div class="body">
      <div><h1>Review</h1><p class="lead">Tap a row to change it.</p></div>
      {#if error}<div class="msg error">{error}</div>{/if}
      <div class="glass" style="padding:4px 20px">
        <button type="button" class="list-row" onclick={() => go('/new/3')}><div class="main"><div class="t">{#if d.icon}<span class="h-icon">{@html iconSvg(d.icon, 20)}</span>{/if}{d.title}</div><div class="s">{d.description || 'No description'}</div></div><span class="chev">›</span></button>
        <button type="button" class="list-row" onclick={() => go('/new/1')}><div class="main"><div class="t">{d.dates.length} {d.dates.length === 1 ? 'day' : 'days'}</div><div class="s">{d.dates.map((x) => fmtDate(x)).join(', ')}</div></div><span class="chev">›</span></button>
        <button type="button" class="list-row" onclick={() => go('/new/2')}><div class="main"><div class="t">Your times</div><div class="s">{d.mySlots.length ? `${d.mySlots.length * 15 / 60}h selected · hours ${hoursLabel}` : `Nothing selected yet · hours ${hoursLabel}`}</div></div><span class="chev">›</span></button>
        <button type="button" class="list-row" onclick={() => go('/new/4')}><div class="main"><div class="t">{d.plannerName}</div><div class="s">{d.plannerEmail}</div></div><span class="chev">›</span></button>
        <button type="button" class="list-row" onclick={() => go('/new/5')}><div class="main"><div class="t">{d.invitees.length} invited</div><div class="s">{d.invitees.length ? d.invitees.map((i) => i.name || i.email).join(', ') : 'Nobody yet'}</div></div><span class="chev">›</span></button>
      </div>
      <div>
        <button type="button" class="list-row opt" onclick={() => (optionsOpen = !optionsOpen)}><div class="main"><div class="t">Options</div><div class="s">{d.paintMode === 'free' ? 'Anyone can select any time' : 'Only the times I picked'}{d.location ? ` · ${d.location}` : ''}</div></div><span class="chev">{optionsOpen ? '⌃' : '⌄'}</span></button>
        {#if optionsOpen}
          <div class="stack" style="margin-top:12px">
            <div>
              <div class="label" style="margin-bottom:10px">Time selection</div>
              <div class="stack" style="gap:8px">
                <button type="button" class="choice" class:on={d.paintMode === 'free'} onclick={() => (d.paintMode = 'free')}><span class="dot"></span><span><div class="t">Anyone can select any time</div><div class="s">Best for finding out when everyone is free.</div></span></button>
                <button type="button" class="choice" class:on={d.paintMode === 'restricted'} onclick={() => (d.paintMode = 'restricted')}><span class="dot"></span><span><div class="t">Only the times I picked</div><div class="s">Invitees can only choose within the times you selected.</div></span></button>
              </div>
            </div>
            <MapPicker bind:location={d.location} />
          </div>
        {/if}
      </div>
      <p class="caption">Times are in {tzText}.</p>
    </div>
    <div class="bottom"><button type="button" class="btn" disabled={busy} onclick={create}>{busy ? 'Creating…' : 'Create meetup'}</button></div>
  </div>
{/if}

<style>
  .fixed { height: 100dvh; }
  .fixed .body { min-height: 0; }
  .gridbox { flex: 1; min-height: 0; display: flex; flex-direction: column; margin: 0 calc(var(--pad) * -1); }
  .linkcard { padding: 16px; display: flex; flex-direction: column; gap: 10px; }
  .linkcard .who { font-weight: 700; display: flex; gap: 8px; align-items: center; }
  .linkcard code { font-size: 12px; word-break: break-all; color: var(--text-3); font-family: ui-monospace, Menlo, monospace; }
  .opt { border-top: 1px solid var(--line); }
  .h-icon { display: inline-block; vertical-align: -3px; margin-right: 8px; color: var(--accent); }
  .tile { width: 64px; height: 64px; border-radius: 20px; display: grid; place-items: center; background: var(--accent-soft); border: 1px solid oklch(0.80 0.14 215 / .4); color: var(--accent); margin-bottom: 16px; }
  .inline-link { color: var(--accent); font-weight: 700; text-decoration: underline; }
  @media (min-width: 900px) {
    .screen.column.wide { max-width: 960px; }
    .fixed { height: calc(100dvh - 48px); }
    .gridbox { margin: 0; border: 1px solid var(--edge); border-radius: 16px; overflow: hidden; }
  }
</style>
