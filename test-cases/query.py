##############################################################
# 1. SETUP AND CONFIGURATION
##############################################################

import statistics
from scipy.stats import ttest_1samp
import numpy as np
from scipy import stats
from sqlalchemy import case
from sqlalchemy import case, create_engine, func, cast, Float, and_, desc, text
from sqlalchemy.orm import sessionmaker, aliased
#do not tamper (for now)
from models import (
    Base,
    Heroes,
    Items,
    TeamPlayers,
    Matches,
    MatchPickBans,
    MatchPlayers,
)

## note player-team can vary with league, use steamid as unique key
## patch is one measure of temporality 


# Create database connection
engine = create_engine('sqlite:////Volumes/LNX/NEW/data2/test-cases/db/dota-pro-db/test.db')
Session = sessionmaker(bind=engine)
session = Session()

# Define utility functions for performance metrics
def calculate_impact_score(row, is_tuple=True):
    """
    Calculate a composite impact score for player performance.
    
    Args:
        row: Data row containing performance metrics
        is_tuple: Whether row is a tuple (True) or an object with attributes (False)
    
    Returns:
        float: Impact score
    """
    if is_tuple:
        # First, extract all values and print for debugging
        # print(f"Row length: {len(row)}, Row structure: {row}")
        
        # Based on error, let's inspect what the tuple actually contains
        match_id = row[0]
        player_id = row[1]
        hero_id = row[2]
        role = row[3]  # Role appears to be at position 3
        hero_level = row[4]
        kills = float(row[5])  # Shifting numeric values
        deaths = max(1.0, float(row[6]))
        assists = float(row[7])
        hero_damage = float(row[8])
        tower_damage = float(row[9])
        hero_healing = float(row[10])
        gold_per_min = float(row[11])
    else:
        # Extract metrics from an object with attributes
        role = row.role
        kills = float(row.kills)
        deaths = max(1.0, float(row.deaths))
        assists = float(row.assists)
        hero_damage = float(row.hero_damage)
        tower_damage = float(row.tower_damage)
        hero_healing = float(row.hero_healing)
        gold_per_min = float(row.gold_per_min)

    # Calculate component scores
    kda = (kills + assists) / deaths
    economy = gold_per_min / 600  # Normalize by approximate max GPM
    damage_contribution = hero_damage / 30000  # Normalize by approximate max damage
    objective_contribution = tower_damage / 10000  # Normalize by approximate max tower damage
    

    ## weight adjustments here are hardcoded, base statisticlly later
    ## check the distributions to replace them with patch??? 
    # Adjust weights based on role
    if role == 'CORE':
        score = (0.25 * kda) + (0.3 * economy) + (0.25 * damage_contribution) + (0.2 * objective_contribution)
    else:  # LIGHT_SUPPORT and HARD_SUPPORT
        healing = hero_healing / 10000  # Normalize healing
        score = (0.3 * kda) + (0.15 * economy) + (0.2 * damage_contribution) + (0.35 * healing)
    
    return score


## option to double stratify here, but that might be tricky with DR
def calculate_icc(data, groups):
    """
    Calculate intraclass correlation coefficient (ICC) for one-way random effects model.
    
    Args:
        data: List of performance metrics
        groups: List of corresponding group identifiers (hero levels)
    
    Returns:
        tuple: (icc, f_value, p_value)
    """
    # Group data
    group_dict = {}
    for i, group in enumerate(groups):
        if group not in group_dict:
            group_dict[group] = []
        group_dict[group].append(data[i])
    
    # Only include groups with multiple observations
    valid_groups = {g: vals for g, vals in group_dict.items() if len(vals) >= 2}
    
    if len(valid_groups) < 2:
        return None, None, None
    
    # Calculate group means and overall mean
    group_means = [np.mean(vals) for vals in valid_groups.values()]
    group_sizes = [len(vals) for vals in valid_groups.values()]
    overall_mean = np.mean([val for vals in valid_groups.values() for val in vals])
    
    # Calculate between-group and within-group sum of squares
    n_total = sum(group_sizes)
    
    between_ss = sum([size * ((mean - overall_mean) ** 2) for size, mean in zip(group_sizes, group_means)])
    within_ss = sum([sum([(val - mean) ** 2 for val in vals]) for mean, vals in zip(group_means, valid_groups.values())])
    
    # Calculate mean squares
    n_groups = len(valid_groups)
    between_ms = between_ss / (n_groups - 1) if n_groups > 1 else 0
    within_ms = within_ss / (n_total - n_groups) if n_total > n_groups else 0
    
    # Calculate ICC
    if between_ms + within_ms == 0:
        return 0, 0, 1.0  # No variance at all
    
    icc = (between_ms - within_ms) / (between_ms + (sum(group_sizes) / n_groups - 1) * within_ms)
    
    # F-test for significance
    f_value = between_ms / within_ms if within_ms > 0 else float('inf')
    p_value = 1 - stats.f.cdf(f_value, n_groups - 1, n_total - n_groups)
    
    return icc, f_value, p_value


