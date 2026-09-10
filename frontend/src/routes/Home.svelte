<script>
  import { go, loadRecent, forgetMeetup, copyText, loadHidden, hideMeetup, restoreMeetup } from '../lib/store.js'
  import { probe, api, setToken } from '../lib/api.js'
  import { iconSvg } from '../lib/icons.js'
  import Sheet from '../components/Sheet.svelte'
  let recent = $state(loadRecent())
  let hiding = $state(null)     // the entry being acted on
  let copied = $state(false)
  let dropStep = $state(false)  // second confirmation for dropping out
  let mode = $state('hide')     // hide | remove
  let busy = $state(false)
  let toast = $state('')
  function say(m) { toast = m; setTimeout(() => (toast = ''), 3200) }
  async function dropOut() {
    busy = true
    try {
      setToken(hiding.token)
      await api.leave()
      forgetMeetup(hiding.token); recent = loadRecent(); hidden = loadHidden()
      say(`You dropped out of ${hiding.title}. The planner has been told.`)
      hiding = null; dropStep = false
    } catch (e) { say(e.message) } finally { busy = false }
  }
  const linkFor = (t) => `${location.origin}${location.pathname}#/m/${t}`
  async function copy() { if (await copyText(linkFor(hiding.token))) { copied = true; setTimeout(() => (copied = false), 1500) } }
  function confirmHide() { hideMeetup(hiding.token); recent = loadRecent(); hidden = loadHidden(); hiding = null }

  // ---- restore hidden ----
  let hidden = $state(loadHidden())
  let restoreOpen = $state(false)
  let status = $state({})        // token -> checking | ok | gone | unreachable
  async function openRestore() {
    restoreOpen = true
    hidden = loadHidden()
    for (const m of hidden) {
      status[m.token] = 'checking'
      try { status[m.token] = (await probe(m.token)) ? 'ok' : 'gone' } catch { status[m.token] = 'unreachable' }
    }
  }
  function restore(m) { restoreMeetup(m.token); hidden = loadHidden(); recent = loadRecent(); if (!hidden.length) restoreOpen = false }
  function discard(m) { forgetMeetup(m.token); hidden = loadHidden() }
</script>

