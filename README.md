
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
#### Current thinking, how can we get here? Right now, that answer is as open as it has ever been, example—

% 1. Define the feature vector from the game state (using the 27 variables, abbreviated)
\mathbf{X}(t) = \begin{bmatrix}
\text{Game Time} \\
\text{Kills} \\
\text{Deaths} \\
\text{Assists} \\
\vdots \\
\text{Weaken Duration}
\end{bmatrix}

% 2. Model the win probability (TMP) as a logistic function of the features.
\text{TMP}(t) = \hat{y}(t) = \sigma\Big( \mathbf{w}^\top \mathbf{X}(t) + b \Big)
\quad \text{with} \quad
\sigma(z) = \frac{1}{1 + e^{-z}}

% 3. Interpret the rate of change in TMP as an indicator of in-game momentum shifts.
\frac{d}{dt}\text{TMP}(t) \;>\; 0 \quad \Longrightarrow \quad \text{Team performance is improving}
\\[6mm]
\frac{d}{dt}\text{TMP}(t) \;<\; 0 \quad \Longrightarrow \quad \text{Team performance is declining}

% 4. Game outcome timing when reaching a decisive win probability threshold.
\text{If } \text{TMP}(t) \geq 0.9, \text{ then define the expected time to game closure as:}
\\[3mm]
T_{\text{end}} = t + \Delta t \quad \text{with} \quad
\Delta t = \begin{cases}
10, & \text{if the team is consolidating its win (closing out)} \\
7, & \text{if the team is throwing the game (losing momentum)}
\end{cases}

% 5. Express the dynamic update of TMP as a function of game events.
\text{TMP}(t+\Delta t) = \text{TMP}(t) + \eta(t)
\quad \text{where } \eta(t) \text{ represents the net effect of in-game events (team fights, tactics, etc.)}

