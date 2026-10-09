<script setup>
import { nextTick, ref, watch } from 'vue'
import NearbyHotelsMap from './NearbyHotelsMap.vue'
import { hotelAddressLines } from './hotelAddress.js'

const props = defineProps({
  center: { type: Object, required: true },
  hotels: { type: Array, required: true },
  resultLimit: { type: Number, required: true },
  selectedPlaceId: { type: String, default: null },
  source: { type: String, required: true },
  savedPlaceIds: { type: Array, required: true },
  zipSavedPlaceIds: { type: Array, required: true },
  mutatingPlaceId: { type: String, default: '' },
  actionMessage: { type: String, default: '' },
  actionError: { type: String, default: '' },
})

defineEmits(['select', 'add', 'remove'])

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
const formatRate = (cents) => currency.format(cents / 100)
const isSavedHere = (placeId) => props.zipSavedPlaceIds.includes(placeId)
const isSavedElsewhere = (placeId) => !isSavedHere(placeId) && props.savedPlaceIds.includes(placeId)

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
        <p class="section-kicker">{{ source === 'local' ? 'Saved locally' : 'API results' }}</p>
        <h2 id="nearby-title">Hotels near ZIP {{ center.postcode }}</h2>
      </div>
      <p class="result-count">{{ hotels.length }} {{ hotels.length === 1 ? 'place' : 'places' }} shown</p>
    </div>
    <p v-if="source === 'local'" class="nearby-note">
      Showing hotels saved locally for this ZIP, not a complete list of hotels in the area.
      Rates and room counts below are simulated classroom data, not provider information.
    </p>
    <p v-else class="nearby-note">
      Within 5 km of the resolved ZIP point. Showing up to {{ resultLimit }} provider results;
      this is not a complete hotel inventory or room availability search.
    </p>
    <p v-if="actionMessage" class="nearby-action-message" role="status">{{ actionMessage }}</p>
    <p v-if="actionError" class="alert-message" role="alert">{{ actionError }}</p>
    <p v-if="!hotels.length" class="state-card empty-state" role="status">
      No nearby hotels were returned for this ZIP. Try another ZIP code.
    </p>
    <div v-else class="nearby-layout">
      <div ref="nearbyList" class="nearby-list" aria-label="Nearby hotels">
        <article
          v-for="hotel in hotels"
          :key="hotel.place_id"
          :data-place-id="hotel.place_id"
          class="nearby-card"
          :class="{ 'is-selected': selectedPlaceId === hotel.place_id }"
        >
          <button
            type="button"
            class="nearby-card-select"
            :aria-pressed="selectedPlaceId === hotel.place_id"
            :aria-label="`Select ${hotel.name || 'unnamed hotel'} on map`"
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
          <ul v-if="source === 'local'" class="nearby-nights" aria-label="Simulated classroom nightly data">
            <li v-for="night in hotel.nights" :key="night.stay_date">
              <span>{{ night.stay_date }}</span>
              <span>{{ formatRate(night.nightly_rate_cents) }}/night · {{ night.rooms_available }} rooms</span>
            </li>
          </ul>
          <div class="nearby-card-actions">
            <span v-if="isSavedHere(hotel.place_id)" class="nearby-saved-label">Saved locally</span>
            <span v-else-if="isSavedElsewhere(hotel.place_id)" class="nearby-saved-label">Saved for another ZIP</span>
            <button
              type="button"
              :disabled="isSavedHere(hotel.place_id) || Boolean(mutatingPlaceId)"
              @click="$emit('add', hotel)"
            >{{ mutatingPlaceId === hotel.place_id ? 'Saving…' : 'Add to Local' }}</button>
            <button
              v-if="isSavedHere(hotel.place_id)"
              type="button"
              :disabled="Boolean(mutatingPlaceId)"
              @click="$emit('remove', hotel)"
            >{{ mutatingPlaceId === hotel.place_id ? 'Removing…' : 'Remove from Local' }}</button>
          </div>
        </article>
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
