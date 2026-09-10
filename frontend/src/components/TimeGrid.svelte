<script>
  // The availability grid. Columns are dates, rows are 15-minute slots.
  // Paint:  desktop click-drag / touch press-and-hold then drag. Marks or unmarks my availability (bind:mySlots).
  // Tap:    a quick tap or click reports the cell (ontap) — the parent decides: show who's free, or select a block.
  // Select: `selection` {start,end} is drawn as an outlined block; `highlight` is the confirmed block.
  import { SLOT_MIN, slotKey, fmtTime, fmtDate, addMinutes, rowsFor } from '../lib/time.js'

  let {
    dates = [],
    hourStart = 8,
    hourEnd = 24,
    mySlots = $bindable([]),
    heatmap = {},
    total = 0,
    allowed = null,          // array of slot keys the viewer may paint, or null for anywhere
    readonly = false,        // no painting
    selection = null,        // {start, end}
    highlight = null,        // {start, end}
    fill = false,            // fill the parent's height (parent must be a flex column)
    onchange = () => {},
    ontap = () => {},        // (slotKey) on tap / click without drag
  } = $props()

  const rows = $derived(rowsFor(hourStart, hourEnd))
  const selected = $derived(new Set(mySlots))
  const allowedSet = $derived(allowed ? new Set(allowed) : null)
  const simple = $derived(Object.keys(heatmap).length === 0)   // nobody else yet: paint shows as solid mint

  let drag = $state(null)     // {a:{d,i}, b:{d,i}, add}
  let wrapEl = $state(null)
  let gridEl = $state(null)
  let isTouch = $state(false)

  export function scrollToSlot(key, offsetRows = 2) {
    if (!wrapEl || !gridEl || !key) return
    const d = dates.indexOf(key.slice(0, 10))
    if (d < 0) return
    const m = +key.slice(11, 13) * 60 + +key.slice(14, 16)
    const i = Math.max(0, (m - hourStart * 60) / SLOT_MIN - offsetRows)
    const cell = gridEl.querySelector(`.cell[data-d="${d}"][data-i="${i}"]`)
    if (cell) wrapEl.scrollTop = Math.max(0, cell.offsetTop - 64)
  }

  function keyOf(d, i) { return slotKey(dates[d], hourStart * 60 + i * SLOT_MIN) }
  function minutesOf(i) { return hourStart * 60 + i * SLOT_MIN }
  function rectKeys(dr) {
    const d0 = Math.min(dr.a.d, dr.b.d), d1 = Math.max(dr.a.d, dr.b.d)
    const i0 = Math.min(dr.a.i, dr.b.i), i1 = Math.max(dr.a.i, dr.b.i)
    const out = []
    for (let d = d0; d <= d1; d++) for (let i = i0; i <= i1; i++) {
      const k = keyOf(d, i)
      if (!allowedSet || allowedSet.has(k)) out.push(k)
    }
    return out
  }
  const preview = $derived(drag ? new Set(rectKeys(drag)) : null)

  function blockSet(b) {
    if (!b) return null
    const s = new Set()
    let k = b.start
    for (let n = 0; n < 400 && k < b.end; n++) { s.add(k); k = addMinutes(k, SLOT_MIN) }
    return s
  }
  const selectionSet = $derived(blockSet(selection))
  const highlightSet = $derived(blockSet(highlight))

  function cellAt(x, y) {
    const el = document.elementFromPoint(x, y)
    const c = el && el.closest ? el.closest('.cell') : null
    if (!c || !gridEl || !gridEl.contains(c)) return null
    return { d: +c.dataset.d, i: +c.dataset.i }
  }
  function beginDrag(c) {
    if (readonly) return false
    const k = keyOf(c.d, c.i)
    if (allowedSet && !allowedSet.has(k)) return false
    drag = { a: c, b: c, add: !selected.has(k) }
    return true
  }
  function updateDrag(c) {
    if (!drag || (c.d === drag.b.d && c.i === drag.b.i)) return
    drag = { ...drag, b: c }
  }
  function endDrag() {
    if (!drag) return
    const dr = drag
    drag = null
    const s = new Set(selected)
    for (const k of rectKeys(dr)) dr.add ? s.add(k) : s.delete(k)
    mySlots = [...s].sort()
    onchange(mySlots)
  }

  // ----- mouse: click = tap, move past a few pixels = paint -----
  let mouseStart = null
  function onMouseDown(e) {
    if (e.button !== 0 || isTouch) return
    const c = cellAt(e.clientX, e.clientY)
    if (!c) return
    e.preventDefault()
    mouseStart = { c, x: e.clientX, y: e.clientY, painting: false }
  }
  $effect(() => {
    const move = (e) => {
      if (!mouseStart) return
      if (!mouseStart.painting) {
        if (Math.hypot(e.clientX - mouseStart.x, e.clientY - mouseStart.y) < 6) return
        mouseStart.painting = beginDrag(mouseStart.c)
        if (!mouseStart.painting) { mouseStart = null; return }
      }
      const c = cellAt(e.clientX, e.clientY)
      if (c) updateDrag(c)
    }
    const up = () => {
      if (!mouseStart) return
      if (mouseStart.painting) endDrag()
      else ontap(keyOf(mouseStart.c.d, mouseStart.c.i))
      mouseStart = null
    }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
    return () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up) }
  })

  // ----- touch: hold to paint, swipe to scroll, tap = tap -----
  function touchPaint(node) {
    let holdTimer = null, startCell = null, startXY = null, painting = false, moved = false
    const HOLD_MS = 280, SLOP = 8
    const clear = () => { if (holdTimer) { clearTimeout(holdTimer); holdTimer = null } }
    const onStart = (e) => {
      isTouch = true
      if (e.touches.length !== 1) { clear(); return }
      const t = e.touches[0]
      const c = cellAt(t.clientX, t.clientY)
      if (!c) return
      startCell = c; startXY = [t.clientX, t.clientY]; moved = false; painting = false
      if (readonly) return
      holdTimer = setTimeout(() => {
        holdTimer = null
        painting = beginDrag(c)
        if (painting && navigator.vibrate) { try { navigator.vibrate(12) } catch { /* ignore */ } }
      }, HOLD_MS)
    }
    const onMove = (e) => {
      const t = e.touches[0]
      if (painting) {
        e.preventDefault()
        const c = cellAt(t.clientX, t.clientY)
        if (c) updateDrag(c)
        return
      }
      if (Math.hypot(t.clientX - startXY[0], t.clientY - startXY[1]) > SLOP) { clear(); moved = true }
    }
    const onEnd = (e) => {
      clear()
      if (painting) { e.preventDefault(); endDrag(); painting = false }
      else if (!moved && startCell) ontap(keyOf(startCell.d, startCell.i))
      startCell = null
    }
    node.addEventListener('touchstart', onStart, { passive: true })
    node.addEventListener('touchmove', onMove, { passive: false })
    node.addEventListener('touchend', onEnd, { passive: false })
    node.addEventListener('touchcancel', onEnd, { passive: false })
    return { destroy() {
      node.removeEventListener('touchstart', onStart)
      node.removeEventListener('touchmove', onMove)
      node.removeEventListener('touchend', onEnd)
      node.removeEventListener('touchcancel', onEnd)
    } }
  }

  // ----- appearance -----
  function heatStyle(k) {
    const n = heatmap[k] ? heatmap[k].length : 0
    if (!n || !total) return ''
    const a = 0.16 + 0.84 * Math.min(1, n / total)
    return `background: oklch(0.80 0.14 215 / ${a.toFixed(2)})`
  }
  function cls(d, i) {
    const k = keyOf(d, i)
    const m = minutesOf(i)
    let c = 'cell'
    if (m % 60 === 0) c += ' h'
    else if (m % 30 === 0) c += ' hh'
    if (allowedSet && !allowedSet.has(k)) c += ' off'
    if (selected.has(k)) c += simple ? ' mine-solid' : ' mine'
    if (preview && preview.has(k)) c += drag.add ? ' prev-add' : ' prev-del'
    if (selectionSet && selectionSet.has(k)) {
      c += ' sel'
      if (k === selection.start) c += ' sel-top'
      if (addMinutes(k, SLOT_MIN) === selection.end) c += ' sel-bot'
    }
    if (highlightSet && highlightSet.has(k)) c += ' hl'
    return c
  }
  function timeLabel(i) {
    const m = minutesOf(i)
    if (m % 30 !== 0) return ''
    return m % 60 === 0 ? fmtTime(m, true) : fmtTime(m).replace(/ (AM|PM)$/, '')
  }
