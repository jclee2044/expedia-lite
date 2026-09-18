import { requestJson } from './http.js'

export async function getAccountBookings() {
  return requestJson(
    '/api/account/bookings',
    {},
    'Booking history is unavailable. Please try again.',
  )
}
