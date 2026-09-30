import assert from 'node:assert/strict'
import test from 'node:test'

import { hotelAddressLines } from '../src/components/hotelAddress.js'

test('formats a Geoapify hotel address without repeating the name or country', () => {
  assert.deepEqual(hotelAddressLines({
    name: 'Scholar Hotel State College',
    address: 'Scholar Hotel State College, 205 East Beaver Avenue, State College, PA 16801, United States of America',
  }), ['205 East Beaver Avenue', 'State College, PA 16801'])
})

test('preserves a second street line and groups city, state, and ZIP', () => {
  assert.deepEqual(hotelAddressLines({
    name: 'Harbor Hotel',
    address: 'Harbor Hotel, 12 Main Street, Floor 2, Boston, MA 02108, USA',
  }), ['12 Main Street', 'Floor 2', 'Boston, MA 02108'])
})

test('keeps partial provider addresses honest', () => {
  assert.deepEqual(hotelAddressLines({ name: null, address: '1 Example St' }), ['1 Example St'])
  assert.deepEqual(hotelAddressLines({ name: 'Harbor Hotel', address: null }), ['Address unavailable'])
})
