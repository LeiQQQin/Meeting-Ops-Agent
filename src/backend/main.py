"""
Meeting-Ops-Agent FastAPI application entry point.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.agents.orchestrator import Orchestrator
from src.backend.api.agents import router as agents_router
from src.backend.api.meetings import router as meetings_router
from src.backend.api.tasks import router as tasks_router
from src.backend.config import get_settings

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Global Orchestrator instance (shared across requests)
# --------------------------------------------------------------------------

orchestrator = Orchestrator()

# --------------------------------------------------------------------------
# Lifespan
# --------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Meeting-Ops-Agent starting up …")
    os.makedirs(settings.upload_dir, exist_ok=True)

    enabled_connectors = []
    if settings.github_token:
        enabled_connectors.append("github")
    if settings.jira_api_token and settings.jira_server_url:
        enabled_connectors.append("jira")
    if settings.slack_bot_token:
        enabled_connectors.append("slack")
    if settings.notion_api_key:
        enabled_connectors.append("notion")

    await orchestrator.setup(connector_names=enabled_connectors)
    logger.info("Enabled connectors: %s", enabled_connectors or ["none"])

    yield

    # Shutdown
    logger.info("Meeting-Ops-Agent shutting down …")


# --------------------------------------------------------------------------
# FastAPI app
# --------------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title="Meeting-Ops-Agent",
    description=(
        "AI-powered meeting operations system: multi-agent collaboration for "
        "pre-meeting prep, note-taking, task management, follow-up, and risk alignment."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(meetings_router)
app.include_router(tasks_router)
app.include_router(agents_router)


# --------------------------------------------------------------------------
# Health check
# --------------------------------------------------------------------------


@app.get("/health", tags=["system"])
async def health():
    return {
        "status": "ok",
        "connectors": list(orchestrator._connectors.keys()),
        "meetings": len(orchestrator._meetings),
    }


@app.get("/", tags=["system"])
async def root():
    return {
        "service": "Meeting-Ops-Agent",
        "version": "0.1.0",
        "docs": "/docs",
    }


# --------------------------------------------------------------------------
# Dev entrypoint
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )
