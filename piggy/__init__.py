"""
Piggy API Application

This module defines the FastAPI application and its lifespan management.
"""

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from piggy.api import api_router
from piggy.core.config import config
from piggy.core.i18n import i18n
from piggy.core.tasks import (
    cleanup_unverified_users,
    rebuild_subscription_candidates_nightly,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Async lifespan manager for FastAPI application.
    Starts an asynchronous scheduler and yields control to the application.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cleanup_unverified_users, "interval", hours=1)
    # Nightly at 03:00
    scheduler.add_job(rebuild_subscription_candidates_nightly, "cron", hour=3, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Piggy-Api", dependencies=[Depends(i18n)], lifespan=lifespan)
if config.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in config.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)
