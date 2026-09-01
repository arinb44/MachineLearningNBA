# Documentation

Start with the [project README](../README.md) — it covers setup, the full workflow, and the model's measured accuracy.

## Guides

- **[NBA_ML_COMPLETE_GUIDE.md](NBA_ML_COMPLETE_GUIDE.md)** — background on how NBA stats are categorized into offensive and defensive metrics, aggregated by team, and turned into matchup features. Includes a survey of modeling approaches (gradient boosting, ensembles, neural nets) as general recommendations, not a description of what this project runs. The shipped model is a `RandomForestRegressor`; see [scripts/train_model.py](../scripts/train_model.py).

- **[DUAL_CSV_GUIDE.md](DUAL_CSV_GUIDE.md)** — why accuracy tracking writes two files: `data/tracking/prediction_tracking.csv` accumulates every prediction ever scored, while `data/tracking/session_results.csv` holds only the most recent run.

- **[VISUALIZATION_GUIDE_DUAL.md](VISUALIZATION_GUIDE_DUAL.md)** — how to read the generated charts in `reports/`, panel by panel.

## reference/

Early scaffolding kept for provenance — the original data-structure guide and model template the project grew out of. These are **not part of the pipeline** and are not maintained: `nba_ml_prediction_guide.py` writes to a sandbox path that will not exist on your machine. Nothing in `scripts/` imports them.
