<script setup>
import { nextTick, ref, watch } from 'vue'
import NearbyHotelsMap from './NearbyHotelsMap.vue'

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
        <p class="section-kicker">Live places from Geoapify</p>
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
          <strong>{{ hotel.name || 'Name unavailable' }}</strong>
          <span>{{ hotel.address || 'Address unavailable' }}</span>
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
