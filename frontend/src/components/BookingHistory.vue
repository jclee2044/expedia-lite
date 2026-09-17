<script setup>
import { ref } from 'vue'

defineProps({
  history: {
    type: Object,
    default: null,
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  errorMessage: {
    type: String,
    default: '',
  },
  mutationBookingId: {
    type: String,
    default: '',
  },
  mutationError: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['retry', 'cancel-booking', 'delete-booking'])
const deleteCandidateId = ref('')

function requestDelete(bookingId) {
  deleteCandidateId.value = bookingId
}

function keepBooking() {
  deleteCandidateId.value = ''
}

function confirmDelete(booking) {
  emit('delete-booking', booking)
}

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZone: 'UTC',
})

function formatCurrency(amount) {
  return currencyFormatter.format(amount)
}

function formatDate(date) {
  return dateFormatter.format(new Date(`${date}T00:00:00Z`))
}
</script>

<template>
  <section class="results-section history-section" aria-labelledby="history-title" aria-live="polite">
    <div class="results-heading">
      <div>
        <p class="section-kicker">Booking history</p>
        <h2 id="history-title">
          {{ history ? `${history.user.display_name}’s trips` : 'Your saved trips' }}
        </h2>
      </div>
      <p v-if="history" class="result-count">
        {{ history.booking_count }} {{ history.booking_count === 1 ? 'booking' : 'bookings' }}
      </p>
    </div>

    <div v-if="isLoading" class="state-card loading-state" role="status">
      <span class="loading-ring" aria-hidden="true"></span>
      <div>
        <strong>Loading booking history</strong>
        <p>Retrieving this traveler’s saved SQLite records…</p>
      </div>
    </div>

    <div v-else-if="errorMessage" class="history-error" role="alert">
      <div>
        <strong>Booking history could not be loaded</strong>
        <p>{{ errorMessage }}</p>
      </div>
      <button type="button" @click="$emit('retry')">Try again</button>
    </div>

    <div v-else-if="history?.bookings.length" class="history-list">
      <p v-if="mutationError" class="alert-message mutation-alert" role="alert">
        <span aria-hidden="true">!</span>
        {{ mutationError }}
      </p>

      <article v-for="booking in history.bookings" :key="booking.booking_id" class="booking-card">
        <div class="booking-card-heading">
          <div>
            <p class="location">{{ booking.city }}, {{ booking.state }}</p>
            <h3>{{ booking.hotel_name }}</h3>
            <p class="trip-name">{{ booking.trip_name }}</p>
          </div>
          <span class="status-badge" :class="`status-${booking.status}`">{{ booking.status }}</span>
        </div>

        <dl class="booking-facts">
          <div>
            <dt>Confirmation</dt>
            <dd>{{ booking.booking_id }}</dd>
          </div>
          <div>
            <dt>Booked</dt>
            <dd>{{ formatDate(booking.booked_on) }}</dd>
          </div>
          <div>
            <dt>Check-in</dt>
            <dd>{{ formatDate(booking.check_in) }}</dd>
          </div>
          <div>
            <dt>Check-out</dt>
            <dd>{{ formatDate(booking.check_out) }}</dd>
          </div>
          <div>
            <dt>Length</dt>
            <dd>{{ booking.nights }} {{ booking.nights === 1 ? 'night' : 'nights' }}</dd>
          </div>
          <div>
            <dt>Estimated total</dt>
            <dd>{{ formatCurrency(booking.stay_price_usd) }}</dd>
          </div>
        </dl>

        <div class="booking-actions">
          <button
            v-if="booking.status === 'confirmed'"
            class="secondary-action"
            type="button"
            :disabled="Boolean(mutationBookingId)"
            @click="emit('cancel-booking', booking)"
          >
            {{ mutationBookingId === booking.booking_id ? 'Updating…' : 'Cancel booking' }}
          </button>
          <button
            v-if="deleteCandidateId !== booking.booking_id"
            class="danger-link"
            type="button"
            :disabled="Boolean(mutationBookingId)"
            @click="requestDelete(booking.booking_id)"
          >
            Delete permanently
          </button>
        </div>

        <div v-if="deleteCandidateId === booking.booking_id" class="delete-confirmation" role="alert">
          <div>
            <strong>Delete {{ booking.booking_id }} permanently?</strong>
            <p>This removes the record from booking history and cannot be undone.</p>
          </div>
          <div class="delete-confirmation-actions">
            <button
              type="button"
              :disabled="Boolean(mutationBookingId)"
              @click="keepBooking"
            >
              Keep booking
            </button>
            <button
              class="danger-action"
              type="button"
              :disabled="Boolean(mutationBookingId)"
              @click="confirmDelete(booking)"
            >
              {{ mutationBookingId === booking.booking_id ? 'Deleting…' : 'Yes, delete permanently' }}
            </button>
          </div>
        </div>
      </article>
    </div>

    <div v-else-if="history" class="state-card empty-state">
      <span class="state-icon" aria-hidden="true">◇</span>
      <h3>No bookings yet</h3>
      <p>{{ history.user.display_name }} has no saved trips. Find a stay to create the first one.</p>
    </div>
  </section>
</template>
