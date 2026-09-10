<script>
  // Placeholder for the Google Maps pin picker (later feature). For now a plain text location.
  let { location = $bindable(''), readonly = false } = $props()
</script>

{#if readonly}
  {#if location}<div class="loc"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s7-6.5 7-12a7 7 0 1 0-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>{location}</div>{/if}
{:else}
  <div class="field">
    <label for="loc">Location <span class="muted">(optional)</span></label>
    <input id="loc" type="text" placeholder="Where are we meeting?" bind:value={location} />
    <div class="hint">Map pin picker coming later.</div>
  </div>
{/if}

<style>
  .loc { display: inline-flex; align-items: center; gap: 8px; color: var(--text-2); font-size: 15px; font-weight: 500; }
</style>
