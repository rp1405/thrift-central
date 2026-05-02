import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import http_exception_handler
from app.core.middleware import request_logging_middleware
from app.controllers.router import api_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Thrift Central API",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_logging_middleware)

# ─── Exception Handlers ───────────────────────────────────────────────────────
app.add_exception_handler(HTTPException, http_exception_handler)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.APP_ENV}
