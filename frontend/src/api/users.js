import { requestJson } from './http.js'

export async function listUsers() {
  return requestJson('/api/users', {}, 'Travelers are unavailable. Please try again.')
}

export async function getUserBookings(userId) {
  return requestJson(
    `/api/users/${encodeURIComponent(userId)}/bookings`,
    {},
    'Booking history is unavailable. Please try again.',
  )
}
