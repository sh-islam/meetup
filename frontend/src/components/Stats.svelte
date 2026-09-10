<script>
  // Planner: ranked best windows as cards. Tap a card to decide on it.
  import { fmtBlock, fmtDate } from '../lib/time.js'
  let { stats = null, participants = [], onpick = () => {} } = $props()
  const initial = (n) => (n || '?').trim().charAt(0).toUpperCase()
  function dur(min) { return min >= 60 ? `${Math.floor(min / 60)}h${min % 60 ? ` ${min % 60}m` : ''}` : `${min}m` }
</script>

{#if !stats}
  <p class="muted">Loading…</p>
{:else}
  {#if !stats.windows.length}
    <div class="glass card"><p class="muted">Nobody has selected any times yet. Best times appear here once they do.</p></div>
  {:else}
    <div class="wins">
      {#each stats.windows as w, i (w.start + w.end)}
        <button type="button" class="glass win" class:best={i === 0} onclick={() => onpick({ start: w.start, end: w.end })}>
          <div class="when">{fmtBlock(w.start, w.end)}</div>
          <div class="ring" class:full={w.count === w.total} style="--p:{w.percent}%"><span>{w.percent}%</span></div>
          <div class="meta">{dur(w.minutes)} · {#if w.missing.length}<span class="miss">missing {w.missing.join(', ')}</span>{:else}<span class="mint-text">everyone</span>{/if}</div>
          <div class="faces">
            {#each participants as p (p.id)}
              <span class="face" class:off={!w.available.includes(p.name)}>{initial(p.name)}</span>
            {/each}
          </div>
        </button>
      {/each}
    </div>
    <p class="caption" style="text-align:center">Tap a time to confirm it or nudge someone.</p>
  {/if}

  <div>
    <div class="label" style="margin-bottom:12px">By day</div>
    <div class="glass" style="padding:4px 20px">
      {#each stats.days as d (d.date)}
        <div class="list-row">
          <div class="main"><div class="t" style="font-size:15px">{fmtDate(d.date)}</div><div class="s">{d.people_any} of {d.total} free at some point</div></div>
          <div class="caption" style="text-align:right">{d.best_count} of {d.total}<br />together</div>
        </div>
      {/each}
    </div>
  </div>
{/if}

<style>
  .wins { display: flex; flex-direction: column; gap: 12px; }
  .win { display: grid; grid-template-columns: 1fr auto; grid-template-areas: "when ring" "meta ring" "faces faces"; gap: 6px 16px; padding: 20px; align-items: center; text-align: left; width: 100%; color: var(--text); }
  .win:hover { background: var(--glass-2); }
  .win.best { border-color: oklch(0.80 0.14 215 / .5); background: oklch(0.80 0.14 215 / .08); }
  .when { grid-area: when; font-size: 17px; font-weight: 700; }
  .meta { grid-area: meta; font-size: 13px; color: var(--text-2); font-weight: 500; }
  .meta .miss { color: var(--text-3); }
  .ring { grid-area: ring; width: 56px; height: 56px; border-radius: 50%; display: grid; place-items: center; font-size: 13px; font-weight: 800; background: conic-gradient(var(--accent) var(--p), oklch(1 0 0 / .08) 0); position: relative; }
  .ring::after { content: ''; position: absolute; inset: 5px; border-radius: 50%; background: var(--surface); }
  .ring span { position: relative; z-index: 1; }
  .ring.full { background: conic-gradient(var(--mint) 100%, transparent 0); }
  .ring.full span { color: var(--mint); }
  .faces { grid-area: faces; margin-top: 6px; }
</style>
