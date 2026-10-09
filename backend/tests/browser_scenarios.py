"""Explicitly mocked browser-only provider scenarios; never used by the normal app.

Run with a synthetic demo database, then use ZIP 00501 for mock places,
16804 for empty results, 00000 for unresolved ZIP, and 99999 for provider failure.
Chat questions containing MOCK rate-limit, MOCK rejected-sql, or MOCK bad-answer
exercise those failures without calling a remote model or spending quota.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import AsyncIterator
from pathlib import Path

import uvicorn

from backend.app import routes
from backend.app.main import create_app
from backend.controllers import rag_chat
from backend.controllers.errors import GeoapifyRequestError, PostcodeNotFoundError
from backend.controllers.gemini import ChatTurn, GeminiStreamError, SqlProposal
from backend.models import ExternalHotel, NearbyHotelSearch, PostcodeLocation
from backend.models.retrieval import HotelListRequest, HotelListResult, RetrievalResult, StayRequest

SQL = (
    "SELECT DISTINCT h.hotel_id AS hotel_id FROM saved_hotels h "
    "JOIN saved_hotel_zips z ON z.hotel_id=h.hotel_id "
    "LEFT JOIN demo_hotel_nights n ON n.hotel_id=h.hotel_id "
    "AND n.stay_date>=:check_in AND n.stay_date<:check_out WHERE z.postcode=:postcode"
)


def nearby(postcode: str) -> NearbyHotelSearch:
    if postcode == "00000":
        raise PostcodeNotFoundError(postcode)
    if postcode == "99999":
        raise GeoapifyRequestError("Labeled mock provider failure")
    center = PostcodeLocation(postcode, "us", 40.0, -77.0, "MOCK location")
    hotels = [] if postcode == "16804" else [
        ExternalHotel("mock:alpha", "MOCK Alpha Hotel", "1 Synthetic Street", 40.001, -77.001),
        ExternalHotel("mock:beta", "MOCK Beta Hotel", "2 Synthetic Street", 40.002, -77.002),
    ]
    return NearbyHotelSearch(center, 5000, 50, hotels)


async def propose(question: str, stay: StayRequest | HotelListRequest, history: list[ChatTurn], prompt: str) -> SqlProposal:
    if "MOCK rate-limit" in question:
        raise GeminiStreamError("Gemini is busy or at its rate limit. Try again later.")
    if isinstance(stay, HotelListRequest):
        return SqlProposal(
            "SELECT h.hotel_id AS hotel_id FROM saved_hotels h "
            "JOIN saved_hotel_zips z ON z.hotel_id=h.hotel_id WHERE z.postcode=:postcode",
            {"postcode": stay.postcode},
        )
    sql = "UPDATE saved_hotels SET name=:postcode" if "MOCK rejected-sql" in question else SQL
    if "MOCK filtered" in question:
        sql += " AND n.nightly_rate_cents <= 5000"
    return SqlProposal(sql, {
        "postcode": stay.postcode, "check_in": stay.check_in, "check_out": stay.check_out,
    })


async def answer(question: str, stay: StayRequest | HotelListRequest, result: RetrievalResult | HotelListResult,
                 history: list[ChatTurn], prompt: str) -> AsyncIterator[str]:
    if "MOCK bad-answer" in question:
        yield json.dumps({"hotel_ids": [], "reason": "no_match", "answer": "October 14 costs $140"})
        return
    if isinstance(result, HotelListResult):
        ids = [hotel.hotel_id for hotel in result.hotels[:10]]
        yield json.dumps({"hotel_ids": ids, "reason": "saved_hotels" if ids else "no_match"})
        return
    ids = [item.hotel_id for item in result.matches[:3]]
    reason = "lowest_total_cost" if ids else "insufficient_data" if result.incomplete_ids else "no_match"
    yield json.dumps({"hotel_ids": ids, "reason": reason})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="existing synthetic demo database")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    demo_directory = Path(__file__).resolve().parents[1] / "db"
    if (not args.database.is_file() or not args.database.name.startswith("part2-")
            or args.database.resolve().parent != demo_directory.resolve()):
        raise ValueError("Use an existing, explicitly named part2- synthetic database.")
    routes.search_nearby_hotels = nearby
    rag_chat.propose_sql = propose
    rag_chat.stream_grounded_answer = answer
    print("MOCK PROVIDERS: no Geoapify or Gemini requests; synthetic browser verification only.")
    uvicorn.run(create_app(args.database), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
