#!/usr/bin/env python3
"""
NBA Model Accuracy Tracker
Compares predictions against actual game results and tracks performance
Outputs TWO CSV files:
1. prediction_tracking.csv - Historical cumulative data (all runs)
2. session_results.csv - Current session only (this run)
"""

import pandas as pd
from datetime import datetime
import os
import re

import config

class AccuracyTracker:
    def __init__(self):
        self.predictions_file = "data/output/predictions_output.txt"
        self.results_file = config.game_results_file()
        self.tracking_file = "data/tracking/prediction_tracking.csv"
        self.session_file = "data/tracking/session_results.csv"

    def parse_predictions(self):
        """Parse predictions from the output file - expects 'HOME vs AWAY' format"""
        if not os.path.exists(self.predictions_file):
            print(f"Predictions file not found: {self.predictions_file}")
            return None, None

        predictions = []
        current_game = {}

        try:
            with open(self.predictions_file, 'r') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()

                # Skip empty lines, separators, and main headers
                if not line or line.startswith('=') or line.startswith('-'):
                    continue
                if "NBA GAME PREDICTIONS" in line or "Generated:" in line or "Total Games" in line:
                    continue
                if "BETTING TIPS" in line or line.startswith('•') or line.startswith('â€¢'):
                    continue

                # Match game line: "GAME X: HOME vs AWAY"
                game_match = re.search(r'GAME\s+\d+:\s*([A-Z]{3})\s+vs\s+([A-Z]{3})', line, re.IGNORECASE)
                if game_match:
                    # Save previous game if complete
                    if current_game and all(k in current_game for k in ['home', 'away', 'winner', 'confidence']):
                        predictions.append(current_game.copy())

                    # Start new game (HOME vs AWAY format)
                    current_game = {
                        'home': game_match.group(1).upper(),
                        'away': game_match.group(2).upper()
                    }
                    continue

                # Parse winner: "Predicted Winner: GSW (HOME)"
                if "Predicted Winner:" in line or "PREDICTED WINNER:" in line:
                    winner = re.search(r'Winner:\s*([A-Z]{3})', line, re.IGNORECASE)
                    if winner:
                        current_game['winner'] = winner.group(1).upper()

                # Parse margin: "Margin: 11.5 points"
                if "Margin:" in line and "Predicted Winner" not in line:
                    margin = re.search(r'Margin:\s*([-+]?\d+\.?\d*)', line, re.IGNORECASE)
                    if margin:
                        current_game['margin'] = float(margin.group(1))

                # Parse confidence: "Confidence: 50.0%"
                if "Confidence:" in line:
                    confidence = re.search(r'Confidence:\s*(\d+\.?\d*)%?', line, re.IGNORECASE)
                    if confidence:
                        current_game['confidence'] = float(confidence.group(1))

            # Add last game
            if current_game and all(k in current_game for k in ['home', 'away', 'winner', 'confidence']):
                predictions.append(current_game.copy())

            if not predictions:
                print("No predictions found")
                print("Make sure 'predictions_output.txt' exists and has predictions")
                print("   Run 'python predict_games.py' first to generate predictions")
                return None, None

            df = pd.DataFrame(predictions)
            return df, None

        except Exception as e:
            print(f"Error parsing predictions: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    def load_actual_results(self):
        """Load actual game results"""
        if not os.path.exists(self.results_file):
            print(f"Results file not found: {self.results_file}")
            return None, None

        try:
            df = pd.read_csv(self.results_file)
            return df, None
        except Exception as e:
            print(f"Error loading results: {e}")
            return None, None

    def match_predictions_to_results(self, predictions_df, results_df):
        """Match predictions to actual game results"""
        matched_predictions = []

        for _, pred in predictions_df.iterrows():
            home = pred['home']
            away = pred['away']

            # Find matching game in results
            match = results_df[
                ((results_df['home_team'] == home) & (results_df['away_team'] == away)) |
                ((results_df['home_team'] == away) & (results_df['away_team'] == home))
            ]

            if not match.empty:
                game = match.iloc[0]

                # Determine actual winner
                actual_winner = game['home_team'] if game['home_win'] == 1 else game['away_team']

                # Calculate actual margin
                actual_margin = abs(game['home_score'] - game['away_score'])
                if actual_winner == game['away_team']:
                    actual_margin = -actual_margin

                # Check if prediction was correct
                correct = (pred['winner'] == actual_winner)

                # Calculate margin error
                margin_error = abs(abs(pred.get('margin', 0)) - abs(actual_margin))

                # Margin signed from the home team's perspective
                model_home_margin = pred.get('margin', 0)
                if pred['winner'] != home:
                    model_home_margin = -model_home_margin

                row = {
                    'date': game['date'],
                    'home_team': home,
                    'away_team': away,
                    'predicted_winner': pred['winner'],
                    'actual_winner': actual_winner,
                    'correct': correct,
                    'confidence': pred['confidence'],
                    'predicted_margin': pred.get('margin', 0),
                    'model_home_margin': model_home_margin,
                    'actual_margin': actual_margin,
                    'margin_error': margin_error,
                    'home_score': game['home_score'],
                    'away_score': game['away_score']
                }
                if 'vegas_home_margin' in results_df.columns and pd.notna(game['vegas_home_margin']):
                    row['vegas_home_margin'] = game['vegas_home_margin']
                matched_predictions.append(row)

        return pd.DataFrame(matched_predictions)

    def calculate_metrics(self, matched_df):
        """Calculate accuracy metrics"""
        if matched_df.empty:
            return None

        total = len(matched_df)
        correct = matched_df['correct'].sum()
        accuracy = (correct / total) * 100

        metrics = {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy': accuracy,
            'avg_confidence': matched_df['confidence'].mean(),
            'avg_margin_error': matched_df['margin_error'].mean()
        }

        # Accuracy by confidence level
        confidence_bins = [
            (50, 55, "Low (50-55%)"),
            (55, 65, "Medium (55-65%)"),
            (65, 75, "High (65-75%)"),
            (75, 100, "Very High (75%+)")
        ]

        confidence_accuracy = {}
        for min_conf, max_conf, label in confidence_bins:
            subset = matched_df[
                (matched_df['confidence'] >= min_conf) &
                (matched_df['confidence'] < max_conf)
            ]
            if not subset.empty:
                acc = (subset['correct'].sum() / len(subset)) * 100
                confidence_accuracy[label] = {
                    'correct': subset['correct'].sum(),
                    'total': len(subset),
                    'accuracy': acc
                }

        metrics['confidence_accuracy'] = confidence_accuracy

        # Per-team accuracy
        team_accuracy = {}
        for team in pd.concat([matched_df['home_team'], matched_df['away_team']]).unique():
            team_games = matched_df[
                (matched_df['home_team'] == team) |
                (matched_df['away_team'] == team)
            ]
            if not team_games.empty:
                acc = (team_games['correct'].sum() / len(team_games)) * 100
                team_accuracy[team] = {
                    'correct': team_games['correct'].sum(),
                    'total': len(team_games),
                    'accuracy': acc
                }

        metrics['team_accuracy'] = team_accuracy

        # Model vs Vegas, on games that have a line
        # (add lines with scripts/merge_vegas_lines.py)
        if 'vegas_home_margin' in matched_df.columns:
            lined = matched_df.dropna(subset=['vegas_home_margin'])
            if not lined.empty:
                actual = lined['actual_margin']
                metrics['vegas'] = {
                    'games': len(lined),
                    'model_mae': (lined['model_home_margin'] - actual).abs().mean(),
                    'vegas_mae': (lined['vegas_home_margin'] - actual).abs().mean(),
                    'model_acc': lined['correct'].mean() * 100,
                    'vegas_acc': ((lined['vegas_home_margin'] > 0) == (actual > 0)).mean() * 100,
                }

        return metrics

    def print_report(self, metrics):
        """Print formatted accuracy report"""
        print("\n" + "="*60)
        print("NBA MODEL ACCURACY REPORT")
        print("="*60)

        print("\nOverall Performance:")
        print(f"   Total Predictions:     {metrics['total_predictions']}")
        print(f"   Correct Predictions:   {metrics['correct_predictions']}")
        print(f"   Accuracy:              {metrics['accuracy']:.2f}%")
        print(f"   Average Confidence:    {metrics['avg_confidence']:.2f}%")
        print(f"   Avg Margin Error:      {metrics['avg_margin_error']:.2f} points")

        print("\nAccuracy by Confidence Level:")
        for label, data in metrics['confidence_accuracy'].items():
            print(f"   {label:20s}: {data['correct']}/{data['total']} ({data['accuracy']:.1f}%)")

        if 'vegas' in metrics:
            v = metrics['vegas']
            print(f"\nModel vs Vegas ({v['games']} games with lines):")
            print(f"   Margin MAE:      model {v['model_mae']:.2f}  vs  Vegas {v['vegas_mae']:.2f}")
            print(f"   Winner accuracy: model {v['model_acc']:.1f}%  vs  Vegas {v['vegas_acc']:.1f}%")
            if v['model_mae'] < v['vegas_mae']:
                print("   Model is beating the closing line — verify before trusting!")
            else:
                print("   Vegas is still sharper (expected — beating the line is very hard)")

        print("\nTop 5 Teams (Prediction Accuracy):")
        sorted_teams = sorted(
            metrics['team_accuracy'].items(),
            key=lambda x: (x[1]['accuracy'], x[1]['total']),
            reverse=True
        )[:5]
        for team, data in sorted_teams:
            print(f"   {team:5s}: {data['correct']}/{data['total']} ({data['accuracy']:.1f}%)")

        print("\nBottom 5 Teams (Prediction Accuracy):")
        sorted_teams = sorted(
            metrics['team_accuracy'].items(),
            key=lambda x: (x[1]['accuracy'], -x[1]['total'])
        )[:5]
        for team, data in sorted_teams:
            print(f"   {team:5s}: {data['correct']}/{data['total']} ({data['accuracy']:.1f}%)")

        print("="*60)

    def save_tracking_data(self, matched_df):
        """Save tracking data to TWO CSV files"""
        # Add timestamp
        matched_df['tracked_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # File 1: Historical cumulative tracking
        if os.path.exists(self.tracking_file):
            # Append to existing historical data
            existing_df = pd.read_csv(self.tracking_file)
            combined_df = pd.concat([existing_df, matched_df], ignore_index=True)
            combined_df.to_csv(self.tracking_file, index=False)
            print(f"Updated historical tracking: {self.tracking_file}")
        else:
            # Create new historical file
            matched_df.to_csv(self.tracking_file, index=False)
            print(f"Created historical tracking: {self.tracking_file}")

        # File 2: Current session only
        matched_df.to_csv(self.session_file, index=False)
        print(f"Created session results: {self.session_file}")

    def run(self):
        """Run the full accuracy tracking process"""
        print("Starting accuracy tracking...")

        # Load predictions
        print("Loading predictions...")
        predictions_df, error = self.parse_predictions()
        if predictions_df is None:
            return None, None
        print(f"Loaded {len(predictions_df)} predictions")

        # Load actual results
        print("Loading actual game results...")
        results_df, error = self.load_actual_results()
        if results_df is None:
            return None, None
        print(f"Loaded {len(results_df)} game results")

        # Match predictions to results
        print("Matching predictions to results...")
        matched_df = self.match_predictions_to_results(predictions_df, results_df)
        if matched_df.empty:
            print("No matching games found")
            print("Make sure the games you predicted have been played")
            return None, None
        print(f"Matched {len(matched_df)} predictions to results")

        # Calculate metrics
        print("Calculating metrics...")
        metrics = self.calculate_metrics(matched_df)

        # Print report
        self.print_report(metrics)

        # Save tracking data (both files)
        print("\nSaving tracking data...")
        self.save_tracking_data(matched_df)

        print("\nAccuracy tracking complete!")
        print(f"\nFiles created:")
        print(f"   1. {self.tracking_file} - All historical predictions")
        print(f"   2. {self.session_file} - This session's predictions only")

        return matched_df, metrics

def main():
    tracker = AccuracyTracker()
    result = tracker.run()

    if result is not None:
        matched_df, metrics = result
        if matched_df is not None and not matched_df.empty:
            return matched_df, metrics

    print("\nAccuracy tracking could not be completed")
    return None, None

if __name__ == "__main__":
    main()