import { requestJson } from './http.js'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

export async function createBooking(tripId, searchQuery) {
  return requestJson(
    '/api/bookings',
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({ trip_id: tripId, search_query: searchQuery }),
    },
    'The booking could not be created. Please try again.',
  )
}

export async function getBooking(bookingId) {
  return requestJson(
    `/api/bookings/${encodeURIComponent(bookingId)}`,
    {},
    'The booking could not be loaded. Please try again.',
  )
}

export async function updateBookingStatus(bookingId, status) {
  return requestJson(
    `/api/bookings/${encodeURIComponent(bookingId)}`,
    {
      method: 'PATCH',
      headers: JSON_HEADERS,
      body: JSON.stringify({ status }),
    },
    'The booking could not be updated. Please try again.',
  )
}

export async function deleteBooking(bookingId) {
  return requestJson(
    `/api/bookings/${encodeURIComponent(bookingId)}`,
    { method: 'DELETE' },
    'The booking could not be deleted. Please try again.',
  )
}
