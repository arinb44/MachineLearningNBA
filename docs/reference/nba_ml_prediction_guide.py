"""
NBA Game Prediction ML Data Structure Guide
============================================

This guide shows how to structure NBA advanced stats data for machine learning game prediction.
Since we can't fetch live data, this provides the framework and sample data structure.

STEP 1: Data Collection
------------------------
You'll need to collect the following advanced metrics from NBA.com/stats:

OFFENSIVE METRICS:
- OFF_RATING: Points scored per 100 possessions
- TS_PCT: True Shooting Percentage (accounts for 2PT, 3PT, FT)
- EFG_PCT: Effective Field Goal Percentage
- AST_PCT: Percentage of teammate FGs assisted
- AST_RATIO: Assists per 100 possessions
- OREB_PCT: Offensive Rebound Percentage
- USG_PCT: Usage Percentage (% of team plays used)
- PACE: Possessions per 48 minutes

DEFENSIVE METRICS:
- DEF_RATING: Points allowed per 100 possessions (LOWER is better)
- DREB_PCT: Defensive Rebound Percentage
- REB_PCT: Total Rebound Percentage
- STL: Steals per game
- BLK: Blocks per game
- OPP_EFG_PCT: Opponent Effective FG%

OVERALL IMPACT:
- NET_RATING: OFF_RATING - DEF_RATING
- PIE: Player Impact Estimate (0-1 scale)
- PLUS_MINUS: Plus/Minus rating

STEP 2: Data Aggregation by Team
---------------------------------
For each team, calculate aggregate statistics:
"""

import pandas as pd
import numpy as np

# Sample data structure for player stats
sample_player_data = {
    'PLAYER_NAME': ['Player A', 'Player B', 'Player C', 'Player D', 'Player E'],
    'TEAM_ABBREVIATION': ['LAL', 'LAL', 'LAL', 'BOS', 'BOS'],
    'MIN': [35.2, 32.1, 28.5, 34.8, 30.2],
    'OFF_RATING': [118.5, 115.2, 110.8, 120.3, 116.7],
    'DEF_RATING': [108.2, 110.5, 112.3, 106.8, 109.2],
    'NET_RATING': [10.3, 4.7, -1.5, 13.5, 7.5],
    'TS_PCT': [0.625, 0.598, 0.542, 0.638, 0.611],
    'EFG_PCT': [0.587, 0.563, 0.521, 0.612, 0.588],
    'AST_PCT': [35.2, 22.8, 15.3, 38.5, 25.1],
    'OREB_PCT': [3.2, 8.5, 12.3, 2.8, 9.1],
    'DREB_PCT': [18.5, 22.3, 28.7, 19.2, 24.5],
    'REB_PCT': [10.8, 15.4, 20.5, 11.0, 16.8],
    'USG_PCT': [32.1, 28.5, 18.2, 33.5, 26.8],
    'PIE': [0.185, 0.162, 0.121, 0.198, 0.171]
}

df_players = pd.DataFrame(sample_player_data)

