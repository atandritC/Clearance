from collections.abc import AsyncIterator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from clearance.config import settings

connect_args = {}
if settings.postgres_ssl:
    connect_args["ssl"] = "require"
if settings.postgres_pooler:
    connect_args["prepared_statement_name_func"] = lambda: f"__asyncpg_{uuid4()}__"

engine = create_async_engine(
    settings.database_url,
    connect_args=connect_args,
    **({"poolclass": NullPool} if settings.postgres_pooler else {}),
    pool_pre_ping=True,
)

SessionFactory = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
