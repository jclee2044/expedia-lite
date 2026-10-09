"""Resolve an explicit ZIP and stay dates before asking a model for SQL."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from backend.models.retrieval import StayRequest

_ZIP = re.compile(r"(?<![0-9])[0-9]{5}(?![0-9])")
_ISO_DATE = re.compile(r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b")
_MONTH_DATE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+[0-9]{1,2},?\s+[0-9]{4}\b",
    re.IGNORECASE,
)
_SAME_CONTEXT = re.compile(r"\b(?:same|that|those|there)\b", re.IGNORECASE)


class ChatContextError(ValueError):
    """The question does not establish a safe, unambiguous stay request."""


def _read_date(value: str) -> date:
    try:
        if _ISO_DATE.fullmatch(value):
            parsed = date.fromisoformat(value)
            if parsed.isoformat() != value:
                raise ValueError
            return parsed
        month, day, year = re.match(
            r"([A-Za-z]+)\s+([0-9]{1,2}),?\s+([0-9]{4})", value
        ).groups()
        return datetime.strptime(f"{month.title()} {day} {year}", "%B %d %Y").date()
    except (AttributeError, ValueError) as exc:
        raise ChatContextError("Use a valid date with a year, such as 2026-10-11.") from exc


def parse_stay_request(question: str, previous: StayRequest | None = None) -> StayRequest:
    """Accept one ZIP and one night or check-in/checkout dates in text.

    A follow-up can reuse earlier context only when it explicitly says
    "same", "that", "those", or "there". Two dates are ordered check-in then
    checkout. Questions with more dates or conflicting ZIPs are rejected.
    """
    zip_codes = _ZIP.findall(question)
    if len(set(zip_codes)) > 1:
        raise ChatContextError("Please use one five-digit ZIP code.")
    reuse = previous is not None and _SAME_CONTEXT.search(question) is not None
    postcode = zip_codes[0] if zip_codes else previous.postcode if reuse else None
    if postcode is None:
        raise ChatContextError("Include a five-digit ZIP code in your question.")

    spans = [(match.start(), match.end(), match.group()) for pattern in (_ISO_DATE, _MONTH_DATE)
             for match in pattern.finditer(question)]
    spans.sort()
    if len(spans) > 2:
        raise ChatContextError("Please give one night or a check-in and checkout date.")
    dates = [_read_date(value) for _, _, value in spans]
    if not dates:
        if not reuse:
            raise ChatContextError("Include a dated night or check-in and checkout dates.")
        check_in = date.fromisoformat(previous.check_in)
        check_out = date.fromisoformat(previous.check_out)
    elif len(dates) == 1:
        check_in = dates[0]
        check_out = check_in + timedelta(days=1)
    else:
        check_in, check_out = dates
    nights = (check_out - check_in).days
    if not 1 <= nights <= 14:
        raise ChatContextError("A stay must be one to fourteen nights, with checkout after check-in.")
    return StayRequest(postcode, check_in.isoformat(), check_out.isoformat())
