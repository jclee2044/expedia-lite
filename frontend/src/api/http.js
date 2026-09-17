export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function readErrorMessage(response, fallbackMessage) {
  try {
    const body = await response.json()
    return typeof body.detail === 'string' ? body.detail : fallbackMessage
  } catch {
    return fallbackMessage
  }
}

export async function requestJson(url, options = {}, fallbackMessage = 'The request failed.') {
  const response = await fetch(url, options)

  if (!response.ok) {
    const message = await readErrorMessage(response, fallbackMessage)
    throw new ApiError(message, response.status)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}
