import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routes import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Running lifespan before the application startup!")
    await init_db()
    yield
    logger.info("Running lifespan after the application shutdown!")


version = "v1"
version_prefix = f"/api/{version}"

app = FastAPI(
    title="RAG Chatbot API",
    description="RAG Chatbot API",
    version=version,
    openapi_url=f"{version_prefix}/openapi.json",
    docs_url=f"{version_prefix}/docs",
    redoc_url=f"{version_prefix}/redoc",
    lifespan=lifespan,
    license_info={"name": "MIT License", "url": "https://opensource.org/license/mit"},
)

app.include_router(api_router, prefix=version_prefix, tags=["API"])
