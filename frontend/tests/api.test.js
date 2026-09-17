import assert from 'node:assert/strict'
import test from 'node:test'

import {
  createBooking,
  deleteBooking,
  getBooking,
  updateBookingStatus,
} from '../src/api/bookings.js'
import { searchHotels } from '../src/api/hotels.js'
import { ApiError } from '../src/api/http.js'
import { getUserBookings, listUsers } from '../src/api/users.js'

async function withFetch(stub, action) {
  const originalFetch = globalThis.fetch
  globalThis.fetch = stub
  try {
    return await action()
  } finally {
    globalThis.fetch = originalFetch
  }
}

function jsonResponse(body, init = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

test('searchHotels encodes the query and returns the response body', async () => {
  const expected = { query: 'Harbor & Bay', hotel_count: 0, results: [] }

  const actual = await withFetch(async (url, options) => {
    assert.equal(url, '/api/hotels/search?name=Harbor+%26+Bay')
    assert.deepEqual(options, {})
    return jsonResponse(expected)
  }, () => searchHotels('Harbor & Bay'))

  assert.deepEqual(actual, expected)
})

test('listUsers requests the documented users endpoint', async () => {
  const expected = { users: [{ user_id: 'U001', display_name: 'Demo Traveler 1' }] }

  const actual = await withFetch(async (url, options) => {
    assert.equal(url, '/api/users')
    assert.deepEqual(options, {})
    return jsonResponse(expected)
  }, listUsers)

  assert.deepEqual(actual, expected)
})

test('getUserBookings safely encodes the traveler identifier', async () => {
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/users/U%20006/bookings')
    assert.deepEqual(options, {})
    return jsonResponse({ user: {}, booking_count: 0, bookings: [] })
  }, () => getUserBookings('U 006'))
})

test('createBooking sends only the documented identifiers as JSON', async () => {
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/bookings')
    assert.equal(options.method, 'POST')
    assert.deepEqual(options.headers, { 'Content-Type': 'application/json' })
    assert.deepEqual(JSON.parse(options.body), { user_id: 'U006', trip_id: 'T001' })
    return jsonResponse({ booking_id: 'B007' }, { status: 201 })
  }, () => createBooking('U006', 'T001'))
})

test('getBooking safely encodes the booking identifier', async () => {
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/bookings/B%20007')
    assert.deepEqual(options, {})
    return jsonResponse({ booking_id: 'B007' })
  }, () => getBooking('B 007'))
})

test('updateBookingStatus sends the documented PATCH body', async () => {
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/bookings/B007')
    assert.equal(options.method, 'PATCH')
    assert.deepEqual(options.headers, { 'Content-Type': 'application/json' })
    assert.deepEqual(JSON.parse(options.body), { status: 'cancelled' })
    return jsonResponse({ booking_id: 'B007', status: 'cancelled' })
  }, () => updateBookingStatus('B007', 'cancelled'))
})

test('deleteBooking handles the documented empty 204 response', async () => {
  const result = await withFetch(async (url, options) => {
    assert.equal(url, '/api/bookings/B007')
    assert.deepEqual(options, { method: 'DELETE' })
    return new Response(null, { status: 204 })
  }, () => deleteBooking('B007'))

  assert.equal(result, null)
})

test('API detail messages and status codes are preserved', async () => {
  await assert.rejects(
    withFetch(
      async () => jsonResponse({ detail: 'Booking B999 was not found.' }, { status: 404 }),
      () => getBooking('B999'),
    ),
    (error) => {
      assert.ok(error instanceof ApiError)
      assert.equal(error.message, 'Booking B999 was not found.')
      assert.equal(error.status, 404)
      return true
    },
  )
})

test('a non-JSON failure uses the operation-specific fallback', async () => {
  await assert.rejects(
    withFetch(
      async () => new Response('Service unavailable', { status: 503 }),
      () => listUsers(),
    ),
    (error) => {
      assert.equal(error.message, 'Travelers are unavailable. Please try again.')
      assert.equal(error.status, 503)
      return true
    },
  )
})
