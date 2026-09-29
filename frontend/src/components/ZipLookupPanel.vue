<script setup>
import { ref } from 'vue'

const postcode = ref('')

defineProps({
  isLoading: { type: Boolean, default: false },
  location: { type: Object, default: null },
  errorMessage: { type: String, default: '' },
})

defineEmits(['lookup', 'change'])
</script>

<template>
  <section class="zip-demo-panel" aria-labelledby="zip-demo-title">
    <div class="zip-demo-heading">
      <div>
        <p class="section-kicker">Location search</p>
        <h2 id="zip-demo-title">Find hotels near a U.S. ZIP code</h2>
        <p>Explore hotels within 5 km of the ZIP code's mapped point.</p>
      </div>
    </div>

    <form class="zip-form" novalidate @submit.prevent="$emit('lookup', postcode)">
      <label for="zip-postcode">ZIP code</label>
      <div class="zip-form-controls">
        <input
          id="zip-postcode"
          v-model="postcode"
          type="text"
          inputmode="numeric"
          autocomplete="postal-code"
          placeholder="e.g. 16802"
          :disabled="isLoading"
          :aria-invalid="Boolean(errorMessage)"
          :aria-describedby="errorMessage ? 'zip-error' : 'zip-help'"
          @input="$emit('change')"
        />
        <button type="submit" :disabled="isLoading" :aria-busy="isLoading">
          Find nearby hotels
        </button>
      </div>
      <p id="zip-help" class="field-help">Five numeric digits are required.</p>
    </form>

    <div class="zip-demo-feedback" aria-live="polite">
      <p v-if="isLoading" class="zip-loading" role="status">
        <span class="loading-ring" aria-hidden="true"></span>
        Finding hotels near {{ postcode }}…
      </p>

      <p v-else-if="errorMessage" id="zip-error" class="alert-message zip-error" role="alert">
        <span aria-hidden="true">!</span>
        {{ errorMessage }}
      </p>

      <dl v-else-if="location" class="zip-location-facts">
        <div>
          <dt>Postcode</dt>
          <dd>{{ location.postcode }}</dd>
        </div>
        <div v-if="location.locality">
          <dt>Locality</dt>
          <dd>{{ location.locality }}</dd>
        </div>
        <div>
          <dt>Latitude</dt>
          <dd>{{ location.latitude }}</dd>
        </div>
        <div>
          <dt>Longitude</dt>
          <dd>{{ location.longitude }}</dd>
        </div>
      </dl>
    </div>
  </section>
</template>
