# --------------- resolvers.py ---------------
import logging
from typing import Any, Dict, List, Optional
import asyncpg
from redis import asyncio as aioredis
import json

logger = logging.getLogger(__name__)

class GraphQLResolver:
    """GraphQL resolver implementation for the API."""
    
    def __init__(self, db_pool: asyncpg.Pool, redis_conn: aioredis.Redis):
        """Initialize resolver with database pool and Redis connection."""
        self.db_pool = db_pool
        self.redis = redis_conn
        
    async def __aenter__(self):
        """Async context manager enter."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources."""
        if hasattr(self, 'session') and self.session:
            await self.session.close()

    async def resolve_hero_timeline(self, hero_id: int, **kwargs) -> List[Dict[str, Any]]:
        """Resolve hero timeline data."""
        cache_key = f"hero:{hero_id}:timeline"
        try:
            # Try to get data from cache
            if cached := await self.redis.get(cache_key):
                logger.info(f"Cache hit for {cache_key}")
                return json.loads(cached)
            
            # Cache miss, fetch from database
            logger.info(f"Cache miss for {cache_key}")
            async with self.db_pool.acquire() as conn:
                records = await conn.fetch(
                    "SELECT * FROM hero_meta WHERE hero_id = $1", hero_id
                )
            
            processed = self._process_timeline(records)
            
            # Store in cache with expiration
            await self.redis.setex(cache_key, 300, json.dumps(processed))
            return processed
            
        except Exception as e:
            logger.error(f"Error resolving hero timeline: {e}")
            raise

    def _process_timeline(self, records: List[asyncpg.Record]) -> List[Dict[str, Any]]:
        """Process database records into timeline data."""
        try:
            # Convert database records to dictionaries
            result = []
            for record in records:
                # Convert record to dict (proper way to handle Records)
                record_dict = dict(record.items())
                # Process and transform data as needed
                result.append(record_dict)
            
            return result
        except Exception as e:
            logger.error(f"Error processing timeline data: {e}")
            raise

    async def resolve_optimal_build(self, hero_id: int, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve optimal build for a hero based on constraints."""
        try:
            # Machine learning model integration would go here
            # This is a simplified implementation
            
            # Example logic for optimal build calculation
            cache_key = f"optimal_build:{hero_id}:{hash(frozenset(constraints.items()))}"
            
            # Try to get from cache
            if cached := await self.redis.get(cache_key):
                return json.loads(cached)
            
            # Calculate optimal build (simplified)
            async with self.db_pool.acquire() as conn:
                # Fetch possible items for hero
                items = await conn.fetch(
                    "SELECT item_id, win_rate FROM hero_items WHERE hero_id = $1", 
                    hero_id
                )
                
                # Apply constraints
                filtered_items = []
                for item in items:
                    # Apply max cost constraint if provided
                    if constraints.get("maxCost") and await self._get_item_cost(item["item_id"]) > constraints["maxCost"]:
                        continue
                    
                    # Apply forbidden items constraint if provided
                    if constraints.get("forbiddenItems") and item["item_id"] in constraints["forbiddenItems"]:
                        continue
                    
                    filtered_items.append(dict(item))
                
                # Sort by win rate
                filtered_items.sort(key=lambda x: x["win_rate"], reverse=True)
                
                # Take top 6 items as optimal build
                optimal_items = [item["item_id"] for item in filtered_items[:6]]
                
                result = {
                    "items": optimal_items,
                    "expected_win_rate": sum(item["win_rate"] for item in filtered_items[:6]) / 6 if filtered_items else 0,
                    "timing_efficiency": 0.8  # Placeholder
                }
                
                # Cache the result
                await self.redis.setex(cache_key, 3600, json.dumps(result))
                return result
                
        except Exception as e:
            logger.error(f"Error resolving optimal build: {e}", exc_info=True)
            raise
            
    async def _get_item_cost(self, item_id: int) -> int:
        """Get the cost of an item."""
        try:
            async with self.db_pool.acquire() as conn:
                record = await conn.fetchrow(
                    "SELECT cost FROM items WHERE id = $1", item_id
                )
                return record["cost"] if record else 0
        except Exception as e:
            logger.error(f"Error getting item cost: {e}")
            return 0

# --------------- main.py GraphQL context ---------------

async def get_context():
    """Get context for GraphQL resolver."""
    try:
        # These connections should be properly configured
        db_pool = await asyncpg.create_pool(
            os.getenv("DB_DSN", "postgres://user:pass@localhost/dota")
        )
        redis = aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost")
        )
        
        # Return context with resolver
        return {
            "resolver": GraphQLResolver(db_pool, redis),
            "db_pool": db_pool,
            "redis": redis
        }
    except Exception as e:
        logger.error(f"Error creating GraphQL context: {e}")
        raise

# The GraphQL router setup would be updated to:
graphql_app = GraphQLRouter(
    schema=schema,
    context_getter=get_context,
    graphiql=True
)

app.include_router(graphql_app, prefix="/graphql")