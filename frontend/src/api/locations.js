import { requestJson } from './http.js'

export async function getDemoZipLocation() {
  return requestJson(
    '/api/demo/zip-location',
    {},
    'ZIP lookup is unavailable. Please try again.',
  )
}
