"""
NBA Game Prediction ML Model Template
Ready-to-use implementation for predicting game outcomes
Uses XGBoost (better macOS compatibility than LightGBM)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

class NBAGamePredictor:
    """
    Complete NBA game prediction system
    Handles data processing, feature engineering, training, and prediction
    """
    
    def __init__(self, target='point_differential'):
        """
        Initialize predictor
        
        Args:
            target: 'point_differential', 'win_loss', or 'total_points'
        """
        self.target = target
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = None
        
    def create_matchup_features(self, team_stats_df, game_date=None):
        """
        Create all matchup features from team stats
        
        Args:
            team_stats_df: DataFrame with team-level aggregated stats
            game_date: Date for filtering (if available)
            
        Returns:
            DataFrame with matchup features
        """
        matchups = []
        teams = team_stats_df['team'].unique()
        
        for home_team in teams:
            for away_team in teams:
                if home_team != away_team:
                    home = team_stats_df[team_stats_df['team'] == home_team].iloc[0]
                    away = team_stats_df[team_stats_df['team'] == away_team].iloc[0]
                    
                    matchup = {
                        'home_team': home_team,
                        'away_team': away_team,
                    }
                    
                    # TIER 1: Critical differential features
                    matchup['net_rating_diff'] = (
                        home.get('net_rating_weighted', 0) - 
                        away.get('net_rating_weighted', 0)
                    )
                    
                    matchup['home_off_vs_away_def'] = (
                        home.get('off_off_rating_weighted', 0) - 
                        away.get('def_def_rating_weighted', 0)
                    )
                    
                    matchup['away_off_vs_home_def'] = (
                        away.get('off_off_rating_weighted', 0) - 
                        home.get('def_def_rating_weighted', 0)
                    )
                    
                    matchup['home_court_advantage'] = 1  # Binary indicator
                    
                    # TIER 2: Strong predictors
                    matchup['ts_pct_diff'] = (
                        home.get('off_ts_pct_weighted', 0) - 
                        away.get('off_ts_pct_weighted', 0)
                    )
                    
                    matchup['def_rating_diff'] = (
                        away.get('def_def_rating_weighted', 0) - 
                        home.get('def_def_rating_weighted', 0)
                    )
                    
                    matchup['star_power_diff'] = (
                        home.get('star_power', 0) - 
                        away.get('star_power', 0)
                    )
                    
                    matchup['rebounding_advantage'] = (
                        home.get('def_reb_pct_weighted', 0) - 
                        away.get('def_reb_pct_weighted', 0)
                    )
                    
                    # TIER 3: Supporting features
                    matchup['rotation_size_diff'] = (
                        home.get('rotation_size', 0) - 
                        away.get('rotation_size', 0)
                    )
                    
                    matchup['ast_pct_diff'] = (
                        home.get('off_ast_pct_weighted', 0) - 
                        away.get('off_ast_pct_weighted', 0)
                    )
                    
                    # Interaction features
                    matchup['quality_gap'] = abs(matchup['net_rating_diff'])
                    matchup['offensive_mismatch'] = (
                        matchup['home_off_vs_away_def'] * 
                        matchup['ts_pct_diff']
                    )
                    
                    matchups.append(matchup)
        
        return pd.DataFrame(matchups)
    
    def engineer_features(self, df):
        """
        Add advanced engineered features
        
        Args:
            df: DataFrame with basic matchup features
            
        Returns:
            DataFrame with additional features
        """
        df = df.copy()
        
        # Squared terms for non-linear relationships
        df['net_rating_diff_squared'] = df['net_rating_diff'] ** 2
        df['quality_gap_squared'] = df['quality_gap'] ** 2
        
        # Ratio features
        if 'home_off_vs_away_def' in df.columns and 'away_off_vs_home_def' in df.columns:
            df['offensive_balance'] = (
                df['home_off_vs_away_def'] / 
                (df['away_off_vs_home_def'] + 1)  # Avoid division by zero
            )
        
        # Combined impact score
        df['expected_home_advantage'] = (
            df['net_rating_diff'] * 0.4 +
            df['home_off_vs_away_def'] * 0.3 +
            df['star_power_diff'] * 20 +  # Scale PIE to points
            df['home_court_advantage'] * 2.5  # Historical advantage
        )
        
        return df
    
    def prepare_data(self, matchups_df, results_df=None):
        """
        Prepare data for modeling
        
        Args:
            matchups_df: DataFrame with matchup features
            results_df: DataFrame with actual game results (for training)
            
        Returns:
            X (features), y (target), feature_names
        """
        # Engineer features
        df = self.engineer_features(matchups_df)
        
        # If results provided, merge them
        if results_df is not None:
            df = df.merge(
                results_df,
                on=['home_team', 'away_team'],
                how='inner'
            )
            
            # Create target variable
            if self.target == 'point_differential':
                y = df['home_score'] - df['away_score']
            elif self.target == 'win_loss':
                y = (df['home_score'] > df['away_score']).astype(int)
            elif self.target == 'total_points':
                y = df['home_score'] + df['away_score']
            else:
                raise ValueError(f"Unknown target: {self.target}")
        else:
            y = None
        
        # Select features (exclude team names, scores, and metadata)
        feature_cols = [col for col in df.columns 
                       if col not in ['home_team', 'away_team', 
                                     'home_score', 'away_score', 'date',
                                     'game_id', 'home_win']]
        
        X = df[feature_cols]
        
        # Handle any missing values
        X = X.fillna(X.mean())
        
        return X, y, feature_cols
    
    def train(self, X, y, scale_features=True, cv_folds=5):
        """
        Train the model with cross-validation
        
        Args:
            X: Feature matrix
            y: Target variable
            scale_features: Whether to standardize features
            cv_folds: Number of cross-validation folds
            
        Returns:
            dict with training metrics
        """
        # Scale features if requested
        if scale_features:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        
        # Choose model based on target type
        if self.target == 'win_loss':
            self.model = xgb.XGBClassifier(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='logloss',
                use_label_encoder=False
            )
            scoring = 'accuracy'
        else:
            self.model = xgb.XGBRegressor(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
            scoring = 'neg_mean_absolute_error'
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=cv_folds)
        cv_scores = cross_val_score(
            self.model, X_scaled, y, 
            cv=tscv, 
            scoring=scoring
        )
        
        # Train on full dataset
        self.model.fit(X_scaled, y)
        
        # Get feature importance
        self.feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Calculate metrics
        y_pred = self.model.predict(X_scaled)
        
        if self.target == 'win_loss':
            train_accuracy = accuracy_score(y, y_pred.round())
            metrics = {
                'cv_accuracy_mean': cv_scores.mean(),
                'cv_accuracy_std': cv_scores.std(),
                'train_accuracy': train_accuracy
            }
        else:
            train_mae = mean_absolute_error(y, y_pred)
            train_rmse = np.sqrt(mean_squared_error(y, y_pred))
            metrics = {
                'cv_mae_mean': -cv_scores.mean(),  # Negative because sklearn uses neg_mae
                'cv_mae_std': cv_scores.std(),
                'train_mae': train_mae,
                'train_rmse': train_rmse
            }
        
        return metrics
    
    def predict(self, X):
        """
        Make predictions on new data
        
        Args:
            X: Feature matrix
            
        Returns:
            Predictions array
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_game(self, home_team, away_team, team_stats_df):
        """
        Predict outcome of a specific game
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            team_stats_df: Current team statistics
            
        Returns:
            dict with prediction and confidence
        """
        # Create matchup features for this specific game
        home_stats = team_stats_df[team_stats_df['team'] == home_team].iloc[0]
        away_stats = team_stats_df[team_stats_df['team'] == away_team].iloc[0]
        
        matchup = pd.DataFrame([{
            'home_team': home_team,
            'away_team': away_team,
        }])
        
        # This would use the same feature creation logic
        # For simplicity, using create_matchup_features
        temp_df = team_stats_df[team_stats_df['team'].isin([home_team, away_team])]
        matchup_full = self.create_matchup_features(temp_df)
        matchup_full = matchup_full[
            (matchup_full['home_team'] == home_team) & 
            (matchup_full['away_team'] == away_team)
        ]
        
        X, _, _ = self.prepare_data(matchup_full)
        prediction = self.predict(X)[0]
        
        result = {
            'home_team': home_team,
            'away_team': away_team,
        }
        
        if self.target == 'point_differential':
            result['predicted_margin'] = round(prediction, 1)
            result['predicted_winner'] = home_team if prediction > 0 else away_team
            result['confidence'] = min(abs(prediction) / 15 * 100, 100)  # Scale to 0-100
        elif self.target == 'win_loss':
            result['home_win_probability'] = round(prediction * 100, 1)
            result['predicted_winner'] = home_team if prediction > 0.5 else away_team
            result['confidence'] = abs(prediction - 0.5) * 200  # Scale to 0-100
        elif self.target == 'total_points':
            result['predicted_total'] = round(prediction, 1)
        
        return result
    
    def get_top_features(self, n=10):
        """Get top n most important features"""
        if self.feature_importance is None:
            raise ValueError("Model not trained yet")
        return self.feature_importance.head(n)


