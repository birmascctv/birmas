<template>
  <div ref="containerRef" class="relative w-full select-none"
       style="height: 200px"
       @mousedown.prevent="onMouseDown"
       @touchstart.prevent="onTouchStart">

    <!-- Event lines + dots -->
    <template v-for="ev in positioned" :key="ev.id">
      <!-- vertical stem -->
      <div class="absolute rounded-full"
           :style="stemStyle(ev)"
           :class="colorBg(ev.event_type)"></div>
      <!-- dot at tip -->
      <div class="absolute rounded-full cursor-pointer z-[3] border-2 border-white dark:border-gray-800 shadow transition-all duration-200"
           :style="dotStyle(ev)"
           :class="[colorBg(ev.event_type), nearScrubber(ev) ? 'scale-125' : '']"
           @mouseenter.stop="hover(ev, $event)"
           @mouseleave.stop="unhover"
           @click.stop="select(ev)"></div>
    </template>

    <!-- Timeline line -->
    <div class="absolute h-[2px] bg-gray-300 dark:bg-gray-600 z-[1]"
         :style="{ top: TL_Y + 'px', left: PAD + 'px', right: PAD + 'px' }"></div>

    <!-- Hour dots + labels -->
    <template v-for="h in 25" :key="'h'+h">
      <div class="absolute w-[8px] h-[8px] rounded-full bg-white dark:bg-gray-800 border-2 border-gray-400 dark:border-gray-500 z-[2]"
           :style="{ left: (hourPx(h-1) - 4) + 'px', top: (TL_Y - 4) + 'px' }"></div>
      <div v-if="(h-1) % labelStep === 0"
           class="absolute text-[9px] font-mono text-gray-400 dark:text-gray-500 z-[1]"
           :style="{ left: hourPx(h-1) + 'px', top: (TL_Y + 10) + 'px', transform: 'translateX(-50%)' }">
        {{ pad(h === 25 ? 0 : h-1) }}:00
      </div>
    </template>

    <!-- Scrubber -->
    <div class="absolute top-0 z-[6] pointer-events-none"
         :style="{ left: scrubPx + 'px', height: '100%' }">
      <div class="absolute left-0 top-[22px] bottom-[28px] w-[2px] -translate-x-[1px] bg-red-500 opacity-80"></div>
      <!-- time pill -->
      <div class="absolute -translate-x-1/2 top-[4px] bg-red-600 text-white text-[10px] font-mono leading-none px-1.5 py-[3px] rounded shadow whitespace-nowrap">
        {{ scrubTimeStr }}
      </div>
      <!-- arrow -->
      <div class="absolute -translate-x-1/2" :style="{ top: (TL_Y - 5) + 'px' }">
        <svg width="10" height="6"><polygon points="0,0 10,0 5,6" fill="#dc2626"/></svg>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && positioned.length === 0"
         class="absolute inset-0 flex items-center justify-center text-gray-400 dark:text-gray-500 text-sm pointer-events-none z-0">
      No events for today
    </div>

    <!-- Hover tooltip -->
    <Transition name="fade">
      <div v-if="hovered"
           class="absolute z-[20] bg-white dark:bg-gray-800 shadow-xl rounded-lg border border-gray-200 dark:border-gray-700 pointer-events-none overflow-hidden"
           :style="tooltipStyle" style="width: 240px">
        <img v-if="hovered.hasFrame" :src="frameUrl(hovered.id)"
             class="w-full h-28 object-cover bg-gray-100 dark:bg-gray-700" alt="" @error="hovered.hasFrame = false" />
        <div v-else class="w-full h-20 bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-400 text-xs">
          No capture
        </div>
        <div class="p-2.5">
          <p class="text-sm font-semibold truncate">{{ hovered.product_brand }} — {{ hovered.product_name }}</p>
          <p class="text-[11px] text-gray-500 mt-0.5">{{ fmtTime(hovered.ts) }} ·
            <span :class="colorText(hovered.event_type)">{{ label(hovered.event_type) }}</span>
          </p>
          <p class="text-[10px] text-gray-400">{{ (hovered.confidence * 100).toFixed(1) }}% confidence</p>
        </div>
      </div>
    </Transition>

    <!-- Full-page overlay -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="selected"
             class="fixed inset-0 z-[100] bg-black/80 flex items-center justify-center p-4"
             @click="selected = null">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-auto"
               @click.stop>
            <img v-if="selected.hasFrame" :src="frameUrl(selected.id)"
                 class="w-full max-h-[50vh] object-contain bg-black" alt="" />
            <div v-else class="w-full h-48 bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-400">
              No frame capture available
            </div>
            <div class="p-5">
              <div class="flex items-start justify-between gap-2 mb-3">
                <div>
                  <h3 class="text-lg font-bold">{{ selected.product_brand }}</h3>
                  <p class="text-sm text-gray-500">{{ selected.product_name }}</p>
                </div>
                <span class="shrink-0 px-2 py-0.5 rounded text-xs font-bold text-white"
                      :class="badgeBg(selected.event_type)">{{ label(selected.event_type) }}</span>
              </div>
              <div class="grid grid-cols-2 gap-2 text-sm text-gray-600 dark:text-gray-300">
                <div><span class="text-gray-400">Time</span><br>{{ fmtTime(selected.ts) }}</div>
                <div><span class="text-gray-400">Camera</span><br>{{ selected.camera_id }}</div>
                <div><span class="text-gray-400">Confidence</span><br>{{ (selected.confidence * 100).toFixed(1) }}%</div>
                <div><span class="text-gray-400">BBox</span><br>{{ selected.bbox || '—' }}</div>
              </div>
              <button @click="selected = null"
                      class="mt-4 w-full py-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition">
                Close
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import API from '../api'

