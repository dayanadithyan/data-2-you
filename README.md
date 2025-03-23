# Data of the Ancients 2 (DATA2) (WIP)

![image](https://github.com/user-attachments/assets/c4723bf6-f5d9-4420-801c-dd76f164ad69)


> Lead: Devinda S (Tony Todd)
> Analytics: Dayan S (dogg)
- Please hit us up on steam if you wanna work together, this is not closed

Advanced analytical engine for Dota 2 strategy optimization and meta-analysis

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)

## Project Overview

- (WIP) DATA2 is an analytics platform that parses and disaggregates Dota 2 match data to allow for analysis beyond limits. Your only limit is creativity. Designed for competitive players, coaches, and analysts seeking evidence-based strategy optimization.

- Inspired by STRATZ AI: The IMP-ire Strikes Back, Devinda's fantasy league obsession, and Hawkie's [brilliant tools](https://github.com/VirenDias?tab=repositories) for the global D2 fantasy league

- Our thesis is to use interrupted-time-series analysis to create metrics to better understand the game. As the game has grown exponentially in difficulty, data must start to play an even larger role in understanding its beauty. 

- By gamers, for gamers. Reach out to contribute, this is for the community.

## Key Features we want to build (WIP): What we ideally want to get to as an MVP (at minimal)  

- **Research on what metrics might be useful**: Words are power, we have more data than we know what to do with, so much time will be spent on what we could look at, but of course, this is iterative
- **Temporal Meta Analysis**: Track hero, item, and other key metric performance across game versions, incl. hypothesis testing for meta shifts.  
- **Power Spike Detection**: Identify critical match moments with statistical significance.  
- **Creative**: Pass the data into even a graph database (Neo4J) to allow for even more fun analysis  
- **Knowlege graph (neo4J**: To run RAG for fast queries, identify unexpected relationships, using graph algorithms. Connect across any kind of variable in the schema

## Even more TO DO
Data Format Standardization: The most crucial step is to define a consistent data format for your Dota 2 match data. This will make it much easier to write generic analysis functions.

Data Cleaning and Preprocessing: Implement robust data cleaning and preprocessing steps to handle missing values, incorrect data types, and outliers.

Example using generic names```
frequency_table <- table(secondary_data$date_column)
frequency_df <- data.frame(frequency_table)
colnames(frequency_df) <- c("date", "frequency")
frequency_df$date <- as.Date(frequency_df$date)```

# Insert missing dates```
all_dates <- seq(min(frequency_df$date), max(frequency_df$date), by="day")
missing_dates_df <- data.frame(date = all_dates, frequency = 0)```

# Merge the dataframes
merged_frequency_df <- merge(frequency_df, missing_dates_df, by="date", all=TRUE)
merged_frequency_df$frequency <- ifelse(is.na(merged_frequency_df$frequency.x),
                                       merged_frequency_df$frequency.y,
                                       merged_frequency_df$frequency.x)
final_frequency_df <- merged_frequency_df[, c("date", "frequency")]

Feature Engineering

More Sophisticated Power Spike Detection: Implement more advanced power spike detection algorithms. 

Statistical Testing: identifying meta shifts. Consider using techniques like t-tests, ANOVA, or chi-squared tests.

Neo4j Integration: Design a schema for your Neo4j graph database and implement the code to load data from your Dota 2 match data into the graph. Explore graph algorithms for relationship discovery. Look into using RAG to efficiently query the database, and use knowledge graph for better searching data.

Iterative Development: Start with a small set of features and gradually add more as you get feedback from users. Focus on building a solid foundation and then iterate.

Community Feedback: Actively solicit feedback from the Dota 2 community to ensure that your platform is meeting their needs.

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
```

#### Generate optimal item build

```graphql
mutation OptimizeBuild($heroId: ID!, $constraints: BuildConstraints!) {
    calculateOptimalBuild(heroId: $heroId, constraints: $constraints) {
        items
        expectedWinRate
        timingEfficiency
    }
}
```

#### Get hero meta evolution

```graphql
query HeroTimeline($heroId: ID!) {
    heroMetaTimeline(heroId: $heroId) {
        timestamp
        patchVersion
        overallWinRate
    }
}
```

#### Optimize hero build

```graphql
mutation OptimizeBuild($heroId: ID!, $constraints: BuildConstraints!) {
    calculateOptimalBuild(heroId: $heroId, constraints: $constraints) {
        items
        expectedWinRate
    }
}
```

### Current thinking, how can we get here? Right now, that answer is as open as it has ever been, example—

#### Define the feature vector from the game state (using the 27 variables, abbreviated)

$$
\mathbf{X}(t) = \begin{bmatrix}
\text{Game Time} \\
\text{Kills} \\
\text{Deaths} \\
\text{Assists} \\
\vdots \\
\text{Weaken Duration}
\end{bmatrix}
$$

#### Model the win probability (TMP) as a logistic function of the features.

$$
\text{TMP}(t) = \hat{y}(t) = \sigma\Big( \mathbf{w}^\top \mathbf{X}(t) + b \Big) \quad \text{with} \quad \sigma(z) = \frac{1}{1 + e^{-z}}
$$

#### Interpret the rate of change in TMP as an indicator of in-game momentum shifts.

$$
\frac{d}{dt}\text{TMP}(t) > 0 \quad \Longrightarrow \quad \text{Team performance is improving}
$$

$$
\frac{d}{dt}\text{TMP}(t) < 0 \quad \Longrightarrow \quad \text{Team performance is declining}
$$

#### Game outcome timing when reaching a decisive win probability threshold.

$$
\text{If } \text{TMP}(t) \geq 0.9, \text{ then define the expected time to game closure as:}
$$

$$
T_{\text{end}} = t + \Delta t \quad \text{with} \quad \Delta t = \begin{cases}
10, & \text{if the team is consolidating its win (closing out)} \\
7, & \text{if the team is throwing the game (losing momentum)}
\end{cases}
$$

#### Express the dynamic update of TMP as a function of game events.

$$
\text{TMP}(t+\Delta t) = \text{TMP}(t) + \eta(t) \quad \text{where } \eta(t) \text{ represents the net effect of in-game events (team fights, tactics, etc.)}
$$

### Game-Theoretic TMP for Dota 2

Extending the TMP model with Dota 2-specific game theory for strategic insights:

#### Redefine the feature vector for Dota 2 (using 9 key variables, abbreviated)

$$
\mathbf{X}(t) = \begin{bmatrix}
\text{Game Time (min)} \\
\text{Net Kills (Kills - Deaths)} \\
\text{Assists} \\
\text{Gold Advantage (k)} \\
\text{Towers Destroyed} \\
\text{Roshan Kills} \\
\text{Ward Placements} \\
\text{Courier Kills} \\
\text{Buybacks Used}
\end{bmatrix}
$$

#### Model TMP as Radiant's win probability, a logistic function reflecting strategic payoffs.

$$
\text{TMP}(t) = \hat{y}(t) = \sigma\Big( \mathbf{w}^\top \mathbf{X}(t) + b \Big) \quad \text{with} \quad \sigma(z) = \frac{1}{1 + e^{-z}}
$$

Dire's payoff is 

$$
1 - \text{TMP}(t)
$$

framing a two-team game.

#### Interpret momentum shifts as strategic outcomes in Dota 2.

$$
\frac{d}{dt}\text{TMP}(t) > 0 \quad \Longrightarrow \quad \text{Radiant gaining edge (e.g., Aegis secured)}
$$

$$
\frac{d}{dt}\text{TMP}(t) < 0 \quad \Longrightarrow \quad \text{Dire fighting back (e.g., smoke gank)}
$$

#### Define game closure timing with Dota-specific thresholds.

$$
\text{If } \text{TMP}(t) \geq 0.9, \text{ then define the expected time to throne as:}
$$

$$
T_{\text{end}} = t + \Delta t \quad \text{with} \quad \Delta t = \begin{cases}
8, & \text{if Radiant pushes with Aegis advantage} \\
5, & \text{if Radiant throws at high ground}
\end{cases}
$$

#### Express the dynamic update of TMP with Dota events as strategic moves.

$$
\text{TMP}(t+\Delta t) = \text{TMP}(t) + \eta(t) \quad \text{where } \eta(t) \text{ captures events (team fights, Roshan contests, etc.)}
$$
