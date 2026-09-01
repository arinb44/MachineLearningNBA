"""
Merge Vegas point spreads into the game-results file so track_accuracy.py
can compare the model against the closing line.

Input: a CSV with columns
    date, home_team, away_team, home_spread
where home_spread is the standard spread for the home team
(negative = home favored, e.g. -6.5 means home favored by 6.5).

Historical spread data sources (download, then reshape to the format above):
    - sportsbookreviewsonline.com (free season workbooks)
    - Kaggle NBA odds datasets
    - the-odds-api.com (API, free tier)

Usage:
    python scripts/merge_vegas_lines.py path/to/odds.csv [--season 2025-26]
"""

import argparse
import pandas as pd

import config

REQUIRED_COLUMNS = {'date', 'home_team', 'away_team', 'home_spread'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('odds_csv', help='CSV with date,home_team,away_team,home_spread')
    config.add_season_arg(parser)
    args = parser.parse_args()

    odds = pd.read_csv(args.odds_csv)
    missing = REQUIRED_COLUMNS - set(odds.columns)
    if missing:
        print(f"Odds CSV is missing columns: {sorted(missing)}")
        print("   Expected: date, home_team, away_team, home_spread")
        return

    odds = odds[list(REQUIRED_COLUMNS)].copy()
    odds['date'] = pd.to_datetime(odds['date']).dt.strftime('%Y-%m-%d')
    # A -6.5 home spread means Vegas expects the home team to win by 6.5
    odds['vegas_home_margin'] = -odds['home_spread']
    odds = odds.drop(columns=['home_spread'])

    results_file = config.game_results_file(args.season)
    results = pd.read_csv(results_file)
    results['date'] = pd.to_datetime(results['date']).dt.strftime('%Y-%m-%d')
    before = results.get('vegas_home_margin')
    already = int(before.notna().sum()) if before is not None else 0
    results = results.drop(columns=['vegas_home_margin'], errors='ignore')

    merged = results.merge(odds, on=['date', 'home_team', 'away_team'], how='left')
    matched = int(merged['vegas_home_margin'].notna().sum())

    merged.to_csv(results_file, index=False)
    print(f"Merged lines for {matched}/{len(merged)} games "
          f"(was {already}) → {results_file}")
    if matched < len(odds):
        print(f"{len(odds) - matched} odds rows didn't match any game — "
              f"check team abbreviations and dates")
    print("\nRun scripts/track_accuracy.py to see model vs Vegas.")


if __name__ == '__main__':
    main()
