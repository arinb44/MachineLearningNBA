"""
Fetch NBA game results for 2025-26 season
This script downloads all completed games and saves them to a CSV file
"""

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder
from datetime import datetime
import time

print("Fetching 2025-26 NBA season game data...")
print("This may take 30-60 seconds...\n")

try:
    # Fetch all games from the 2025-26 season
    # Season format: '2025-26' for the 2025-26 season
    gamefinder = leaguegamefinder.LeagueGameFinder(
        season_nullable='2025-26',
        league_id_nullable='00',  # NBA
        season_type_nullable='Regular Season'
    )
    
    games = gamefinder.get_data_frames()[0]
    print(f"✓ Fetched {len(games)} game records (includes both teams for each game)")
    
    # Each game appears twice (once for each team), so we need to deduplicate
    # Group by GAME_ID and process
    game_results = []
    
    processed_games = set()
    
    for game_id in games['GAME_ID'].unique():
        if game_id in processed_games:
            continue
            
        game_data = games[games['GAME_ID'] == game_id]
        
        if len(game_data) == 2:  # Should have exactly 2 rows (home and away)
            # Identify home and away teams
            # The team with '@' in MATCHUP is the away team
            away_row = game_data[game_data['MATCHUP'].str.contains('@')]
            home_row = game_data[~game_data['MATCHUP'].str.contains('@')]
            
            if len(away_row) == 1 and len(home_row) == 1:
                game_result = {
                    'game_id': game_id,
                    'date': home_row['GAME_DATE'].iloc[0],
                    'home_team': home_row['TEAM_ABBREVIATION'].iloc[0],
                    'away_team': away_row['TEAM_ABBREVIATION'].iloc[0],
                    'home_score': int(home_row['PTS'].iloc[0]),
                    'away_score': int(away_row['PTS'].iloc[0]),
                    'home_win': 1 if home_row['WL'].iloc[0] == 'W' else 0,
                }
                game_results.append(game_result)
                processed_games.add(game_id)
    
    # Create DataFrame
    results_df = pd.DataFrame(game_results)
    
    if len(results_df) == 0:
        print("\n⚠️  No games found for 2025-26 season yet.")
        print("The season may not have started or games haven't been played yet.")
        print("Check back after games have been played!")
    else:
        # Sort by date
        results_df = results_df.sort_values('date')
        
        # Save to CSV
        output_file = 'data/tracking/nba_game_results_2025-26.csv'
        results_df.to_csv(output_file, index=False)
        
        print(f"\n✓ Processed {len(results_df)} unique games")
        print(f"✓ Date range: {results_df['date'].min()} to {results_df['date'].max()}")
        print(f"✓ Saved to: {output_file}")
        
        # Show some stats
        print("\n" + "="*60)
        print("SAMPLE DATA (first 5 games):")
        print("="*60)
        print(results_df.head().to_string(index=False))
        
        print("\n" + "="*60)
        print("WINS BY TEAM (Home Games Only):")
        print("="*60)
        home_wins = results_df.groupby('home_team')['home_win'].agg(['sum', 'count'])
        home_wins.columns = ['Wins', 'Games']
        home_wins['Win%'] = (home_wins['Wins'] / home_wins['Games'] * 100).round(1)
        home_wins = home_wins.sort_values('Win%', ascending=False)
        print(home_wins.head(10))

except Exception as e:
    print(f"\n❌ Error fetching data: {e}")
    print("\nTroubleshooting tips:")
    print("1. Make sure nba_api is installed: pip install nba_api")
    print("2. Check your internet connection")
    print("3. The 2025-26 season may not have started yet")
    print("4. Try running again in a few seconds (NBA API rate limiting)")

print("\n✓ Script complete!")