const props = defineProps({
  filter:     String,
  camera:     String,
  customFrom: String,
  customTo:   String,
})

/* ── layout constants (px) ── */
const PAD    = 28
const TL_Y   = 100          // timeline y-center
const STEM_H = 42           // event line height
const DOT_R  = 10           // dot diameter
const NUDGE  = 8            // px dots shift when near scrubber
const SNAP_H = 0.35         // hours — scrubber proximity for nudge

/* ── refs / state ── */
const containerRef = ref(null)
const cW           = ref(800)
const events       = ref([])
const loading      = ref(false)
const hovered      = ref(null)
const tooltipPx    = ref({ x: 0, y: 0 })
const selected     = ref(null)
const scrubFrac    = ref(0.5)        // 0‑1 along timeline
let   dragging     = false

/* ── WIB (UTC+7) helpers ── */
const WIB = 7 * 60
function nowWIB () {
  const d = new Date()
  return new Date(d.getTime() + (d.getTimezoneOffset() + WIB) * 60000)
}
function todayStartISO () {
  const n = nowWIB()
  return `${n.getFullYear()}-${pad(n.getMonth()+1)}-${pad(n.getDate())}T00:00:00`
}
function todayEndISO () {
  const n = nowWIB()
  const t = new Date(n); t.setDate(t.getDate() + 1)
  return `${t.getFullYear()}-${pad(t.getMonth()+1)}-${pad(t.getDate())}T00:00:00`
}
function pad (n) { return String(n).padStart(2, '0') }

/* ── coordinate mapping ── */
const usable  = computed(() => cW.value - PAD * 2)
function hourPx (h)  { return PAD + (h / 24) * usable.value }
function fracPx (f)  { return PAD + f * usable.value }
function pxFrac (px) { return Math.max(0, Math.min(1, (px - PAD) / usable.value)) }
const labelStep = computed(() => cW.value < 500 ? 3 : cW.value < 700 ? 2 : 1)

/* ── scrubber ── */
const scrubPx      = computed(() => fracPx(scrubFrac.value))
const scrubTimeStr = computed(() => {
  const total = scrubFrac.value * 24
  const h = Math.floor(total)
  const m = Math.floor((total - h) * 60)
  return `${pad(h % 24)}:${pad(m)}`
})

/* ── fetch events ── */
async function fetchEvents () {
  loading.value = true
  try {
    const params = { limit: 5000, start_date: todayStartISO(), end_date: todayEndISO() }
    if (props.camera && props.camera !== 'all') params.camera_id = props.camera
    const { data } = await API.get('/events', { params })
    events.value = data.map(e => ({ ...e, hasFrame: true }))
  } catch { events.value = [] }
  loading.value = false
}

