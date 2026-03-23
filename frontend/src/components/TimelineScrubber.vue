<template>
  <div ref="container" class="w-full h-64 relative">
    <svg ref="svg" class="w-full h-full"></svg>
    <!-- scrubber label -->
    <div ref="scrubberLabel"
         class="absolute bg-black text-white text-xs px-2 py-1 rounded hidden"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  filter: String,
  camera: String,
  customFrom: String,
  customTo: String,
})

// refs
const container = ref(null)
const svg = ref(null)
const scrubberLabel = ref(null)

// demo events (replace with API data later)
const events = [
  { date: new Date().setHours(1), type: 'sold' },
  { date: new Date().setHours(2), type: 'restocked' },
  { date: new Date().setHours(3), type: 'detected' },
]

const colorMap = { sold:'#27ae60', restocked:'#2980b9', detected:'#e74c3c' }

onMounted(() => renderTimeline())
watch(() => [props.filter, props.camera, props.customFrom, props.customTo], () => renderTimeline())

function renderTimeline() {
  const svgEl = d3.select(svg.value)
  svgEl.selectAll('*').remove()

  const width = container.value.clientWidth
  const height = container.value.clientHeight
  const margin = { left: 40, right: 20, top: 20, bottom: 40 }
  const innerW = width - margin.left - margin.right
  const centerY = height / 2

  const start = new Date(new Date().setHours(0,0,0,0))
  const end = new Date(new Date().setHours(24,0,0,0))
  const xScale = d3.scaleTime().domain([start, end]).range([0, innerW])

  const g = svgEl.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  // baseline
  g.append('line')
    .attr('x1',0).attr('x2',innerW)
    .attr('y1',centerY).attr('y2',centerY)
    .attr('class','baseline').attr('stroke','#ccc')

  // hour dots + labels
  const ticks = d3.timeHour.range(start, end, 1).concat([end])
  ticks.forEach(t => {
    const hx = xScale(t)
    g.append('circle').attr('cx',hx).attr('cy',centerY).attr('r',4).attr('fill','#fff').attr('stroke','#999')
    g.append('text').attr('x',hx).attr('y',centerY+16).text(d3.utcFormat('%H:%M')(t)).attr('text-anchor','middle').attr('font-size',10)
  })

  // events
  const ev = g.selectAll('g.event').data(events).enter().append('g').attr('transform', d => `translate(${xScale(d.date)},0)`)

  ev.append('line')
    .attr('x1',0).attr('x2',0).attr('y1',centerY)
    .attr('y2',d => d.type==='sold'? centerY+40 : centerY-40)
    .attr('stroke',d => colorMap[d.type])

  ev.append('circle')
    .attr('class','event-dot')
    .attr('cx',0).attr('cy',d => d.type==='sold'? centerY+40 : centerY-40)
    .attr('r',6).attr('fill',d => colorMap[d.type])
}
</script>

<style scoped>
.event-dot.nudge-up { transform: translateY(-10px); }
.event-dot.nudge-down { transform: translateY(10px); }
.event-dot.highlight { transform: scale(1.25); stroke-width:2.2px; }
</style>
