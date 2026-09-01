#!/usr/bin/env python3
"""
NBA Consistency Finder
Identifies the most consistent players (lowest standard deviations) in various stats
Requirements: Players must average at least 20 minutes per game
"""

import pandas as pd
import os

class ConsistencyFinder:
    def __init__(self):
        self.data_file = 'data/input/nba_player_stats_with_std_2025-26.csv'
        self.fallback_file = 'data/input/nba_player_stats_2025-26.csv'
        self.game_log_file = 'data/input/nba_game_logs_2025-26.csv'  # Optional
        self.min_minutes = 20
        
    def load_data(self):
        """Load NBA player statistics"""
        # Try enhanced file first (with standard deviations)
        if os.path.exists(self.data_file):
            try:
                df = pd.read_csv(self.data_file)
                print(f"✅ Loaded {len(df)} players (with standard deviations)")
                return df
            except Exception as e:
                print(f"❌ Error loading enhanced file: {e}")
        
        # Fallback to basic file
        if os.path.exists(self.fallback_file):
            try:
                df = pd.read_csv(self.fallback_file)
                print(f"✅ Loaded {len(df)} players (without standard deviations)")
                print(f"⚠️  Run fetch_game_logs.py first to get standard deviations!")
                return df
            except Exception as e:
                print(f"❌ Error loading fallback file: {e}")
        
        print(f"❌ No data files found")
        return None
    
    def filter_players(self, df):
        """Filter players who average at least 20 minutes per game"""
        filtered = df[df['MIN'] >= self.min_minutes].copy()
        print(f"📊 {len(filtered)} players average {self.min_minutes}+ minutes per game")
        return filtered
    
    def find_most_consistent(self, df, stat_name, std_col, top_n=10):
        """Find players with lowest standard deviation in a stat"""
        # Sort by standard deviation (ascending = most consistent)
        consistent = df.nsmallest(top_n, std_col)
        
        return consistent[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', stat_name, std_col]]
    
    def generate_report(self, df):
        """Generate comprehensive consistency report"""
        print("\n" + "="*80)
        print("🎯 NBA CONSISTENCY REPORT - MOST RELIABLE PLAYERS")
        print("="*80)
        print(f"Minimum: {self.min_minutes} minutes per game")
        print(f"Sample: {len(df)} qualified players")
        print("="*80)
        
        # Define stats to analyze
        stats = [
            ('Points', 'PTS', 'PTS_STD'),
            ('Rebounds', 'REB', 'REB_STD'),
            ('Assists', 'AST', 'AST_STD'),
            ('Blocks', 'BLK', 'BLK_STD'),
            ('Steals', 'STL', 'STL_STD')
        ]
        
        results = {}
        
        for stat_label, stat_col, std_col in stats:
            print(f"\n📈 MOST CONSISTENT IN {stat_label.upper()}")
            print("-"*80)
            
            # Check if columns exist
            if stat_col not in df.columns or std_col not in df.columns:
                print(f"⚠️  Column not found: {stat_col} or {std_col}")
                print(f"Available columns: {', '.join(df.columns[:20])}...")
                continue
            
            # Find most consistent players
            top_players = self.find_most_consistent(df, stat_col, std_col, top_n=10)
            results[stat_label] = top_players
            
            # Display results
            print(f"{'Rank':<6}{'Player':<25}{'Team':<6}{'MPG':<7}{stat_label:<8}{'Std Dev':<10}")
            print("-"*80)
            
            for idx, (i, row) in enumerate(top_players.iterrows(), 1):
                print(f"{idx:<6}{row['PLAYER_NAME']:<25}{row['TEAM_ABBREVIATION']:<6}"
                      f"{row['MIN']:<7.1f}{row[stat_col]:<8.1f}{row[std_col]:<10.2f}")
        
        return results
    
    def save_results(self, results):
        """Save results to CSV files"""
        output_dir = "data/output"
        os.makedirs(output_dir, exist_ok=True)
        
        for stat_name, df in results.items():
            filename = f"{output_dir}/most_consistent_{stat_name.lower()}.csv"
            df.to_csv(filename, index=False)
            print(f"💾 Saved: {filename}")
    
    def create_summary(self, df, results):
        """Create an overall consistency summary"""
        print("\n" + "="*80)
        print("🏆 OVERALL CONSISTENCY LEADERS")
        print("="*80)
        print("Players who appear in multiple consistency categories:\n")
        
        # Count appearances in top 10
        all_players = []
        for stat_name, stat_df in results.items():
            all_players.extend(stat_df['PLAYER_NAME'].tolist())
        
        # Find players who appear multiple times
        from collections import Counter
        player_counts = Counter(all_players)
        multi_category = {player: count for player, count in player_counts.items() if count > 1}
        
        if multi_category:
            sorted_players = sorted(multi_category.items(), key=lambda x: x[1], reverse=True)
            
            print(f"{'Player':<30}{'Categories':<15}{'Teams'}")
            print("-"*80)
            
            for player, count in sorted_players:
                # Get player's team
                team = df[df['PLAYER_NAME'] == player]['TEAM_ABBREVIATION'].iloc[0]
                categories = []
                
                for stat_name, stat_df in results.items():
                    if player in stat_df['PLAYER_NAME'].values:
                        categories.append(stat_name)
                
                print(f"{player:<30}{count} ({', '.join(categories):<25}){team}")
        else:
            print("No players appear in multiple top-10 consistency categories")
    
    def run(self):
        """Main execution"""
        print("🎯 NBA Player Consistency Analyzer")
        print("Finding the most consistent players (lowest standard deviations)")
        print("="*80)
        
        # Load data
        df = self.load_data()
        if df is None:
            return False
        
        # Filter players
        filtered_df = self.filter_players(df)
        if filtered_df.empty:
            print("❌ No players meet the criteria")
            return False
        
        # Generate report
        results = self.generate_report(filtered_df)
        
        if not results:
            print("\n❌ No results generated")
            print("\n💡 Available columns in your data:")
            print(df.columns.tolist())
            return False
        
        # Create summary
        self.create_summary(filtered_df, results)
        
        # Save results
        print("\n" + "="*80)
        print("💾 SAVING RESULTS")
        print("="*80)
        self.save_results(results)
        
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE!")
        print("="*80)
        print("\n📊 Use these consistent players for:")
        print("   • DFS lineups (predictable production)")
        print("   • Fantasy basketball (reliable weekly output)")
        print("   • Game modeling (stable performance metrics)")
        
        return True

def main():
    finder = ConsistencyFinder()
    finder.run()

if __name__ == "__main__":
    main()