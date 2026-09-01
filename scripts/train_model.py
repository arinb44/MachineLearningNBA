#!/usr/bin/env python3
"""
NBA ML Model Training — leak-free version.

- Features are point-in-time (each game only sees earlier games), built by features.py
- Walk-forward (time-ordered) validation instead of a random split
- Compares against naive baselines so we know the model earns its keep
- Fits a calibrated win-probability model on out-of-fold predictions
"""

import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit

import features

MODEL_FILE = 'models/nba_predictor.pkl'
FEATURE_IMPORTANCE_FILE = 'data/output/feature_importance.csv'
N_SPLITS = 5
MIN_GAMES_PLAYED = 5


def make_model():
    return RandomForestRegressor(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )


def walk_forward_evaluate(table):
    """
    Walk-forward validation: each fold trains on the past, tests on the future.
    Returns out-of-fold (margin_pred, home_win) pairs for probability calibration.
    """
    X = table[features.FEATURE_COLUMNS].values
    y = table['home_margin'].values
    wins = table['home_win'].values

    oof_preds, oof_wins = [], []
    fold_rows = []

    splitter = TimeSeriesSplit(n_splits=N_SPLITS)
    for fold, (train_idx, test_idx) in enumerate(splitter.split(X), 1):
        model = make_model()
        model.fit(X[train_idx], y[train_idx])
        pred = model.predict(X[test_idx])

        # Baseline: predict the average home margin seen so far (pure home-court edge)
        baseline_pred = np.full(len(test_idx), y[train_idx].mean())

        mae = mean_absolute_error(y[test_idx], pred)
        baseline_mae = mean_absolute_error(y[test_idx], baseline_pred)
        winner_acc = ((pred > 0).astype(int) == wins[test_idx]).mean()
        home_acc = wins[test_idx].mean()  # accuracy of "always pick home team"

        fold_rows.append({
            'fold': fold, 'test_games': len(test_idx),
            'mae': mae, 'baseline_mae': baseline_mae,
            'winner_acc': winner_acc, 'always_home_acc': home_acc,
        })
        oof_preds.extend(pred)
        oof_wins.extend(wins[test_idx])

    return pd.DataFrame(fold_rows), np.array(oof_preds), np.array(oof_wins)


def report(folds):
    print("\n" + "=" * 72)
    print("📊 WALK-FORWARD VALIDATION (train on past, test on future)")
    print("=" * 72)
    print(f"{'Fold':>4} {'Games':>6} {'Model MAE':>10} {'Baseline MAE':>13} "
          f"{'Winner Acc':>11} {'Always-Home':>12}")
    for row in folds.itertuples():
        print(f"{row.fold:>4} {row.test_games:>6} {row.mae:>10.2f} "
              f"{row.baseline_mae:>13.2f} {row.winner_acc:>10.1%} "
              f"{row.always_home_acc:>11.1%}")
    print("-" * 72)
    total_games = folds['test_games'].sum()
    weights = folds['test_games'] / total_games
    avg_mae = (folds['mae'] * weights).sum()
    avg_base = (folds['baseline_mae'] * weights).sum()
    avg_acc = (folds['winner_acc'] * weights).sum()
    avg_home = (folds['always_home_acc'] * weights).sum()
    print(f"{'ALL':>4} {total_games:>6} {avg_mae:>10.2f} {avg_base:>13.2f} "
          f"{avg_acc:>10.1%} {avg_home:>11.1%}")
    print("=" * 72)
    if avg_mae < avg_base:
        print(f"✅ Model beats the home-court baseline by "
              f"{avg_base - avg_mae:.2f} points of MAE")
    else:
        print(f"⚠️  Model does NOT beat the home-court baseline "
              f"({avg_mae:.2f} vs {avg_base:.2f} MAE) — treat predictions with care")
    if avg_acc > avg_home:
        print(f"✅ Winner accuracy beats always-picking-home by "
              f"{avg_acc - avg_home:.1%}")
    else:
        print(f"⚠️  Winner accuracy does not beat always-picking-home")
    return {'mae': avg_mae, 'baseline_mae': avg_base,
            'winner_acc': avg_acc, 'always_home_acc': avg_home}


def fit_calibrator(oof_preds, oof_wins):
    """Map predicted margin -> honest home-win probability."""
    calibrator = LogisticRegression()
    calibrator.fit(oof_preds.reshape(-1, 1), oof_wins)
    for margin in (1, 3, 5, 10):
        prob = calibrator.predict_proba([[margin]])[0, 1]
        print(f"   predicted margin {margin:+3d} → home win prob {prob:.1%}")
    return calibrator


def save_feature_importance(model):
    importance = pd.DataFrame({
        'feature': features.FEATURE_COLUMNS,
        'importance': model.feature_importances_,
    }).sort_values('importance', ascending=False)
    os.makedirs('data/output', exist_ok=True)
    importance.to_csv(FEATURE_IMPORTANCE_FILE, index=False)
    print("\n🏆 FEATURE IMPORTANCE")
    for row in importance.itertuples():
        print(f"   {row.feature:24s} {row.importance:.4f}")


def main():
    print("🤖 NBA ML Model Training (point-in-time features)")
    print("=" * 72)

    games = features.load_games()
    print(f"✅ Loaded {len(games)} games "
          f"({games['date'].min():%Y-%m-%d} → {games['date'].max():%Y-%m-%d})")

    table = features.build_training_table(games, min_gp=MIN_GAMES_PLAYED)
    print(f"✅ {len(table)} training rows "
          f"(skipped {len(games) - len(table)} early games where a team "
          f"had <{MIN_GAMES_PLAYED} prior games)")

    folds, oof_preds, oof_wins = walk_forward_evaluate(table)
    metrics = report(folds)

    print("\n🎯 Calibrating win probabilities on out-of-fold predictions...")
    calibrator = fit_calibrator(oof_preds, oof_wins)

    print("\n🌲 Training final model on all data...")
    model = make_model()
    model.fit(table[features.FEATURE_COLUMNS].values, table['home_margin'].values)
    save_feature_importance(model)

    os.makedirs('models', exist_ok=True)
    joblib.dump({
        'model': model,
        'features': features.FEATURE_COLUMNS,
        'calibrator': calibrator,
        'trained_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'metrics': metrics,
    }, MODEL_FILE)
    print(f"\n💾 Model saved to: {MODEL_FILE}")
    print("\n💡 Next: python scripts/predict_games.py")


if __name__ == '__main__':
    main()
