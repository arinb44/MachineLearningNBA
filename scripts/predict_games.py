"""
NBA Game Predictor.

Uses the trained model + the same point-in-time features as training
(features.py), computed from all completed games. Win probabilities come
from the calibrator fit during training, not a hand-tuned formula.

OUTPUT FORMAT: HOME vs AWAY
"""

import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime

import features

MODEL_FILE = 'models/nba_predictor.pkl'
GAMES_FILE = 'data/input/games_to_predict.txt'
PREDICTIONS_CSV = 'data/output/predictions.csv'
PREDICTIONS_TXT = 'data/output/predictions_output.txt'


class NBAPredictor:
    def __init__(self):
        self.model = None
        self.feature_names = []
        self.calibrator = None

    def load_model(self):
        if not os.path.exists(MODEL_FILE):
            print(f"❌ Model not found: {MODEL_FILE}")
            print("   Run: python scripts/train_model.py")
            return False
        model_data = joblib.load(MODEL_FILE)
        self.model = model_data['model']
        self.feature_names = model_data['features']
        self.calibrator = model_data.get('calibrator')
        print(f"✅ Loaded model (trained: {model_data.get('trained_date', 'unknown')})")
        if self.feature_names != features.FEATURE_COLUMNS:
            print("❌ Model was trained with a different feature set than features.py")
            print("   Re-run: python scripts/train_model.py")
            return False
        return True

    def load_games_to_predict(self):
        """Accepts both 'HOME vs AWAY' and 'AWAY @ HOME' formats."""
        if not os.path.exists(GAMES_FILE):
            print(f"❌ Games file not found: {GAMES_FILE}")
            print("   Format: HOME vs AWAY  (or)  AWAY @ HOME, one per line")
            return None

        games = []
        with open(GAMES_FILE) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ' VS ' in line.upper():
                    home, away = [p.strip() for p in line.upper().split(' VS ', 1)]
                    games.append({'home_team': home, 'away_team': away})
                elif ' @ ' in line:
                    away, home = [p.strip() for p in line.upper().split(' @ ', 1)]
                    games.append({'home_team': home, 'away_team': away})

        if not games:
            print(f"⚠️  No games found in {GAMES_FILE}")
            return None
        print(f"✅ Loaded {len(games)} games to predict")
        return games

    def win_probability(self, margin):
        """Calibrated home-win probability for a predicted margin."""
        if self.calibrator is not None:
            return float(self.calibrator.predict_proba([[margin]])[0, 1])
        # fallback if the model predates calibration
        return min(0.95, 0.5 + abs(margin) * 0.02)

    def predict_game(self, game, builder, as_of_date):
        feats = builder.game_features(
            game['home_team'], game['away_team'], as_of_date
        )
        if feats is None:
            print(f"⚠️  Skipping {game['home_team']} vs {game['away_team']}: "
                  f"no game history for one of the teams (check the abbreviation)")
            return None

        vector = np.array([[feats[name] for name in self.feature_names]])
        margin = float(self.model.predict(vector)[0])

        home_prob = self.win_probability(margin)
        if margin > 0:
            winner, win_prob = game['home_team'], home_prob
        else:
            winner, win_prob = game['away_team'], 1 - home_prob

        return {
            'home_team': game['home_team'],
            'away_team': game['away_team'],
            'predicted_margin': margin,
            'predicted_winner': winner,
            'win_probability': win_prob * 100,
            # confidence == calibrated win probability, so track_accuracy.py's
            # accuracy-by-confidence report doubles as a calibration check
            'confidence': win_prob * 100,
            'date': datetime.now().strftime('%Y-%m-%d'),
        }

    def display_predictions(self, predictions):
        print("\n" + "=" * 80)
        print("🎯 NBA GAME PREDICTIONS")
        print("=" * 80)
        for pred in predictions:
            print(f"\n🏀 {pred['home_team']} vs {pred['away_team']}")
            print("-" * 80)
            side = 'HOME' if pred['predicted_winner'] == pred['home_team'] else 'AWAY'
            print(f"   Winner: {pred['predicted_winner']} ({side})")
            print(f"   Predicted Margin: {abs(pred['predicted_margin']):.1f} points")
            print(f"   Win Probability: {pred['win_probability']:.1f}%")
            print(f"   Confidence: {pred['confidence']:.1f}%")
        print("\n" + "=" * 80)

    def save_predictions(self, predictions):
        os.makedirs('data/output', exist_ok=True)
        pd.DataFrame(predictions).to_csv(PREDICTIONS_CSV, index=False)
        print(f"\n💾 Predictions saved to: {PREDICTIONS_CSV}")

        with open(PREDICTIONS_TXT, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("🎯 NBA GAME PREDICTIONS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"Total Games: {len(predictions)}\n")
            f.write("=" * 80 + "\n\n")
            for i, pred in enumerate(predictions, 1):
                f.write(f"GAME {i}: {pred['home_team']} vs {pred['away_team']}\n")
                f.write("-" * 80 + "\n")
                side = 'HOME' if pred['predicted_winner'] == pred['home_team'] else 'AWAY'
                f.write(f"🏆 Predicted Winner: {pred['predicted_winner']} ({side})\n")
                f.write(f"   Margin: {abs(pred['predicted_margin']):.1f} points\n")
                f.write(f"   Win Probability: {pred['win_probability']:.1f}%\n")
                f.write(f"   Confidence: {pred['confidence']:.1f}%\n\n")
            f.write("=" * 80 + "\n")
            f.write("💡 Win probability is calibrated on held-out games.\n")
            f.write("   Check injury reports — the model only sees game results.\n")
            f.write("=" * 80 + "\n")
        print(f"💾 Text version saved to: {PREDICTIONS_TXT}")

    def run(self):
        print("🎯 NBA Game Predictor")
        print("=" * 80)

        if not self.load_model():
            return False

        games_history = features.load_games()
        print(f"✅ Loaded {len(games_history)} completed games through "
              f"{games_history['date'].max():%Y-%m-%d}")
        builder = features.FeatureBuilder(games_history)
        # Predicting future games: every completed game counts as history
        as_of_date = games_history['date'].max() + pd.Timedelta(days=1)

        games = self.load_games_to_predict()
        if games is None:
            return False

        predictions = []
        for game in games:
            pred = self.predict_game(game, builder, as_of_date)
            if pred:
                predictions.append(pred)

        if not predictions:
            print("❌ No predictions generated")
            return False

        self.display_predictions(predictions)
        self.save_predictions(predictions)

        print("\n✅ PREDICTIONS COMPLETE")
        print("💡 Next: wait for results, then run scripts/track_accuracy.py")
        return True


def main():
    NBAPredictor().run()


if __name__ == '__main__':
    main()
