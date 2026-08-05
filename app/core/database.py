from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import settings
from app.core.logging import logger


def _create_engine_for_url(db_url: str):
    engine_kwargs = {
        "echo": False,
        "future": True,
    }
    if db_url.startswith("postgresql"):
        engine_kwargs.update({
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_pre_ping": True,
        })
    elif db_url.startswith("sqlite"):
        engine_kwargs.update({
            "connect_args": {"check_same_thread": False}
        })
    return create_async_engine(db_url, **engine_kwargs)


engine = _create_engine_for_url(settings.DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    pass


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
