<script>
  // Details sheet body: who, where, what, progress, the best time so far, and the time-selection setting.
  import MapPicker from './MapPicker.svelte'
  import { fmtBlock, tzLabel } from '../lib/time.js'
  import { iconSvg } from '../lib/icons.js'
  let { meetup, planner, people = [], confirmedNames = [], responded = 0, best = null, isPlanner = false, onclose = () => {}, onsave = () => {}, ondropout = () => {} } = $props()
</script>

<h2>{meetup.title}{#if meetup.icon}<span class="h-icon">{@html iconSvg(meetup.icon, 20)}</span>{/if}</h2>
<div class="muted" style="font-size:15px">Planned by {planner.name} · {people.length} people</div>
{#if meetup.location}<MapPicker location={meetup.location} readonly />{/if}
{#if meetup.description}<p class="desc">{meetup.description}</p>{/if}
{#if meetup.status === 'confirmed'}
  <div class="msg ok"><b>Confirmed:</b> {fmtBlock(meetup.confirmed_start, meetup.confirmed_end)}<br /><span style="font-size:13px">Coming: {confirmedNames.length ? confirmedNames.join(', ') : 'nobody marked this time'}</span></div>
{/if}
<div class="glass facts">
  <div class="fact"><span class="caption">Answered</span><b>{responded} of {people.length}</b></div>
  <div class="fact"><span class="caption">Best time so far</span>{#if best}<b>{fmtBlock(best.start, best.end)}</b><span class="caption">{best.count} of {best.total} free · {best.percent}%</span>{:else}<b class="muted">No times selected yet</b>{/if}</div>
  <div class="fact"><span class="caption">Time selection</span><b>{meetup.paint_mode === 'free' ? 'Anyone can select any time' : `Only the times ${isPlanner ? 'I' : planner.name} picked`}</b></div>
  <div class="fact"><span class="caption">Timezone</span><b>{tzLabel(meetup.timezone, meetup.dates[0])}</b></div>
</div>
<div>
  <div class="label" style="margin-bottom:8px">Who's invited</div>
  <div class="chips">
    {#each people as p (p.id)}<span class="chip solo" class:dim={!p.responded}><span class="txt">{p.name}{p.role === 'planner' ? ' · planner' : ''}</span></span>{/each}
  </div>
  <div class="hint">Faded names have yet to respond.</div>
</div>
<button type="button" class="btn ghost sm" onclick={onsave}>Save this meetup</button>
{#if !isPlanner}<button type="button" class="link danger-text" onclick={ondropout}>Drop out of this meetup</button>{/if}
<button type="button" class="link" onclick={onclose}>Close</button>

<style>
  .h-icon { display: inline-block; vertical-align: -3px; margin-left: 8px; color: var(--accent); }
  .desc { white-space: pre-line; font-size: 16px; line-height: 1.5; color: var(--text); }
  .facts { padding: 4px 16px; }
  .fact { display: flex; flex-direction: column; gap: 2px; padding: 12px 0; border-bottom: 1px solid var(--line); }
  .fact:last-child { border-bottom: 0; }
  .fact b { font-size: 16px; font-weight: 700; }
  .chip.dim { opacity: .5; }
</style>
