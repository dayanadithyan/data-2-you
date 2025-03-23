
# Data of the Ancients 2 (DATA2) (WIP)

Advanced analytical engine for Dota 2 strategy optimization and meta-analysis

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)

## Project Overview

- (WIP) DATA2 is an analytics platform that parses and dissaggregates Dota 2 match data to allow for analysis beyond limits. Your only limit is creativity. Designed for competitive players, coaches, and analysts seeking evidence-based strategy optimization.

- Inspired by STRATZ AI: The IMP-ire Strikes Back and Devinda's fantasy league obsession.

- Our thesis is to use interupted-time-series analysis to create metrics to better understand the game. As the game has grown exponentially in difficulty, data must start to play an even larger role in understanding its beauty. 

- By gamers, for gamers. Reach out to contribute, this is for the community.

## Key Features (WIP): What we ideally want to get to as an MVP (at minimal)  

- **Temporal Meta Analysis**: Track hero, item, and other key metric performance across game versions, incl. hypothesis testing for meta shifts.  
- **Power Spike Detection**: Identify critical match moments with statistical significance.  
- **Creative**: Pass the data into even a graph database (Neo4J) to allow for even more fun analysis
- **AI (lmao): Because nothing is complete without a pointless use of an LLM

### Examples (Illustrative for POC, not fully functional)

#### Retrieve hero meta evolution

```graphql
    query HeroTimeline($heroId: ID!) {
    heroMetaTimeline(heroId: $heroId) {
        timestamp
        patchVersion
        positions {
        position
        pickRate
        winRate
        }
    }
    }

    # Generate optimal item build

    mutation OptimizeBuild($heroId: ID!, $constraints: BuildConstraints!) {
    calculateOptimalBuild(heroId: $heroId, constraints: $constraints) {
        items
        expectedWinRate
        timingEfficiency
    }
    }
```

# Get hero meta evolution

```graphql
    query HeroTimeline($heroId: ID!) {
    heroMetaTimeline(heroId: $heroId) {
        timestamp
        patchVersion
        overallWinRate
    }
    }

    # Optimize hero build

    mutation OptimizeBuild($heroId: ID!, $constraints: BuildConstraints!) {
    calculateOptimalBuild(heroId: $heroId, constraints: $constraints) {
        items
        expectedWinRate
    }
```
