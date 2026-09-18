<script setup>
import { ref } from 'vue'

defineProps({
  account: { type: Object, default: null },
  isBusy: { type: Boolean, default: false },
  errorMessage: { type: String, default: '' },
  successMessage: { type: String, default: '' },
})

const emit = defineEmits(['create-account', 'login', 'logout'])

const mode = ref('login')
const username = ref('')
const password = ref('')
const email = ref('')

function selectMode(nextMode) {
  mode.value = nextMode
  password.value = ''
}

function submit() {
  const payload = {
    username: username.value,
    password: password.value,
    email: email.value,
  }
  password.value = ''
  if (mode.value === 'create') {
    emit('create-account', payload)
  } else {
    emit('login', payload)
  }
}
</script>

<template>
  <section class="account-section" aria-labelledby="account-title">
    <div class="account-heading">
      <p class="section-kicker">Your Expedia Lite account</p>
      <h1 id="account-title">{{ account ? `Hello, ${account.username}` : 'Create an account or log in' }}</h1>
      <p>
        {{
          account
            ? 'Searches, bookings, and trip history now use this account.'
            : 'Use made-up classroom credentials. Do not reuse a personal password.'
        }}
      </p>
    </div>

    <div v-if="account" class="signed-in-card">
      <div>
        <span class="account-avatar" aria-hidden="true">{{ account.username.charAt(0).toUpperCase() }}</span>
        <div>
          <strong>Signed in as {{ account.username }}</strong>
          <p>{{ account.email || 'No email provided' }} · {{ account.user_id }}</p>
        </div>
      </div>
      <button type="button" :disabled="isBusy" @click="emit('logout')">
        {{ isBusy ? 'Logging out…' : 'Logout' }}
      </button>
    </div>

    <div v-else class="account-card">
      <div class="account-tabs" role="tablist" aria-label="Account action">
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'login'"
          @click="selectMode('login')"
        >
          Login
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'create'"
          @click="selectMode('create')"
        >
          Create account
        </button>
      </div>

      <form class="account-form" @submit.prevent="submit">
        <label for="account-username">Username</label>
        <input
          id="account-username"
          v-model="username"
          name="username"
          type="text"
          autocomplete="username"
          minlength="3"
          maxlength="32"
          pattern="[A-Za-z0-9_.-]+"
          required
        />

        <label for="account-password">Password</label>
        <input
          id="account-password"
          v-model="password"
          name="password"
          type="password"
          :autocomplete="mode === 'create' ? 'new-password' : 'current-password'"
          minlength="4"
          maxlength="72"
          required
        />

        <template v-if="mode === 'create'">
          <label for="account-email">Email <span>(optional)</span></label>
          <input
            id="account-email"
            v-model="email"
            name="email"
            type="email"
            autocomplete="email"
            maxlength="254"
          />
        </template>

        <p class="field-help">
          Usernames use 3–32 letters, numbers, dots, hyphens, or underscores.
        </p>
        <button class="primary-action" type="submit" :disabled="isBusy">
          {{ isBusy ? 'Please wait…' : mode === 'create' ? 'Create account' : 'Login' }}
        </button>
      </form>
    </div>

    <p v-if="errorMessage" class="alert-message" role="alert">
      <span aria-hidden="true">!</span>
      {{ errorMessage }}
    </p>
    <p v-else-if="successMessage" class="account-success" role="status">
      {{ successMessage }}
    </p>
  </section>
</template>
