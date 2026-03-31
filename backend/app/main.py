import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.articles import router as articles_router
from app.services.scheduler import run_parse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        run_parse,
        "interval",
        hours=24,
        id="daily_parse",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: parse every 24 hours")
    logger.info("Running initial parse in background...")
    asyncio.create_task(run_parse())
    yield
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="Innopolis University Articles API",
    description="API for collecting and searching scientific articles from Innopolis University",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
