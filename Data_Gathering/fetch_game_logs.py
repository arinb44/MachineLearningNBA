#!/usr/bin/env python3
"""
NBA Game-by-Game Data Fetcher
Fetches individual player game logs from NBA Stats API
Calculates standard deviations for consistency analysis
"""

import pandas as pd
import requests
import time
import os
from datetime import datetime

class GameLogFetcher:
    def __init__(self):
        self.player_file = 'Input_Data/nba_player_stats_2025-26.csv'
        self.output_file = 'Input_Data/nba_player_stats_with_std_2025-26.csv'
        self.season = '2025-26'
        
        # NBA Stats API headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nba.com/',
            'Origin': 'https://www.nba.com',
        }
        
        self.base_url = 'https://stats.nba.com/stats/playergamelog'
        
    def load_players(self):
        """Load player list from existing file"""
        if not os.path.exists(self.player_file):
            print(f"❌ File not found: {self.player_file}")
            return None
        
        try:
            df = pd.read_csv(self.player_file)
            print(f"✅ Loaded {len(df)} players")
            return df
        except Exception as e:
            print(f"❌ Error loading players: {e}")
            return None
    
    def fetch_player_game_log(self, player_id):
        """Fetch game log for a specific player"""
        params = {
            'PlayerID': player_id,
            'Season': self.season,
            'SeasonType': 'Regular Season',
        }
        
        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'resultSets' in data and len(data['resultSets']) > 0:
                    result_set = data['resultSets'][0]
                    headers = result_set['headers']
                    rows = result_set['rowSet']
                    
                    if rows:
                        df = pd.DataFrame(rows, columns=headers)
                        return df
                    else:
                        return None
            else:
                print(f"  ⚠️ API returned status code: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ❌ Error fetching data: {e}")
            return None
    
    def calculate_standard_deviations(self, game_log_df):
        """Calculate standard deviations from game log"""
        if game_log_df is None or game_log_df.empty:
            return None
        
        stats = {}
        
        # Stats to calculate std for
        stat_columns = {
            'PTS': 'PTS_STD',
            'REB': 'REB_STD',
            'AST': 'AST_STD',
            'STL': 'STL_STD',
            'BLK': 'BLK_STD',
            'FG_PCT': 'FG_PCT_STD',
            'FG3_PCT': 'FG3_PCT_STD',
            'MIN': 'MIN_STD'
        }
        
        for stat, std_name in stat_columns.items():
            if stat in game_log_df.columns:
                # Convert to numeric and calculate std
                values = pd.to_numeric(game_log_df[stat], errors='coerce')
                stats[std_name] = values.std()
            else:
                stats[std_name] = None
        
        # Also return number of games played
        stats['GAMES_LOGGED'] = len(game_log_df)
        
        return stats
    
    def process_all_players(self, players_df, max_players=None):
        """Process all players and add standard deviations"""
        print("\n" + "="*80)
        print("🔄 FETCHING GAME LOGS AND CALCULATING STANDARD DEVIATIONS")
        print("="*80)
        
        # If max_players is set, only process that many (for testing)
        if max_players:
            players_df = players_df.head(max_players)
            print(f"⚠️  TEST MODE: Processing only {max_players} players")
        
        print(f"\n📊 Processing {len(players_df)} players...")
        print("⏱️  This will take a while (rate limiting to avoid API blocks)")
        print("-"*80)
        
        # Add columns for standard deviations
        std_columns = ['PTS_STD', 'REB_STD', 'AST_STD', 'STL_STD', 'BLK_STD', 
                      'FG_PCT_STD', 'FG3_PCT_STD', 'MIN_STD', 'GAMES_LOGGED']
        
        for col in std_columns:
            if col not in players_df.columns:
                players_df[col] = None
        
        success_count = 0
        fail_count = 0
        
        for idx, row in players_df.iterrows():
            player_id = row['PLAYER_ID']
            player_name = row['PLAYER_NAME']
            
            print(f"\n[{idx+1}/{len(players_df)}] {player_name} (ID: {player_id})")
            
            # Fetch game log
            game_log = self.fetch_player_game_log(player_id)
            
            if game_log is not None:
                # Calculate standard deviations
                std_data = self.calculate_standard_deviations(game_log)
                
                if std_data:
                    # Update the dataframe
                    for col, value in std_data.items():
                        players_df.at[idx, col] = value
                    
                    print(f"  ✅ Fetched {std_data['GAMES_LOGGED']} games")
                    print(f"     PTS: {row['PTS']:.1f} ± {std_data['PTS_STD']:.2f}")
                    success_count += 1
                else:
                    print(f"  ⚠️ Could not calculate stats")
                    fail_count += 1
            else:
                print(f"  ❌ Failed to fetch game log")
                fail_count += 1
            
            # Rate limiting - wait between requests
            time.sleep(1.5)  # 1.5 seconds between requests
            
            # Save progress every 20 players
            if (idx + 1) % 20 == 0:
                print(f"\n💾 Saving progress... ({success_count} successful, {fail_count} failed)")
                players_df.to_csv(self.output_file, index=False)
        
        print("\n" + "="*80)
        print(f"✅ Processing complete!")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {fail_count}")
        print("="*80)
        
        return players_df
    
    def save_results(self, df):
        """Save the enhanced dataframe"""
        try:
            df.to_csv(self.output_file, index=False)
            print(f"\n💾 Saved enhanced data to: {self.output_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False
    
    def run(self, test_mode=False):
        """Main execution"""
        print("🏀 NBA Game-by-Game Data Fetcher")
        print("="*80)
        
        # Load players
        players_df = self.load_players()
        if players_df is None:
            return False
        
        # Ask if user wants test mode
        if test_mode:
            max_players = 10
            print(f"\n⚡ RUNNING IN TEST MODE")
            print(f"   Processing only {max_players} players to verify API works")
        else:
            max_players = None
            print(f"\n⚠️  WARNING: This will make {len(players_df)} API requests")
            print("   At 1.5 seconds per request, this will take approximately:")
            print(f"   {len(players_df) * 1.5 / 60:.1f} minutes")
            
            response = input("\n   Continue? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("❌ Cancelled by user")
                return False
        
        # Process all players
        enhanced_df = self.process_all_players(players_df, max_players=max_players)
        
        # Save results
        if self.save_results(enhanced_df):
            print("\n" + "="*80)
            print("✅ SUCCESS!")
            print("="*80)
            print(f"\n📊 Enhanced dataset saved with standard deviations:")
            print(f"   {self.output_file}")
            
            print("\n💡 Now you can run find_consistent_players.py to analyze consistency!")
            print("   It will use the _STD columns to find truly consistent players")
            
            return True
        
        return False

def main():
    import sys
    
    # Check for test flag
    test_mode = '--test' in sys.argv or '-t' in sys.argv
    
    fetcher = GameLogFetcher()
    
    if test_mode:
        print("\n🧪 Test mode enabled (--test flag detected)")
    
    fetcher.run(test_mode=test_mode)

if __name__ == "__main__":
    main()
