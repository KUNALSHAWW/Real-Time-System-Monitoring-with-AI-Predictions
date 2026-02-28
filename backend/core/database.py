"""
Database initialisation and session management.

Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite) via the
DATABASE_URL env-var.  On startup, `init_db()` creates all ORM tables
defined in `core.models`.
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.logger import get_logger
from core.models import Base  # ORM declarative base with all models

logger = get_logger("database")

# Module-level singletons — populated by init_db()
engine = None
AsyncSessionLocal = None


async def init_db() -> None:
    """
    Initialise the async engine, session factory, and create all tables
    that don't already exist.
    """
    global engine, AsyncSessionLocal

    try:
        database_url: str = settings.DATABASE_URL

        # --- driver fixups ------------------------------------------------
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        elif database_url.startswith("sqlite:///"):
            # aiosqlite driver for async SQLite
            database_url = database_url.replace(
                "sqlite:///", "sqlite+aiosqlite:///", 1
            )

        url_obj = make_url(database_url)

        engine_kwargs: dict = {
            "echo": settings.DEBUG,
            "pool_pre_ping": True,
        }

        if url_obj.drivername.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs.update(
                {
                    "pool_size": settings.DB_POOL_SIZE,
                    "max_overflow": 10,
                    "pool_recycle": settings.DB_POOL_RECYCLE,
                }
            )

        engine = create_async_engine(database_url, **engine_kwargs)

        AsyncSessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create all tables (safe if they already exist)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Quick connectivity check
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info("✅ Database initialised — all tables ready")

    except Exception as e:
        logger.error(f"❌ Database initialisation error: {e}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async session and closes it afterwards."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db() -> None:
    """Dispose of the engine pool (call on app shutdown)."""
    if engine:
        await engine.dispose()
        logger.info("✅ Database connection closed")
