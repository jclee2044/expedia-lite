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
import { getNearbyHotels, getZipLocation, isValidUsZipCode } from '../src/api/locations.js'
import { getSavedHotels, removeHotel, saveHotel } from '../src/api/savedHotels.js'
import { getAccountBookings } from '../src/api/users.js'
import { searchZipLocalFirst } from '../src/api/zipSearch.js'

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

test('getZipLocation preserves leading zeroes in the backend proxy request', async () => {
  const expected = {
    postcode: '00501',
    country_code: 'us',
    latitude: 40.8154,
    longitude: -73.0451,
    locality: 'Holtsville',
  }

  const actual = await withFetch(async (url, options) => {
    assert.equal(url, '/api/zip-location?postcode=00501')
    assert.deepEqual(options, {})
    return jsonResponse(expected)
  }, () => getZipLocation('00501'))

  assert.deepEqual(actual, expected)
})

test('getNearbyHotels requests the ZIP search through the backend proxy', async () => {
  const expected = {
    center: { postcode: '00501', latitude: 40.8154, longitude: -73.0451 },
    radius_meters: 5000,
    result_limit: 50,
    hotels: [],
  }
  const actual = await withFetch(async (url, options) => {
    assert.equal(url, '/api/hotels/nearby?postcode=00501')
    assert.deepEqual(options, {})
    return jsonResponse(expected)
  }, () => getNearbyHotels('00501'))
  assert.deepEqual(actual, expected)
})

test('local-first ZIP lookup uses saved results without calling the provider route', async () => {
  const calls = []
  const result = await withFetch(async (url) => {
    calls.push(url)
    return jsonResponse({
      center: { postcode: '16802', latitude: 40.8, longitude: -77.8 },
      hotels: [{ place_id: 'provider:1', nights: [] }],
      saved_place_ids: ['provider:1'],
    })
  }, () => searchZipLocalFirst('16802'))
  assert.deepEqual(calls, ['/api/saved-hotels?postcode=16802'])
  assert.equal(result.source, 'local')
  assert.deepEqual(result.savedPlaceIds, ['provider:1'])
  assert.deepEqual(result.zipSavedPlaceIds, ['provider:1'])
})

test('local-first ZIP lookup calls the provider only after an empty local success', async () => {
  const calls = []
  const result = await withFetch(async (url) => {
    calls.push(url)
    if (calls.length === 1) {
      return jsonResponse({ center: null, hotels: [], saved_place_ids: ['provider:elsewhere'] })
    }
    return jsonResponse({
      center: { postcode: '16802' }, hotels: [{ place_id: 'provider:elsewhere' }],
      result_limit: 50,
    })
  }, () => searchZipLocalFirst('16802'))
  assert.deepEqual(calls, [
    '/api/saved-hotels?postcode=16802', '/api/hotels/nearby?postcode=16802',
  ])
  assert.equal(result.source, 'api')
  assert.deepEqual(result.savedPlaceIds, ['provider:elsewhere'])
  assert.deepEqual(result.zipSavedPlaceIds, [])
})

test('a repeated local ZIP lookup returns newly committed nightly values', async () => {
  let roomsAvailable = 20
  const calls = []
  await withFetch(async (url) => {
    calls.push(url)
    return jsonResponse({
      center: { postcode: '16802' },
      hotels: [{
        place_id: 'provider:1',
        nights: [{ stay_date: '2026-10-11', nightly_rate_cents: 10000,
          rooms_available: roomsAvailable }],
      }],
      saved_place_ids: ['provider:1'],
    })
  }, async () => {
    assert.equal((await searchZipLocalFirst('16802')).hotels[0].nights[0].rooms_available, 20)
    roomsAvailable = 3
    assert.equal((await searchZipLocalFirst('16802')).hotels[0].nights[0].rooms_available, 3)
  })
  assert.deepEqual(calls, [
    '/api/saved-hotels?postcode=16802', '/api/saved-hotels?postcode=16802',
  ])
})

test('local lookup failure does not call the provider', async () => {
  const calls = []
  await assert.rejects(withFetch(async (url) => {
    calls.push(url)
    return jsonResponse({ detail: 'Saved hotels could not be loaded.' }, { status: 500 })
  }, () => searchZipLocalFirst('16802')))
  assert.deepEqual(calls, ['/api/saved-hotels?postcode=16802'])
})

test('saved hotel requests preserve provider ID and ZIP context', async () => {
  const hotel = {
    place_id: 'provider:ABC/1', name: null, address: null,
    latitude: 40.8, longitude: -77.8,
  }
  const center = {
    postcode: '16802', country_code: 'us', latitude: 40.81,
    longitude: -77.81, locality: null,
  }
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/saved-hotels')
    assert.equal(options.method, 'POST')
    assert.deepEqual(JSON.parse(options.body), { hotel, center })
    return jsonResponse({ place_id: hotel.place_id })
  }, () => saveHotel(hotel, center))
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/saved-hotels?postcode=16802')
    assert.deepEqual(options, {})
    return jsonResponse({ center: null, hotels: [], saved_place_ids: [] })
  }, () => getSavedHotels('16802'))
  await withFetch(async (url, options) => {
    assert.equal(url, '/api/saved-hotels/provider%3AABC%2F1')
    assert.deepEqual(options, { method: 'DELETE' })
    return new Response(null, { status: 204 })
  }, () => removeHotel(hotel.place_id))
})

test('ZIP validation accepts only five ASCII digits, including leading zeroes', () => {
  assert.equal(isValidUsZipCode('02108'), true)
  for (const postcode of ['', '1234', '123456', '12a45', '12 45', '１２３４５']) {
    assert.equal(isValidUsZipCode(postcode), false)
  }
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
