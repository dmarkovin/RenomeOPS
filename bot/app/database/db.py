from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from .models import Base

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    print("STARTING DATABASE")
    async with engine.begin() as conn:
        # Создаём все таблицы, если их нет
        await conn.run_sync(Base.metadata.create_all)
    print("DATABASE OK")

async def close_db():
    await engine.dispose()
