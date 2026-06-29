from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from kino_bot.config import settings
from kino_bot.database.models import Base

engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if conn.dialect.name == "sqlite":
            result = await conn.execute(text("PRAGMA table_info(movies)"))
            columns = {row[1] for row in result}
            if "poster_file_id" not in columns:
                await conn.execute(
                    text("ALTER TABLE movies ADD COLUMN poster_file_id VARCHAR(512)")
                )


async def close_db() -> None:
    await engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
