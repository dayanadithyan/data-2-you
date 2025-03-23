
# --------------- database/core.py ---------------
from typing import AsyncContextManager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class Database:
    def __init__(self, dsn: str):
        self.engine = create_async_engine(dsn)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncContextManager[AsyncSession]:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

# --------------- main.py ---------------
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends

load_dotenv()

app = FastAPI()

async def get_db():
    db = Database(os.getenv("DB_DSN"))
    try:
        yield db
    finally:
        await db.engine.dispose()

async def get_redis():
    redis = aioredis.from_url(os.getenv("REDIS_URL"))
    try:
        yield redis
    finally:
        await redis.close()

@app.get("/hero/{hero_id}/timeline")
async def get_hero_timeline(
    hero_id: int,
    resolution: TimeResolution = TimeResolution.PATCH,
    db: Database = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    engine = AnalyticsEngine(db, redis)
    return await engine.get_hero_timeline(hero_id, resolution)

@app.get("/analysis/patch-impact")
async def patch_impact_analysis(
    hero_id: int,
    base_patch: str,
    target_patch: str,
    engine: AnalyticsEngine = Depends(AnalyticsEngine)
):
    return await engine.calculate_patch_impact(hero_id, base_patch, target_patch)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)