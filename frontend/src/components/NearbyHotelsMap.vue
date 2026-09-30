<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  center: { type: Object, required: true },
  hotels: { type: Array, required: true },
  selectedPlaceId: { type: String, default: null },
})
const emit = defineEmits(['select'])
const mapElement = ref(null)
let map
let hotelLayer
const markers = new Map()

function renderHotels() {
  if (!map || !hotelLayer) return
  hotelLayer.clearLayers()
  markers.clear()
  for (const hotel of props.hotels) {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'nearby-map-pin'
    button.setAttribute('aria-label', `Select ${hotel.name || 'unnamed hotel'} on map`)
    button.addEventListener('pointerdown', (event) => {
      event.stopPropagation()
      emit('select', hotel.place_id)
    })
    button.addEventListener('click', (event) => {
      if (event.detail === 0) emit('select', hotel.place_id)
    })
    L.DomEvent.disableClickPropagation(button)
    const marker = L.marker([hotel.latitude, hotel.longitude], {
      icon: L.divIcon({ className: '', html: button, iconSize: [20, 20] }),
      keyboard: false,
    }).addTo(hotelLayer)
    const label = document.createElement('span')
    label.textContent = hotel.name || 'Name unavailable'
    marker.bindTooltip(label, {
      direction: 'top',
      offset: [0, -12],
      className: 'nearby-map-tooltip',
    })
    button.addEventListener('focus', () => marker.openTooltip())
    button.addEventListener('blur', () => marker.closeTooltip())
    markers.set(hotel.place_id, { marker, button })
  }
  updateSelection()
}

function updateSelection() {
  for (const [placeId, { marker, button }] of markers) {
    const selected = placeId === props.selectedPlaceId
    button.classList.toggle('is-selected', selected)
    button.setAttribute('aria-pressed', String(selected))
    marker.setZIndexOffset(selected ? 1000 : 0)
  }
  const selectedMarker = markers.get(props.selectedPlaceId)?.marker
  if (selectedMarker) map.panTo(selectedMarker.getLatLng())
}

onMounted(() => {
  map = L.map(mapElement.value).setView([props.center.latitude, props.center.longitude], 12)
  map.attributionControl.setPrefix(false).setPosition('bottomright')
  const brandColor = getComputedStyle(mapElement.value).getPropertyValue('--brand').trim()
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map)
  L.circle([props.center.latitude, props.center.longitude], {
    radius: 5000,
    color: brandColor,
    fillColor: brandColor,
    fillOpacity: 0.06,
    interactive: false,
  }).addTo(map)
  hotelLayer = L.layerGroup().addTo(map)
  renderHotels()
})

watch(() => props.selectedPlaceId, updateSelection)
watch(() => props.hotels, renderHotels)

onBeforeUnmount(() => {
  map?.remove()
  map = null
})
</script>

<template>
  <div class="nearby-map-wrap">
    <h3>Map of nearby hotels</h3>
    <div ref="mapElement" class="nearby-map" role="region" aria-label="Map of nearby hotels"></div>
  </div>
</template>
