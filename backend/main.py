"""Ponto de entrada do backend FastAPI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.database import engine, SessionLocal, Base
from backend.db.seed import seed_admin
from backend.models.user import User  # noqa: F401 - necessário para criar tabelas
from backend.routers import auth, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: cria tabelas e seed do admin."""
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas do banco de dados criadas/verificadas.")

    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="MathBank Auth API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - permite o app desktop e desenvolvimento local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health")
def health_check():
    """Endpoint de health check."""
    return {"status": "ok"}