##############################################################
# 2. DATA ACQUISITION
##############################################################

print("Fetching base data...")

# Get all heroes
heroes = session.query(Heroes.id, Heroes.display_name).all()
hero_names = {hero[0]: hero[1] for hero in heroes}
print(f"Loaded {len(hero_names)} heroes")

# Get all players
players = session.query(TeamPlayers.steam_account_id, TeamPlayers.name).all()
player_names = {player[0]: player[1] for player in players}
print(f"Loaded {len(player_names)} players")

# Get all roles
distinct_roles = session.query(MatchPlayers.role).filter(MatchPlayers.role.isnot(None)).distinct().all()
roles = [role[0] for role in distinct_roles]
print(f"Found {len(roles)} distinct roles: {', '.join(roles)}")

# Function to get player name from ID with fallback
def get_player_name(player_id):
    """Get player name from ID with fallback to ID if not found"""
    return player_names.get(player_id, f"Player {player_id}")


# if no dota plus = 1850 // or reverse case 
## liquidpedia has the stratifiction for hero numeric level to medal
# Get all match player data in one comprehensive query with player names
print("\n===== Retrieving Match Player Data for Analysis =====")
match_players_data = (
    session.query(
        MatchPlayers.match_id,
        MatchPlayers.steam_account_id,
        MatchPlayers.hero_id,
        MatchPlayers.role,
        MatchPlayers.dota_plus_hero_level,
        MatchPlayers.kills,
        MatchPlayers.deaths,
        MatchPlayers.assists,
        MatchPlayers.hero_damage,
        MatchPlayers.tower_damage,
        MatchPlayers.hero_healing,
        MatchPlayers.gold_per_min,
        MatchPlayers.is_victory,
        Matches.start_date_time,
        TeamPlayers.name.label("player_name")  # Include player name directly
    )
    .join(Matches, MatchPlayers.match_id == Matches.id)
    .join(TeamPlayers, MatchPlayers.steam_account_id == TeamPlayers.steam_account_id, isouter=True)  # Left join to handle missing players
    .filter(
        MatchPlayers.role.isnot(None),
        ## re-write this exception
        ## sub or no sub - you cap at level 5 - check numeric value 
        MatchPlayers.dota_plus_hero_level.isnot(None)
    )
    .order_by(Matches.start_date_time)
    .all()
)

print(f"Retrieved {len(match_players_data)} match player records with hero level data")

# Process match data into role-specific datasets
role_data = {role: [] for role in roles}
hero_data = {}
player_hero_data = {}

