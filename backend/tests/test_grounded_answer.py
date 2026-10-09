"""Adversarial recommendation checks and exact rendering of retrieved facts."""

import json

import pytest

from backend.controllers.grounded_answer import GroundingError, render_grounded_answer
from backend.models.retrieval import RetrievalResult, StayRequest, VerifiedNight, VerifiedStay

STAY = StayRequest("16803", "2026-10-11", "2026-10-13")
RESULT = RetrievalResult(
    ("campus", "valley", "budget"),
    (
        VerifiedStay("campus", "Campus Lantern", None, "16803", (
            VerifiedNight("2026-10-11", 12000, 2),
            VerifiedNight("2026-10-12", 11000, 1),
        ), 23000),
        VerifiedStay("valley", "Valley Ridge", None, "16803", (
            VerifiedNight("2026-10-11", 13000, 2),
            VerifiedNight("2026-10-12", 14000, 2),
        ), 27000),
    ), (), ("budget",), 3,
)


def test_two_night_answer_renders_actual_dates_rates_and_totals() -> None:
    answer, recommendation = render_grounded_answer(json.dumps({
        "hotel_ids": ["campus", "valley"], "reason": "lowest_total_cost",
    }), STAY, RESULT)
    assert "Campus Lantern — total $230.00" in answer
    assert "Valley Ridge — total $270.00" in answer
    assert "2026-10-12: $140.00/night; 2 simulated rooms." in answer
    assert "2026-10-12: $110.00/night; 1 simulated room." in answer
    assert "2026-10-14" not in answer
    assert "checkout 2026-10-13 (checkout excluded)" in answer
    assert "simulated classroom data" in answer
    assert recommendation["hotel_ids"] == ["campus", "valley"]


@pytest.mark.parametrize("proposal", [
    {"hotel_ids": ["campus"], "reason": "lowest_total_cost", "answer": "October 14 costs $140"},
    {"hotel_ids": ["unknown"], "reason": "available_for_stay"},
    {"hotel_ids": ["budget"], "reason": "available_for_stay"},
    {"hotel_ids": ["campus", "campus"], "reason": "lowest_total_cost"},
    {"hotel_ids": ["valley"], "reason": "lowest_total_cost"},
    {"hotel_ids": [], "reason": "lowest_total_cost"},
    {"hotel_ids": ["campus"], "reason": "no_match"},
    {"hotel_ids": [], "reason": "insufficient_data"},
    {"hotel_ids": [], "reason": "invented_reason"},
    {"hotel_ids": "campus", "reason": "lowest_total_cost"},
])
def test_unchecked_facts_and_unsupported_recommendations_are_rejected(proposal: dict) -> None:
    with pytest.raises(GroundingError):
        render_grounded_answer(json.dumps(proposal), STAY, RESULT)


def test_empty_filtered_query_does_not_claim_nothing_is_saved() -> None:
    answer, _ = render_grounded_answer(
        '{"hotel_ids":[],"reason":"no_match"}', STAY,
        RetrievalResult((), (), (), (), 3),
    )
    assert "No checked hotel matched" in answer
    assert "No hotel is saved" not in answer
    absent, _ = render_grounded_answer(
        '{"hotel_ids":[],"reason":"no_match"}', STAY,
        RetrievalResult((), (), (), (), 0),
    )
    assert "No hotel is saved for ZIP 16803" in absent


def test_missing_nights_are_unknown_availability() -> None:
    answer, _ = render_grounded_answer(
        '{"hotel_ids":[],"reason":"insufficient_data"}', STAY,
        RetrievalResult(("campus",), (), ("campus",), (), 3),
    )
    assert "Availability cannot be verified" in answer
    assert "nightly records are missing" in answer
    assert "zero" not in answer
