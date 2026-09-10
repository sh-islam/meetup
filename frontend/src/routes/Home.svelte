<script>
  import { go, loadRecent, forgetMeetup, copyText } from '../lib/store.js'
  import { iconSvg } from '../lib/icons.js'
  import Sheet from '../components/Sheet.svelte'
  let recent = $state(loadRecent())
  let hiding = $state(null)     // the entry being hidden
  let copied = $state(false)
  const linkFor = (t) => `${location.origin}${location.pathname}#/m/${t}`
  async function copy() { if (await copyText(linkFor(hiding.token))) { copied = true; setTimeout(() => (copied = false), 1500) } }
  function confirmHide() { forgetMeetup(hiding.token); recent = loadRecent(); hiding = null }
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
            <button type="button" class="icon-btn" onclick={() => (hiding = m)} aria-label="Hide from this list">×</button>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<Sheet open={!!hiding} onclose={() => (hiding = null)} title="Hide">
  {#if hiding}
    <h2 style="text-align:center">Hide from this list?</h2>
    {#if hiding.role === 'planner'}
      <div class="msg error">You're the planner of this meetup. Without the link you can't manage or confirm it, so copy it somewhere safe first.</div>
    {:else}
      <p class="caption" style="text-align:center">The meetup isn't affected. You'll need the link from your email to open it again.</p>
    {/if}
    <div class="glass" style="padding:16px;text-align:left">
      <div style="font-weight:700">{#if hiding.icon}<span class="h-icon">{@html iconSvg(hiding.icon, 18)}</span>{/if}{hiding.title}</div>
      <div class="caption" style="margin-top:2px">{hiding.role === 'planner' ? 'You planned this' : 'You were invited'}</div>
      <code class="link">{linkFor(hiding.token)}</code>
    </div>
    <button type="button" class="btn ghost sm" onclick={copy}>{copied ? 'Copied' : 'Copy link'}</button>
    <button type="button" class="btn danger sm" onclick={confirmHide}>Hide from this list</button>
    <button type="button" class="link" onclick={() => (hiding = null)}>Keep it</button>
  {/if}
</Sheet>

<style>
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
