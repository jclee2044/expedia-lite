import { requestJson } from './http.js'

export async function getSavedHotels(postcode) {
  const query = new URLSearchParams({ postcode })
  return requestJson(
    `/api/saved-hotels?${query}`,
    {},
    'Saved hotels could not be loaded. Please try again.',
  )
}

export async function saveHotel(hotel, center) {
  return requestJson('/api/saved-hotels', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      hotel: {
        place_id: hotel.place_id,
        name: hotel.name,
        address: hotel.address,
        latitude: hotel.latitude,
        longitude: hotel.longitude,
      },
      center,
    }),
  }, 'Hotel could not be saved locally. Please try again.')
}

export async function removeHotel(placeId) {
  return requestJson(
    `/api/saved-hotels/${encodeURIComponent(placeId)}`,
    { method: 'DELETE' },
    'Hotel could not be removed locally. Please try again.',
  )
}
