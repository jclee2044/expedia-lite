import { requestJson } from './http.js'

export function isValidUsZipCode(postcode) {
  return /^[0-9]{5}$/.test(postcode)
}

export async function getZipLocation(postcode) {
  const query = new URLSearchParams({ postcode })
  return requestJson(
    `/api/zip-location?${query}`,
    {},
    'ZIP lookup is unavailable. Please try again.',
  )
}

export async function getNearbyHotels(postcode) {
  const query = new URLSearchParams({ postcode })
  return requestJson(
    `/api/hotels/nearby?${query}`,
    {},
    'Nearby hotel search is unavailable. Please try again.',
  )
}
