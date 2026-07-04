from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from misc.settings import settings


class Database:
    def __init__(self, url: str):
        self.engine = create_async_engine(
            url, 
            pool_pre_ping=True, 
            echo=False, 
            pool_size=100, 
            max_overflow=20
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session


db = Database(settings.database_url)
