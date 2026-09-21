import assert from 'node:assert/strict'
import test from 'node:test'

import { createAccount, getCurrentAccount, login, logout } from '../src/api/accounts.js'
import {
  createBooking,
  deleteBooking,
  getBooking,
  updateBookingStatus,
} from '../src/api/bookings.js'
import { searchHotels } from '../src/api/hotels.js'
import { ApiError } from '../src/api/http.js'
import { getAccountBookings } from '../src/api/users.js'

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
  const expected = {
    query: 'Harbor & Bay',
    hotel_count: 0,
    pricing: {
      daily_search_count: 4,
      multiplier: 1.2,
      adjustment_applied: true,
      time_zone: 'America/New_York',
    },
    results: [],
  }

  const actual = await withFetch(async (url, options) => {
    assert.equal(url, '/api/hotels/search?name=Harbor+%26+Bay')
    assert.deepEqual(options, {})
    return jsonResponse(expected)
  }, () => searchHotels('Harbor & Bay'))

  assert.deepEqual(actual, expected)
})

test('getAccountBookings requests authenticated history', async () => {
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/account/bookings')
    assert.deepEqual(options, {})
    return jsonResponse({ user: {}, booking_count: 0, bookings: [] })
  }, getAccountBookings)
})

test('createBooking sends the selected trip and its search context as JSON', async () => {
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/bookings')
    assert.equal(options.method, 'POST')
    assert.deepEqual(options.headers, { 'Content-Type': 'application/json' })
    assert.deepEqual(JSON.parse(options.body), {
      trip_id: 'T001',
      search_query: 'Harbor',
    })
    return jsonResponse({ booking_id: 'B007' }, { status: 201 })
  }, () => createBooking('T001', 'Harbor'))
})

test('createAccount sends optional email and demo credentials', async () => {
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/accounts')
    assert.equal(options.method, 'POST')
    assert.deepEqual(options.headers, { 'Content-Type': 'application/json' })
    assert.deepEqual(JSON.parse(options.body), {
      username: 'harbor_fan',
      password: 'made-up-pass',
      email: 'harbor@example.test',
    })
    return jsonResponse({ user_id: 'U007', username: 'harbor_fan' }, { status: 201 })
  }, () => createAccount('harbor_fan', 'made-up-pass', 'harbor@example.test'))
})

test('login, current account, and logout use the documented endpoints', async () => {
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/auth/login')
    assert.deepEqual(JSON.parse(options.body), {
      username: 'demo_u001',
      password: 'demo-pass-u001',
    })
    return jsonResponse({ user_id: 'U001', username: 'demo_u001' })
  }, () => login('demo_u001', 'demo-pass-u001'))

  await withFetch(async (url, options) => {
    assert.equal(url, '/api/auth/session')
    assert.deepEqual(options, {})
    return jsonResponse({ user_id: 'U001', username: 'demo_u001' })
  }, getCurrentAccount)

  const result = await withFetch(async (url, options) => {
    assert.equal(url, '/api/auth/logout')
    assert.deepEqual(options, { method: 'POST' })
    return new Response(null, { status: 204 })
  }, logout)
  assert.equal(result, null)
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
      () => getAccountBookings(),
    ),
    (error) => {
      assert.equal(error.message, 'Booking history is unavailable. Please try again.')
      assert.equal(error.status, 503)
      return true
    },
  )
})
