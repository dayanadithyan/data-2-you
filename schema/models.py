# --------------- analytics/models.py ---------------
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple

class TimeResolution(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    PATCH = "patch"

class Position(str, Enum):
    POSITION_1 = "pos1"
    POSITION_2 = "pos2"
    POSITION_3 = "pos3"
    POSITION_4 = "pos4"
    POSITION_5 = "pos5"

class HeroItemBuild(BaseModel):
    item_id: int
    win_rate: float
    purchase_timing: float
    matches: int
    synergy_items: List[Tuple[int, float]]

class PositionMetrics(BaseModel):
    position: Position
    pick_rate: float
    win_rate: float
    gold_per_min: float
    exp_per_min: float

class HeroMetaSnapshot(BaseModel):
    timestamp: datetime
    patch_version: str
    overall_win_rate: float
    positions: List[PositionMetrics]
    item_builds: List[HeroItemBuild]
    skill_priorities: List[Tuple[int, float]]

# --------------- analytics/engine.py ---------------
import asyncpg
from redis import asyncio as aioredis
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import numpy as np
from scipy import stats

class AnalyticsEngine:
    def __init__(self, db_pool: asyncpg.Pool, redis: aioredis.Redis):
        self.db_pool = db_pool
        self.redis = redis
        self.cache_version = "v1"

    @asynccontextmanager
    async def get_db_session(self) -> AsyncGenerator[asyncpg.Connection, None]:
        async with self.db_pool.acquire() as conn:
            try:
                yield conn
            finally:
                await conn.close()

    async def get_hero_timeline(
        self,
        hero_id: int,
        resolution: TimeResolution = TimeResolution.PATCH,
        patch_range: Optional[Tuple[str, str]] = None
    ) -> List[HeroMetaSnapshot]:
        cache_key = f"{self.cache_version}:timeline:{hero_id}:{resolution.value}"
        cached = await self.redis.get(cache_key)
        if cached:
            return [HeroMetaSnapshot.parse_raw(s) for s in cached]

        query = """
            WITH intervals AS (
                SELECT generate_series(
                    MIN(start_time)::timestamp,
                    MAX(end_time)::timestamp,
                    CASE $3
                        WHEN 'daily' THEN '1 day'
                        WHEN 'weekly' THEN '1 week'
                        ELSE '0 days'
                    END
                ) AS interval_start
                FROM matches
            )
            SELECT
                i.interval_start AS timestamp,
                p.version AS patch_version,
                AVG(mh.win::int) AS win_rate,
                ...
            FROM intervals i
            LEFT JOIN matches m ON m.start_time >= i.interval_start
            LEFT JOIN match_heroes mh ON m.match_id = mh.match_id
            LEFT JOIN patches p ON m.patch_id = p.id
            WHERE mh.hero_id = $1
            GROUP BY i.interval_start, p.version
            ORDER BY i.interval_start;
        """

        async with self.get_db_session() as conn:
            records = await conn.fetch(query, hero_id, resolution.value)

        processed = [self._process_timeline_record(r) for r in records]
        await self.redis.setex(cache_key, 3600, [s.json() for s in processed])
        return processed

    def _process_timeline_record(self, record) -> HeroMetaSnapshot:
        # Implementation of complex data processing
        return HeroMetaSnapshot(...)

    async def calculate_patch_impact(
        self,
        hero_id: int,
        base_patch: str,
        target_patch: str,
        confidence_level: float = 0.95
    ) -> dict:
        query = """
            SELECT win, matches FROM hero_patch_stats
            WHERE hero_id = $1 AND patch = ANY($2)
        """
        async with self.get_db_session() as conn:
            base_data = await conn.fetch(query, hero_id, [base_patch])
            target_data = await conn.fetch(query, hero_id, [target_patch])

        base_wins = sum(r['wins'] for r in base_data)
        base_total = sum(r['matches'] for r in base_data)
        target_wins = sum(r['wins'] for r in target_data)
        target_total = sum(r['matches'] for r in target_data)

        z_score, p_value = stats.proportions_ztest(
            [base_wins, target_wins],
            [base_total, target_total]
        )
        
        return {
            "hero_id": hero_id,
            "base_patch": base_patch,
            "target_patch": target_patch,
            "win_rate_change": (target_wins/target_total) - (base_wins/base_total),
            "confidence_interval": stats.norm.interval(confidence_level)[1] * np.sqrt(
                (base_wins/base_total*(1-base_wins/base_total))/base_total +
                (target_wins/target_total*(1-target_wins/target_total))/target_total
            ),
            "p_value": p_value,
            "significant": p_value < (1 - confidence_level)
        }
