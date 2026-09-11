export async function searchHotels(hotelName) {
  const parameters = new URLSearchParams({ name: hotelName })
  const response = await fetch(`/api/hotels/search?${parameters}`)

  if (!response.ok) {
    let message = 'Hotel search is unavailable. Please try again.'

    try {
      const body = await response.json()
      if (typeof body.detail === 'string') {
        message = body.detail
      }
    } catch {
      // Keep the user-friendly fallback when the server does not return JSON.
    }

    throw new Error(message)
  }

  return response.json()
}
