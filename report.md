# Expedia Lite — Assignment 2, Part 1

## Project access

Repository: [Expedia Lite](https://github.com/jclee2044/expedia-lite). Assessed Part 1 implementation checkpoint: [`929cb77`](https://github.com/jclee2044/expedia-lite/commit/929cb777ed0d8ded1e18a4d91f9b31bfcc5387a8) on `zip-search`. This commit contains the ZIP search, interface changes, documentation, and demo files; the report's checkpoint line was updated afterward.

Use Python 3.12 and a supported Node.js version. From the project root:

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend
npm ci
```

Start the backend from the project root with `backend/.venv/bin/python -m uvicorn backend.app.main:app --reload`. In another terminal, run `npm run dev` from `frontend/`, then open `http://127.0.0.1:5173`. See the [README](README.md) for configuration details.

## Research notes

I looked at [Trivago](https://www.trivago.com/), [Expedia](https://www.expedia.com/Hotels), and [Booking.com](https://www.booking.com/). My [Trivago screenshot](docs/mockups/trivago.png) shows the idea I liked most: hotel cards on the left and a map on the right. I also liked seeing a picture next to each hotel name.

The Trivago screen felt clunky and overcrowded to me. Not all the hotel names appeared on screen, and the prices on the map jumped up and down, which was distracting and confusing. I kept the cards-left/map-right idea but made the cards simpler and easier to read.

I also consulted the [Geoapify geocoding](https://apidocs.geoapify.com/docs/geocoding/) and [Places](https://apidocs.geoapify.com/docs/places/) documentation and the [Leaflet quick start](https://leafletjs.com/examples/quick-start/) while building the ZIP search and map.

## Early mockup

![Early left-list/right-map mockup](docs/mockups/a2-mockups.png)

The [mockup](docs/mockups/a2-mockups.png) shows hotel cards on the left and pins on the right, with a name callout. The final interface adds ZIP search and linked selection. I tried an indigo color, did not like it, then liked the [green preview](docs/mockups/green-brand-preview.jpg) and used green instead.

I also tried putting a picture on the left side of each card, like the Trivago example. Most Geoapify results did not have an image, so I dropped that idea rather than showing an ugly placeholder icon. **TODO:** confirm when `docs/mockups/a2-mockups.png` was prepared.

## Screen-recorded demo video

[Expedia Lite A2.1 Demo.mov](<Expedia Lite A2.1 Demo.mov>)

## Verification record

The automated checks passed: **36 backend tests** and **16 frontend tests**. The manual checks are below.

Test 1: When the user searches ZIP `16802`:

- Expected: The app shows hotel results near State College, PA, in the list and on the map.
- Actual: The app resolved `16802` to State College and displayed 21 places, including the Nittany Lion Inn and the Penn Stater, with matching map markers.

Test 2: When the user searches ZIP `17042`:

- Expected: The app shows hotel results in the Lebanon, PA, area.
- Actual: The app resolved `17042` to North Cornwall Township and displayed two places: Days Inn - Lebanon / Hershey in Lebanon and Fairfield Inn & Suites in North Cornwall Township.

Test 3: When the user clicks the hotel card for the Nittany Lion Inn:

- Expected: Its associated map marker is highlighted.
- Actual: The card and its matching marker both showed the selected state after the card was clicked.

Test 4: When the user clicks the map marker for the Penn Stater:

- Expected: The associated hotel card is selected.
- Actual: Activating the marker with the keyboard selected and scrolled to the Penn Stater card.

Test 5: When the user submits ZIP `000000`:

- Expected: The app shows an error about the ZIP code instead of running a hotel search.
- Actual: The app showed “Enter exactly five digits for a U.S. ZIP code.” No hotel results appeared.

Test 6: When the user enters letters such as `abcde` for the ZIP code and submits the form:

- Expected: The interface does not accept letters as a valid ZIP code.
- Actual: The form rejects letters on submission with “Enter exactly five digits for a U.S. ZIP code.”

## AI disclosure and evidence log

I used **Codex with GPT-6 Sol** for the implementation, visual previews, and verification. These prompt excerpts show how I directed the work.

The setup prompt led to the [Geoapify controller](backend/controllers/places.py) and [ZIP request code](frontend/src/api/locations.js):

```vbnet
identify key dependencies and initial setup for PART 1 of assignment 2. Must be able to look up by zip code and find hotels in that area.
develop a step by step plan to get the dependencies setup, following best swe principles and finding the minimal solution.
```

The selection prompt shaped the [list](frontend/src/components/NearbyHotelsPanel.vue) and [map](frontend/src/components/NearbyHotelsMap.vue):

```vbnet
currently clicking a hotel on the left side selects the pin on the right. next step, we need the opposite to be true as well. clicking the pin on the right should select the hotel on the left
```

The hover prompt added the name callout in the [map component](frontend/src/components/NearbyHotelsMap.vue):

```css
on the map, when i hover over a pin, it should have a callout directly above the pin showing the name of the hotel
```

I annotated the left side of the card and asked for pictures, then revised that approach when most results had no image. The [cards](frontend/src/components/NearbyHotelsPanel.vue) no longer depend on hotel pictures:

```sql
add the pull for the hotel image and display it on the left side of the card, with text on the right, for each card.
implement only the backend first. once thats been validated then add the frontend
```

This indigo prompt changed [main.css](frontend/src/assets/main.css). I disliked the result, previewed green, and chose green instead:

```css
this is now the brand color of the app. change the main headings (e.g., "Choose a hotel stay", "Hotels near ZIP #####", etc), icon, pill background colors
background of the hotel icons should be a lighter version of this
```
