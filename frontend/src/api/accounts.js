import { requestJson } from './http.js'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

export async function createAccount(username, password, email = '') {
  return requestJson(
    '/api/accounts',
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({ username, password, email: email || null }),
    },
    'The account could not be created. Please try again.',
  )
}

export async function login(username, password) {
  return requestJson(
    '/api/auth/login',
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({ username, password }),
    },
    'Login is unavailable. Please try again.',
  )
}

export async function getCurrentAccount() {
  return requestJson('/api/auth/session', {}, 'The login session could not be checked.')
}

export async function logout() {
  return requestJson(
    '/api/auth/logout',
    { method: 'POST' },
    'Logout could not be completed. Please try again.',
  )
}