<div class="home">
  <div class="mark" aria-hidden="true">
    <svg viewBox="0 0 512 512" width="64" height="64"><rect width="512" height="512" rx="116" fill="oklch(0.19 0.04 265)"/><rect x="1" y="1" width="510" height="510" rx="115" fill="none" stroke="#fff" stroke-opacity=".12" stroke-width="2"/><g><rect x="88" y="88" width="96" height="96" rx="22" fill="#fff" fill-opacity=".08"/><rect x="208" y="88" width="96" height="96" rx="22" fill="#44d9f5" fill-opacity=".22"/><rect x="328" y="88" width="96" height="96" rx="22" fill="#fff" fill-opacity=".08"/><rect x="88" y="208" width="96" height="96" rx="22" fill="#44d9f5" fill-opacity=".22"/><rect x="208" y="208" width="96" height="96" rx="22" fill="#5ee6ff"/><rect x="328" y="208" width="96" height="96" rx="22" fill="#44d9f5" fill-opacity=".45"/><rect x="88" y="328" width="96" height="96" rx="22" fill="#fff" fill-opacity=".08"/><rect x="208" y="328" width="96" height="96" rx="22" fill="#44d9f5" fill-opacity=".45"/><rect x="328" y="328" width="96" height="96" rx="22" fill="#5ef0b8"/></g></svg>
  </div>
  <h1>Meet<span>up</span></h1>
  <p class="lead">Find the time when everyone's free.<br />No accounts required.</p>
  <div class="actions">
    <button type="button" class="btn" onclick={() => go('/new/1')}>New meetup</button>
    <button type="button" class="btn ghost" onclick={() => go('/open')}>Existing meetup</button>
  </div>
  {#if recent.length}
    <div class="recent">
      <div class="label" style="margin-bottom:12px">Your meetups on this device</div>
      <div class="glass" style="padding:4px 16px;text-align:left">
        {#each recent as m (m.token)}
          <div class="list-row">
            <button type="button" class="main rbtn" onclick={() => go(`/m/${m.token}`)}><div class="t">{#if m.icon}<span class="h-icon">{@html iconSvg(m.icon, 18)}</span>{/if}{m.title}</div><div class="s">{m.role === 'planner' ? 'You planned this' : 'You were invited'}</div></button>
            <div class="row" style="gap:2px">
              <button type="button" class="icon-btn eye" onclick={() => { hiding = m; mode = 'hide'; dropStep = false }} aria-label="Hide from this device"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.7 5.1A10.9 10.9 0 0 1 12 5c7 0 10 7 10 7a13.2 13.2 0 0 1-1.7 2.5"/><path d="M6.6 6.6A13.5 13.5 0 0 0 2 12s3 7 10 7a9.7 9.7 0 0 0 5.4-1.6"/><path d="M14.1 14.1a3 3 0 1 1-4.2-4.2"/><path d="m2 2 20 20"/></svg></button>
              <button type="button" class="icon-btn trash" onclick={() => { hiding = m; mode = 'remove'; dropStep = false }} aria-label={m.role === 'planner' ? 'Delete the meetup' : 'Drop out'}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6"/><path d="M14 11v6"/></svg></button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

{#if hidden.length}
  <button type="button" class="restore" onclick={openRestore}>Restore hidden ({hidden.length})</button>
{/if}

<Sheet open={restoreOpen} onclose={() => (restoreOpen = false)} title="Restore">
  <h2 style="text-align:center">Hidden meetups</h2>
  <p class="caption" style="text-align:center">Only meetups that still exist can be restored.</p>
  <div class="glass" style="padding:4px 16px;text-align:left">
    {#each hidden as m (m.token)}
      <div class="list-row">
        <div class="main">
          <div class="t">{#if m.icon}<span class="h-icon">{@html iconSvg(m.icon, 18)}</span>{/if}{m.title}</div>
          <div class="s">
            {#if status[m.token] === 'checking'}Checking…
            {:else if status[m.token] === 'ok'}{m.role === 'planner' ? 'You planned this' : 'You were invited'}
            {:else if status[m.token] === 'gone'}<span class="danger-text">{m.role === 'planner' ? 'Deleted' : 'The planner deleted this meetup'}</span>
            {:else}Could not reach the server{/if}
          </div>
        </div>
        {#if status[m.token] === 'ok'}
          <button type="button" class="btn ghost sm auto" onclick={() => restore(m)}>Restore</button>
        {:else if status[m.token] === 'gone'}
          <button type="button" class="icon-btn" onclick={() => discard(m)} aria-label="Remove">×</button>
        {/if}
      </div>
    {:else}
      <div class="list-row"><div class="main"><div class="s">Nothing hidden.</div></div></div>
    {/each}
  </div>
  <button type="button" class="link" onclick={() => (restoreOpen = false)}>Close</button>
</Sheet>

<Sheet open={!!hiding} onclose={() => (hiding = null)} title="Remove">
  {#if hiding && dropStep}
    <h2 style="text-align:center">Drop out of “{hiding.title}”?</h2>
    <p class="muted" style="text-align:center;font-size:15px">The planner gets an email saying you're dropping out. Your times are removed and your link stops working. To rejoin later you'd need a new invite.</p>
    <button type="button" class="btn danger sm" disabled={busy} onclick={dropOut}>{busy ? 'Dropping out…' : 'Yes, drop out'}</button>
    <button type="button" class="link" onclick={() => (dropStep = false)}>Back</button>
  {:else if hiding && mode === 'hide'}
    <h2 style="text-align:center">Hide from this device?</h2>
    {#if hiding.role === 'planner'}
      <div class="msg error">You're the planner of this meetup. Without the link you can't manage or confirm it, so copy it somewhere safe first.</div>
    {:else}
      <p class="caption" style="text-align:center">The meetup isn't affected. You can bring it back with Restore hidden, or open it from the link in your email.</p>
    {/if}
    <div class="glass" style="padding:16px;text-align:left">
      <div style="font-weight:700">{#if hiding.icon}<span class="h-icon">{@html iconSvg(hiding.icon, 18)}</span>{/if}{hiding.title}</div>
      <div class="caption" style="margin-top:2px">{hiding.role === 'planner' ? 'You planned this' : 'You were invited'}</div>
      <code class="link">{linkFor(hiding.token)}</code>
    </div>
    <button type="button" class="btn ghost sm" onclick={copy}>{copied ? 'Copied' : 'Copy link'}</button>
    <button type="button" class="btn sm" onclick={confirmHide}>Hide from this device</button>
    <button type="button" class="link" onclick={() => (hiding = null)}>Keep it</button>
  {:else if hiding}
    {#if hiding.role === 'planner'}
      <h2 style="text-align:center">Delete “{hiding.title}”?</h2>
      <p class="caption" style="text-align:center">You're the planner. Deleting removes the meetup for everyone. You'll confirm on the next screen.</p>
      <button type="button" class="btn danger sm" onclick={() => { const t = hiding.token; hiding = null; go(`/m/${t}/settings`) }}>Continue to delete…</button>
    {:else}
      <h2 style="text-align:center">Drop out of “{hiding.title}”?</h2>
      <p class="caption" style="text-align:center">This tells the planner and takes you off the meetup. To only tidy this list, use hide instead.</p>
      <button type="button" class="btn danger sm" onclick={() => (dropStep = true)}>Drop out of the meetup</button>
    {/if}
    <button type="button" class="link" onclick={() => (hiding = null)}>Cancel</button>
  {/if}
</Sheet>
{#if toast}<div class="toast">{toast}</div>{/if}

<style>
  .eye { color: var(--text-3); }
  .eye:hover { color: var(--text); }
  .trash { color: var(--danger); opacity: .8; }
  .trash:hover { opacity: 1; }
  .restore { position: fixed; right: 16px; bottom: calc(16px + env(safe-area-inset-bottom)); z-index: 5; font-size: 13px; font-weight: 700; color: var(--text-3); padding: 10px 14px; border-radius: 999px; background: var(--glass); border: 1px solid var(--edge); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
  .restore:hover { color: var(--text); }
  code.link { display: block; margin-top: 10px; font-size: 12px; word-break: break-all; color: var(--text-3); font-family: ui-monospace, Menlo, monospace; }
  .home { min-height: 100dvh; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 24px var(--pad) calc(24px + env(safe-area-inset-bottom)); max-width: 420px; margin: 0 auto; }
  .mark { margin-bottom: 24px; filter: drop-shadow(0 16px 40px oklch(0.80 0.14 215 / .25)); }
  h1 { font-size: 44px; letter-spacing: -0.03em; }
  h1 span { color: var(--accent); }
  .lead { font-size: 17px; }
  .actions { display: flex; flex-direction: column; gap: 12px; margin-top: 40px; width: 100%; }
  .recent { width: 100%; margin-top: 40px; }
  .rbtn { text-align: left; }
  .h-icon { display: inline-block; vertical-align: -3px; margin-right: 8px; color: var(--accent); }
</style>