for match in match_players_data:
    match_id = match[0]
    player_id = match[1]
    hero_id = match[2]
    role = match[3]
    hero_level = match[4]
    player_name = match[14]  # Get player name from query
    
    # Skip if missing critical data
    if not all([match_id, player_id, hero_id, role, hero_level]):
        continue
    
    # Calculate impact score
    impact_score = calculate_impact_score(match, is_tuple=True)
    
    # Add to role dataset
    if role in role_data:
        role_data[role].append((hero_level, impact_score))
    
    # Add to hero dataset
    if hero_id not in hero_data:
        hero_data[hero_id] = []
    hero_data[hero_id].append((hero_level, impact_score))
    
    # Add to player-hero dataset
    player_hero_key = (player_id, hero_id)
    if player_hero_key not in player_hero_data:
        player_hero_data[player_hero_key] = []
    
    # Update player name if we have it from the query
    if player_name and player_id not in player_names:
        player_names[player_id] = player_name
    elif player_id not in player_names:
        # Try to get it from database if we somehow missed it
        player_name_query = session.query(TeamPlayers.name).filter(TeamPlayers.steam_account_id == player_id).first()
        if player_name_query:
            player_names[player_id] = player_name_query[0]
        else:
            player_names[player_id] = f"Player {player_id}"
    
    # Store with timestamp
    timestamp = match[13]
    player_hero_data[player_hero_key].append((timestamp, hero_level, impact_score, role))


##############################################################
# 3. DESCRIPTIVE STATISTICS
##############################################################

print("\n===== Hero Pick/Ban Analysis =====")

# Most contested heroes
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
print("\n15 Most Contested Heroes (picks + bans):")
for hero, total in most_contested:
    print(f"{hero}: {total}")

# Most picked heroes
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
print("\n15 Most Picked Heroes:")
for hero, count in most_picked:
    print(f"{hero}: {count}")

print("\n===== Player Performance Analysis =====")

# Define the KDA expression
kda_expr = (
    (cast(MatchPlayers.kills, Float) + cast(MatchPlayers.assists, Float))
    /
    case(
        (MatchPlayers.deaths == 0, 1.0),  # No square brackets
        else_=cast(MatchPlayers.deaths, Float)
    )
)


# Top players by KDA
top_players = (
    session.query(
        TeamPlayers.name,
        MatchPlayers.steam_account_id,
        func.avg(kda_expr).label("avg_kda"),
        func.count(MatchPlayers.match_id).label("match_count")
    )
    .join(TeamPlayers, MatchPlayers.steam_account_id == TeamPlayers.steam_account_id)
    .group_by(MatchPlayers.steam_account_id, TeamPlayers.name)
    .having(func.count(MatchPlayers.match_id) >= 5)  # Minimum match count for reliability
    .order_by(func.avg(kda_expr).desc())
    .limit(10)
    .all()
)

print("\nTop 10 Players with Highest Average KDA:")
for player_name, steam_account_id, avg_kda, matches in top_players:
    # Update player_names dictionary with any names we might have missed in the initial query
    if steam_account_id not in player_names:
        player_names[steam_account_id] = player_name
    
    print(f"{player_name} (ID: {steam_account_id}): {avg_kda:.2f} KDA across {matches} matches")

print("\n===== Role-Based Performance Analysis =====")

# Basic role statistics
role_stats = (
    session.query(
        MatchPlayers.role,
        func.count(MatchPlayers.steam_account_id).label("player_count"),
        func.avg(MatchPlayers.kills).label("avg_kills"),
        func.avg(MatchPlayers.deaths).label("avg_deaths"),
        func.avg(MatchPlayers.assists).label("avg_assists"),
        func.avg(MatchPlayers.gold_per_min).label("avg_gpm"),
        func.avg(MatchPlayers.exp_per_min).label("avg_xpm"),
        func.avg(MatchPlayers.hero_damage).label("avg_hero_damage"),
        func.avg(MatchPlayers.tower_damage).label("avg_tower_damage"),
        func.avg(MatchPlayers.hero_healing).label("avg_hero_healing"),
        func.avg(kda_expr).label("avg_kda")
    )
    .filter(MatchPlayers.role.isnot(None))
    .group_by(MatchPlayers.role)
    .all()
)

for stats in role_stats:
    print(f"\nRole: {stats[0]}")
    print(f"  Number of matches: {stats[1]}")
    print(f"  KDA: {stats[10]:.2f} ({stats[2]:.1f}/{stats[3]:.1f}/{stats[4]:.1f})")
    print(f"  Economy: {stats[5]:.1f} GPM, {stats[6]:.1f} XPM")
    print(f"  Impact: {stats[7]:.1f} hero damage, {stats[8]:.1f} tower damage, {stats[9]:.1f} healing")

