# --------------- schema.py ---------------
import strawberry
from datetime import datetime
from typing import List, Optional

@strawberry.type
class PositionMetrics:
    position: str
    pick_rate: float
    win_rate: float
    gold_per_min: float
    exp_per_min: float

@strawberry.type
class ItemSynergy:
    item_id: int
    synergy_score: float

@strawberry.type
class HeroItemBuild:
    item_id: int
    win_rate: float
    purchase_timing: float
    matches: int
    synergy_items: List[ItemSynergy]

@strawberry.type
class SkillPriority:
    ability_id: int
    priority_score: float

@strawberry.type
class HeroMetaSnapshot:
    timestamp: datetime
    patch_version: str
    overall_win_rate: float
    positions: List[PositionMetrics]
    item_builds: List[HeroItemBuild]
    skill_priorities: List[SkillPriority]

@strawberry.type
class PowerSpike:
    time_window: str
    team: str
    advantage_type: str
    magnitude: float

@strawberry.type
class MatchPowerProfile:
    match_id: int
    significant_spikes: List[PowerSpike]
    objective_timeline: List[str]  # Simplified for example
    team_synergy: float

@strawberry.input
class BuildConstraints:
    max_cost: Optional[int] = None
    required_timings: Optional[List[str]] = None
    forbidden_items: Optional[List[int]] = None

@strawberry.type
class OptimalBuildResult:
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
        # Implementation would use data loader pattern
        return []

    @strawberry.field
    async def match_power_analysis(self, match_id: int) -> MatchPowerProfile:
        # Implementation would analyze match data
        return MatchPowerProfile(...)

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def calculate_optimal_build(
        self,
        hero_id: int,
        constraints: BuildConstraints
    ) -> OptimalBuildResult:
        # Implementation would run optimization algorithms
        return OptimalBuildResult(...)

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def live_match_metrics(
        self,
        match_id: int
    ) -> AsyncGenerator[dict, None]:
        # Implementation would connect to live data feed
        yield {}

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)