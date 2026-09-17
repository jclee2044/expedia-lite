<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'

import { createBooking, deleteBooking, updateBookingStatus } from './api/bookings.js'
import { searchHotels } from './api/hotels.js'
import { getUserBookings, listUsers } from './api/users.js'
import BookingConfirmation from './components/BookingConfirmation.vue'
import BookingHistory from './components/BookingHistory.vue'
import StayCard from './components/StayCard.vue'

const activeView = ref('search')
const hotelName = ref('')
const submittedQuery = ref('')
const hotelCount = ref(0)
const results = ref([])
const hasSearched = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const users = ref([])
const selectedUserId = ref('')
const isUsersLoading = ref(false)
const travelerError = ref('')
const travelerMessage = ref('')
const bookingTripId = ref('')
const bookingError = ref('')
const confirmedBooking = ref(null)
const history = ref(null)
const isHistoryLoading = ref(false)
const historyError = ref('')
const mutationBookingId = ref('')
const mutationError = ref('')
const travelerSelect = ref(null)
const confirmationRegion = ref(null)

const resultSummary = computed(() => {
  const hotelNoun = hotelCount.value === 1 ? 'hotel' : 'hotels'
  const stayNoun = results.value.length === 1 ? 'stay' : 'stays'
  return `${hotelCount.value} ${hotelNoun} · ${results.value.length} ${stayNoun}`
})

const selectedTraveler = computed(() =>
  users.value.find((user) => user.user_id === selectedUserId.value),
)

async function loadTravelers() {
  isUsersLoading.value = true
  travelerError.value = ''

  try {
    const response = await listUsers()
    users.value = response.users
  } catch (error) {
    users.value = []
    travelerError.value = error instanceof Error ? error.message : 'Travelers are unavailable.'
  } finally {
    isUsersLoading.value = false
  }
}

async function focusTravelerSelect() {
  await nextTick()
  travelerSelect.value?.focus()
}

async function loadHistory() {
  if (!selectedUserId.value) {
    return
  }

  isHistoryLoading.value = true
  historyError.value = ''

  try {
    history.value = await getUserBookings(selectedUserId.value)
  } catch (error) {
    history.value = null
    historyError.value = error instanceof Error ? error.message : 'Booking history is unavailable.'
  } finally {
    isHistoryLoading.value = false
  }
}

async function cancelBooking(booking) {
  mutationBookingId.value = booking.booking_id
  mutationError.value = ''

  try {
    await updateBookingStatus(booking.booking_id, 'cancelled')
    await loadHistory()
  } catch (error) {
    mutationError.value = error instanceof Error ? error.message : 'The booking could not be updated.'
  } finally {
    mutationBookingId.value = ''
  }
}

async function deleteBookingRecord(booking) {
  mutationBookingId.value = booking.booking_id
  mutationError.value = ''

  try {
    await deleteBooking(booking.booking_id)
    await loadHistory()
  } catch (error) {
    mutationError.value = error instanceof Error ? error.message : 'The booking could not be deleted.'
  } finally {
    mutationBookingId.value = ''
  }
}

async function handleTravelerChange() {
  travelerMessage.value = ''
  bookingError.value = ''
  confirmedBooking.value = null
  history.value = null
  historyError.value = ''
  mutationError.value = ''

  if (activeView.value === 'history' && selectedUserId.value) {
    await loadHistory()
  }
}

function showSearch() {
  activeView.value = 'search'
  travelerMessage.value = ''
}

async function showHistory() {
  if (!selectedUserId.value) {
    activeView.value = 'search'
    travelerMessage.value = 'Choose a demo traveler to review booking history.'
    await focusTravelerSelect()
    return
  }

  activeView.value = 'history'
  travelerMessage.value = ''
  await loadHistory()
}