# Top heroes by role
print("\n===== Top 5 Heroes by Role =====")
for role in roles:
    top_heroes = (
        session.query(
            Heroes.display_name,
            func.count(MatchPlayers.hero_id).label("pick_count"),
            func.avg(kda_expr).label("avg_kda"),
            func.sum(case((MatchPlayers.is_victory == 1, 1), else_=0)).label("wins"),
            func.count(MatchPlayers.match_id).label("matches")
        )
        .join(Heroes, MatchPlayers.hero_id == Heroes.id)
        .filter(MatchPlayers.role == role)
        .group_by(Heroes.id)
        .having(func.count(MatchPlayers.match_id) >= 3)  # Minimum match threshold
        .order_by(desc("pick_count"))
        .limit(5)
        .all()
    )
    
    if top_heroes:
        print(f"\nTop 5 Heroes for {role}:")
        for hero, count, kda, wins, matches in top_heroes:
            win_rate = (wins / matches) * 100 if matches > 0 else 0
            print(f"  {hero}: {count} picks, {kda:.2f} KDA, {win_rate:.1f}% win rate")


##############################################################
# 4. CORRELATION ANALYSIS
##############################################################

print("\n===== Hero Level Correlation with Performance =====")

# Analyze correlation by role
for role, data in role_data.items():
    if len(data) >= 10:  # Ensure enough data for meaningful analysis
        levels = [d[0] for d in data]
        impacts = [d[1] for d in data]
        
        # Only calculate if we have variation in levels
        if len(set(levels)) > 1:
            try:
                corr = stats.pearsonr(levels, impacts)
                print(f"\nRole: {role} - {len(data)} matches")
                print(f"  Hero level range: {min(levels)}-{max(levels)}")
                print(f"  Correlation with performance: r={corr[0]:.3f}, p={corr[1]:.3f}")
                
                # Interpret the correlation
                if corr[1] < 0.05:
                    strength = "strong" if abs(corr[0]) > 0.5 else "moderate" if abs(corr[0]) > 0.3 else "weak"
                    direction = "positive" if corr[0] > 0 else "negative"
                    print(f"  There is a statistically significant {strength} {direction} correlation")
                else:
                    print("  No statistically significant correlation found")
            except Exception as e:
                print(f"  Error calculating correlation: {e}")
        else:
            print(f"\nRole: {role} - Insufficient variation in hero levels")


##############################################################
# 5. ADVANCED STATISTICAL ANALYSIS
##############################################################

print("\n===== Intraclass Correlation Analysis =====")

# Create a lookup of top players for each hero
hero_specialists = {}
for player_hero_key, matches in player_hero_data.items():
    player_id, hero_id = player_hero_key
    if len(matches) >= 5:  # Minimum matches to be considered a specialist
        if hero_id not in hero_specialists:
            hero_specialists[hero_id] = []
        
        # Calculate average impact score for this player-hero combination
        impacts = [m[2] for m in matches]
        avg_impact = np.mean(impacts)
        
        hero_specialists[hero_id].append({
            'player_id': player_id,
            'player_name': get_player_name(player_id),
            'matches': len(matches),
            'avg_impact': avg_impact
        })

# Sort specialists by average impact
for hero_id in hero_specialists:
    hero_specialists[hero_id] = sorted(hero_specialists[hero_id], key=lambda x: x['avg_impact'], reverse=True)

