"""Async SQLAlchemy engine, session factory and FastAPI DB dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession, create_async_engine

from src.conf.config import settings

engine: AsyncEngine = create_async_engine( settings.database_url, echo=settings.debug, pool_pre_ping=True, )

SessionFactory = async_sessionmaker( bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, )


async def get_db() -> AsyncGenerator[ AsyncSession, None ]:
	"""Yield one async database session per request."""

	async with SessionFactory() as session:
		yield session
