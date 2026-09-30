const US_COUNTRY = /^(?:United States(?: of America)?|USA|US)\.?$/i
const US_STATE_ZIP = /^[A-Z]{2}\s+\d{5}(?:-\d{4})?$/

export function hotelAddressLines(hotel) {
  let address = hotel.address?.trim()
  if (!address) return ['Address unavailable']

  const name = hotel.name?.trim()
  if (name && address.toLocaleLowerCase().startsWith(`${name.toLocaleLowerCase()},`)) {
    address = address.slice(name.length + 1).trim()
  }

  const parts = address.split(',').map((part) => part.trim()).filter(Boolean)
  if (US_COUNTRY.test(parts.at(-1) || '')) parts.pop()

  if (parts.length >= 2 && US_STATE_ZIP.test(parts.at(-1))) {
    const stateZip = parts.pop()
    const city = parts.pop()
    parts.push(`${city}, ${stateZip}`)
  }

  return parts.length ? parts : ['Address unavailable']
}