# Example usage
if __name__ == "__main__":
    print("NBA Game Prediction ML Model Template (XGBoost)")
    print("=" * 60)
    
    # Example: Load your data
    # team_stats = pd.read_csv('nba_team_aggregated_stats.csv')
    # game_results = pd.read_csv('historical_game_results.csv')
    
    # Initialize predictor
    predictor = NBAGamePredictor(target='point_differential')
    
    # Create matchup features
    # matchups = predictor.create_matchup_features(team_stats)
    
    # Prepare data
    # X, y, features = predictor.prepare_data(matchups, game_results)
    
    # Train model
    # metrics = predictor.train(X, y)
    # print("\nTraining Metrics:")
    # for key, value in metrics.items():
    #     print(f"  {key}: {value:.3f}")
    
    # View feature importance
    # print("\nTop 10 Most Important Features:")
    # print(predictor.get_top_features(10))
    
    # Predict a specific game
    # prediction = predictor.predict_game('LAL', 'BOS', team_stats)
    # print(f"\nPrediction: {prediction}")
    
    print("\n✓ Model template ready!")
    print("\nTo use:")
    print("1. Load your team_stats and game_results data")
    print("2. Create matchup features")
    print("3. Train the model")
    print("4. Make predictions on upcoming games")
    print("\nNote: Using XGBoost for better macOS compatibility")