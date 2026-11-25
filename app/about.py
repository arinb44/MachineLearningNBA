"""About page: what drives the number (the Model, position 5 on the Home court) and where the data comes from (Data, the sixth man)."""

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.common import ACCENT, INK, section, show, style_fig

st.title('About')
st.caption('How the model makes its call, and where the numbers come from.')

# ---------- model ----------

section('Model', 'What drives the number: each input\'s share of the model\'s feature importance.')

LABELS = {
    'avg_margin_diff': 'Season average margin',
    'last10_margin_diff': 'Last-10 margin',
    'min_games_played': 'Games played (sample size)',
    'pts_against_diff': 'Points allowed',
    'venue_margin_diff': 'Home / road margin',
    'pts_for_diff': 'Points scored',
    'win_pct_diff': 'Win %',
    'last10_win_pct_diff': 'Last-10 win %',
    'rest_diff': 'Rest days',
    'home_b2b': 'Home team on a back-to-back',
    'away_b2b': 'Away team on a back-to-back',
}
path = 'data/output/feature_importance.csv'
if os.path.exists(path):
    imp = pd.read_csv(path).sort_values('importance')
    labels = [LABELS.get(f, f) for f in imp['feature']]
    fig = go.Figure(go.Bar(
        x=imp['importance'] * 100, y=labels, orientation='h',
        marker=dict(color=ACCENT, cornerradius=3),
        text=[f'{v:.0f}%' if v >= 1 else '<1%' for v in imp['importance'] * 100],
        textposition='outside', textfont=dict(color=INK), cliponaxis=False,
        hovertemplate='%{y}: %{x:.1f}%<extra></extra>',
    ))
    fig.update_xaxes(showgrid=False, showticklabels=False, range=[0, imp['importance'].max() * 115])
    fig.update_yaxes(tickfont=dict(color=INK, size=13), showgrid=False)
    show(style_fig(fig, height=34 * len(imp) + 40))
else:
    st.info('No feature importances yet. Run `python scripts/train_model.py` to build the model.')

st.markdown(
    """
**Measured on the full 2025-26 regular season (1,225 games)**, scored only on
games the model had never seen during training:

| Metric | Model | Naive baseline |
|---|---|---|
| Winner accuracy | **67.5%** | 55.2% (always pick the home team) |
| Margin error (MAE) | **11.91 pts** | 13.40 (constant home-court edge) |

- **No data leakage.** Every game's features come only from games played
  *before* it: season-to-date margin, last-10 form, home/road splits, rest
  days, back-to-backs.
- **Walk-forward validation.** The model always trains on the past and is
  tested on the future, never on a random split of the season.
- **Calibrated probabilities.** Win probability comes from a logistic
  calibrator fit on held-out predictions, so a stated 65% really does win
  about 65% of the time.
- **Injuries** are pulled from ESPN and each absent player is valued by
  minutes and PIE, weighted by their status.

An ~11.9 point average margin error is normal for NBA models - single-game
variance is genuinely large. Predictions are one input, not betting advice.
    """
)

# ---------- data ----------

section('Data', 'Where every number on the site comes from.')
st.markdown(
    """
- **Game results and last season's player stats:** the NBA stats API (`nba_api`).
- **Schedule, current rosters, this season's player stats and injuries:** ESPN,
  refreshed every Monday at 6 AM Eastern by a scheduled GitHub Actions job.
- **Team logos:** stored in the repo under `static/logos/`.

Source code: [github.com/arinb44/MachineLearningNBA](https://github.com/arinb44/MachineLearningNBA)
    """
)
