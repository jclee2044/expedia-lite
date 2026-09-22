<script setup>
defineProps({
  isLoading: { type: Boolean, default: false },
  location: { type: Object, default: null },
  errorMessage: { type: String, default: '' },
})

defineEmits(['lookup'])
</script>

<template>
  <section class="zip-demo-panel" aria-labelledby="zip-demo-title">
    <div class="zip-demo-heading">
      <div>
        <p class="section-kicker">Location service demo</p>
        <h2 id="zip-demo-title">ZIP lookup demonstration</h2>
        <p>Resolve the fixed classroom ZIP through the Expedia Lite backend.</p>
      </div>
      <button type="button" :disabled="isLoading" :aria-busy="isLoading" @click="$emit('lookup')">
        Look up ZIP 16802
      </button>
    </div>

    <div class="zip-demo-feedback" aria-live="polite">
      <p v-if="isLoading" class="zip-loading" role="status">
        <span class="loading-ring" aria-hidden="true"></span>
        Looking up ZIP 16802…
      </p>

      <p v-else-if="errorMessage" class="alert-message zip-error" role="alert">
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
