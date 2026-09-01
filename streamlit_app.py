"""
Interactive demo for the NBA game predictor.

Reuses the exact prediction code path from scripts/predict_games.py, so the
demo can never drift from the command-line tool or the trained model.

Run locally:  streamlit run streamlit_app.py
"""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

import features  # noqa: E402
from predict_games import NBAPredictor, load_injury_impacts  # noqa: E402

TEAM_NAMES = {
    'ATL': 'Atlanta Hawks', 'BOS': 'Boston Celtics', 'BKN': 'Brooklyn Nets',
    'CHA': 'Charlotte Hornets', 'CHI': 'Chicago Bulls', 'CLE': 'Cleveland Cavaliers',
    'DAL': 'Dallas Mavericks', 'DEN': 'Denver Nuggets', 'DET': 'Detroit Pistons',
    'GSW': 'Golden State Warriors', 'HOU': 'Houston Rockets', 'IND': 'Indiana Pacers',
    'LAC': 'LA Clippers', 'LAL': 'Los Angeles Lakers', 'MEM': 'Memphis Grizzlies',
    'MIA': 'Miami Heat', 'MIL': 'Milwaukee Bucks', 'MIN': 'Minnesota Timberwolves',
    'NOP': 'New Orleans Pelicans', 'NYK': 'New York Knicks', 'OKC': 'Oklahoma City Thunder',
    'ORL': 'Orlando Magic', 'PHI': 'Philadelphia 76ers', 'PHX': 'Phoenix Suns',
    'POR': 'Portland Trail Blazers', 'SAC': 'Sacramento Kings', 'SAS': 'San Antonio Spurs',
    'TOR': 'Toronto Raptors', 'UTA': 'Utah Jazz', 'WAS': 'Washington Wizards',
}


@st.cache_resource
def load_predictor():
    predictor = NBAPredictor()
    if not predictor.load_model():
        return None
    return predictor


@st.cache_data
def load_history():
    games = features.load_games()
    return games


@st.cache_resource
def load_injuries():
    return load_injury_impacts()


def label(abbr):
    return f"{abbr} - {TEAM_NAMES.get(abbr, abbr)}"


st.set_page_config(page_title='NBA Game Predictor', page_icon='basketball', layout='centered')

st.title('NBA Game Predictor')
st.caption(
    'Predicts game margin and a calibrated win probability from point-in-time '
    'team form. Trained with walk-forward validation on the 2025-26 season.'
)

predictor = load_predictor()
if predictor is None:
    st.error('Model not found. Run `python scripts/train_model.py` to build it.')
    st.stop()

games = load_history()
injuries = load_injuries()
builder = features.FeatureBuilder(games)
as_of_date = games['date'].max() + pd.Timedelta(days=1)

teams = sorted(set(games['home_team']) | set(games['away_team']))

st.subheader('Pick a matchup')
col1, col2 = st.columns(2)
with col1:
    away = st.selectbox('Away team', teams, index=teams.index('GSW') if 'GSW' in teams else 0,
                        format_func=label)
with col2:
    home_options = [t for t in teams if t != away]
    home = st.selectbox('Home team', home_options,
                        index=home_options.index('BOS') if 'BOS' in home_options else 0,
                        format_func=label)

result = predictor.predict_game(
    {'home_team': home, 'away_team': away}, builder, as_of_date, injuries
)

if result is None:
    st.warning('Not enough game history for one of these teams.')
    st.stop()

margin = result['predicted_margin']
winner = result['predicted_winner']
side = 'at home' if winner == home else 'on the road'

st.subheader('Prediction')
st.markdown(f"### {winner} wins by {abs(margin):.1f} ({side})")

m1, m2, m3 = st.columns(3)
m1.metric('Predicted margin', f"{abs(margin):.1f} pts")
m2.metric('Win probability', f"{result['win_probability']:.1f}%")
if abs(result['injury_adjustment']) >= 0.05:
    m3.metric('Injury adjustment', f"{result['injury_adjustment']:+.1f} pts",
              help='Injured players valued by minutes and PIE, weighted by status')
else:
    m3.metric('Injury adjustment', 'none')

if result['win_probability'] < 60:
    st.info(
        'This one is close to a coin flip. Probabilities here are calibrated '
        'against held-out games rather than inflated for effect: a 10-point '
        'favorite sits near 76%, and only lopsided matchups clear 85%.'
    )

st.subheader('Season form going in')
rows = []
for team, role in ((home, 'Home'), (away, 'Away')):
    form = builder.team_form(team, as_of_date)
    rows.append({
        'Team': label(team),
        'Role': role,
        'Record': f"{int(form['win_pct'] * form['gp'])}-{form['gp'] - int(form['win_pct'] * form['gp'])}",
        'Avg margin': f"{form['avg_margin']:+.1f}",
        'Last 10 margin': f"{form['last_margin']:+.1f}",
        'Pts for': f"{form['pts_for']:.1f}",
        'Pts against': f"{form['pts_against']:.1f}",
    })
st.dataframe(pd.DataFrame(rows).set_index('Team'), use_container_width=True)

with st.expander('How this model works, and how well'):
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

st.caption(
    f"Model trained on games through {games['date'].max():%B %d, %Y}. "
    'Source: github.com/arinb44/MachineLearningNBA'
)
