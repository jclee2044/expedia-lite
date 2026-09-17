import { requestJson } from './http.js'

export async function searchHotels(hotelName) {
  const parameters = new URLSearchParams({ name: hotelName })
  return requestJson(
    `/api/hotels/search?${parameters}`,
    {},
    'Hotel search is unavailable. Please try again.',
  )
}
