#!/usr/bin/env python3
"""
NBA ML Model Training with Team Power Features
Trains a model using:
- Team statistics
- Player statistics
- Team power ratings (adjusted for injuries/lineups)
- Home/away factors
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os
from datetime import datetime

class NBAModelTrainer:
    def __init__(self):
        # Data files
        self.game_results_file = 'data/input/TrainingAccuracyGameData.csv'
        self.player_stats_file = 'data/input/nba_player_stats_2025-26.csv'
        self.team_power_file = 'data/input/adjusted_team_rankings.csv'
        
        # Output files
        self.model_file = 'models/nba_predictor.pkl'
        self.feature_importance_file = 'data/output/feature_importance.csv'
        
        # Model
        self.model = None
        self.features = []
        
    def load_data(self):
        """Load all necessary data"""
        print("📂 Loading data...")
        
        # Load game results
        if not os.path.exists(self.game_results_file):
            print(f"❌ Game results not found: {self.game_results_file}")
            return None
        
        games = pd.read_csv(self.game_results_file)
        print(f"✅ Loaded {len(games)} games")
        
        # Load player stats
        if not os.path.exists(self.player_stats_file):
            print(f"❌ Player stats not found: {self.player_stats_file}")
            return None
        
        player_stats = pd.read_csv(self.player_stats_file)
        print(f"✅ Loaded {len(player_stats)} players")
        
        # Load team power rankings (optional but recommended)
        team_power = None
        if os.path.exists(self.team_power_file):
            team_power = pd.read_csv(self.team_power_file)
            print(f"✅ Loaded power rankings for {len(team_power)} teams")
        else:
            print(f"⚠️  No team power rankings found")
            print(f"   Run adjust_team_power.py to generate")
        
        return games, player_stats, team_power
    
    def calculate_team_stats(self, player_stats):
        """Calculate aggregated team statistics"""
        print("\n📊 Calculating team statistics...")
        
        team_stats = []
        
        for team in player_stats['TEAM_ABBREVIATION'].unique():
            team_players = player_stats[player_stats['TEAM_ABBREVIATION'] == team]
            
            # Get rotation players (20+ minutes)
            rotation = team_players[team_players['MIN'] >= 20.0]
            
            if len(rotation) == 0:
                rotation = team_players.nlargest(8, 'MIN')
            
            stats = {
                'team': team,
                
                # Offensive stats
                'team_ppg': rotation['PTS'].sum(),
                'team_fg_pct': rotation['FG_PCT'].mean(),
                'team_3p_pct': rotation['FG3_PCT'].mean(),
                'team_ft_pct': rotation['FT_PCT'].mean(),
                'team_ts_pct': rotation['TS_PCT'].mean(),
                'team_efg_pct': rotation['EFG_PCT'].mean(),
                
                # Defensive stats
                'team_def_rating': rotation['DEF_RATING'].mean(),
                
                # Rebounding
                'team_rpg': rotation['REB'].sum(),
                'team_oreb_pct': rotation['OREB_PCT'].mean(),
                'team_dreb_pct': rotation['DREB_PCT'].mean(),
                
                # Playmaking
                'team_apg': rotation['AST'].sum(),
                'team_ast_ratio': rotation['AST_RATIO'].mean(),
                
                # Defense
                'team_spg': rotation['STL'].sum(),
                'team_bpg': rotation['BLK'].sum(),
                
                # Turnovers
                'team_tov': rotation['TOV'].sum(),
                
                # Advanced stats
                'team_off_rating': rotation['OFF_RATING'].mean(),
                'team_net_rating': rotation['NET_RATING'].mean(),
                'team_pace': rotation['PACE'].mean(),
                'team_pie': rotation['PIE'].sum(),
                'team_usg_pct': rotation['USG_PCT'].mean(),
                
                # Star power
                'star_power': rotation.nlargest(3, 'PIE')['PIE'].mean(),
                'best_player_pie': rotation['PIE'].max(),
            }
            
            team_stats.append(stats)
        
        return pd.DataFrame(team_stats)
    
    def create_training_features(self, games, team_stats, team_power):
        """Create features for model training"""
        print("\n🔧 Creating training features...")
        
        training_data = []
        
        for idx, game in games.iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Get team stats
            home_stats = team_stats[team_stats['team'] == home_team]
            away_stats = team_stats[team_stats['team'] == away_team]
            
            if home_stats.empty or away_stats.empty:
                continue
            
            # Base features from team stats
            features = {
                # Target variable
                'home_margin': game['home_score'] - game['away_score'],
                
                # Team offense differentials
                'ppg_diff': home_stats['team_ppg'].iloc[0] - away_stats['team_ppg'].iloc[0],
                'fg_pct_diff': home_stats['team_fg_pct'].iloc[0] - away_stats['team_fg_pct'].iloc[0],
                'ts_pct_diff': home_stats['team_ts_pct'].iloc[0] - away_stats['team_ts_pct'].iloc[0],
                'efg_pct_diff': home_stats['team_efg_pct'].iloc[0] - away_stats['team_efg_pct'].iloc[0],
                
                # Team defense differentials
                'def_rating_diff': away_stats['team_def_rating'].iloc[0] - home_stats['team_def_rating'].iloc[0],
                
                # Rebounding differentials
                'rpg_diff': home_stats['team_rpg'].iloc[0] - away_stats['team_rpg'].iloc[0],
                'oreb_pct_diff': home_stats['team_oreb_pct'].iloc[0] - away_stats['team_oreb_pct'].iloc[0],
                
                # Playmaking differentials
                'apg_diff': home_stats['team_apg'].iloc[0] - away_stats['team_apg'].iloc[0],
                'ast_ratio_diff': home_stats['team_ast_ratio'].iloc[0] - away_stats['team_ast_ratio'].iloc[0],
                
                # Defense differentials
                'spg_diff': home_stats['team_spg'].iloc[0] - away_stats['team_spg'].iloc[0],
                'bpg_diff': home_stats['team_bpg'].iloc[0] - away_stats['team_bpg'].iloc[0],
                
                # Advanced stats differentials
                'off_rating_diff': home_stats['team_off_rating'].iloc[0] - away_stats['team_off_rating'].iloc[0],
                'net_rating_diff': home_stats['team_net_rating'].iloc[0] - away_stats['team_net_rating'].iloc[0],
                'pace_diff': home_stats['team_pace'].iloc[0] - away_stats['team_pace'].iloc[0],
                'pie_diff': home_stats['team_pie'].iloc[0] - away_stats['team_pie'].iloc[0],
                
                # Star power differentials
                'star_power_diff': home_stats['star_power'].iloc[0] - away_stats['star_power'].iloc[0],
                'best_player_diff': home_stats['best_player_pie'].iloc[0] - away_stats['best_player_pie'].iloc[0],
            }
            
            # Add team power features if available
            if team_power is not None:
                home_power = team_power[team_power['team'] == home_team]
                away_power = team_power[team_power['team'] == away_team]
                
                if not home_power.empty and not away_power.empty:
                    # Power rating differential
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
                    
                    # Injury impact differential (if available)
                    if 'injury_impact' in team_power.columns:
                        features['injury_impact_diff'] = (
                            away_power['injury_impact'].iloc[0] - 
                            home_power['injury_impact'].iloc[0]
                        )
                    
                    # Adjustment percentage (if available)
                    if 'adjustment_pct' in team_power.columns:
                        features['home_health'] = home_power['adjustment_pct'].iloc[0]
                        features['away_health'] = away_power['adjustment_pct'].iloc[0]
            
            # Home court advantage (constant factor)
            features['home_court'] = 1.0  # Will be scaled by the model
            
            training_data.append(features)
        
        df = pd.DataFrame(training_data)
        
        print(f"✅ Created {len(df)} training samples")
        print(f"✅ Features: {len(df.columns) - 1}")
        
        return df
    
    def train_model(self, training_data):
        """Train the ML model"""
        print("\n🤖 Training model...")
        
        # Separate features and target
        X = training_data.drop('home_margin', axis=1)
        y = training_data['home_margin']
        
        self.features = X.columns.tolist()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"📊 Training set: {len(X_train)} games")
        print(f"📊 Test set: {len(X_test)} games")
        
        # Train model
        print("\n🎯 Training Random Forest...")
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        print("\n📈 Evaluating model...")
        
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        
        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
        
        train_r2 = r2_score(y_train, train_pred)
        test_r2 = r2_score(y_test, test_pred)
        
        print("\n" + "="*60)
        print("📊 MODEL PERFORMANCE")
        print("="*60)
        print(f"Training MAE:   {train_mae:.2f} points")
        print(f"Test MAE:       {test_mae:.2f} points")
        print(f"Training RMSE:  {train_rmse:.2f} points")
        print(f"Test RMSE:      {test_rmse:.2f} points")
        print(f"Training R²:    {train_r2:.3f}")
        print(f"Test R²:        {test_r2:.3f}")
        print("="*60)
        
        # Cross-validation
        print("\n🔄 Running 5-fold cross-validation...")
        cv_scores = cross_val_score(self.model, X, y, cv=5, 
                                     scoring='neg_mean_absolute_error')
        cv_mae = -cv_scores.mean()
        cv_std = cv_scores.std()
        
        print(f"CV MAE: {cv_mae:.2f} ± {cv_std:.2f} points")
        
        # Feature importance
        self.analyze_feature_importance(X)
        
        return self.model
    
    def analyze_feature_importance(self, X):
        """Analyze and save feature importance"""
        print("\n🔍 Analyzing feature importance...")
        
        importance_df = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Save to file
        os.makedirs('data/output', exist_ok=True)
        importance_df.to_csv(self.feature_importance_file, index=False)
        
        print("\n" + "="*60)
        print("🏆 TOP 10 MOST IMPORTANT FEATURES")
        print("="*60)
        for idx, row in importance_df.head(10).iterrows():
            print(f"{row['feature']:30s} {row['importance']:.4f}")
        print("="*60)
    
    def save_model(self):
        """Save the trained model"""
        os.makedirs('models', exist_ok=True)
        
        model_data = {
            'model': self.model,
            'features': self.features,
            'trained_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        joblib.dump(model_data, self.model_file)
        print(f"\n💾 Model saved to: {self.model_file}")
    
    def run(self):
        """Main execution"""
        print("🤖 NBA ML Model Training")
        print("="*60)
        
        # Load data
        result = self.load_data()
        if result is None:
            return False
        
        games, player_stats, team_power = result
        
        # Calculate team stats
        team_stats = self.calculate_team_stats(player_stats)
        
        # Create features
        training_data = self.create_training_features(games, team_stats, team_power)
        
        if training_data.empty:
            print("❌ No training data created")
            return False
        
        # Train model
        self.train_model(training_data)
        
        # Save model
        self.save_model()
        
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETE!")
        print("="*60)
        print("\n💡 Next steps:")
        print("   1. Review feature importance")
        print("   2. Run predict_games.py to make predictions")
        print("   3. Track accuracy with track_accuracy.py")
        
        return True

def main():
    trainer = NBAModelTrainer()
    trainer.run()

if __name__ == "__main__":
    main()