"""MoneyKeeper 应用入口。"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .routers import auth, bills, categories, dev, stats

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="MoneyKeeper", version="1.0.0", lifespan=lifespan)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(bills.router, prefix="/api/bills", tags=["bills"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(dev.router, prefix="/api/dev", tags=["dev"])

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
