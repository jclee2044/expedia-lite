<script setup>
import { computed } from 'vue'

const props = defineProps({
  stay: {
    type: Object,
    required: true,
  },
  bookingEnabled: {
    type: Boolean,
    default: false,
  },
  bookingBusy: {
    type: Boolean,
    default: false,
  },
  isBooking: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['book'])

const hotelPhotos = [
  'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=900&q=82',
  'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=900&q=82',
  'https://images.unsplash.com/photo-1445019980597-93fa8acb246c?auto=format&fit=crop&w=900&q=82',
]

const photoUrl = computed(() => {
  const numericId = Number.parseInt(props.stay.hotel_id.replace(/\D/g, ''), 10)
  return hotelPhotos[(numericId - 1) % hotelPhotos.length]
})

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
  <article class="stay-card">
    <div class="stay-photo">
      <img :src="photoUrl" alt="" loading="lazy" referrerpolicy="no-referrer" />
      <span class="photo-label">Fictional stay</span>
    </div>

    <div class="stay-details">
      <div class="stay-copy">
        <p class="location">{{ stay.city }}, {{ stay.state }}</p>
        <h3>{{ stay.hotel_name }}</h3>
        <p class="trip-name">{{ stay.trip_name }}</p>

        <dl class="stay-facts">
          <div>
            <dt>Check-in</dt>
            <dd>{{ formatDate(stay.check_in) }}</dd>
          </div>
          <div>
            <dt>Check-out</dt>
            <dd>{{ formatDate(stay.check_out) }}</dd>
          </div>
        </dl>
      </div>

      <div class="price-panel">
        <span class="price-ribbon">{{ stay.nights }}-night stay</span>
        <p class="nightly-rate">{{ formatCurrency(stay.nightly_rate_usd) }} per night</p>
        <p class="stay-price">{{ formatCurrency(stay.stay_price_usd) }}</p>
        <p class="price-caption">estimated stay total</p>
        <button
          class="book-button"
          type="button"
          :disabled="bookingBusy"
          @click="emit('book', stay)"
        >
          {{ isBooking ? 'Booking…' : bookingEnabled ? 'Book this stay' : 'Log in to book' }}
        </button>
      </div>
    </div>
  </article>
</template>