# Function to aggregate team statistics
def aggregate_team_stats(player_df, min_minutes=15):
    """
    Aggregate player stats to team level
    
    Args:
        player_df: DataFrame with player statistics
        min_minutes: Minimum minutes played to include player
    
    Returns:
        DataFrame with team-level aggregated stats
    """
    
    # Filter for regular rotation players
    df_filtered = player_df[player_df['MIN'] >= min_minutes].copy()
    
    # Group by team
    team_stats = []
    
    for team in df_filtered['TEAM_ABBREVIATION'].unique():
        team_df = df_filtered[df_filtered['TEAM_ABBREVIATION'] == team]
        
        team_record = {'team': team}
        
        # Offensive aggregations
        offensive_metrics = ['OFF_RATING', 'TS_PCT', 'EFG_PCT', 'AST_PCT', 'OREB_PCT', 'USG_PCT']
        for metric in offensive_metrics:
            if metric in team_df.columns:
                team_record[f'off_{metric.lower()}_mean'] = team_df[metric].mean()
                team_record[f'off_{metric.lower()}_weighted'] = (
                    (team_df[metric] * team_df['MIN']).sum() / team_df['MIN'].sum()
                )
                team_record[f'off_{metric.lower()}_std'] = team_df[metric].std()
                team_record[f'off_{metric.lower()}_max'] = team_df[metric].max()
        
        # Defensive aggregations
        defensive_metrics = ['DEF_RATING', 'DREB_PCT', 'REB_PCT']
        for metric in defensive_metrics:
            if metric in team_df.columns:
                team_record[f'def_{metric.lower()}_mean'] = team_df[metric].mean()
                team_record[f'def_{metric.lower()}_weighted'] = (
                    (team_df[metric] * team_df['MIN']).sum() / team_df['MIN'].sum()
                )
                team_record[f'def_{metric.lower()}_std'] = team_df[metric].std()
                # For DEF_RATING, lower is better
                if metric == 'DEF_RATING':
                    team_record[f'def_{metric.lower()}_min'] = team_df[metric].min()
                else:
                    team_record[f'def_{metric.lower()}_max'] = team_df[metric].max()
        
        # Overall metrics
        team_record['net_rating_mean'] = team_df['NET_RATING'].mean()
        team_record['net_rating_weighted'] = (
            (team_df['NET_RATING'] * team_df['MIN']).sum() / team_df['MIN'].sum()
        )
        team_record['pie_mean'] = team_df['PIE'].mean()
        team_record['pie_sum'] = team_df['PIE'].sum()
        
        # Team depth (number of quality players)
        team_record['rotation_size'] = len(team_df)
        team_record['star_power'] = team_df['PIE'].nlargest(3).mean()
        
        team_stats.append(team_record)
    
    return pd.DataFrame(team_stats)

# Aggregate the sample data
team_stats_df = aggregate_team_stats(df_players)
print("\nSAMPLE TEAM AGGREGATED STATS:")
print("="*80)
print(team_stats_df.to_string(index=False))

# STEP 3: Create matchup features for ML model
def create_matchup_features(team_stats_df):
    """
    Create features for each possible game matchup
    
    Returns:
        DataFrame where each row represents a potential game with home/away features
    """
    
    matchups = []
    teams = team_stats_df['team'].tolist()
    
    for home_team in teams:
        for away_team in teams:
            if home_team != away_team:
                home_stats = team_stats_df[team_stats_df['team'] == home_team].iloc[0]
                away_stats = team_stats_df[team_stats_df['team'] == away_team].iloc[0]
                
                matchup = {
                    'home_team': home_team,
                    'away_team': away_team,
                }
                
                # Add raw home and away stats
                for col in team_stats_df.columns:
                    if col != 'team':
                        matchup[f'home_{col}'] = home_stats[col]
                        matchup[f'away_{col}'] = away_stats[col]
                
                # CRITICAL: Create differential features
                # These are often the most predictive features
                
                # Offensive vs Defensive matchups
                matchup['home_off_vs_away_def'] = (
                    home_stats.get('off_off_rating_weighted', 0) - 
                    away_stats.get('def_def_rating_weighted', 0)
                )
                
                matchup['away_off_vs_home_def'] = (
                    away_stats.get('off_off_rating_weighted', 0) - 
                    home_stats.get('def_def_rating_weighted', 0)
                )
                
                matchup['net_rating_differential'] = (
                    home_stats.get('net_rating_weighted', 0) - 
                    away_stats.get('net_rating_weighted', 0)
                )
                
                # Shooting efficiency differentials
                matchup['ts_pct_differential'] = (
                    home_stats.get('off_ts_pct_weighted', 0) - 
                    away_stats.get('off_ts_pct_weighted', 0)
                )
                
                # Rebounding battle
                matchup['rebounding_advantage'] = (
                    home_stats.get('def_reb_pct_weighted', 0) - 
                    away_stats.get('def_reb_pct_weighted', 0)
                )
                
                # Star power differential
                matchup['star_power_differential'] = (
                    home_stats.get('star_power', 0) - 
                    away_stats.get('star_power', 0)
                )
                
                # Home court advantage (you can add a constant or use historical data)
                matchup['home_court_advantage'] = 1  # Binary indicator
                
                matchups.append(matchup)
    
    return pd.DataFrame(matchups)

