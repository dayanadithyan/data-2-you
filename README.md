# Data of the Ancients 2 (DATA2) (WIP)
# DATA2: Data of the Ancients 2

> **Lead**: Devinda S (Tony Todd)  
> **Analytics**: Dayan S (dogg)

## Project Overview

DATA2 (Data of the Ancients 2) is an advanced analytical engine designed for Dota 2 strategy optimization and meta-analysis. The platform parses and disaggregates match data to enable sophisticated analysis beyond conventional limits.

This project applies statistical methods, particularly interrupted time-series analysis, to create metrics that better understand the game's complexity. As Dota 2 has grown exponentially in difficulty, data-driven approaches become increasingly valuable for understanding strategic nuances.

## Minimum Viable Product (MVP)

Our MVP aims to deliver:

1. **Temporal Meta Analysis**: Track hero, item, and key metric performance across game versions with statistical significance testing for meta shifts.

2. **Power Spike Detection**: Identify critical match moments through statistical analysis of game state variables.

3. **Knowledge Graph Integration**: Implement a Neo4J graph database to discover unexpected relationships between game variables and support Retrieval-Augmented Generation (RAG) for rapid queries.

4. **Research Framework**: Develop a structured approach to identify which metrics provide the most strategic value from the wealth of available data.

5. **API-to-Neo4j Pipeline**: Automated extraction, transformation, and loading of Dota 2 match data from API sources directly into a Neo4j graph database for relationship analysis and pattern detection.

## Technical Implementation

The platform implements:

- **Data Schema**: Comprehensive GraphQL schema defining heroes, matches, items, abilities, and their relationships.

- **Analytics Engine**: Mathematical models for win probability and momentum prediction, including:
  - Team Match Performance (TMP) modeling using logistic functions
  - Game-theoretic frameworks for momentum shift analysis
  - Statistical validation of meta changes

- **Backend Architecture**: Python-based system with:
  - SQLAlchemy for database operations
  - FastAPI for API endpoint management
  - Redis for caching
  - Neo4j driver for graph database operations

- **Data Pipeline**: Robust ETL process to transform API data into graph structures:
  - Automated extraction from Dota 2 API endpoints
  - Transformation of relational data into graph-optimized structures
  - Incremental loading to maintain database efficiency

## Graph Data Model

The Neo4j graph implementation enables:

1. **Entity Relationships**: Modeling of complex relationships between heroes, items, players, matches, and game events.

2. **Temporal Analysis**: Tracking relationship changes across game versions and meta shifts.

3. **Pattern Detection**: Using graph algorithms to identify winning combinations, counter strategies, and optimal team compositions.

4. **Knowledge Querying**: Supporting natural language queries through graph-enhanced retrieval augmented generation.

## Mathematical Approach

The project applies rigorous mathematical modeling:

- Feature vector extraction from game state variables
- Logistic regression for win probability estimation
- Time-derivative analysis for momentum shifts
- Statistical hypothesis testing for meta analysis
- Graph centrality metrics for identifying key relationship nodes

## Development Roadmap

1. **Core Feature Engineering**: Implement basic metrics and analysis framework
2. **Advanced Spike Detection**: Develop sophisticated algorithms for power spike identification
3. **Statistical Testing**: Implement robust methods for identifying meta shifts
4. **Database Integration**: Connect Neo4j for graph-based relationship discovery
5. **API Pipeline Implementation**: Build automated data extraction and transformation processes
6. **Graph Schema Optimization**: Refine Neo4j data model for analytical performance
7. **Community Feedback Loop**: Establish mechanisms for user input to guide feature development

## Illustrative Example: Hero Synergy Analysis

Here's how DATA2 would work in practice for a hero synergy analysis:

```
1. Data Ingestion:
   - The system polls the Dota 2 API for recent match data
   - Match details including hero picks, item purchases, and game events are captured

2. Neo4j Graph Creation:
   - Heroes become nodes with properties (e.g., strength, agility, intelligence)
   - Matches become nodes with properties (e.g., duration, winner)
   - Relationships are created:
     (Hero)-[:PICKED_IN]->(Match)
     (Hero)-[:PLAYED_WITH]->(Hero)
     (Hero)-[:PURCHASED]->(Item)

3. Analysis Query:
   MATCH (h1:Hero)-[:PICKED_IN]->(m:Match)<-[:PICKED_IN]-(h2:Hero)
   WHERE h1.id = 1 AND m.is_victory = true AND h1.team = h2.team
   RETURN h2.name, count(*) as games, avg(m.duration) as avg_duration
   ORDER BY games DESC
   LIMIT 5

4. Insight Generation:
   - System identifies that Hero 1 (e.g., Crystal Maiden) has highest win rate when paired with Hero 23 (e.g., Juggernaut)
   - Power spike detection shows this combo is strongest at 15-25 minute mark
   - Meta analysis reveals this synergy became prominent in patch 7.32
```

Using the TMP model, the system can further analyze:

```
TMP(t) = σ(w⊤X(t) + b)

Where X(t) = [Game Time, Net Kills, Gold Advantage, Towers Destroyed, Roshan Kills, ...]

For the Crystal Maiden + Juggernaut combo, the model detects:
- d/dt TMP(t) shows significant positive spike after CM reaches level 6
- Win probability increases by 15% when Juggernaut builds BKB before 18 minutes
```

This analysis provides actionable intelligence for team composition and strategic timing decisions.

## Contribution

This is an open community project. Please reach out via Steam if you're interested in contributing. We welcome developers, analysts, and Dota 2 enthusiasts who want to bring data science to the game.

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)

## License

Custom evaluation license - see LICENSE file for details.