# Analyze hero-specific ICC
for hero_id, data in hero_data.items():
    if len(data) >= 10:  # Need sufficient data
        hero_name = hero_names.get(hero_id, f"Hero {hero_id}")
        levels = [d[0] for d in data]
        impacts = [d[1] for d in data]
        
        # Only calculate if we have multiple hero levels
        if len(set(levels)) >= 2:
            try:
                icc, f_value, p_value = calculate_icc(impacts, levels)
                if icc is not None:
                    print(f"\n{hero_name}:")
                    print(f"  ICC = {icc:.3f}, F = {f_value:.2f}, p = {p_value:.3f}")
                    
                    # Interpret ICC
                    if icc <= 0:
                        reliability = "No consistency"
                    elif icc < 0.5:
                        reliability = "Poor consistency"
                    elif icc < 0.75:
                        reliability = "Moderate consistency"
                    elif icc < 0.9:
                        reliability = "Good consistency"
                    else:
                        reliability = "Excellent consistency"
                    
                    print(f"  Interpretation: {reliability} between hero level and performance")
                    print(f"  Data points: {len(data)}, Hero level range: {min(levels)}-{max(levels)}")
                    
                    # Show top specialists for this hero if available
                    if hero_id in hero_specialists and hero_specialists[hero_id]:
                        top_specialist = hero_specialists[hero_id][0]
                        print(f"  Top specialist: {top_specialist['player_name']} with {top_specialist['matches']} matches")
            except Exception as e:
                print(f"  Error calculating ICC for {hero_name}: {e}")

# Role-specific ICC
for role, data in role_data.items():
    if len(data) >= 20:  # Need substantial data
        levels = [d[0] for d in data]
        impacts = [d[1] for d in data]
        
        if len(set(levels)) >= 2:
            try:
                icc, f_value, p_value = calculate_icc(impacts, levels)
                if icc is not None:
                    significance = "significant" if p_value < 0.05 else "not significant"
                    print(f"\nRole {role}:")
                    print(f"  ICC = {icc:.3f}, F = {f_value:.2f}, p = {p_value:.3f} ({significance})")
                    
                    # Interpret
                    if icc <= 0:
                        print("  No consistency between hero level and performance")
                    elif icc < 0.5:
                        print("  Poor consistency between hero level and performance")
                    elif icc < 0.75:
                        print("  Moderate consistency between hero level and performance")
                    else:
                        print("  Good to excellent consistency between hero level and performance")
                    
                    # Add analysis of players with this role
                    role_players = {}
                    for (player_id, hero_id), matches in player_hero_data.items():
                        if [m[3] for m in matches].count(role) >= 5:  # Played this role at least 5 times
                            if player_id not in role_players:
                                role_players[player_id] = 0
                            role_players[player_id] += len([m for m in matches if m[3] == role])
                    
                    # Show top players for this role
                    if role_players:
                        top_role_players = sorted(role_players.items(), key=lambda x: x[1], reverse=True)[:3]
                        print("  Top specialists in this role:")
                        for player_id, match_count in top_role_players:
                            print(f"    {get_player_name(player_id)}: {match_count} matches")
            except Exception as e:
                print(f"  Error calculating ICC for {role}: {e}")


##############################################################
# 6. TEMPORAL ANALYSIS
##############################################################

print("\n===== Temporal Analysis of Hero Mastery and Performance =====")

# Sort player-hero matches chronologically
for player_hero, matches in player_hero_data.items():
    player_hero_data[player_hero] = sorted(matches, key=lambda x: x[0])

# Analyze player progression
progression_analysis = []
for (player_id, hero_id), matches in player_hero_data.items():
    if len(matches) >= 5:  # Need sufficient matches
        # Extract temporal progression
        times = [m[0] for m in matches]
        levels = [m[1] for m in matches]
        impacts = [m[2] for m in matches]
        role = max(set([m[3] for m in matches]), key=[m[3] for m in matches].count)  # Most common role
        
        # Get player and hero names
        player_name = get_player_name(player_id)
        hero_name = hero_names.get(hero_id, f"Hero {hero_id}")
        
        # Check if hero level changed
        level_changes = len(set(levels)) > 1
        
        if level_changes:
            # Calculate performance changes
            first_impact = np.mean(impacts[:min(3, len(impacts))])
            last_impact = np.mean(impacts[-min(3, len(impacts)):])
            impact_change = ((last_impact - first_impact) / first_impact) * 100 if first_impact > 0 else 0
            
            # Store analysis results
            progression_analysis.append({
                'player_id': player_id,
                'player_name': player_name,
                'hero_id': hero_id,
                'hero_name': hero_name,
                'matches': len(matches),
                'role': role,
                'start_level': levels[0],
                'end_level': levels[-1],
                'level_change': levels[-1] - levels[0],
                'impact_change_pct': impact_change,
                'first_impact': first_impact,
                'last_impact': last_impact,
                'times': times,
                'levels': levels,
                'impacts': impacts
            })

