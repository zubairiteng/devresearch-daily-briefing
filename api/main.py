"""Main FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from database.connection import init_db
from scheduler.runner import start_scheduler
from api.routes import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("devresearch")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database schema and Scheduler
    logger.info("Initializing database schema...")
    init_db()

    logger.info("Starting background scheduler...")
    start_scheduler()
    logger.info("DevResearch Daily Briefing application initialized.")
    yield
    # Shutdown
    logger.info("DevResearch server shutting down.")


app = FastAPI(
    title="DevResearch Daily Briefing",
    description="Personal briefing dashboard and automated daily digest engine",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API
app.include_router(api_router)

# Mount Static / Frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "DevResearch Daily API is running. Access /docs for swagger specifications."}
