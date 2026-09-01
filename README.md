# NBA Game Predictor 🏀

Machine learning system for predicting NBA game outcomes (predicted winner, margin, and confidence) from team stats, player stats, and injury-adjusted power ratings.

## Project Structure

```
├── scripts/            All runnable scripts (run them from the repo root)
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

### 2. (Optional) Adjust for injuries

```bash
python scripts/adjust_team_power.py
```

### 3. Train the model

```bash
python scripts/train_model.py
```

Saves the model to `models/nba_predictor.pkl` and feature importance to `data/output/feature_importance.csv`.

### 4. Predict games

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

### 5. Track accuracy & visualize

```bash
python scripts/track_accuracy.py
python scripts/visualize_predictions.py
```

Graphs are saved to `reports/`.

## Team Abbreviations

ATL BOS BKN CHA CHI CLE DAL DEN DET GSW HOU IND LAC LAL MEM MIA MIL MIN NOP NYK OKC ORL PHI PHX POR SAC SAS TOR UTA WAS

## Understanding Confidence

- **0–30%**: Very close game (≤3 point margin)
- **30–50%**: Moderate advantage (3–7 points)
- **50–80%**: Strong favorite (7–12 points)
- **80–100%**: Heavy favorite (12+ points)

Low confidence is normal early in the season; predictions improve as more games are played (100+ games, usually by January).

## Caveats

- The model doesn't account for rest, travel, or same-day injury news — check injury reports before using predictions.
- Early-season data is less predictive.
- Don't use for playoff games (different dynamics), and treat predictions as one input among many.

More detail in [docs/NBA_ML_COMPLETE_GUIDE.md](docs/NBA_ML_COMPLETE_GUIDE.md).
