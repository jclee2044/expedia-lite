import { getNearbyHotels } from './locations.js'
import { getSavedHotels } from './savedHotels.js'

export async function searchZipLocalFirst(postcode) {
  const local = await getSavedHotels(postcode)
  if (local.hotels.length) {
    return {
      source: 'local',
      center: local.center,
      hotels: local.hotels,
      resultLimit: local.hotels.length,
      savedPlaceIds: local.saved_place_ids,
      zipSavedPlaceIds: local.hotels.map((hotel) => hotel.place_id),
    }
  }

  const api = await getNearbyHotels(postcode)
  return {
    source: 'api',
    center: api.center,
    hotels: api.hotels,
    resultLimit: api.result_limit,
    savedPlaceIds: local.saved_place_ids,
    zipSavedPlaceIds: [],
  }
}
