from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from loguru import logger
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.config import settings

connection: AsyncConnection | None = None
checkpointer: AsyncPostgresSaver | None = None


async def create_connection() -> AsyncConnection:
    global connection

    if connection is not None:
        return connection

    logger.info("Creating checkpointer connection...")
    connection_kwargs = {"autocommit": True, "row_factory": dict_row}
    connection = await AsyncConnection.connect(conninfo=settings.checkpointer_uri, **connection_kwargs)
    logger.info("✅ Checkpointer connection created successfully")
    return connection


async def get_checkpointer() -> AsyncPostgresSaver:
    global checkpointer

    if checkpointer is not None:
        return checkpointer

    conn = await create_connection()
    checkpointer = AsyncPostgresSaver(conn=conn)  # type: ignore
    await checkpointer.setup()
    logger.info("✅ PostgresCheckpointer initialized successfully")
    return checkpointer


async def close_connection() -> None:
    global connection

    if connection is not None:
        logger.info("Closing checkpointer connection...")
        await connection.close()
        logger.info("✅ Checkpointer connection closed successfully")
        connection = None
