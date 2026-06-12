"""FastAPI ilovasi — kirish nuqtasi."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import settings
from app.db.seed import init_models, seed_data
from app.services.backup_service import backup_database

UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        backup_database()  # migratsiyalardan oldin xavfsizlik nusxasi
    except Exception:
        logger.exception("Boshlang'ich zaxira nusxa olishda xato")
    await init_models()
    await seed_data()
    logger.info("IQTM API ishga tushdi.")
    yield


app = FastAPI(title="IQTM Mini App API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin] if settings.frontend_origin != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}
