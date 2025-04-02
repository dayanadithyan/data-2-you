import statistics
from sqlalchemy import case, create_engine, func, cast, Float
from sqlalchemy.orm import sessionmaker
from models import (
    Base,
    GorpMigrations,
    Heroes,
    Items,
    Leagues,
    TeamPlayers,
    Teams,
    Series,
    Matches,
    MatchPickBans,
    MatchPlayers,
)

# Create the engine for 'test.db'
engine = create_engine('sqlite:///test.db')

# Create a session factory
Session = sessionmaker(bind=engine)

# Create a session
session = Session()

# Query to list all match numbers (IDs)

# matches = session.query(Matches).all()
# for match in matches:
#     print(str(match))

# # List all match numbers in the DB
# matches = session.query(Matches.id).all()
# print("All match IDs:")
# for match_id, in matches:
#     print(match_id) ## working

# 5 most contested heroes (highest ban and pick rates)
# join the MatchPickBans table and count the total appearances (picks + bans)
# because either way, we'll have another third join for the name unless we can read hero IDs with eyes
most_contested = (
    session.query(
        Heroes.display_name,
        func.count(MatchPickBans.hero_id).label("total_appearances")
    )
    .join(MatchPickBans, Heroes.id == MatchPickBans.hero_id)
    .group_by(Heroes.id)
    .order_by(func.count(MatchPickBans.hero_id).desc())
    .limit(15)
    .all()
)
print("\n5 Most Contested Heroes (picks + bans):")
for hero, total in most_contested:
    print(f"{hero}: {total}")

# Query 3: 5 most picked heroes (highest pick rates)
# Filter for only picks (is_pick == 1)
most_picked = (
    session.query(
        Heroes.display_name,
        func.count(MatchPickBans.hero_id).label("pick_count")
    )
    .join(MatchPickBans, Heroes.id == MatchPickBans.hero_id)
    .filter(MatchPickBans.is_pick == 1)
    .group_by(Heroes.id)
    .order_by(func.count(MatchPickBans.hero_id).desc())
    .limit(15)
    .all()
)
print("\n5 Most Picked Heroes:")
for hero, count in most_picked:
    print(f"{hero}: {count}")

# Define the KDA expression with floating-point division
# kda_expr = (
#     (cast(MatchPlayers.kills, Float) + cast(MatchPlayers.assists, Float))
#     /
#     case(
#         (MatchPlayers.deaths == 0, 1),
#         else_=cast(MatchPlayers.deaths, Float)
#     )
# )

# # Query for top 5 players based on average KDA
# top_players = (
#     session.query(
#         MatchPlayers.steam_account_id,
#         func.avg(kda_expr).label("avg_kda")
#     )
#     .group_by(MatchPlayers.steam_account_id)
#     .order_by(func.avg(kda_expr).desc())
#     .limit(5)
#     .all()
# )

# print("Top 5 Players with Highest Average KDA:")
# for steam_account_id, avg_kda in top_players:
#     print(f"Steam Account ID: {steam_account_id}, Average KDA: {avg_kda:.2f}")
## this is okay but i shoould have joined with the names (i think its in team)
## steam account id to name


# # Q 5: How does dota plus hero level correlate with hero performance?
## needs a bit more thibking here, esp. with the test, correlation
# # First demo, we use hero_damage as a proxy for performance.
# # We retrieve pairs of (dota_plus_hero_level, hero_damage) for analysis.
## we could check with IMP, and then develop our own vision, what defines impact severely varies
## its v subjective

# data = session.query(
#     MatchPlayers.dota_plus_hero_level,
#     MatchPlayers.hero_damage
# ).filter(MatchPlayers.dota_plus_hero_level.isnot(None)).all()

# if data:
#     # Separate the pairs into two lists
#     levels, damages = zip(*data)
#     # Compute Pearson correlation (requires Python 3.10+ for statistics.correlation)
#     correlation = statistics.correlation(levels, damages)
#     print(f"\nPearson correlation between Dota Plus Hero Level and Hero Damage: {correlation:.2f}")
# else:
#     print("\nNo data available for Dota Plus Hero Level correlation analysis.")