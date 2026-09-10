<script>
  // Details sheet body for a meetup: title, planner, description, location, status.
  // (Nudging itself lives in ConfirmDialog, the decision sheet.)
  import MapPicker from './MapPicker.svelte'
  import { fmtBlock } from '../lib/time.js'
  let { meetup, planner, people = [], confirmedNames = [], onclose = () => {} } = $props()
</script>

<h2>{meetup.title}</h2>
<div class="muted" style="font-size:15px">Planned by {planner.name} · {people.length} people</div>
{#if meetup.location}<MapPicker location={meetup.location} readonly />{/if}
{#if meetup.description}<p class="desc">{meetup.description}</p>{:else}<p class="caption">No description.</p>{/if}
{#if meetup.status === 'confirmed'}
  <div class="msg ok"><b>Confirmed:</b> {fmtBlock(meetup.confirmed_start, meetup.confirmed_end)}<br /><span style="font-size:13px">Coming: {confirmedNames.length ? confirmedNames.join(', ') : 'nobody marked this time'}</span></div>
{/if}
<div>
  <div class="label" style="margin-bottom:8px">Who's invited</div>
  <div class="chips">
    {#each people as p (p.id)}<span class="chip solo"><span class="txt">{p.name}{p.role === 'planner' ? ' · planner' : ''}</span></span>{/each}
  </div>
</div>
<div class="caption">Times are in {meetup.timezone}.</div>
<button type="button" class="btn ghost sm" onclick={onclose}>Close</button>

<style>
  .desc { white-space: pre-line; font-size: 16px; line-height: 1.5; color: var(--text); }
</style>
