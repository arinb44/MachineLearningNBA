"""
Fetch NBA player stats for a season (--season, default from config.py)
This script downloads all player statistics and saves them to a CSV file
"""

import argparse
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats

import config

parser = argparse.ArgumentParser(description=__doc__)
config.add_season_arg(parser)
args = parser.parse_args()

print(f"Fetching {args.season} NBA season player statistics...")
print("This may take 30-60 seconds...\n")

try:
    player_stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=args.season,
        season_type_all_star='Regular Season',
        per_mode_detailed='PerGame',
        measure_type_detailed_defense='Base'
    )

    # Get the data
    df = player_stats.get_data_frames()[0]

    print(f"Fetched stats for {len(df)} players")

    # Filter for players with at least 1 game played
    df = df[df['GP'] > 0]

    print(f"Filtered to {len(df)} players with games played")

    # Select and rename relevant columns
    columns_to_keep = {
        'PLAYER_ID': 'PLAYER_ID',
        'PLAYER_NAME': 'PLAYER_NAME',
        'TEAM_ID': 'TEAM_ID',
        'TEAM_ABBREVIATION': 'TEAM_ABBREVIATION',
        'AGE': 'AGE',
        'GP': 'GP',
        'W': 'W',
        'L': 'L',
        'W_PCT': 'W_PCT',
        'MIN': 'MIN',
        'FGM': 'FGM',
        'FGA': 'FGA',
        'FG_PCT': 'FG_PCT',
        'FG3M': 'FG3M',
        'FG3A': 'FG3A',
        'FG3_PCT': 'FG3_PCT',
        'FTM': 'FTM',
        'FTA': 'FTA',
        'FT_PCT': 'FT_PCT',
        'OREB': 'OREB',
        'DREB': 'DREB',
        'REB': 'REB',
        'AST': 'AST',
        'TOV': 'TOV',
        'STL': 'STL',
        'BLK': 'BLK',
        'BLKA': 'BLKA',
        'PF': 'PF',
        'PFD': 'PFD',
        'PTS': 'PTS',
        'PLUS_MINUS': 'PLUS_MINUS',
    }

    # Keep only columns that exist in the dataframe
    columns_present = {k: v for k, v in columns_to_keep.items() if k in df.columns}
    df_filtered = df[list(columns_present.keys())].copy()
    df_filtered.columns = list(columns_present.values())

    # Now fetch advanced stats
    print("\nFetching advanced statistics...")

    advanced_stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=args.season,
        season_type_all_star='Regular Season',
        per_mode_detailed='PerGame',
        measure_type_detailed_defense='Advanced'
    )

    df_advanced = advanced_stats.get_data_frames()[0]
    print(f"Fetched advanced stats for {len(df_advanced)} players")

    # Select advanced metrics we need
    advanced_columns = {
        'PLAYER_ID': 'PLAYER_ID',
        'OFF_RATING': 'OFF_RATING',
        'DEF_RATING': 'DEF_RATING',
        'NET_RATING': 'NET_RATING',
        'AST_PCT': 'AST_PCT',
        'AST_RATIO': 'AST_RATIO',
        'OREB_PCT': 'OREB_PCT',
        'DREB_PCT': 'DREB_PCT',
        'REB_PCT': 'REB_PCT',
        'TM_TOV_PCT': 'TM_TOV_PCT',
        'EFG_PCT': 'EFG_PCT',
        'TS_PCT': 'TS_PCT',
        'USG_PCT': 'USG_PCT',
        'PACE': 'PACE',
        'PIE': 'PIE',
    }

    # Keep only columns that exist
    advanced_present = {k: v for k, v in advanced_columns.items() if k in df_advanced.columns}
    df_advanced_filtered = df_advanced[list(advanced_present.keys())].copy()
    df_advanced_filtered.columns = list(advanced_present.values())

    # Merge basic and advanced stats
    df_final = df_filtered.merge(df_advanced_filtered, on='PLAYER_ID', how='left')

    # Sort by points per game
    df_final = df_final.sort_values('PTS', ascending=False)

    # Save to CSV
    output_file = config.player_stats_file(args.season)
    df_final.to_csv(output_file, index=False)

    print(f"\nMerged {len(df_final)} player records")
    print(f"Saved to: {output_file}")

    # Show some stats
    print("\n" + "="*80)
    print("TOP 10 SCORERS (PPG):")
    print("="*80)
    top_scorers = df_final[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', 'PTS', 'REB', 'AST']].head(10)
    print(top_scorers.to_string(index=False))

    print("\n" + "="*80)
    print("PLAYERS BY TEAM:")
    print("="*80)
    team_counts = df_final['TEAM_ABBREVIATION'].value_counts().sort_index()
    print(team_counts)

    print("\n" + "="*80)
    print("DATASET SUMMARY:")
    print("="*80)
    print(f"Total Players: {len(df_final)}")
    print(f"Total Teams: {df_final['TEAM_ABBREVIATION'].nunique()}")
    print(f"Columns: {len(df_final.columns)}")
    print(f"Average PPG: {df_final['PTS'].mean():.1f}")
    print(f"Average MIN: {df_final['MIN'].mean():.1f}")

except Exception as e:
    print(f"\nError fetching data: {e}")
    print("\nTroubleshooting tips:")
    print("1. Make sure nba_api is installed: pip install nba_api")
    print("2. Check your internet connection")
    print("3. The season may not have started yet")
    print("4. Try running again in a few seconds (NBA API rate limiting)")
    import traceback
    print("\nFull error:")
    traceback.print_exc()

print("\nScript complete!")
