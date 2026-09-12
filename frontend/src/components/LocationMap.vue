<template>
  <div class="rv-map">
    <h3>Location map</h3>
    <template v-if="map">
      <iframe :src="map.embed" title="Customer location map" loading="lazy" referrerpolicy="no-referrer" />
      <p class="rv-footnote">Map by OpenStreetMap. Coordinates are sent to the map provider.
        <a :href="map.link" target="_blank" rel="noopener noreferrer">Open larger map</a>
      </p>
    </template>
    <p v-else>Enter valid latitude and longitude, or use current location, to preview the location on the map.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { locationMap } from '../services/map.js'
const props = defineProps({ latitude: [String, Number], longitude: [String, Number] })
const map = computed(() => locationMap(props.latitude, props.longitude))
</script>