# Report top improvers and decliners
progression_analysis.sort(key=lambda x: x['impact_change_pct'], reverse=True)

print("\nTop 5 Player-Hero Combinations with Greatest Improvement:")
for i, data in enumerate(progression_analysis[:5]):
    print(f"{i+1}. {data['player_name']} playing {data['hero_name']} as {data['role']}:")
    print(f"   Hero level: {data['start_level']} → {data['end_level']}")
    print(f"   Performance change: +{data['impact_change_pct']:.1f}% ({data['first_impact']:.3f} → {data['last_impact']:.3f})")
    print(f"   Matches analyzed: {data['matches']}")

print("\nTop 5 Player-Hero Combinations with Greatest Decline:")
for i, data in enumerate(sorted(progression_analysis, key=lambda x: x['impact_change_pct'])[:5]):
    print(f"{i+1}. {data['player_name']} playing {data['hero_name']} as {data['role']}:")
    print(f"   Hero level: {data['start_level']} → {data['end_level']}")
    print(f"   Performance change: {data['impact_change_pct']:.1f}% ({data['first_impact']:.3f} → {data['last_impact']:.3f})")
    print(f"   Matches analyzed: {data['matches']}")

# Analyze performance trend after level increases
print("\n===== Performance Changes After Hero Level Increases =====")

level_increase_effects = []
for data in progression_analysis:
    # Find points where level increased
    level_changes = [(i, data['levels'][i]) for i in range(1, len(data['levels'])) 
                     if data['levels'][i] > data['levels'][i-1]]
    
    if level_changes:
        for change_idx, new_level in level_changes:
            # Get performance before and after level increase
            before_impacts = data['impacts'][max(0, change_idx-3):change_idx]
            after_impacts = data['impacts'][change_idx:min(len(data['impacts']), change_idx+3)]
            
            if before_impacts and after_impacts:
                before_avg = np.mean(before_impacts)
                after_avg = np.mean(after_impacts)
                pct_change = ((after_avg - before_avg) / before_avg) * 100 if before_avg > 0 else 0
                
                level_increase_effects.append({
                    'player_id': data['player_id'],
                    'player_name': data['player_name'],
                    'hero_id': data['hero_id'],
                    'hero_name': data['hero_name'],
                    'role': data['role'],
                    'old_level': data['levels'][change_idx-1],
                    'new_level': new_level,
                    'before_avg': before_avg,
                    'after_avg': after_avg,
                    'pct_change': pct_change
                })

# Summarize level increase effects by role
if level_increase_effects:
    print("\nMost significant individual level up effects:")
    # Sort by absolute percentage change to find most dramatic effects
    dramatic_effects = sorted(level_increase_effects, key=lambda x: abs(x['pct_change']), reverse=True)[:5]
    for i, effect in enumerate(dramatic_effects):
        print(f"{i+1}. {effect['player_name']} with {effect['hero_name']} (Level {effect['old_level']} → {effect['new_level']}):")
        direction = "increased" if effect['pct_change'] > 0 else "decreased"
        print(f"   Performance {direction} by {abs(effect['pct_change']):.1f}% ({effect['before_avg']:.3f} → {effect['after_avg']:.3f})")
    
    role_effects = {role: [] for role in roles}
    for effect in level_increase_effects:
        if effect['role'] in role_effects:
            role_effects[effect['role']].append(effect['pct_change'])
    
    if role_effects:
        print("\nAverage performance change after level increase by role:")
        for role, changes in role_effects.items():
            if changes:
                avg_change = np.mean(changes)
                count = len(changes)
                print(f"  {role}: {avg_change:.1f}% average change (n={count})")
                
                # Is the change statistically significant?
                if count >= 5:
                    t_stat, p_val = ttest_1samp(changes, 0)
                    sig = "significant" if p_val < 0.05 else "not significant"
                    print(f"    Statistical significance: t={t_stat:.2f}, p={p_val:.3f} ({sig})")

