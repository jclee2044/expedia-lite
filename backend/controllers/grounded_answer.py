"""Validate model selections and render hotel facts from checked SQLite rows."""

from __future__ import annotations

import json

from backend.models.retrieval import HotelListRequest, HotelListResult, RetrievalResult, StayRequest

MAX_GROUNDED_HOTELS = 10
RECOMMENDATION_REASONS = (
    "lowest_total_cost", "available_for_stay", "no_match", "insufficient_data"
)
HOTEL_LIST_REASONS = ("saved_hotels", "no_match")


class GroundingError(ValueError):
    """A model answer cannot be supported by the retrieved records."""


def render_grounded_answer(
    raw: str, request: StayRequest | HotelListRequest, result: RetrievalResult | HotelListResult
) -> tuple[str, dict[str, object]]:
    """Accept IDs and a supported reason only; never display model-written facts."""
    if isinstance(request, HotelListRequest) and isinstance(result, HotelListResult):
        return _render_hotel_list(raw, request, result)
    try:
        recommendation = json.loads(raw)
        if not isinstance(recommendation, dict) or set(recommendation) != {"hotel_ids", "reason"}:
            raise ValueError
        ids = recommendation["hotel_ids"]
        reason = recommendation["reason"]
        allowed = {stay.hotel_id: stay for stay in result.matches[:MAX_GROUNDED_HOTELS]}
        if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
            raise ValueError
        if len(ids) != len(set(ids)) or any(item not in allowed for item in ids):
            raise ValueError
        if reason not in RECOMMENDATION_REASONS:
            raise ValueError
        if bool(ids) != (reason in {"lowest_total_cost", "available_for_stay"}):
            raise ValueError
        if reason == "lowest_total_cost" and ids[0] != result.matches[0].hotel_id:
            raise ValueError
        if reason == "insufficient_data" and (result.matches or not result.incomplete_ids):
            raise ValueError
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise GroundingError("The model's recommendation could not be checked. Try again.") from exc

    label = "Rates and room counts are simulated classroom data. No booking is made."
    context = f"ZIP {request.postcode}, check-in {request.check_in}, checkout {request.check_out} (checkout excluded)."
    if not ids:
        if result.saved_hotel_count == 0:
            summary = f"No hotel is saved for ZIP {request.postcode}."
        elif not result.matches and result.incomplete_ids:
            summary = "Availability cannot be verified: requested nightly records are missing."
        else:
            summary = "No checked hotel matched the question's requested conditions."
        return f"{summary}\n{context}\n{label}", recommendation

    selected = sorted((allowed[item] for item in ids), key=lambda stay: (stay.total_cents, stay.hotel_id))
    lines = [context, "", "Selected saved hotels, ordered by checked total cost:"]
    for stay in selected:
        total = f"${stay.total_cents // 100:,}.{stay.total_cents % 100:02d}"
        lines.extend(["", f"{stay.name or 'Name unavailable'} — total {total}"])
        for night in stay.nights:
            rate = f"${night.nightly_rate_cents // 100:,}.{night.nightly_rate_cents % 100:02d}"
            rooms = "room" if night.rooms_available == 1 else "rooms"
            lines.append(f"{night.stay_date}: {rate}/night; {night.rooms_available} simulated {rooms}.")
    lines.extend(["", "Each selected hotel has positive simulated room availability for every requested night."])
    if reason == "lowest_total_cost":
        lines.append(f"{selected[0].name or 'The first hotel'} has the lowest total cost among the checked matches.")
    if result.incomplete_ids:
        count = len(result.incomplete_ids)
        lines.append(f"{count} query {'candidate lacks' if count == 1 else 'candidates lack'} complete nightly records.")
    if result.unavailable_ids:
        count = len(result.unavailable_ids)
        lines.append(f"{count} query {'candidate has' if count == 1 else 'candidates have'} zero simulated rooms for a requested night.")
    if len(result.matches) > MAX_GROUNDED_HOTELS:
        lines.append(f"The model considered the {MAX_GROUNDED_HOTELS} cheapest checked matches; additional matches exist.")
    lines.extend(["", label])
    return "\n".join(lines), recommendation


def _render_hotel_list(
    raw: str, request: HotelListRequest, result: HotelListResult
) -> tuple[str, dict[str, object]]:
    """Render checked hotel identities without inventing stay dates or prices."""
    try:
        recommendation = json.loads(raw)
        if not isinstance(recommendation, dict) or set(recommendation) != {"hotel_ids", "reason"}:
            raise ValueError
        ids, reason = recommendation["hotel_ids"], recommendation["reason"]
        allowed = {hotel.hotel_id: hotel for hotel in result.hotels[:MAX_GROUNDED_HOTELS]}
        if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
            raise ValueError
        if len(ids) != len(set(ids)) or any(item not in allowed for item in ids):
            raise ValueError
        if reason not in HOTEL_LIST_REASONS or bool(ids) != (reason == "saved_hotels"):
            raise ValueError
    except (ValueError, TypeError, KeyError) as exc:
        raise GroundingError("The model's recommendation could not be checked. Try again.") from exc
    if not ids:
        summary = (f"No hotel is saved for ZIP {request.postcode}." if result.saved_hotel_count == 0
                   else "No checked saved hotel matched the question's requested conditions.")
        return (summary + "\nUse ZIP Code search to discover hotels and Add to Local to save them. "
                "This is a local saved list, not a complete area inventory."), recommendation
    lines = [f"Saved hotels associated with ZIP {request.postcode}:"]
    for hotel_id in ids:
        hotel = allowed[hotel_id]
        lines.append(f"• {hotel.name or 'Name unavailable'}" + (f" — {hotel.address}" if hotel.address else ""))
    if len(result.hotels) > MAX_GROUNDED_HOTELS:
        lines.append(f"The model considered the first {MAX_GROUNDED_HOTELS} checked hotels; additional saved hotels exist.")
    lines.extend(["", "These are local saved records, not a complete area inventory.",
                  "Ask with a dated night or check-in/checkout dates to check simulated rates and room availability."])
    return "\n".join(lines), recommendation
