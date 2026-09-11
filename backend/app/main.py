"""FastAPI routes for Expedia Lite."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from backend.app.schemas import HotelSearchResponse
from backend.app.search import DataValidationError, search_hotel_stays

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"

app = FastAPI(title="Expedia Lite API")


@app.get("/api/hotels/search", response_model=HotelSearchResponse)
def search_hotels(
    name: str = Query(description="Case-insensitive partial hotel name"),
) -> HotelSearchResponse:
    """Search hotel names and return their joined available stays."""
    try:
        search = search_hotel_stays(
            name,
            DATA_DIRECTORY / "hotels.csv",
            DATA_DIRECTORY / "trips.csv",
        )
    except DataValidationError as error:
        raise HTTPException(
            status_code=500,
            detail="The supplied hotel data could not be loaded.",
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return HotelSearchResponse.model_validate(search)
