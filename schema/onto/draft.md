# DraftII

DotaOntology
├── GameEnvironment
│   ├── Map
│   │   ├── Lane
│   │   │   ├── TopLane
│   │   │   ├── MidLane
│   │   │   └── BottomLane
│   │   ├── Jungle
│   │   │   ├── RadiantJungle
│   │   │   └── DireJungle
│   │   ├── River
│   │   ├── Base
│   │   │   ├── RadiantBase
│   │   │   └── DireBase
│   │   ├── RoshanPit
│   │   ├── TormentorPit
│   │   │   ├── RadiantTormentor
│   │   │   └── DireTormentor
│   │   ├── SecretShop
│   │   ├── OutpostLocation
│   │   └── RuneSpawnLocation
│   │       ├── PowerRuneLocation
│   │       ├── BountyRuneLocation
│   │       └── WaterRuneLocation
│   ├── Structure
│   │   ├── Ancient
│   │   ├── Tower
│   │   │   ├── Tier1Tower
│   │   │   ├── Tier2Tower
│   │   │   ├── Tier3Tower
│   │   │   └── Tier4Tower
│   │   ├── Barracks
│   │   │   ├── MeleeBarracks
│   │   │   └── RangedBarracks
│   │   ├── Outpost
│   │   ├── Fountain
│   │   └── NeutralItemStash
│   ├── Terrain
│   │   ├── Pathable
│   │   ├── Unpathable
│   │   ├── Trees
│   │   ├── HighGround
│   │   └── LowGround
│   ├── TimeState
│   │   ├── GameTime
│   │   ├── DayNightCycle
│   │   ├── GamePhase
│   │   │   ├── PreGame
│   │   │   ├── Strategy
│   │   │   ├── HeroSelection
│   │   │   ├── LanePhase
│   │   │   ├── MidGame
│   │   │   └── LateGame
│   │   └── SpawnTimer
│   │       ├── CreepSpawnTimer
│   │       ├── NeutralSpawnTimer
│   │       ├── RuneSpawnTimer
│   │       ├── TormentorSpawnTimer
│   │       └── RoshanRespawnTimer
│   └── Position
│       ├── Coordinate
│       ├── Direction
│       └── Facing
├── Entity
│   ├── Team
│   │   ├── Radiant
│   │   └── Dire
│   ├── Unit
│   │   ├── Hero
│   │   │   ├── StrengthHero
│   │   │   ├── AgilityHero
│   │   │   ├── IntelligenceHero
│   │   │   └── TalentTree
│   │   │       ├── Level10Talents
│   │   │       ├── Level15Talents
│   │   │       ├── Level20Talents
│   │   │       └── Level25Talents
│   │   ├── CreepUnit
│   │   │   ├── LaneCreep
│   │   │   │   ├── MeleeCreep
│   │   │   │   ├── RangedCreep
│   │   │   │   └── SiegeCreep
│   │   │   └── NeutralCreep
│   │   │       ├── SmallCamp
│   │   │       ├── MediumCamp
│   │   │       ├── LargeCamp
│   │   │       └── AncientCamp
│   │   ├── SummonedUnit
│   │   │   ├── IllusionUnit
│   │   │   └── ControlledSummon
│   │   ├── Courier
│   │   ├── Roshan
│   │   ├── Tormentor
│   │   └── Ward
│   │       ├── ObserverWard
│   │       └── SentryWard
│   ├── Item
│   │   ├── PurchasableItem
│   │   │   ├── BasicItem
│   │   │   └── RecipeItem
│   │   ├── ConsumableItem
│   │   │   ├── Tango
│   │   │   ├── Clarity
│   │   │   ├── HealthPotion
│   │   │   └── DustOfAppearance
│   │   ├── EquippableItem
│   │   │   ├── WeaponItem
│   │   │   ├── ArmorItem
│   │   │   ├── AccessoryItem
│   │   │   └── BootsItem
│   │   ├── FragmentItem
│   │   │   ├── AghanimsShard
│   │   │   └── AghanimsScepter
│   │   ├── NeutralItem
│   │   │   ├── Tier1NeutralItem
│   │   │   ├── Tier2NeutralItem
│   │   │   ├── Tier3NeutralItem
│   │   │   ├── Tier4NeutralItem
│   │   │   └── Tier5NeutralItem
│   │   └── SpecialItem
│   │       ├── AegisOfTheImmortal
│   │       ├── CheeseItem
│   │       └── RefresherShard
│   ├── Ability
│   │   ├── BasicAbility
│   │   ├── UltimateAbility
│   │   ├── ActiveAbility
│   │   ├── PassiveAbility
│   │   ├── ToggleAbility
│   │   ├── VectorTargetedAbility
│   │   ├── ItemAbility
│   │   └── TalentAbility
│   └── Rune
│       ├── PowerRune
│       │   ├── HasteRune
│       │   ├── DoubleDamageRune
│       │   ├── RegenerationRune
│       │   ├── ArcaneRune
│       │   ├── InvisibilityRune
│       │   └── IllusionRune
│       ├── BountyRune
│       └── WaterRune
├── GameMechanics
│   ├── MatchState
│   │   ├── DraftPhase
│   │   │   ├── PickPhase
│   │   │   └── BanPhase
│   │   ├── Score
│   │   ├── NetWorth
│   │   └── ObjectiveStatus
│   ├── Vision
│   │   ├── FogOfWar
│   │   ├── TrueVision
│   │   ├── NightVision
│   │   └── SharedVision
│   ├── Combat
│   │   ├── DamageType
│   │   │   ├── PhysicalDamage
│   │   │   ├── MagicalDamage
│   │   │   ├── PureDamage
│   │   │   └── HPRemoval
│   │   ├── AttackType
│   │   │   ├── MeleeAttack
│   │   │   └── RangedAttack
│   │   ├── ArmorType
│   │   ├── Resistance
│   │   │   ├── PhysicalResistance
│   │   │   ├── MagicalResistance
│   │   │   └── StatusResistance
│   │   └── CombatModifier
│   │       ├── Evasion
│   │       ├── BlockChance
│   │       ├── CriticalStrike
│   │       ├── LifeSteal
│   │       └── CastPointModification
│   ├── Resources
│   │   ├── Gold
│   │   │   ├── ReliableGold
│   │   │   └── UnreliableGold
│   │   ├── Experience
│   │   ├── Health
│   │   ├── Mana
│   │   ├── Charges
│   │   └── Cooldown
│   ├── StatusEffect
│   │   ├── Buff
│   │   │   ├── MovementBuff
│   │   │   ├── DamageBuff
│   │   │   ├── ArmorBuff
│   │   │   └── RegenerationBuff
│   │   ├── Debuff
│   │   │   ├── Stun
│   │   │   ├── Slow
│   │   │   ├── Silence
│   │   │   ├── Root
│   │   │   ├── Disarm
│   │   │   ├── Break
│   │   │   ├── Fear
│   │   │   └── Rupture
│   │   ├── SuspendedState
│   │   └── DispelType
│   │       ├── BasicDispel
│   │       ├── StrongDispel
│   │       └── Hidden
│   ├── Movement
│   │   ├── WalkingMovement
│   │   ├── ForcedMovement
│   │   ├── Teleportation
│   │   └── PhaseMovement
│   └── GameObjective
│       ├── PrimaryObjective
│       │   └── AncientDestruction
│       └── SecondaryObjective
│           ├── TowerDestruction
│           ├── RoshanKill
│           ├── TormentorKill
│           ├── CourierKill
│           └── OutpostCapture
├── AISystem
│   ├── AgentArchitecture
│   │   ├── Observation
│   │   │   ├── VisibleObservation
│   │   │   ├── DerivativeObservation
│   │   │   └── HistoricalObservation
│   │   ├── Action
│   │   │   ├── MovementAction
│   │   │   │   ├── PositionTargetAction
│   │   │   │   └── UnitTargetAction
│   │   │   ├── AttackAction
│   │   │   │   ├── UnitAttackAction
│   │   │   │   └── AreaAttackAction
│   │   │   ├── AbilityAction
│   │   │   │   ├── PositionTargetAbility
│   │   │   │   ├── UnitTargetAbility
│   │   │   │   ├── NoTargetAbility
│   │   │   │   ├── VectorTargetAbility
│   │   │   │   └── ToggleAbility
│   │   │   ├── ItemAction
│   │   │   │   ├── UseItemAction
│   │   │   │   ├── PurchaseItemAction
│   │   │   │   └── DropItemAction
│   │   │   └── SpecialAction
│   │   │       ├── BuybackAction
│   │   │       ├── CourierAction
│   │   │       └── GlyphAction
│   │   ├── Policy
│   │   │   ├── TrainedPolicy
│   │   │   ├── PastOpponentPolicy
│   │   │   ├── CurrentPolicy
│   │   │   └── ContextualDecision
│   │   └── RewardFunction
│   │       ├── WinLossReward
│   │       ├── ResourceReward
│   │       ├── CombatReward
│   │       ├── ObjectiveReward
│   │       └── TeamSpiritParameter
│   ├── NeuralNetworkComponent
│   │   ├── InputProcessing
│   │   │   ├── UnitEmbedding
│   │   │   ├── AbilityEmbedding
│   │   │   ├── ItemEmbedding
│   │   │   └── MultimodalProcessing
│   │   ├── CoreNetwork
│   │   │   ├── LSTM
│   │   │   └── CrossHeroPooling
│   │   ├── OutputHeads
│   │   │   ├── ActionSelection
│   │   │   ├── UnitTargetSelection
│   │   │   └── PositionSelection
│   │   └── AuxiliaryHeads
│   │       ├── WinPrediction
│   │       ├── NetWorthPrediction
│   │       └── ObjectivePrediction
│   ├── TrainingInfrastructure
│   │   ├── DataCollection
│   │   │   ├── RolloutWorker
│   │   │   ├── ForwardPassGPU
│   │   │   └── ExperienceBuffer
│   │   ├── Optimization
│   │   │   ├── OptimizerGPU
│   │   │   ├── GradientCalculation
│   │   │   └── ParameterServer
│   │   ├── DistributedSystem
│   │   │   ├── Controller
│   │   │   ├── Synchronization
│   │   │   └── LoadBalancing
│   │   └── LearningAlgorithm
│   │       ├── PPO
│   │       ├── GAE
│   │       └── Adam
│   ├── SurgeryOperation
│   │   ├── ModelModification
│   │   │   ├── LayerExpansion
│   │   │   └── WeightPreservation
│   │   ├── ObservationSpaceChange
│   │   │   ├── FeatureAddition
│   │   │   └── FeatureRemoval
│   │   └── ActionSpaceChange
│   │       ├── ActionAddition
│   │       └── ActionRemoval
│   └── EvaluationSystem
│       ├── TrueSkillRating
│       ├── WinRateMetric
│       ├── HumanEvaluation
│       ├── SelfPlayEvaluation
│       └── AdversarialValidation
└── MetaGameConcepts
    ├── Strategy
    │   ├── TeamComposition
    │   ├── LaneAssignment
    │   ├── ItemProgression
    │   ├── AbilityProgression
    │   └── EmergentBehavior
    ├── Tactics
    │   ├── Ganking
    │   ├── Pushing
    │   ├── Farming
    │   ├── Teamfight
    │   └── Warding
    ├── Role
    │   ├── Position1_Carry
    │   ├── Position2_Mid
    │   ├── Position3_Offlane
    │   ├── Position4_SoftSupport
    │   └── Position5_HardSupport
    └── Metagame
        ├── PatchVersion
        ├── PopularHeroes
        ├── BannedHeroes
        └── StrategyTrends
