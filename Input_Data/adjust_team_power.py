#!/usr/bin/env python3
"""
Team Power Adjuster
Adjusts team power rankings based on:
- Starting lineups
- Injured players
- Player availability
"""

import pandas as pd
import os

class PowerAdjuster:
    def __init__(self):
        self.player_stats_file = 'Input_Data/nba_player_stats_2025-26.csv'
        self.adjustments_file = 'Input_Data/team_power_adjustments.csv'
        self.output_file = 'Input_Data/adjusted_team_rankings.csv'
    
    def load_data(self):
        """Load player stats and adjustment data"""
        print("📂 Loading data...")
        
        # Load player stats
        if not os.path.exists(self.player_stats_file):
            print(f"❌ Player stats not found: {self.player_stats_file}")
            return None, None
        
        player_stats = pd.read_csv(self.player_stats_file)
        print(f"✅ Loaded {len(player_stats)} players")
        
        # Load adjustments (if available)
        adjustments = None
        if os.path.exists(self.adjustments_file):
            adjustments = pd.read_csv(self.adjustments_file)
            print(f"✅ Loaded adjustments for {len(adjustments)} teams")
        else:
            print(f"⚠️  No adjustments file found")
            print(f"   Run fetch_lineups.py first")
        
        return player_stats, adjustments
    
    def calculate_base_team_strength(self, player_stats):
        """Calculate baseline team strength from player stats"""
        print("\n📊 Calculating base team strength...")
        
        team_strength = []
        
        for team in player_stats['TEAM_ABBREVIATION'].unique():
            team_players = player_stats[player_stats['TEAM_ABBREVIATION'] == team]
            
            # Get top 8 rotation players (20+ mins)
            rotation = team_players[team_players['MIN'] >= 20.0]
            
            if len(rotation) == 0:
                rotation = team_players.nlargest(8, 'MIN')
            
            # Calculate team metrics
            metrics = {
                'team': team,
                'roster_size': len(team_players),
                'rotation_players': len(rotation),
                
                # Offensive strength
                'avg_offensive_rating': rotation['OFF_RATING'].mean(),
                'avg_ts_pct': rotation['TS_PCT'].mean(),
                'total_ppg': rotation['PTS'].sum(),
                
                # Defensive strength
                'avg_defensive_rating': rotation['DEF_RATING'].mean(),
                
                # Overall strength
                'avg_net_rating': rotation['NET_RATING'].mean(),
                'total_pie': rotation['PIE'].sum(),
                
                # Star power (top 3 players)
                'star_power': rotation.nlargest(3, 'PIE')['PIE'].mean(),
            }
            
            team_strength.append(metrics)
        
        df = pd.DataFrame(team_strength)
        
        # Calculate composite power rating (0-100 scale)
        df['power_rating'] = (
            (df['avg_net_rating'] - df['avg_net_rating'].min()) / 
            (df['avg_net_rating'].max() - df['avg_net_rating'].min()) * 40 +
            (df['total_pie'] / df['total_pie'].max()) * 40 +
            (df['star_power'] / df['star_power'].max()) * 20
        )
        
        return df.sort_values('power_rating', ascending=False)
    
    def apply_adjustments(self, base_rankings, adjustments):
        """Apply injury/lineup adjustments to base rankings"""
        if adjustments is None:
            return base_rankings
        
        print("\n🔧 Applying lineup adjustments...")
        
        adjusted = base_rankings.merge(
            adjustments[['team', 'adjustment_pct', 'injured_count', 'injury_impact']], 
            on='team', 
            how='left'
        )
        
        # Fill NaN values for teams without adjustments
        adjusted['adjustment_pct'].fillna(100, inplace=True)
        adjusted['injured_count'].fillna(0, inplace=True)
        adjusted['injury_impact'].fillna(0, inplace=True)
        
        # Apply adjustment to power rating
        adjusted['adjusted_power_rating'] = (
            adjusted['power_rating'] * (adjusted['adjustment_pct'] / 100)
        )
        
        # Re-sort by adjusted rating
        adjusted = adjusted.sort_values('adjusted_power_rating', ascending=False)
        
        return adjusted
    
    def display_rankings(self, rankings):
        """Display the rankings in a nice format"""
        print("\n" + "="*100)
        print("🏆 NBA TEAM POWER RANKINGS")
        print("="*100)
        
        if 'adjusted_power_rating' in rankings.columns:
            print("✅ Including injury/lineup adjustments")
            display_cols = ['team', 'power_rating', 'adjusted_power_rating', 
                          'adjustment_pct', 'injured_count', 'star_power', 
                          'avg_net_rating']
        else:
            print("⚠️  No adjustments applied (baseline rankings)")
            display_cols = ['team', 'power_rating', 'star_power', 
                          'avg_net_rating', 'total_ppg']
        
        print("\n" + "-"*100)
        
        for idx, row in rankings.iterrows():
            rank = list(rankings.index).index(idx) + 1
            team = row['team']
            base_power = row['power_rating']
            
            if 'adjusted_power_rating' in row:
                adj_power = row['adjusted_power_rating']
                adj_pct = row['adjustment_pct']
                injured = int(row['injured_count'])
                
                status = "🟢" if adj_pct >= 95 else "🟡" if adj_pct >= 85 else "🔴"
                
                print(f"{rank:2d}. {status} {team:4s} | "
                      f"Base: {base_power:5.1f} → Adjusted: {adj_power:5.1f} "
                      f"({adj_pct:5.1f}%) | "
                      f"Injured: {injured} | "
                      f"Star: {row['star_power']:.2f} | "
                      f"Net: {row['avg_net_rating']:+.1f}")
            else:
                print(f"{rank:2d}. {team:4s} | "
                      f"Power: {base_power:5.1f} | "
                      f"Star: {row['star_power']:.2f} | "
                      f"Net: {row['avg_net_rating']:+.1f} | "
                      f"PPG: {row['total_ppg']:.1f}")
        
        print("-"*100)
    
    def save_rankings(self, rankings):
        """Save rankings to CSV"""
        os.makedirs('Output_Data', exist_ok=True)
        rankings.to_csv(self.output_file, index=False)
        print(f"\n💾 Saved rankings to: {self.output_file}")
    
    def run(self):
        """Main execution"""
        print("📊 NBA Team Power Adjuster")
        print("="*100)
        
        # Load data
        player_stats, adjustments = self.load_data()
        if player_stats is None:
            return False
        
        # Calculate base strength
        base_rankings = self.calculate_base_team_strength(player_stats)
        
        # Apply adjustments
        final_rankings = self.apply_adjustments(base_rankings, adjustments)
        
        # Display
        self.display_rankings(final_rankings)
        
        # Save
        self.save_rankings(final_rankings)
        
        print("\n" + "="*100)
        print("✅ RANKINGS COMPLETE!")
        print("="*100)
        
        print("\n💡 USE THESE RANKINGS:")
        print("   • Updated team power ratings for predictions")
        print("   • Account for injuries and lineup changes")
        print("   • More accurate game outcome predictions")
        
        return True

def main():
    adjuster = PowerAdjuster()
    adjuster.run()

if __name__ == "__main__":
    main()
