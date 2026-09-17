<script setup>
defineProps({
  booking: {
    type: Object,
    required: true,
  },
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
  <section class="confirmation-card" aria-labelledby="confirmation-title" tabindex="-1">
    <div class="confirmation-icon" aria-hidden="true">✓</div>
    <div class="confirmation-content">
      <p class="section-kicker">Booking confirmed</p>
      <h2 id="confirmation-title">Your stay is saved</h2>
      <p class="confirmation-lead">
        {{ booking.display_name }}, your simulated booking at
        <strong>{{ booking.hotel_name }}</strong> is confirmed.
      </p>

      <dl class="confirmation-facts">
        <div>
          <dt>Confirmation</dt>
          <dd>{{ booking.booking_id }}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd class="status-confirmed">{{ booking.status }}</dd>
        </div>
        <div>
          <dt>Stay</dt>
          <dd>{{ booking.trip_name }}</dd>
        </div>
        <div>
          <dt>Dates</dt>
          <dd>{{ formatDate(booking.check_in) }}–{{ formatDate(booking.check_out) }}</dd>
        </div>
        <div>
          <dt>Booked on</dt>
          <dd>{{ formatDate(booking.booked_on) }}</dd>
        </div>
        <div>
          <dt>Estimated total</dt>
          <dd>{{ formatCurrency(booking.stay_price_usd) }}</dd>
        </div>
      </dl>
    </div>
  </section>
</template>
