<script>
  // "Save this meetup": the ways to get back to a link that work across browsers.
  import { copyText, installPrompt } from '../lib/store.js'
  let { url = '', title = 'Meetup', onclose = () => {} } = $props()

  let copied = $state(false)
  let installed = $state(false)
  const canShare = typeof navigator !== 'undefined' && !!navigator.share
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : ''
  const isIOS = /iPhone|iPad|iPod/.test(ua)
  const isMac = /Macintosh/.test(ua) && !isIOS
  const isMobile = isIOS || /Android/.test(ua)
  const standalone = typeof window !== 'undefined' && (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone)

  async function copy() { if (await copyText(url)) { copied = true; setTimeout(() => (copied = false), 1500) } }
  async function share() { try { await navigator.share({ title, url }) } catch { /* cancelled */ } }
  async function install() {
    const p = installPrompt.get()
    if (!p) return
    p.prompt()
    try { const r = await p.userChoice; if (r.outcome === 'accepted') installed = true } catch { /* ignore */ }
    installPrompt.clear()
  }
</script>

<h2 style="text-align:center">Save this meetup</h2>
<p class="caption" style="text-align:center">Your link is already remembered on this device, so the Meetup home screen will list it. To get back even faster:</p>
<div class="stack" style="gap:8px">
  <button type="button" class="btn ghost sm" onclick={copy}>{copied ? 'Copied' : 'Copy link'}</button>
  {#if canShare}<button type="button" class="btn ghost sm" onclick={share}>Share or add to reading list…</button>{/if}
  {#if installPrompt.get() && !standalone}<button type="button" class="btn sm" onclick={install}>{installed ? 'Installed' : 'Install Meetup as an app'}</button>{/if}
</div>
<div class="glass" style="padding:14px 16px">
  {#if isIOS}
    <div class="caption"><b style="color:var(--text)">iPhone or iPad:</b> tap Share, then <b style="color:var(--text)">Add to Home Screen</b> for an app icon, or <b style="color:var(--text)">Add Bookmark</b>.</div>
  {:else if isMobile}
    <div class="caption"><b style="color:var(--text)">Android:</b> open the browser menu and choose <b style="color:var(--text)">Add to Home screen</b> or the star to bookmark.</div>
  {:else}
    <div class="caption"><b style="color:var(--text)">Bookmark:</b> press <b style="color:var(--text)">{isMac ? 'Cmd' : 'Ctrl'} + D</b> right now.</div>
  {/if}
</div>
<button type="button" class="link" onclick={onclose}>Close</button>
