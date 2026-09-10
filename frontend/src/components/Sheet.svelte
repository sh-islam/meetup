<script>
  // Bottom sheet on phones; a right-hand panel on wide screens (when `panel` is true).
  // Children render via the `children` snippet. Close by tapping the scrim or pressing Escape.
  let { open = false, onclose = () => {}, panel = false, title = '', children } = $props()

  $effect(() => {
    if (!open) return
    const onKey = (e) => { if (e.key === 'Escape') onclose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })
</script>

{#if open}
  <div class="scrim" class:panel onclick={onclose} role="presentation"></div>
  <div class="sheet" class:panel role="dialog" aria-modal="true" aria-label={title}>
    <div class="grab"></div>
    {@render children?.()}
  </div>
{/if}

<style>
  .scrim { position: fixed; inset: 0; z-index: 40; background: oklch(0 0 0 / .35); animation: fade .18s ease-out; }
  .sheet {
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 41;
    padding: 12px var(--pad) calc(20px + env(safe-area-inset-bottom));
    border-radius: 28px 28px 0 0;
    background: oklch(0.16 0.03 265 / .94);
    backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
    border-top: 1px solid var(--edge-2);
    box-shadow: 0 -20px 60px oklch(0 0 0 / .45);
    display: flex; flex-direction: column; gap: 16px;
    max-height: calc(100dvh - 48px); overflow: auto;
    animation: rise .22s cubic-bezier(.2,.8,.2,1);
  }
  .grab { width: 40px; height: 5px; border-radius: 3px; background: oklch(1 0 0 / .22); margin: 0 auto; flex: none; }
  @keyframes rise { from { transform: translateY(24px); opacity: 0; } to { transform: none; opacity: 1; } }
  @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
  @media (min-width: 900px) {
    .sheet { left: auto; right: 24px; bottom: 24px; top: 24px; width: 380px; border-radius: 22px; border: 1px solid var(--edge-2); padding: 24px; max-height: none; animation: slide .22s cubic-bezier(.2,.8,.2,1); }
    .sheet .grab { display: none; }
    .scrim { background: oklch(0 0 0 / .2); }
    @keyframes slide { from { transform: translateX(24px); opacity: 0; } to { transform: none; opacity: 1; } }
  }
</style>
