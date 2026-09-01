"""
NBA Game Predictor with Team Power Features
Makes predictions using:
- Trained ML model
- Current team statistics
- Team power ratings (adjusted for today's lineups/injuries)

OUTPUT FORMAT: HOME vs AWAY
"""

import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime

class NBAPredictor:
    def __init__(self):
        # Data files
        self.model_file = 'models/nba_predictor.pkl'
        self.player_stats_file = 'data/input/nba_player_stats_2025-26.csv'
        self.team_power_file = 'data/input/adjusted_team_rankings.csv'
        self.games_file = 'data/input/games_to_predict.txt'
        
        # Output
        self.predictions_file = 'data/output/predictions.csv'
        
        # Model
        self.model = None
        self.features = []
    
    def load_model(self):
        """Load the trained model"""
        if not os.path.exists(self.model_file):
            print(f"❌ Model not found: {self.model_file}")
            print("   Run train_model_with_power.py first!")
            return False
        
        try:
            model_data = joblib.load(self.model_file)
            self.model = model_data['model']
            self.features = model_data['features']
            trained_date = model_data.get('trained_date', 'Unknown')
            
            print(f"✅ Loaded model (trained: {trained_date})")
            print(f"✅ Model expects {len(self.features)} features")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def load_data(self):
        """Load necessary data"""
        print("\n📂 Loading data...")
        
        # Load player stats
        if not os.path.exists(self.player_stats_file):
            print(f"❌ Player stats not found: {self.player_stats_file}")
            return None
        
        player_stats = pd.read_csv(self.player_stats_file)
        print(f"✅ Loaded {len(player_stats)} players")
        
        # Load team power rankings
        team_power = None
        if os.path.exists(self.team_power_file):
            team_power = pd.read_csv(self.team_power_file)
            print(f"✅ Loaded power rankings for {len(team_power)} teams")
            
            # Check if adjusted ratings are available
            if 'adjusted_power_rating' in team_power.columns:
                print(f"   ✅ Using ADJUSTED power ratings (with injury data)")
            else:
                print(f"   ⚠️  Using baseline power ratings (no injury adjustments)")
                print(f"      Run fetch_lineups.py + adjust_team_power.py for better accuracy")
        else:
            print(f"⚠️  No team power rankings found")
            print(f"   Run adjust_team_power.py for better predictions")
        
        return player_stats, team_power
    
    def calculate_team_stats(self, player_stats):
        """Calculate aggregated team statistics"""
        print("\n📊 Calculating team statistics...")
        
        team_stats = []
        
        for team in player_stats['TEAM_ABBREVIATION'].unique():
            team_players = player_stats[player_stats['TEAM_ABBREVIATION'] == team]
            rotation = team_players[team_players['MIN'] >= 20.0]
            
            if len(rotation) == 0:
                rotation = team_players.nlargest(8, 'MIN')
            
            stats = {
                'team': team,
                'team_ppg': rotation['PTS'].sum(),
                'team_fg_pct': rotation['FG_PCT'].mean(),
                'team_3p_pct': rotation['FG3_PCT'].mean(),
                'team_ft_pct': rotation['FT_PCT'].mean(),
                'team_ts_pct': rotation['TS_PCT'].mean(),
                'team_efg_pct': rotation['EFG_PCT'].mean(),
                'team_def_rating': rotation['DEF_RATING'].mean(),
                'team_rpg': rotation['REB'].sum(),
                'team_oreb_pct': rotation['OREB_PCT'].mean(),
                'team_dreb_pct': rotation['DREB_PCT'].mean(),
                'team_apg': rotation['AST'].sum(),
                'team_ast_ratio': rotation['AST_RATIO'].mean(),
                'team_spg': rotation['STL'].sum(),
                'team_bpg': rotation['BLK'].sum(),
                'team_tov': rotation['TOV'].sum(),
                'team_off_rating': rotation['OFF_RATING'].mean(),
                'team_net_rating': rotation['NET_RATING'].mean(),
                'team_pace': rotation['PACE'].mean(),
                'team_pie': rotation['PIE'].sum(),
                'team_usg_pct': rotation['USG_PCT'].mean(),
                'star_power': rotation.nlargest(3, 'PIE')['PIE'].mean(),
                'best_player_pie': rotation['PIE'].max(),
            }
            
            team_stats.append(stats)
        
        return pd.DataFrame(team_stats)
    
    def load_games_to_predict(self):
        """Load games from file - accepts both 'HOME vs AWAY' and 'AWAY @ HOME' formats"""
        if not os.path.exists(self.games_file):
            print(f"❌ Games file not found: {self.games_file}")
            print(f"   Create {self.games_file} with format:")
            print(f"   HOME vs AWAY  (or)  AWAY @ HOME")
            return None
        
        games = []
        with open(self.games_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse "HOME vs AWAY" format
                if ' VS ' in line.upper():
                    parts = line.upper().replace(' VS ', '|').split('|')
                    if len(parts) == 2:
                        home = parts[0].strip()
                        away = parts[1].strip()
                        games.append({'home_team': home, 'away_team': away})
                # Parse "AWAY @ HOME" format
                elif ' @ ' in line:
                    parts = line.upper().replace(' @ ', '|').split('|')
                    if len(parts) == 2:
                        away = parts[0].strip()
                        home = parts[1].strip()
                        games.append({'home_team': home, 'away_team': away})
        
        if not games:
            print(f"⚠️  No games found in {self.games_file}")
            return None
        
        print(f"\n✅ Loaded {len(games)} games to predict")
        return games
    
    def create_prediction_features(self, game, team_stats, team_power):
        """Create features for a single game prediction"""
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get team stats
        home_stats = team_stats[team_stats['team'] == home_team]
        away_stats = team_stats[team_stats['team'] == away_team]
        
        if home_stats.empty or away_stats.empty:
            return None
        
        # Calculate feature differentials
        features = {
            'ppg_diff': home_stats['team_ppg'].iloc[0] - away_stats['team_ppg'].iloc[0],
            'fg_pct_diff': home_stats['team_fg_pct'].iloc[0] - away_stats['team_fg_pct'].iloc[0],
            'ts_pct_diff': home_stats['team_ts_pct'].iloc[0] - away_stats['team_ts_pct'].iloc[0],
            'efg_pct_diff': home_stats['team_efg_pct'].iloc[0] - away_stats['team_efg_pct'].iloc[0],
            'def_rating_diff': away_stats['team_def_rating'].iloc[0] - home_stats['team_def_rating'].iloc[0],
            'rpg_diff': home_stats['team_rpg'].iloc[0] - away_stats['team_rpg'].iloc[0],
            'oreb_pct_diff': home_stats['team_oreb_pct'].iloc[0] - away_stats['team_oreb_pct'].iloc[0],
            'apg_diff': home_stats['team_apg'].iloc[0] - away_stats['team_apg'].iloc[0],
            'ast_ratio_diff': home_stats['team_ast_ratio'].iloc[0] - away_stats['team_ast_ratio'].iloc[0],
            'spg_diff': home_stats['team_spg'].iloc[0] - away_stats['team_spg'].iloc[0],
            'bpg_diff': home_stats['team_bpg'].iloc[0] - away_stats['team_bpg'].iloc[0],
            'off_rating_diff': home_stats['team_off_rating'].iloc[0] - away_stats['team_off_rating'].iloc[0],
            'net_rating_diff': home_stats['team_net_rating'].iloc[0] - away_stats['team_net_rating'].iloc[0],
            'pace_diff': home_stats['team_pace'].iloc[0] - away_stats['team_pace'].iloc[0],
            'pie_diff': home_stats['team_pie'].iloc[0] - away_stats['team_pie'].iloc[0],
            'star_power_diff': home_stats['star_power'].iloc[0] - away_stats['star_power'].iloc[0],
            'best_player_diff': home_stats['best_player_pie'].iloc[0] - away_stats['best_player_pie'].iloc[0],
            'home_court': 1.0,
        }
        
        # Add power features if available
        if team_power is not None:
            home_power = team_power[team_power['team'] == home_team]
            away_power = team_power[team_power['team'] == away_team]
            
            if not home_power.empty and not away_power.empty:
                # Use adjusted power rating if available, otherwise base rating
                if 'adjusted_power_rating' in team_power.columns:
                    features['power_rating_diff'] = (
                        home_power['adjusted_power_rating'].iloc[0] - 
                        away_power['adjusted_power_rating'].iloc[0]
                    )
                else:
                    features['power_rating_diff'] = (
                        home_power['power_rating'].iloc[0] - 
                        away_power['power_rating'].iloc[0]
                    )
                
                # Add injury impact if available
                if 'injury_impact' in team_power.columns:
                    features['injury_impact_diff'] = (
                        away_power['injury_impact'].iloc[0] - 
                        home_power['injury_impact'].iloc[0]
                    )
                
                # Add health adjustment if available
                if 'adjustment_pct' in team_power.columns:
                    features['home_health'] = home_power['adjustment_pct'].iloc[0]
                    features['away_health'] = away_power['adjustment_pct'].iloc[0]
        
        return features
    
    def predict_game(self, game, team_stats, team_power):
        """Predict a single game"""
        # Create features
        features = self.create_prediction_features(game, team_stats, team_power)
        
        if features is None:
            return None
        
        # Ensure all required features are present
        feature_vector = []
        for feat in self.features:
            if feat in features:
                feature_vector.append(features[feat])
            else:
                feature_vector.append(0.0)  # Default value for missing features
        
        # Make prediction
        predicted_margin = self.model.predict([feature_vector])[0]
        
        # Calculate confidence based on prediction strength and model agreement
        if hasattr(self.model, 'estimators_'):
            # Get predictions from all trees
            tree_predictions = [tree.predict([feature_vector])[0] 
                              for tree in self.model.estimators_]
            std = np.std(tree_predictions)
            mean_prediction = np.mean(tree_predictions)
            
            # DEBUG: Show std values (comment out after tuning)
            # print(f"  DEBUG: {game['home_team']} vs {game['away_team']} - STD: {std:.2f}, Mean: {mean_prediction:.2f}")
            
            # Confidence based on:
            # 1. Model agreement (lower std = higher confidence)
            # 2. Predicted margin strength (larger margin = higher confidence)
            
            # Base confidence from model agreement (inverted std)
            # Scale: std of 0-3 = high confidence, 3-8 = medium, 8+ = low
            if std < 3:
                base_confidence = 85
            elif std < 5:
                base_confidence = 75
            elif std < 8:
                base_confidence = 65
            elif std < 12:
                base_confidence = 55
            else:
                base_confidence = 50
            
            # Adjust confidence based on margin strength
            margin_boost = min(15, abs(predicted_margin) * 1.5)
            
            confidence = min(95, base_confidence + margin_boost)
        else:
            # For non-ensemble models, use margin as confidence proxy
            confidence = min(90, 50 + abs(predicted_margin) * 2)
        
        # Determine winner
        if predicted_margin > 0:
            winner = game['home_team']
            win_probability = min(95, 50 + (abs(predicted_margin) * 2))
        else:
            winner = game['away_team']
            win_probability = min(95, 50 + (abs(predicted_margin) * 2))
        
        return {
            'home_team': game['home_team'],
            'away_team': game['away_team'],
            'predicted_margin': predicted_margin,
            'predicted_winner': winner,
            'confidence': confidence,
            'win_probability': win_probability,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def display_predictions(self, predictions):
        """Display predictions in a nice format"""
        print("\n" + "="*80)
        print("🎯 NBA GAME PREDICTIONS")
        print("="*80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        for pred in predictions:
            print(f"\n🏀 {pred['home_team']} vs {pred['away_team']}")
            print("-"*80)
            
            if pred['predicted_margin'] > 0:
                print(f"   Winner: {pred['home_team']} (HOME)")
                print(f"   Predicted Margin: {pred['predicted_margin']:.1f} points")
            else:
                print(f"   Winner: {pred['away_team']} (AWAY)")
                print(f"   Predicted Margin: {abs(pred['predicted_margin']):.1f} points")
            
            print(f"   Win Probability: {pred['win_probability']:.1f}%")
            print(f"   Confidence: {pred['confidence']:.1f}%")
        
        print("\n" + "="*80)
    
    def save_predictions(self, predictions):
        """Save predictions to CSV and TXT - OUTPUT FORMAT: HOME vs AWAY"""
        df = pd.DataFrame(predictions)
    
        os.makedirs('data/output', exist_ok=True)
    
        # Save CSV
        df.to_csv(self.predictions_file, index=False)
        print(f"\n💾 Predictions saved to: {self.predictions_file}")
    
        # Save TXT in "HOME vs AWAY" format
        txt_file = 'data/output/predictions_output.txt'
        with open(txt_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("🎯 NBA GAME PREDICTIONS\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Games: {len(predictions)}\n")
            f.write("="*80 + "\n\n")

            for i, pred in enumerate(predictions, 1):
                # OUTPUT FORMAT: HOME vs AWAY
                f.write(f"GAME {i}: {pred['home_team']} vs {pred['away_team']}\n")
                f.write("-"*80 + "\n")

                if pred['predicted_margin'] > 0:
                    f.write(f"🏆 Predicted Winner: {pred['home_team']} (HOME)\n")
                    f.write(f"   Margin: {pred['predicted_margin']:.1f} points\n")
                else:
                    f.write(f"🏆 Predicted Winner: {pred['away_team']} (AWAY)\n")
                    f.write(f"   Margin: {abs(pred['predicted_margin']):.1f} points\n")

                f.write(f"   Win Probability: {pred['win_probability']:.1f}%\n")
                f.write(f"   Confidence: {pred['confidence']:.1f}%\n")
                f.write("\n")

            f.write("="*80 + "\n")
            f.write("💡 BETTING TIPS:\n")
            f.write("="*80 + "\n")
            f.write("• Focus on predictions with >70% confidence\n")
            f.write("• Larger margins = more confidence in the pick\n")
            f.write("• Never bet more than 2-5% of bankroll per game\n")
            f.write("• Track all bets to measure real accuracy\n")
            f.write("="*80 + "\n")

        print(f"💾 Text version saved to: {txt_file}")

    def run(self):
        """Main execution"""
        print("🎯 NBA Game Predictor")
        print("="*80)
        
        # Load model
        if not self.load_model():
            return False
        
        # Load data
        result = self.load_data()
        if result is None:
            return False
        
        player_stats, team_power = result
        
        # Calculate team stats
        team_stats = self.calculate_team_stats(player_stats)
        
        # Load games to predict
        games = self.load_games_to_predict()
        if games is None:
            return False
        
        # Make predictions
        print("\n🤖 Making predictions...")
        predictions = []
        
        for game in games:
            pred = self.predict_game(game, team_stats, team_power)
            if pred:
                predictions.append(pred)
        
        if not predictions:
            print("❌ No predictions generated")
            return False
        
        # Display and save
        self.display_predictions(predictions)
        self.save_predictions(predictions)
        
        print("\n" + "="*80)
        print("✅ PREDICTIONS COMPLETE!")
        print("="*80)
        print("\n💡 Next steps:")
        print("   1. Wait for games to finish")
        print("   2. Run track_accuracy.py to evaluate predictions")
        
        return True

def main():
    predictor = NBAPredictor()
    predictor.run()

if __name__ == "__main__":
    main()