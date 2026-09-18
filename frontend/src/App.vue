<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'

import { createAccount, getCurrentAccount, login, logout } from './api/accounts.js'
import { createBooking, deleteBooking, updateBookingStatus } from './api/bookings.js'
import { searchHotels } from './api/hotels.js'
import { ApiError } from './api/http.js'
import { getAccountBookings } from './api/users.js'
import AccountPanel from './components/AccountPanel.vue'
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
const currentAccount = ref(null)
const isAccountBusy = ref(false)
const accountError = ref('')
const accountMessage = ref('')
const bookingTripId = ref('')
const bookingError = ref('')
const confirmedBooking = ref(null)
const history = ref(null)
const isHistoryLoading = ref(false)
const historyError = ref('')
const mutationBookingId = ref('')
const mutationError = ref('')
const confirmationRegion = ref(null)

const resultSummary = computed(() => {
  const hotelNoun = hotelCount.value === 1 ? 'hotel' : 'hotels'
  const stayNoun = results.value.length === 1 ? 'stay' : 'stays'
  return `${hotelCount.value} ${hotelNoun} · ${results.value.length} ${stayNoun}`
})

function clearAccountFeedback() {
  accountError.value = ''
  accountMessage.value = ''
}

function clearUserData() {
  confirmedBooking.value = null
  history.value = null
  historyError.value = ''
  mutationError.value = ''
  bookingError.value = ''
}

async function restoreSession() {
  try {
    currentAccount.value = await getCurrentAccount()
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) {
      accountError.value = error instanceof Error ? error.message : 'The login session could not be checked.'
    }
  }
}

async function handleCreateAccount(credentials) {
  isAccountBusy.value = true
  clearAccountFeedback()
  clearUserData()

  try {
    currentAccount.value = await createAccount(
      credentials.username,
      credentials.password,
      credentials.email,
    )
    accountMessage.value = `Account created. You are signed in as ${currentAccount.value.username}.`
  } catch (error) {
    currentAccount.value = null
    accountError.value = error instanceof Error ? error.message : 'The account could not be created.'
  } finally {
    isAccountBusy.value = false
  }
}

async function handleLogin(credentials) {
  isAccountBusy.value = true
  clearAccountFeedback()
  clearUserData()

  try {
    currentAccount.value = await login(credentials.username, credentials.password)
    accountMessage.value = `Welcome back, ${currentAccount.value.username}.`
  } catch (error) {
    currentAccount.value = null
    accountError.value = error instanceof Error ? error.message : 'Login failed.'
  } finally {
    isAccountBusy.value = false
  }
}

async function handleLogout() {
  isAccountBusy.value = true
  clearAccountFeedback()

  try {
    await logout()
    currentAccount.value = null
    clearUserData()
    activeView.value = 'search'
    accountMessage.value = 'You are logged out.'
  } catch (error) {
    accountError.value = error instanceof Error ? error.message : 'Logout failed.'
  } finally {
    isAccountBusy.value = false
  }
}

async function loadHistory() {
  if (!currentAccount.value) {
    return
  }

  isHistoryLoading.value = true
  historyError.value = ''

  try {
    history.value = await getAccountBookings()
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

function showSearch() {
  activeView.value = 'search'
}

function showAccount(message = '') {
  activeView.value = 'account'
  clearAccountFeedback()
  accountMessage.value = message
}

async function showHistory() {
  if (!currentAccount.value) {
    showAccount('Log in or create an account to review your trips.')
    return
  }

  activeView.value = 'history'
  await loadHistory()
}

async function bookStay(stay) {
  bookingError.value = ''

  if (!currentAccount.value) {
    showAccount('Log in or create an account before booking a stay.')
    return
  }

  bookingTripId.value = stay.trip_id
  confirmedBooking.value = null

  try {
    confirmedBooking.value = await createBooking(stay.trip_id)
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

onMounted(restoreSession)
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <a class="brand" href="#top" aria-label="Expedia Lite home" @click="showSearch">
        <span class="brand-mark" aria-hidden="true">✦</span>
        <span>Expedia Lite</span>
      </a>
      <div class="header-actions">
        <span v-if="currentAccount" class="signed-in-name">{{ currentAccount.username }}</span>
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
          <button
            type="button"
            :aria-current="activeView === 'account' ? 'page' : undefined"
            @click="showAccount()"
          >
            {{ currentAccount ? 'Account' : 'Login' }}
          </button>
        </nav>
      </div>
    </header>

    <main id="top" class="page-shell">
      <AccountPanel
        v-if="activeView === 'account'"
        :account="currentAccount"
        :is-busy="isAccountBusy"
        :error-message="accountError"
        :success-message="accountMessage"
        @create-account="handleCreateAccount"
        @login="handleLogin"
        @logout="handleLogout"
      />

      <template v-else>
        <section class="search-hero" aria-labelledby="page-title">
          <p class="eyebrow">{{ activeView === 'search' ? 'Find your next stay' : 'Your saved travel' }}</p>
          <h1 id="page-title">{{ activeView === 'search' ? 'Choose a hotel stay' : 'Review your trips' }}</h1>
          <p class="hero-copy">
            {{
              activeView === 'search'
                ? 'Search fictional properties and compare their available dates and prices.'
                : `Booking history for ${currentAccount?.username} is loaded from SQLite.`
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
            <p id="search-help" class="field-help">
              Search by partial hotel name.
              {{ currentAccount ? ` Signed in as ${currentAccount.username}.` : ' Login to book a stay.' }}
            </p>
          </form>

          <p v-if="activeView === 'search' && errorMessage" id="search-error" class="alert-message" role="alert">
            <span aria-hidden="true">!</span>
            {{ errorMessage }}
          </p>
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
              :booking-enabled="Boolean(currentAccount)"
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
      </template>
    </main>

    <footer>
      <p>Expedia Lite uses synthetic classroom travel data.</p>
    </footer>
  </div>
</template>
