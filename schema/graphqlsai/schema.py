import strawberry
from datetime import datetime
from typing import List, Optional, AsyncGenerator
from strawberry.types import Info

@strawberry.type
class PositionMetrics:
    """Metrics for a hero in a specific position."""
    position: str
    pick_rate: float
    win_rate: float
    gold_per_min: float
    exp_per_min: float

@strawberry.type
class ItemSynergy:
    """Synergy between items for a specific hero."""
    item_id: int
    synergy_score: float

@strawberry.type
class HeroItemBuild:
    """Item build information for a hero."""
    item_id: int
    win_rate: float
    purchase_timing: float
    matches: int
    synergy_items: List[ItemSynergy]

@strawberry.type
class SkillPriority:
    """Priority scores for hero abilities."""
    ability_id: int
    priority_score: float

@strawberry.type
class HeroMetaSnapshot:
    """A snapshot of a hero's meta statistics at a specific point in time."""
    timestamp: datetime
    patch_version: str
    overall_win_rate: float
    positions: List[PositionMetrics]
    item_builds: List[HeroItemBuild]
    skill_priorities: List[SkillPriority]

@strawberry.type
class PowerSpike:
    """Represents a significant power spike during a match."""
    time_window: str
    team: str
    advantage_type: str
    magnitude: float

@strawberry.type
class MatchPowerProfile:
    """Contains analysis of power dynamics throughout a match."""
    match_id: int
    significant_spikes: List[PowerSpike]
    objective_timeline: List[str]  # Simplified for example
    team_synergy: float

@strawberry.input
class BuildConstraints:
    """Input type for build optimization constraints."""
    max_cost: Optional[int] = None
    required_timings: Optional[List[str]] = None
    forbidden_items: Optional[List[int]] = None

@strawberry.type
class OptimalBuildResult:
    """Result of a build optimization calculation."""
    items: List[int]
    expected_win_rate: float
    timing_efficiency: float

@strawberry.type
class Query:
    @strawberry.field
    async def hero_meta_timeline(
        self,
        hero_id: int,
        resolution: str = "PATCH",
        patch_range: Optional[str] = None
    ) -> List[HeroMetaSnapshot]:
        """Get the meta evolution timeline for a specific hero."""
        # Implementation would use data loader pattern
        return []

    @strawberry.field
    async def match_power_analysis(self, match_id: int) -> MatchPowerProfile:
        """Analyze power dynamics for a specific match."""
        # Implementation would analyze match data
        return MatchPowerProfile(
            match_id=match_id,
            significant_spikes=[], 
            objective_timeline=[],
            team_synergy=0.0
        )

    @strawberry.field
    async def sql_query(self, question: str, info: Info) -> str:
        """Natural-language to SQL query via LangChain and return answer."""
        # delegate to resolver on the context
        return await info.context["resolver"].resolve_sql_query(question)

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def calculate_optimal_build(
        self,
        hero_id: int,
        constraints: BuildConstraints
    ) -> OptimalBuildResult:
        """Calculate the optimal item build for a hero based on constraints."""
        # Implementation would run optimization algorithms
        return OptimalBuildResult(
            items=[],
            expected_win_rate=0.0,
            timing_efficiency=0.0
        )

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def live_match_metrics(
        self,
        match_id: int
    ) -> AsyncGenerator[dict, None]:
        """Subscribe to live match metrics for a specific match."""
        # Implementation would connect to live data feed
        yield {}

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)