async function bookStay(stay) {
  bookingError.value = ''

  if (!selectedUserId.value) {
    bookingError.value = 'Choose a demo traveler before booking this stay.'
    await focusTravelerSelect()
    return
  }

  bookingTripId.value = stay.trip_id
  confirmedBooking.value = null

  try {
    confirmedBooking.value = await createBooking(selectedUserId.value, stay.trip_id)
    await loadHistory()
    await nextTick()
    confirmationRegion.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch (error) {
    bookingError.value = error instanceof Error ? error.message : 'The booking could not be created.'
  } finally {
    bookingTripId.value = ''
  }
}

async function submitSearch() {
  const query = hotelName.value.trim()
  errorMessage.value = ''

  if (!query) {
    hasSearched.value = false
    hotelCount.value = 0
    results.value = []
    errorMessage.value = 'Enter a hotel name.'
    return
  }

  isLoading.value = true

  try {
    const search = await searchHotels(query)
    submittedQuery.value = search.query
    hotelCount.value = search.hotel_count
    results.value = search.results
    hasSearched.value = true
  } catch (error) {
    hasSearched.value = false
    hotelCount.value = 0
    results.value = []
    errorMessage.value = error instanceof Error ? error.message : 'Hotel search failed.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadTravelers)
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <a class="brand" href="#top" aria-label="Expedia Lite home">
        <span class="brand-mark" aria-hidden="true">✦</span>
        <span>Expedia Lite</span>
      </a>
      <nav class="view-nav" aria-label="Primary navigation">
        <button
          type="button"
          :aria-current="activeView === 'search' ? 'page' : undefined"
          @click="showSearch"
        >
          Find stays
        </button>
        <button
          type="button"
          :aria-current="activeView === 'history' ? 'page' : undefined"
          @click="showHistory"
        >
          My trips
        </button>
      </nav>
    </header>

    <main id="top" class="page-shell">
      <section class="search-hero" aria-labelledby="page-title">
        <p class="eyebrow">{{ activeView === 'search' ? 'Find your next stay' : 'Your saved travel' }}</p>
        <h1 id="page-title">{{ activeView === 'search' ? 'Choose a hotel stay' : 'Review your trips' }}</h1>
        <p class="hero-copy">
          {{
            activeView === 'search'
              ? 'Search fictional properties and compare their available dates and prices.'
              : 'Booking history is loaded from the same SQLite records created through the app.'
          }}
        </p>

        <form v-if="activeView === 'search'" class="search-form" role="search" @submit.prevent="submitSearch">
          <label for="hotel-name">Hotel name</label>
          <div class="search-control">
            <span class="search-icon" aria-hidden="true"></span>
            <input
              id="hotel-name"
              v-model="hotelName"
              name="hotel-name"
              type="search"
              placeholder="Try Harbor or Capitol"
              autocomplete="off"
              :aria-describedby="errorMessage ? 'search-error' : 'search-help'"
            />
            <button type="submit" :disabled="isLoading">
              {{ isLoading ? 'Searching…' : 'Search' }}
            </button>
          </div>
          <p id="search-help" class="field-help">Search by partial hotel name.</p>
        </form>

        <p v-if="activeView === 'search' && errorMessage" id="search-error" class="alert-message" role="alert">
          <span aria-hidden="true">!</span>
          {{ errorMessage }}
        </p>

        <section class="traveler-panel" aria-labelledby="traveler-title">
          <div>
            <p class="section-kicker">Who is traveling?</p>
            <h2 id="traveler-title">Choose a demo traveler</h2>
            <p>Bookings and history are saved under the selected synthetic traveler.</p>
          </div>

          <div class="traveler-control">
            <label for="traveler">Demo traveler</label>
            <select
              id="traveler"
              ref="travelerSelect"
              v-model="selectedUserId"
              :disabled="isUsersLoading || !users.length"
              :aria-describedby="travelerError ? 'traveler-error' : travelerMessage ? 'traveler-message' : 'traveler-help'"
              @change="handleTravelerChange"
            >
              <option value="">{{ isUsersLoading ? 'Loading travelers…' : 'Select a traveler' }}</option>
              <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                {{ user.display_name }} ({{ user.user_id }})
              </option>
            </select>
            <p id="traveler-help" class="field-help">
              {{ selectedTraveler ? `${selectedTraveler.display_name} is selected.` : 'Required to book a stay.' }}
            </p>
            <div v-if="travelerError" id="traveler-error" class="inline-error" role="alert">
              <span>{{ travelerError }}</span>
              <button type="button" @click="loadTravelers">Retry</button>
            </div>
            <p v-else-if="travelerMessage" id="traveler-message" class="selection-message" role="alert">
              {{ travelerMessage }}
            </p>
          </div>
        </section>
      </section>

      <section
        v-if="activeView === 'search'"
        class="results-section"
        aria-labelledby="results-title"
        aria-live="polite"
      >
        <div v-if="confirmedBooking" ref="confirmationRegion" class="confirmation-region">
          <BookingConfirmation :booking="confirmedBooking" />
        </div>

        <p v-if="bookingError" class="alert-message booking-alert" role="alert">
          <span aria-hidden="true">!</span>
          {{ bookingError }}
        </p>

        <div class="results-heading">
          <div>
            <p class="section-kicker">Available stays</p>
            <h2 id="results-title">
              {{ hasSearched ? `Results for “${submittedQuery}”` : 'Start with a hotel search' }}
            </h2>
          </div>
          <p v-if="hasSearched" class="result-count">{{ resultSummary }}</p>
        </div>

        <div v-if="hasSearched && results.length" class="context-chips" aria-label="Result details">
          <span>Hotel matches</span>
          <span>Fixed stay dates</span>
          <span>Prices in USD</span>
        </div>

        <div v-if="isLoading" class="state-card loading-state" role="status">
          <span class="loading-ring" aria-hidden="true"></span>
          <div>
            <strong>Searching available stays</strong>
            <p>Checking the local Expedia Lite database…</p>
          </div>
        </div>

        <div v-else-if="hasSearched && results.length" class="stay-list">
          <StayCard
            v-for="stay in results"
            :key="stay.trip_id"
            :stay="stay"
            :booking-enabled="Boolean(selectedUserId)"
            :booking-busy="Boolean(bookingTripId)"
            :is-booking="bookingTripId === stay.trip_id"
            @book="bookStay"
          />
        </div>

        <div v-else-if="hasSearched" class="state-card empty-state">
          <span class="state-icon" aria-hidden="true">⌕</span>
          <h3>No stays found</h3>
          <p>We couldn’t find a hotel matching “{{ submittedQuery }}”. Try another hotel name.</p>
        </div>

        <div v-else class="state-card welcome-state">
          <span class="state-icon" aria-hidden="true">⌂</span>
          <div>
            <h3>Your stay search starts here</h3>
            <p>Use a fictional hotel name above to see matching dates and prices.</p>
          </div>
        </div>
      </section>

      <BookingHistory
        v-else
        :history="history"
        :is-loading="isHistoryLoading"
        :error-message="historyError"
        :mutation-booking-id="mutationBookingId"
        :mutation-error="mutationError"
        @cancel-booking="cancelBooking"
        @delete-booking="deleteBookingRecord"
        @retry="loadHistory"
      />
    </main>

    <footer>
      <p>Expedia Lite uses synthetic classroom travel data.</p>
    </footer>
  </div>
</template>
