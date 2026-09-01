"""
Fetch NBA game results for a season and save them to the tracking CSV.

Usage:
    python scripts/fetch_game_results.py [--season 2025-26]
"""

import argparse
import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder

import config


def fetch_games(season):
    gamefinder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        league_id_nullable='00',  # NBA
        season_type_nullable='Regular Season',
    )
    return gamefinder.get_data_frames()[0]


def to_results(games):
    """Each game appears twice (once per team) — collapse to one row per game."""
    game_results = []
    for game_id in games['GAME_ID'].unique():
        game_data = games[games['GAME_ID'] == game_id]
        if len(game_data) != 2:
            continue
        away_row = game_data[game_data['MATCHUP'].str.contains('@')]
        home_row = game_data[~game_data['MATCHUP'].str.contains('@')]
        if len(away_row) == 1 and len(home_row) == 1:
            game_results.append({
                'game_id': game_id,
                'date': home_row['GAME_DATE'].iloc[0],
                'home_team': home_row['TEAM_ABBREVIATION'].iloc[0],
                'away_team': away_row['TEAM_ABBREVIATION'].iloc[0],
                'home_score': int(home_row['PTS'].iloc[0]),
                'away_score': int(away_row['PTS'].iloc[0]),
                'home_win': 1 if home_row['WL'].iloc[0] == 'W' else 0,
            })
    return pd.DataFrame(game_results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    config.add_season_arg(parser)
    args = parser.parse_args()

    print(f"Fetching {args.season} NBA season game data (30-60 seconds)...\n")
    try:
        games = fetch_games(args.season)
        print(f"Fetched {len(games)} game records (both teams per game)")

        results_df = to_results(games)
        if results_df.empty:
            print(f"\nNo games found for the {args.season} season yet.")
            return

        results_df = results_df.sort_values('date')
        output_file = config.game_results_file(args.season)
        results_df.to_csv(output_file, index=False)

        print(f"\nProcessed {len(results_df)} unique games")
        print(f"Date range: {results_df['date'].min()} to {results_df['date'].max()}")
        print(f"Saved to: {output_file}")
    except Exception as e:
        print(f"\nError fetching data: {e}")
        print("\nTroubleshooting:")
        print("1. pip install nba_api")
        print("2. Check your internet connection")
        print(f"3. The {args.season} season may not have started yet")
        print("4. Try again in a few seconds (NBA API rate limiting)")


if __name__ == '__main__':
    main()