/* ── position events ── */
function tsToFrac (tsStr) {
  const t = tsStr.split('T')[1] || '00:00:00'
  const [h, m, s] = t.split(':').map(Number)
  return (h + m / 60 + (s || 0) / 3600) / 24
}
const positioned = computed(() => {
  const arr = events.value.map(e => ({ ...e, frac: tsToFrac(e.ts) }))
  // slight y-jitter for close events
  arr.sort((a, b) => a.frac - b.frac)
  for (let i = 1; i < arr.length; i++) {
    if (Math.abs(arr[i].frac - arr[i-1].frac) < 0.003) {
      arr[i]._jitter = (arr[i-1]._jitter || 0) + 6
    }
  }
  return arr
})

/* ── styling helpers ── */
function stemStyle (ev) {
  const x   = fracPx(ev.frac)
  const up  = ev.event_type === 'sold'
  const jit = ev._jitter || 0
  const h   = STEM_H - jit
  return {
    left:   (x - 1) + 'px',
    width:  '2px',
    top:    up ? (TL_Y - h) + 'px' : TL_Y + 'px',
    height: h + 'px',
  }
}
function dotStyle (ev) {
  const x   = fracPx(ev.frac)
  const up  = ev.event_type === 'sold'
  const jit = ev._jitter || 0
  const h   = STEM_H - jit
  const nudge = nearScrubber(ev) ? (up ? NUDGE : -NUDGE) : 0
  const cy  = up ? TL_Y - h - DOT_R/2 + nudge : TL_Y + h - DOT_R/2 + nudge
  return {
    left:   (x - DOT_R/2) + 'px',
    top:    cy + 'px',
    width:  DOT_R + 'px',
    height: DOT_R + 'px',
  }
}
function nearScrubber (ev) {
  return Math.abs(ev.frac - scrubFrac.value) < SNAP_H / 24
}
function colorBg (t) {
  return t === 'sold' ? 'bg-green-500' : t === 'restock' ? 'bg-blue-500' : 'bg-red-500'
}
function colorText (t) {
  return t === 'sold' ? 'text-green-600' : t === 'restock' ? 'text-blue-600' : 'text-red-600'
}
function badgeBg (t) {
  return t === 'sold' ? 'bg-green-600' : t === 'restock' ? 'bg-blue-600' : 'bg-red-600'
}
function label (t) {
  return t === 'sold' ? 'Sold' : t === 'restock' ? 'Restocked' : 'Detected'
}
function frameUrl (id) { return `/api/frames/${id}` }
function fmtTime (ts) {
  const t = (ts || '').split('T')[1] || ''
  return t.substring(0, 8)
}

/* ── tooltip ── */
const tooltipStyle = computed(() => {
  if (!hovered.value) return { display: 'none' }
  const up = hovered.value.event_type === 'sold'
  return {
    left: Math.min(Math.max(tooltipPx.value.x - 120, 4), cW.value - 248) + 'px',
    top:  (up ? tooltipPx.value.y - 220 : tooltipPx.value.y + 16) + 'px',
  }
})
function hover (ev, e) { hovered.value = ev; tooltipPx.value = { x: e.offsetX || e.layerX || 0, y: e.offsetY || e.layerY || 0 } }
function unhover ()     { hovered.value = null }
function select (ev)    { selected.value = ev }

/* ── mouse / touch drag ── */
function scrubTo (clientX) {
  const r = containerRef.value.getBoundingClientRect()
  scrubFrac.value = pxFrac(clientX - r.left)
}
function onMouseDown (e) { dragging = true; scrubTo(e.clientX) }
function onMouseMove (e) { if (dragging) scrubTo(e.clientX) }
function onMouseUp   ()  { dragging = false }
function onTouchStart (e) { dragging = true; scrubTo(e.touches[0].clientX) }
function onTouchMove (e)  { if (dragging) scrubTo(e.touches[0].clientX) }
function onTouchEnd ()    { dragging = false }

/* ── resize observer ── */
let ro = null
function measure () { if (containerRef.value) cW.value = containerRef.value.clientWidth }

onMounted(() => {
  measure()
  ro = new ResizeObserver(measure)
  ro.observe(containerRef.value)
  // Init scrubber at current WIB time
  const n = nowWIB()
  scrubFrac.value = (n.getHours() + n.getMinutes() / 60) / 24
  fetchEvents()
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  document.addEventListener('touchmove', onTouchMove)
  document.addEventListener('touchend', onTouchEnd)
})
onUnmounted(() => {
  ro?.disconnect()
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', onTouchEnd)
})

watch(() => [props.filter, props.camera, props.customFrom, props.customTo], fetchEvents)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .15s }
.fade-enter-from, .fade-leave-to { opacity: 0 }
</style>