</script>

<div class="tg-wrap" class:fill class:dragging={!!drag} class:readonly bind:this={wrapEl}>
  <div class="tg" style="--cols:{dates.length}" bind:this={gridEl} use:touchPaint onmousedown={onMouseDown}
       oncontextmenu={(e) => e.preventDefault()} role="grid" tabindex="0" aria-label="Availability grid">
    <div class="tg-corner"></div>
    {#each dates as d (d)}
      <div class="tg-head"><span class="wd">{fmtDate(d, { weekday: 'short' })}</span><span class="dt">{fmtDate(d, { month: 'short', day: 'numeric' })}</span></div>
    {/each}
    <div class="tg-time spacer"></div>
    {#each dates as _d, j (j)}<div class="tg-foot spacer"></div>{/each}
    {#each Array(rows) as _, i}
      <div class="tg-time"><span>{timeLabel(i)}</span></div>
      {#each dates as _d, di}
        <div class={cls(di, i)} data-d={di} data-i={i} style={heatStyle(keyOf(di, i))}></div>
      {/each}
    {/each}
    <div class="tg-time end"><span>{fmtTime(hourEnd * 60, true)}</span></div>
    {#each dates as _d, j (j)}<div class="tg-foot"></div>{/each}
  </div>
</div>

<style>
  .tg-wrap {
    overflow: auto;
    background: var(--surface);
    border-top: 1px solid var(--edge); border-bottom: 1px solid var(--edge);
    -webkit-user-select: none; user-select: none; -webkit-touch-callout: none;
    overscroll-behavior: contain;
    max-height: min(72dvh, 900px);
  }
  .tg-wrap.fill { flex: 1; min-height: 0; max-height: none; }
  .tg-wrap.dragging { cursor: crosshair; }
  .tg { display: grid; grid-template-columns: 60px repeat(var(--cols), minmax(64px, 1fr)); grid-template-rows: auto; grid-auto-rows: 13px; min-width: 100%; outline: none; }
  .tg-corner, .tg-head { position: sticky; top: 0; z-index: 3; background: var(--surface); border-bottom: 1px solid var(--line-2); }
  .tg-corner { left: 0; z-index: 4; }
  .tg-head { padding: 10px 4px 8px; text-align: center; line-height: 1.15; }
  .tg-head .wd { display: block; font-size: 12px; font-weight: 700; letter-spacing: .06em; color: var(--text-3); text-transform: uppercase; }
  .tg-head .dt { display: block; font-size: 15px; font-weight: 700; margin-top: 2px; }
  .tg-time { position: sticky; left: 0; z-index: 2; background: var(--surface); border-right: 1px solid var(--line-2); }
  .tg-time span { position: absolute; right: 10px; top: -8px; font-size: 12px; font-weight: 600; color: var(--text-3); white-space: nowrap; line-height: 1; }
  .tg-time.spacer, .tg-foot.spacer { height: 12px; }
  .tg-time.end, .tg-foot { height: 13px; }
  .cell { border-top: 1px solid var(--line); border-right: 1px solid var(--line); position: relative; cursor: pointer; }
  .cell.hh { border-top-color: var(--line-2); }
  .cell.h { border-top-color: oklch(1 0 0 / .22); }
  .cell.off { cursor: not-allowed; background-image: repeating-linear-gradient(135deg, oklch(1 0 0 / .06) 0 3px, transparent 3px 6px) !important; }
  .cell.mine-solid { background: oklch(0.84 0.16 160 / .55) !important; }
  .cell.mine { box-shadow: inset -6px 0 0 0 var(--mint); }
  .cell.prev-add { background: oklch(0.84 0.16 160 / .55) !important; box-shadow: inset -6px 0 0 0 var(--mint); }
  .cell.prev-del { background: oklch(0.72 0.19 20 / .35) !important; box-shadow: none; }
  .cell.sel { box-shadow: inset 2px 0 0 0 var(--accent), inset -2px 0 0 0 var(--accent); filter: brightness(1.15); }
  .cell.sel.mine { box-shadow: inset 2px 0 0 0 var(--accent), inset -6px 0 0 0 var(--mint); }
  .cell.sel-top { border-top: 2px solid var(--accent); }
  .cell.sel-bot { box-shadow: inset 2px 0 0 0 var(--accent), inset -2px 0 0 0 var(--accent), inset 0 -2px 0 0 var(--accent); }
  .cell.hl { box-shadow: inset 0 0 0 2px oklch(0.85 0.17 80); }
  .readonly .cell { cursor: default; }
</style>