matchup_df = create_matchup_features(team_stats_df)
print("\n\nSAMPLE MATCHUP FEATURES:")
print("="*80)
print(matchup_df[['home_team', 'away_team', 'home_off_vs_away_def', 
                   'net_rating_differential', 'star_power_differential']].to_string(index=False))

# STEP 4: ML Model Feature Recommendations
print("\n\nML MODEL FEATURE RECOMMENDATIONS:")
print("="*80)

feature_recommendations = """
TIER 1 FEATURES (Most Predictive):
- net_rating_differential: Overall team quality gap
- home_off_vs_away_def: Home team offense vs away defense
- away_off_vs_home_def: Away team offense vs home defense
- home_court_advantage: Historical ~2.5 point advantage

TIER 2 FEATURES (Strong Predictors):
- ts_pct_differential: Shooting efficiency gap
- def_rating differential: Defensive quality gap
- star_power_differential: Top player quality gap
- rebounding_advantage: Rebounding battle

TIER 3 FEATURES (Supporting Context):
- rotation_size: Team depth
- off_ast_pct: Ball movement quality
- pace differential: Game speed preference
- Recent form (last 10 games) - add if available

FEATURE ENGINEERING IDEAS:
1. Four Factors differentials:
   - Shooting (TS%)
   - Turnovers (if available)
   - Rebounding (OREB%, DREB%)
   - Free throws (FT rate if available)

2. Tempo matchups:
   - Fast pace team vs slow pace team dynamics

3. Style matchups:
   - High usage stars vs defensive rating
   - Ball movement (AST%) vs defensive schemes

4. Recent performance:
   - Last 5 games weighted average
   - Back-to-back games indicator
   - Rest days

5. Interaction features:
   - home_off_rating * away_def_rating_weakness
   - star_power * usage_pct

TARGET VARIABLE:
- Point differential (for regression)
- Win/Loss (for classification)
- Over/Under total points (for totals betting)

SUGGESTED ML MODELS:
1. Gradient Boosting (XGBoost, LightGBM) - Best for tabular data
2. Random Forest - Good baseline
3. Linear Regression with polynomial features - Interpretable
4. Neural Networks - For complex interactions

VALIDATION STRATEGY:
- Time-based split (train on past games, test on future)
- Cross-validation within seasons
- Separate validation for playoff games
"""

print(feature_recommendations)

# Save sample datasets
df_players.to_csv('/mnt/user-data/outputs/sample_player_stats.csv', index=False)
team_stats_df.to_csv('/mnt/user-data/outputs/sample_team_stats.csv', index=False)
matchup_df.to_csv('/mnt/user-data/outputs/sample_matchup_features.csv', index=False)

print("\n\nSAVED FILES:")
print("="*80)
print("✓ sample_player_stats.csv - Individual player advanced metrics")
print("✓ sample_team_stats.csv - Aggregated team offensive/defensive stats")
print("✓ sample_matchup_features.csv - Game-level features for ML prediction")

print("\n\nNEXT STEPS:")
print("="*80)
print("""
1. Collect actual NBA data from NBA.com/stats using their API or web scraping
2. Run the aggregation functions on the full dataset
3. Add historical game results as your target variable
4. Engineer additional features based on team matchups
5. Train your ML model using gradient boosting or neural networks
6. Validate using time-based splits to avoid lookahead bias
7. Consider adding:
   - Injury reports
   - Rest days between games
   - Travel distance
   - Recent form (rolling averages)
   - Head-to-head history
""")
