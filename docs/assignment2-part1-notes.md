# Assignment 2 Part 1 design notes

The [layout sketch](assignment2-part1-mockup.svg) records the ZIP form, provider
feedback, linked list, and map. It was drawn during implementation on 2026-09-29;
it should not be represented as a pre-implementation artifact.

## Research and decisions

- [Geoapify Geocoding](https://apidocs.geoapify.com/docs/geocoding/) supports
  postcode lookup and a country filter. The existing controller additionally
  checks the returned postcode, country, and coordinates, because a near match
  would move the search to the wrong place.
- [Geoapify Places](https://apidocs.geoapify.com/docs/places/) provides
  `accommodation.hotel`, a radius filter in meters, place identifiers, and
  coordinates. The app uses a 5,000-meter circle around the resolved ZIP point;
  proximity is used only to order the results. The 50-result cap keeps the
  display manageable and is stated in the UI. Provider coverage and fields vary.
- [Leaflet Quick Start](https://leafletjs.com/examples/quick-start/) shows
  basic maps, markers, and tile attribution. The app uses Leaflet directly,
  with one selected place ID shared by list and map. HTML map pins avoid an
  extra icon asset package. An interactive map alone would be hard to use with
  a keyboard, so list items and markers support keyboard selection.
- [OpenStreetMap tile policy](https://operations.osmfoundation.org/policies/tiles/)
  allows normal interactive viewing with visible attribution and normal browser
  caching. The map requests only the tiles needed for the displayed viewport.

No source was found that establishes live room inventory or prices from Places;
the UI presents places and addresses only. The existing fictional stay and
booking search remains a separate classroom feature.