# Learning rate analysis
print("\n===== Learning Curve Analysis by Hero Level =====")

# Calculate learning rates using linear regression
learning_rates = {role: {} for role in roles}

for data in progression_analysis:
    if len(data['times']) >= 8:  # Need enough points for reliable trend
        role = data['role']
        initial_level = data['start_level']
        
        # Normalize times to months
        normalized_times = [(t - data['times'][0]) / (86400 * 30) for t in data['times']]
        
        # Only analyze if we have at least a month of data
        if max(normalized_times) >= 1.0:
            try:
                # Linear regression for learning rate
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    normalized_times, data['impacts']
                )
                
                # Store by role and initial level
                if role in learning_rates:
                    if initial_level not in learning_rates[role]:
                        learning_rates[role][initial_level] = []
                    
                    learning_rates[role][initial_level].append({
                        'slope': slope,
                        'r_value': r_value,
                        'p_value': p_value,
                        'player_id': data['player_id'],
                        'player_name': data['player_name'],
                        'hero_id': data['hero_id'],
                        'hero_name': data['hero_name']
                    })
            except Exception:
                continue

# Analyze learning rates
for role, level_data in learning_rates.items():
    if level_data:
        print(f"\n{role} learning curve analysis:")
        
        # Get average learning rate by level
        for level in sorted(level_data.keys()):
            rates = [r['slope'] for r in level_data[level]]
            if len(rates) >= 3:
                avg_rate = np.mean(rates)
                median_rate = np.median(rates)
                count = len(rates)
                
                sig_count = sum(1 for r in level_data[level] if r['p_value'] < 0.05)
                pos_count = sum(1 for r in level_data[level] if r['slope'] > 0)
                
                print(f"  Starting at Hero Level {level}:")
                print(f"    Average improvement rate: {avg_rate:.4f} impact points/month (n={count})")
                print(f"    Median improvement rate: {median_rate:.4f} impact points/month")
                print(f"    Proportion improving: {pos_count}/{count} ({pos_count/count*100:.1f}%)")
                
                if sig_count > 0:
                    print(f"    Statistically significant trends: {sig_count}/{count} ({sig_count/count*100:.1f}%)")
                    
                    # Show best improver for this level if we have significant trends
                    best_improver = max(level_data[level], key=lambda x: x['slope'] if x['p_value'] < 0.05 else -float('inf'))
                    if best_improver['p_value'] < 0.05:
                        print(f"    Best improver: {best_improver['player_name']} with {best_improver['hero_name']}")
                        print(f"      Rate: {best_improver['slope']:.4f} points/month (r² = {best_improver['r_value']**2:.2f})")
        
        # Compare learning rates between levels
        if len(level_data.keys()) >= 2:
            levels = []
            rates = []
            
            for level, slopes in level_data.items():
                if len(slopes) >= 3:
                    levels.append(level)
                    rates.append(np.mean([r['slope'] for r in slopes]))
            
            if len(levels) >= 2:
                try:
                    corr, p_value = stats.pearsonr(levels, rates)
                    print(f"\n  Correlation between starting hero level and learning rate:")
                    print(f"    r = {corr:.3f}, p = {p_value:.3f}")
                    
                    if p_value < 0.05:
                        if corr > 0:
                            print("    Players with higher hero levels improve more rapidly (significant)")
                        else:
                            print("    Players with lower hero levels improve more rapidly (significant)")
                    else:
                        print("    No significant relationship between hero level and improvement rate")
                except Exception as e:
                    print(f"    Error analyzing learning rate correlation: {e}")


##############################################################
# 7. SUMMARY AND INSIGHTS
##############################################################

print("\n===== ANALYSIS SUMMARY =====")

