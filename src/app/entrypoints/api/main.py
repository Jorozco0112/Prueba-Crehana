import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.entrypoints.api.errors import register_error_handlers
from app.entrypoints.api.routers import auth, health, task_lists, tasks, users
from app.infrastructure.config import get_auth_settings

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Fail at startup, not on the first login, if the JWT secret is missing (DEC-042).
    get_auth_settings()
    yield


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app = FastAPI(
        title="Task Lists API",
        version="1.0.0",
        description=(
            "Task lists and tasks with filters, completion percentage, JWT "
            "authentication, assignment and simulated email notifications."
        ),
        lifespan=lifespan,
    )
    register_error_handlers(app)

    api = APIRouter(prefix=API_PREFIX)
    for router in (auth.router, task_lists.router, tasks.router, users.router):
        api.include_router(router)
    app.include_router(health.router)
    app.include_router(api)
    return app


app = create_app()
