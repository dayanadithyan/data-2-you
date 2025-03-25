# Dependency for analytics engine
async def get_analytics_engine(
    db: Database = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
) -> AnalyticsEngine:
    """Dependency to get analytics engine with database and Redis connections."""
    try:
        return AnalyticsEngine(db, redis)
    except Exception as e:
        logger.error(f"Analytics engine initialization error: {e}")
        raise HTTPException(status_code=500, detail="Analytics engine initialization error")

@app.get("/hero/{hero_id}/timeline")
async def get_hero_timeline(
    hero_id: int,
    resolution: TimeResolution = TimeResolution.PATCH,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """Get a hero's performance timeline."""
    try:
        return await analytics_engine.get_hero_timeline(hero_id, resolution)
    except Exception as e:
        logger.error(f"Error fetching hero timeline: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching hero timeline: {str(e)}")

@app.get("/analysis/patch-impact")
async def patch_impact_analysis(
    hero_id: int,
    base_patch: str,
    target_patch: str,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """Analyze the impact of a patch on a hero's performance."""
    try:
        return await analytics_engine.calculate_patch_impact(hero_id, base_patch, target_patch)
    except Exception as e:
        logger.error(f"Error analyzing patch impact: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing patch impact: {str(e)}")

# Add GraphQL endpoint
from strawberry.fastapi import GraphQLRouter
from .schema.schema import schema

graphql_app = GraphQLRouter(
    schema=schema,
    graphiql=True  # Enable GraphiQL interface for development
)

app.include_router(graphql_app, prefix="/graphql")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)