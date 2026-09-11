<script setup>
import { computed, ref } from 'vue'

import { searchHotels } from './api/hotels.js'

const hotelName = ref('')
const submittedQuery = ref('')
const hotelCount = ref(0)
const results = ref([])
const hasSearched = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

const resultSummary = computed(() => {
  const noun = hotelCount.value === 1 ? 'hotel' : 'hotels'
  return `${hotelCount.value} ${noun} found.`
})

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

function formatCurrency(amount) {
  return currencyFormatter.format(amount)
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
</script>

<template>
  <main>
    <header>
      <h1>Expedia Lite</h1>
      <p>Hotel Search</p>
    </header>

    <form @submit.prevent="submitSearch">
      <label for="hotel-name">Hotel name</label>
      <input
        id="hotel-name"
        v-model="hotelName"
        name="hotel-name"
        type="search"
        autocomplete="off"
        :aria-describedby="errorMessage ? 'search-error' : undefined"
      />
      <button type="submit" :disabled="isLoading">
        {{ isLoading ? 'Searching…' : 'Search' }}
      </button>
    </form>

    <p v-if="errorMessage" id="search-error" role="alert">
      {{ errorMessage }}
    </p>

    <section aria-labelledby="results-title" aria-live="polite">
      <h2 id="results-title">Results</h2>

      <p v-if="isLoading">Searching…</p>

      <template v-else-if="hasSearched">
        <p>{{ resultSummary }}</p>

        <table v-if="results.length">
          <thead>
            <tr>
              <th scope="col">Hotel</th>
              <th scope="col">Location</th>
              <th scope="col">Stay</th>
              <th scope="col">Check-in</th>
              <th scope="col">Check-out</th>
              <th scope="col">Nights</th>
              <th scope="col">Nightly rate</th>
              <th scope="col">Stay price</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stay in results" :key="stay.trip_id">
              <td>{{ stay.hotel_name }}</td>
              <td>{{ stay.city }}, {{ stay.state }}</td>
              <td>{{ stay.trip_name }}</td>
              <td>{{ stay.check_in }}</td>
              <td>{{ stay.check_out }}</td>
              <td>{{ stay.nights }}</td>
              <td>{{ formatCurrency(stay.nightly_rate_usd) }}</td>
              <td>{{ formatCurrency(stay.stay_price_usd) }}</td>
            </tr>
          </tbody>
        </table>

        <p v-else>No results found for “{{ submittedQuery }}”.</p>
      </template>
    </section>
  </main>
</template>

<style scoped>
table {
  border-collapse: collapse;
}

th,
td {
  padding: 0.25rem 0.5rem;
  border: 1px solid;
  text-align: left;
}
</style>
