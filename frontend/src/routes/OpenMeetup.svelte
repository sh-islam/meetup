<script>
  import { go, tokenFromInput, back } from '../lib/store.js'
  let value = $state('')
  let error = $state('')
  function open() {
    const t = tokenFromInput(value)
    if (!t) { error = 'Paste the link from your email, or just the code at the end of it.'; return }
    go(`/m/${t}`)
  }
</script>

<div class="screen column">
  <div class="top">
    <button type="button" class="icon-btn" onclick={() => back('/')} aria-label="Back"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg></button>
  </div>
  <div class="body">
    <div>
      <h1>Existing meetup</h1>
      <p class="lead">Paste your personal link, or just the code at the end of it. It's in the email you got.</p>
    </div>
    {#if error}<div class="msg error">{error}</div>{/if}
    <div class="field">
      <label for="tok">Link or code</label>
      <input id="tok" type="text" placeholder="https://…/#/m/abc123" bind:value={value} onkeydown={(e) => e.key === 'Enter' && open()} autocomplete="off" />
    </div>
  </div>
  <div class="bottom"><button type="button" class="btn" onclick={open} disabled={!value.trim()}>Open</button></div>
</div>
