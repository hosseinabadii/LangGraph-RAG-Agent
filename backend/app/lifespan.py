from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.db.checkpointer import close_connection, create_connection
from app.db.main import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Running lifespan before the application startup!")
    await init_db()
    await create_connection()
    yield
    logger.info("Running lifespan after the application shutdown!")
    await close_connection()