# Summarize player counts and distribution
player_counts = {}
for (player_id, hero_id), matches in player_hero_data.items():
    if player_id not in player_counts:
        player_counts[player_id] = {
            'total_matches': 0,
            'heroes_played': set(),
            'roles_played': set()
        }
    player_counts[player_id]['total_matches'] += len(matches)
    player_counts[player_id]['heroes_played'].add(hero_id)
    for match in matches:
        player_counts[player_id]['roles_played'].add(match[3])

# Most versatile and specialized players
if player_counts:
    most_matches = max(player_counts.items(), key=lambda x: x[1]['total_matches'])
    most_heroes = max(player_counts.items(), key=lambda x: len(x[1]['heroes_played']))
    most_roles = max(player_counts.items(), key=lambda x: len(x[1]['roles_played']))
    
    print("\nPlayer Statistics:")
    print(f"  Most active player: {get_player_name(most_matches[0])} with {most_matches[1]['total_matches']} matches")
    print(f"  Most versatile player (heroes): {get_player_name(most_heroes[0])} with {len(most_heroes[1]['heroes_played'])} different heroes")
    print(f"  Most versatile player (roles): {get_player_name(most_roles[0])} with {len(most_roles[1]['roles_played'])} different roles")

# Summarize role performance differences
if role_data:
    print("\nRole Performance Metrics:")
    for role in roles:
        if role in role_data and len(role_data[role]) >= 10:
            levels = [d[0] for d in role_data[role]]
            impacts = [d[1] for d in role_data[role]]
            
            # Find correlation
            if len(set(levels)) > 1:
                try:
                    corr, p_val = stats.pearsonr(levels, impacts)
                    significance = "significant" if p_val < 0.05 else "not significant"
                    print(f"  {role}: r = {corr:.3f} (p = {p_val:.3f}, {significance})")
                except:
                    print(f"  {role}: Unable to calculate correlation")

# Summarize heroes with strongest hero level effects
hero_correlations = []
for hero_id, data in hero_data.items():
    if len(data) >= 10 and len(set([d[0] for d in data])) > 1:
        try:
            corr, p_val = stats.pearsonr([d[0] for d in data], [d[1] for d in data])
            if not np.isnan(corr) and not np.isnan(p_val):
                hero_correlations.append((hero_id, corr, p_val))
        except:
            continue

if hero_correlations:
    print("\nHeroes with Strongest Hero Level Effects:")
    significant_heroes = [(h, c, p) for h, c, p in hero_correlations if p < 0.05]
    if significant_heroes:
        for hero_id, corr, p_val in sorted(significant_heroes, key=lambda x: abs(x[1]), reverse=True)[:5]:
            hero_name = hero_names.get(hero_id, f"Hero {hero_id}")
            direction = "positive" if corr > 0 else "negative"
            print(f"  {hero_name}: {direction} correlation (r = {corr:.3f}, p = {p_val:.3f})")
    else:
        print("  No heroes with statistically significant correlations found")

# Final statement about hero mastery
print("\nOverall Hero Mastery Impact:")
role_avg_corrs = {}
for role in roles:
    if role in role_data and len(role_data[role]) >= 10:
        levels = [d[0] for d in role_data[role]]
        impacts = [d[1] for d in role_data[role]]
        
        if len(set(levels)) > 1:
            try:
                corr, _ = stats.pearsonr(levels, impacts)
                role_avg_corrs[role] = corr
            except:
                pass

if role_avg_corrs:
    overall_effect = np.mean(list(role_avg_corrs.values()))
    if overall_effect > 0.1:
        print("  Hero mastery generally shows a positive correlation with performance across roles.")
        print(f"  Average correlation: r = {overall_effect:.3f}")
        strongest_role = max(role_avg_corrs.items(), key=lambda x: x[1])
        print(f"  Strongest effect in {strongest_role[0]} role (r = {strongest_role[1]:.3f})")
    elif overall_effect < -0.1:
        print("  Hero mastery generally shows a negative correlation with performance across roles.")
        print(f"  Average correlation: r = {overall_effect:.3f}")
    else:
        print("  Hero mastery shows minimal overall correlation with performance across roles.")
        print(f"  Average correlation: r = {overall_effect:.3f}")


## one player with top x preferefered heroes 
## denies with XPM 