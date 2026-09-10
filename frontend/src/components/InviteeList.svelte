<script>
  // Add invitees by email (name optional). Paste a comma / newline separated list to add many at once.
  let { invitees = $bindable([]), exclude = '' } = $props()

  let email = $state('')
  let name = $state('')
  let error = $state('')
  const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

  function add() {
    error = ''
    const parts = email.split(/[\s,;]+/).map((s) => s.trim().toLowerCase()).filter(Boolean)
    if (!parts.length) return
    const bad = parts.filter((p) => !EMAIL_RE.test(p))
    if (bad.length) { error = `Not an email address: ${bad.join(', ')}`; return }
    const have = new Set(invitees.map((i) => i.email))
    const added = []
    for (const p of parts) {
      if (have.has(p) || p === exclude.toLowerCase()) continue
      have.add(p)
      added.push({ email: p, name: parts.length === 1 ? name.trim() : '' })
    }
    invitees = [...invitees, ...added]
    email = ''; name = ''
  }
  function remove(em) { invitees = invitees.filter((i) => i.email !== em) }
  function onKey(e) { if (e.key === 'Enter') { e.preventDefault(); add() } }
</script>

<div class="stack" style="gap:12px">
  <div class="field">
    <label for="inv-email">Email</label>
    <input id="inv-email" type="email" placeholder="friend@example.com" bind:value={email} onkeydown={onKey} autocomplete="off" />
  </div>
  <div class="field">
    <label for="inv-name">Name <span class="muted">(optional)</span></label>
    <input id="inv-name" type="text" placeholder="What you call them" bind:value={name} onkeydown={onKey} autocomplete="off" />
  </div>
  <button type="button" class="btn ghost sm" onclick={add} disabled={!email.trim()}>Add</button>
  <div class="hint" style="margin-top:0">Paste several addresses at once, separated by commas or new lines.</div>
  {#if error}<div class="msg error">{error}</div>{/if}
</div>
{#if invitees.length}
  <div>
    <div class="label" style="margin-bottom:12px">{invitees.length} invited</div>
    <div class="chips">
      {#each invitees as inv (inv.email)}
        <span class="chip"><span class="txt">{inv.name ? `${inv.name} · ` : ''}{inv.email}</span><button type="button" class="x" onclick={() => remove(inv.email)} aria-label="Remove">×</button></span>
      {/each}
    </div>
  </div>
{/if}
