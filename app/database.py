import logging

import aiosqlite

from app.config import settings

DB_PATH = settings.db_path
logger = logging.getLogger(__name__)


async def create_chat_history_table() -> None:
    """Create the chat_history table if it doesn't exist."""

    query = """CREATE TABLE IF NOT EXISTS chat_history
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    user_prompt TEXT,
    llm_response TEXT,
    model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(query)
        await db.commit()


async def insert_chat_history(session_id: str, user_prompt: str, llm_response: str, model: str) -> None:
    """Insert chat history into the database."""

    query = "INSERT INTO chat_history (session_id, user_prompt, llm_response, model) VALUES (?, ?, ?, ?)"

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(query, (session_id, user_prompt, llm_response, model))
        await db.commit()


async def get_chat_history(session_id: str) -> list:
    """Get chat history from the database."""

    messages = []
    query = "SELECT user_prompt, llm_response FROM chat_history WHERE session_id = ? ORDER BY created_at"

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, (session_id,)) as cursor:
            async for row in cursor:
                messages.extend(
                    [
                        {"role": "human", "content": row["user_prompt"]},
                        {"role": "ai", "content": row["llm_response"]},
                    ]
                )

    return messages


async def init_db():
    """Initialize the database by creating necessary tables."""

    await create_chat_history_table()
    logger.info("Database initialized.")
