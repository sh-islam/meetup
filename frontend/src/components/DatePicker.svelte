<script>
  // Month calendar; tap dates to toggle them. Past dates are disabled.
  import { todayISO, fmtDate } from '../lib/time.js'

  let { dates = $bindable([]), max = 21 } = $props()

  const today = todayISO()
  const t = new Date()
  let viewYear = $state(t.getFullYear())
  let viewMonth = $state(t.getMonth())

  const pad = (n) => String(n).padStart(2, '0')
  const selected = $derived(new Set(dates))

  const weeks = $derived.by(() => {
    const first = new Date(viewYear, viewMonth, 1)
    const startDow = first.getDay()
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()
    const cells = []
    for (let i = 0; i < startDow; i++) cells.push(null)
    for (let d = 1; d <= daysInMonth; d++) cells.push(`${viewYear}-${pad(viewMonth + 1)}-${pad(d)}`)
    while (cells.length % 7) cells.push(null)
    const out = []
    for (let i = 0; i < cells.length; i += 7) out.push(cells.slice(i, i + 7))
    return out
  })
  const monthLabel = $derived(new Date(viewYear, viewMonth, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' }))
  const canGoBack = $derived(viewYear > t.getFullYear() || (viewYear === t.getFullYear() && viewMonth > t.getMonth()))

  function prev() { if (!canGoBack) return; if (viewMonth === 0) { viewMonth = 11; viewYear-- } else viewMonth-- }
  function next() { if (viewMonth === 11) { viewMonth = 0; viewYear++ } else viewMonth++ }
  function toggle(iso) {
    if (!iso || iso < today) return
    if (selected.has(iso)) dates = dates.filter((d) => d !== iso)
    else if (dates.length < max) dates = [...dates, iso].sort()
  }
</script>

<div class="glass cal">
  <div class="cal-head">
    <button type="button" class="icon-btn" onclick={prev} disabled={!canGoBack} aria-label="Previous month">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>
    </button>
    <strong>{monthLabel}</strong>
    <button type="button" class="icon-btn" onclick={next} aria-label="Next month">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>
    </button>
  </div>
  <div class="cal-grid">
    {#each ['S', 'M', 'T', 'W', 'T', 'F', 'S'] as dow, i (i)}<div class="dow">{dow}</div>{/each}
    {#each weeks as week}
      {#each week as iso}
        {#if iso}
          <button type="button" class="day" class:on={selected.has(iso)} class:today={iso === today} class:past={iso < today}
            disabled={iso < today || (!selected.has(iso) && dates.length >= max)} onclick={() => toggle(iso)}>{+iso.slice(8)}</button>
        {:else}
          <div></div>
        {/if}
      {/each}
    {/each}
  </div>
</div>
{#if dates.length}
  <div>
    <div class="label" style="margin-bottom:12px">{dates.length} {dates.length === 1 ? 'day' : 'days'} picked</div>
    <div class="chips">
      {#each dates as d (d)}
        <span class="chip"><span class="txt">{fmtDate(d)}</span><button type="button" class="x" onclick={() => toggle(d)} aria-label="Remove">×</button></span>
      {/each}
    </div>
  </div>
{/if}

<style>
  .cal { padding: 20px; }
  .cal-head { display: flex; align-items: center; justify-content: space-between; height: 44px; margin-bottom: 12px; }
  .cal-head strong { font-size: 17px; font-weight: 700; }
  .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }
  .dow { text-align: center; font-size: 12px; font-weight: 700; color: var(--text-3); letter-spacing: .04em; height: 32px; line-height: 32px; }
  .day { height: 44px; display: grid; place-items: center; border-radius: 12px; font-size: 16px; font-weight: 600; color: var(--text); }
  .day:hover:not(:disabled) { background: var(--glass-2); }
  .day.past { color: var(--text-3); }
  .day.today { box-shadow: inset 0 0 0 1px var(--edge-2); }
  .day.on { background: var(--accent); color: var(--accent-ink); font-weight: 800; }
  .day:disabled { opacity: .6; }
</style>
