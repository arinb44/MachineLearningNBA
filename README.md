# NBA Game Predictor 🏀

Machine learning system for predicting NBA game outcomes (winner, margin, and calibrated win probability) from game results.

## How the model works

- **Point-in-time features** ([scripts/features.py](scripts/features.py)): every game's features are computed only from games played *before* it — season-to-date margin, last-10 form, home/road splits, rest days, back-to-backs. No information from the future leaks into training.
- **Walk-forward validation**: the model is always trained on the past and tested on the future (`TimeSeriesSplit`), and compared against a naive home-court baseline so we know it earns its keep. Current numbers: **11.5 MAE vs 11.9 baseline; 61.9% winner accuracy vs 54.5% for always-picking-home**.
- **Calibrated probabilities**: win probability comes from a logistic calibrator fit on held-out predictions, not a hand-tuned formula. A reported 60% should win about 60% of the time — `track_accuracy.py`'s accuracy-by-confidence report is the check.

## Project Structure

```
├── scripts/            All runnable scripts (run them from the repo root)
│   ├── features.py                 Shared point-in-time feature engineering
│   ├── fetch_player_stats.py       Fetch latest player stats from the NBA API
│   ├── fetch_game_results.py       Fetch latest game results
│   ├── fetch_game_logs.py          Fetch game logs / per-game std deviations
│   ├── injury_tracker.py           Manually track injuries, adjust predictions
│   ├── adjust_team_power.py        Build injury-adjusted team power ratings
│   ├── find_consistent_players.py  Find most consistent players per stat
│   ├── train_model.py              Train the prediction model
│   ├── predict_games.py            Predict games listed in data/input/games_to_predict.txt
│   ├── track_accuracy.py           Compare predictions vs. actual results
│   ├── visualize_predictions.py    Generate accuracy graphs and dashboards
│   └── check_files.py              Debug helper: verify data files exist
├── data/
│   ├── input/          Fetched stats, training data, games to predict
│   ├── output/         Predictions and model analysis outputs
│   └── tracking/       Accuracy tracking history (all-time + per-session)
├── models/             Trained model (nba_predictor.pkl)
├── docs/               Guides (+ docs/reference/ for the original ML templates)
└── reports/            Generated graphs and betting spreadsheets
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On macOS, XGBoost needs OpenMP: `brew install libomp`.

## Workflow

All scripts are run from the repository root.

### 1. Update data (weekly)

```bash
python scripts/fetch_player_stats.py
python scripts/fetch_game_results.py
```

### 2. Train the model

```bash
python scripts/train_model.py
```

Prints the walk-forward validation report (model vs. baseline), then saves the model to `models/nba_predictor.pkl` and feature importance to `data/output/feature_importance.csv`. Retrain whenever you fetch new results.

### 3. Predict games

Edit `data/input/games_to_predict.txt` (away team first):

```txt
DET vs CLE
PHI vs ORL
GSW vs BOS
```

```bash
python scripts/predict_games.py
```

Results land in `data/output/predictions_output.txt` and `data/output/predictions.csv`.

### 4. Track accuracy & visualize

```bash
python scripts/track_accuracy.py
python scripts/visualize_predictions.py
```

Graphs are saved to `reports/`.

## Team Abbreviations

ATL BOS BKN CHA CHI CLE DAL DEN DET GSW HOU IND LAC LAL MEM MIA MIL MIN NOP NYK OKC ORL PHI PHX POR SAC SAS TOR UTA WAS

## Understanding the numbers

- **Win probability / confidence** is calibrated: ~50% means a true coin flip, ~68% is roughly a 10-point favorite. Don't expect many games above 75% — NBA games are genuinely uncertain, and honest probabilities reflect that.
- **Predicted margin** has a typical error of ~11 points (MAE) — that's normal for NBA models; single-game variance is huge.

## Caveats

- The model accounts for rest days and back-to-backs, but not travel or same-day injury news — check injury reports before using predictions (`scripts/injury_tracker.py` can apply manual adjustments).
- Early-season predictions are skipped/noisier until each team has 5+ games.
- Don't use for playoff games (different dynamics), and treat predictions as one input among many.

More detail in [docs/NBA_ML_COMPLETE_GUIDE.md](docs/NBA_ML_COMPLETE_GUIDE.md).
