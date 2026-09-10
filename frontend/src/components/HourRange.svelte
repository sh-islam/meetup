<script>
  // Visible hour range as two steppers (whole hours).
  import { fmtTime } from '../lib/time.js'
  let { hourStart = $bindable(8), hourEnd = $bindable(24) } = $props()
  const lbl = (h) => (h === 24 ? 'Midnight' : h === 0 ? 'Midnight' : fmtTime(h * 60, true))
  function s(d) { const v = hourStart + d; if (v >= 0 && v < hourEnd) hourStart = v }
  function e(d) { const v = hourEnd + d; if (v > hourStart && v <= 24) hourEnd = v }
</script>

<div class="range">
  <div class="stepper">
    <button type="button" onclick={() => s(-1)} disabled={hourStart <= 0} aria-label="Earlier start">−</button>
    <b>{lbl(hourStart)}</b>
    <button type="button" onclick={() => s(1)} disabled={hourStart + 1 >= hourEnd} aria-label="Later start">+</button>
  </div>
  <div class="to">to</div>
  <div class="stepper">
    <button type="button" onclick={() => e(-1)} disabled={hourEnd - 1 <= hourStart} aria-label="Earlier end">−</button>
    <b>{lbl(hourEnd)}</b>
    <button type="button" onclick={() => e(1)} disabled={hourEnd >= 24} aria-label="Later end">+</button>
  </div>
</div>
