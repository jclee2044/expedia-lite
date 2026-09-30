<script setup>
import { nextTick, ref, watch } from 'vue'
import NearbyHotelsMap from './NearbyHotelsMap.vue'
import { hotelAddressLines } from './hotelAddress.js'

const props = defineProps({
  center: { type: Object, required: true },
  hotels: { type: Array, required: true },
  resultLimit: { type: Number, required: true },
  selectedPlaceId: { type: String, default: null },
})

defineEmits(['select'])

const nearbyList = ref(null)

watch(() => props.selectedPlaceId, async (placeId) => {
  if (!placeId) return
  await nextTick()
  const list = nearbyList.value
  const card = Array.from(list?.querySelectorAll('.nearby-card') || [])
    .find((item) => item.dataset.placeId === placeId)
  if (!list || !card) return

  const listBounds = list.getBoundingClientRect()
  const cardBounds = card.getBoundingClientRect()
  if (cardBounds.top >= listBounds.top && cardBounds.bottom <= listBounds.bottom) return
  list.scrollTop += cardBounds.top - listBounds.top - (list.clientHeight - card.clientHeight) / 2
})
</script>

<template>
  <section class="nearby-section" aria-labelledby="nearby-title">
    <div class="results-heading">
      <div>
        <p class="section-kicker">Nearby hotels</p>
        <h2 id="nearby-title">Hotels near ZIP {{ center.postcode }}</h2>
      </div>
      <p class="result-count">{{ hotels.length }} {{ hotels.length === 1 ? 'place' : 'places' }} returned</p>
    </div>
    <p class="nearby-note">
      Within 5 km of the resolved ZIP point. Showing up to {{ resultLimit }} provider results;
      this is not a complete hotel inventory or room availability search.
    </p>
    <p v-if="!hotels.length" class="state-card empty-state" role="status">
      No nearby hotels were returned for this ZIP. Try another ZIP code.
    </p>
    <div v-else class="nearby-layout">
      <div ref="nearbyList" class="nearby-list" aria-label="Nearby hotels">
        <button
          v-for="hotel in hotels"
          :key="hotel.place_id"
          :data-place-id="hotel.place_id"
          type="button"
          class="nearby-card"
          :class="{ 'is-selected': selectedPlaceId === hotel.place_id }"
          :aria-pressed="selectedPlaceId === hotel.place_id"
          @click="$emit('select', hotel.place_id)"
        >
          <span class="nearby-card-title">
            <span class="nearby-card-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 21V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v16M3 21h18M9 21v-5h6v5M8 8h2m4 0h2M8 12h2m4 0h2" />
              </svg>
            </span>
            <strong>{{ hotel.name || 'Name unavailable' }}</strong>
          </span>
          <span class="nearby-card-address">
            <span v-for="(line, index) in hotelAddressLines(hotel)" :key="index" class="nearby-card-address-line">{{ line }}</span>
          </span>
        </button>
      </div>
      <NearbyHotelsMap
        :center="center"
        :hotels="hotels"
        :selected-place-id="selectedPlaceId"
        @select="$emit('select', $event)"
      />
    </div>
  </section>
</template>
