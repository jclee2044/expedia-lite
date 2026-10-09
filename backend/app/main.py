"""FastAPI application composition for Expedia Lite."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from backend.app.routes import router
from backend.config import geoapify_key_is_configured
from backend.controllers.database import (
    DEFAULT_DATABASE_PATH,
    DEFAULT_DATA_DIRECTORY,
    initialize_database,
)
from backend.controllers.gemini import load_assistant_prompt
from backend.controllers.sessions import SessionStore


def create_app(
    database_path: Path = DEFAULT_DATABASE_PATH,
    data_directory: Path = DEFAULT_DATA_DIRECTORY,
) -> FastAPI:
    """Create an application configured for one database and seed directory."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        application.state.assistant_prompt = load_assistant_prompt()
        initialize_database(database_path, data_directory)
        yield

    application = FastAPI(title="Expedia Lite API", lifespan=lifespan)
    application.state.database_path = database_path
    application.state.geoapify_key_configured = geoapify_key_is_configured()
    application.state.sessions = SessionStore()
    application.include_router(router)
    return application


app = create_app()
