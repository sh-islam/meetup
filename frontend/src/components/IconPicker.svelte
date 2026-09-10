<script>
  // Optional event icon. First option is blank and the default.
  import { ICONS, iconSvg } from '../lib/icons.js'
  let { value = $bindable('') } = $props()
</script>

<div class="picker" role="radiogroup" aria-label="Event icon">
  {#each ICONS as ic (ic.name)}
    <button type="button" class="ic" class:on={value === ic.name} role="radio" aria-checked={value === ic.name} title={ic.label} onclick={() => (value = ic.name)}>
      {#if ic.svg}{@html iconSvg(ic.name, 26)}{:else}<span class="none">—</span>{/if}
    </button>
  {/each}
</div>

<style>
  .picker { display: flex; gap: 10px; overflow-x: auto; padding: 4px 2px 8px; margin: 0 -2px; scrollbar-width: none; }
  .picker::-webkit-scrollbar { display: none; }
  .ic { flex: none; width: 56px; height: 56px; border-radius: 18px; display: grid; place-items: center; background: var(--glass-2); border: 1px solid var(--edge); color: var(--text-2); }
  .ic.on { background: var(--accent-soft); border-color: oklch(0.80 0.14 215 / .7); color: var(--accent); box-shadow: 0 0 0 3px oklch(0.80 0.14 215 / .18); }
  .none { font-size: 18px; color: var(--text-3); }
</style>
