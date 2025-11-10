"""Database initialization and management."""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.logger import get_logger

logger = get_logger("database")

# Database engine and session factory
engine = None
AsyncSessionLocal = None


async def init_db():
    """Initialize database connection."""
    global engine, AsyncSessionLocal

    try:
        database_url = settings.DATABASE_URL
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        url_obj = make_url(database_url)

        engine_kwargs = {
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

        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))

        logger.info("✅ Database initialized successfully")

    except Exception as e:
        logger.error(f"❌ Database initialization error: {str(e)}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db():
    """Close database connection"""
    if engine:
        await engine.dispose()
        logger.info("✅ Database connection closed")
