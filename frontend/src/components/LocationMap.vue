<template>
  <section class="rv-map" :aria-label="title">
    <div class="rv-heading"><h3>{{ title }}</h3><button v-if="editable || locateEnabled" type="button" :disabled="locating" @click="locate">{{ locating ? 'Fetching geolocation…' : 'Fetch geolocation' }}</button></div>
    <div ref="container" class="rv-map-canvas" :aria-label="title" />
    <p v-if="locating" role="status">Allow location access in your browser to place your current position.</p>
    <p v-if="error" role="alert" class="rv-error">{{ error }}</p>
    <p v-if="tileError" role="status">Map tiles could not load. Check your connection. Coordinates and location actions remain available. <button type="button" @click="retryTiles">Retry map</button></p>
    <p class="rv-footnote">{{ editable ? 'Click the map or fetch geolocation to choose the customer location.' : point ? 'Saved or captured location.' : 'No location captured yet. Use Fetch geolocation or check in with location.' }} Map tiles are provided by OpenStreetMap.</p>
  </section>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { locationMap } from '../services/map.js'
import { currentPosition } from '../services/geo.js'
const props = defineProps({ latitude: [String, Number], longitude: [String, Number], radius: [String, Number], editable: Boolean, locateEnabled: Boolean, title: {type:String, default:'Geolocation'} })
const emit = defineEmits(['pick', 'located'])
const container = ref(null), locating = ref(false), error = ref(''), tileError = ref(false)
const point = computed(() => locationMap(props.latitude, props.longitude) ? [Number(props.latitude), Number(props.longitude)] : null)
let map, tiles, marker, circle, observer, disposed = false
function draw() {
  if (!map) return
  if (marker) { marker.remove(); marker = null }
  if (circle) { circle.remove(); circle = null }
  if (!point.value) return
  marker = L.marker(point.value, {icon:L.divIcon({className:'rv-map-pin',html:'<span></span>',iconSize:[24,32],iconAnchor:[12,32]}), keyboard:true, title:props.title}).addTo(map)
  const radius = Number(props.radius)
  if (Number.isFinite(radius) && radius > 0 && radius <= 10000) circle = L.circle(point.value, {radius, color:'#2563eb', weight:1, fillOpacity:0.1}).addTo(map)
  map.setView(point.value, 16)
}
onMounted(() => {
  map = L.map(container.value, {scrollWheelZoom:false}).setView(point.value || [20,0], point.value ? 16 : 2)
  tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(map)
  tiles.on('tileerror', () => { tileError.value = true })
  L.control.scale().addTo(map)
  map.on('click', event => { if (props.editable) emit('pick', {latitude:Number(event.latlng.lat.toFixed(8)),longitude:Number(event.latlng.wrap().lng.toFixed(8))}) })
  observer = new ResizeObserver(() => map?.invalidateSize()); observer.observe(container.value)
  draw()
})
watch(() => [props.latitude, props.longitude, props.radius], draw)
function retryTiles() { tileError.value = false; tiles?.redraw() }
async function locate() {
  locating.value = true; error.value = ''
  try { const position = await currentPosition(); if (disposed) return; emit(props.editable ? 'pick' : 'located', position) }
  catch (e) { if (!disposed) error.value = e.message } finally { if (!disposed) locating.value = false }
}
onBeforeUnmount(() => { disposed = true; observer?.disconnect(); map?.remove(); map = null })
</script>
