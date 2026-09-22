"""Predictions page: pick a matchup, see it on the Figma matchup card."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from app.common import (add_logo, load_builder, load_games, load_injuries,
                        load_predictor, section, show, style_fig, team,
                        team_game_log, team_label, team_summary)
from app.components import matchup_card, tale_of_the_tape, win_probability_bar

st.title('NBA Game Predictor')
st.caption(
    'Predicted margin and calibrated win probability from point-in-time team '
    'form. Trained with walk-forward validation on the 2025-26 season.'
)

predictor = load_predictor()
if predictor is None:
    st.error('Model not found. Run `python scripts/train_model.py` to build it.')
    st.stop()

games = load_games()
builder = load_builder()
injuries = load_injuries()
as_of_date = games['date'].max() + pd.Timedelta(days=1)
teams = sorted(set(games['home_team']) | set(games['away_team']))


def predict(home, away):
    return predictor.predict_game({'home_team': home, 'away_team': away},
                                  builder, as_of_date, injuries)


# ---------- matchup picker ----------

col1, col2 = st.columns(2)
with col1:
    away = st.selectbox('Away team', teams, index=teams.index('GSW'), format_func=team_label)
with col2:
    home_options = [t for t in teams if t != away]
    home = st.selectbox('Home team', home_options,
                        index=home_options.index('BOS') if 'BOS' in home_options else 0,
                        format_func=team_label)

result = predict(home, away)
if result is None:
    st.warning('Not enough game history for one of these teams.')
    st.stop()

st.write('')
matchup_card(result)
win_probability_bar(result)
st.write('')

m1, m2, m3 = st.columns(3)
m1.metric('Predicted margin', f"{abs(result['predicted_margin']):.1f} pts",
          help=f"In favor of {result['predicted_winner']}")
m2.metric('Win probability', f"{result['win_probability']:.1f}%")
if abs(result['injury_adjustment']) >= 0.05:
    m3.metric('Injury adjustment', f"{result['injury_adjustment']:+.1f} pts",
              help='Positive favors the home team. Injured players are valued '
                   'by minutes and PIE, weighted by status.')
else:
    m3.metric('Injury adjustment', 'none')

if result['win_probability'] < 60:
    st.info(
        'This one is close to a coin flip. Probabilities here are calibrated '
        'against held-out games rather than inflated for effect: a 10-point '
        'favorite sits near 76%, and only lopsided matchups clear 85%.'
    )

# ---------- tale of the tape ----------

section('Tale of the tape', 'Season form going into the game. The better side of each row is '
        'drawn in its team color; bar length shows where the value sits in the league.')

summary = team_summary().set_index('team')
a, h = summary.loc[away], summary.loc[home]


def rng(col):
    return summary[col].min(), summary[col].max()


record_fmt = '{:.3f}'
rows = [
    ('Win %', a.win_pct, h.win_pct, record_fmt, *rng('win_pct'), True),
    ('Avg margin', a.margin, h.margin, '{:+.1f}', *rng('margin'), True),
    ('Last 10 margin', a.last10_margin, h.last10_margin, '{:+.1f}', *rng('last10_margin'), True),
    ('Points scored', a.pts_for, h.pts_for, '{:.1f}', *rng('pts_for'), True),
    ('Points allowed', a.pts_against, h.pts_against, '{:.1f}', *rng('pts_against'), False),
    ('Road / home margin', a.road_margin, h.home_margin, '{:+.1f}',
     min(summary.road_margin.min(), summary.home_margin.min()),
     max(summary.road_margin.max(), summary.home_margin.max()), True),
]
left, right = st.columns([3, 2], gap='large')
with left:
    tale_of_the_tape(away, home, rows)
    st.caption(f"{away} {int(a.wins)}-{int(a.losses)}  ·  {home} {int(h.wins)}-{int(h.losses)}")

with right:
    for abbr in (away, home):
        info = injuries.get(abbr)
        st.markdown(f"**{team(abbr)['name']} injuries**")
        if not info:
            st.caption('No impact players listed.')
            continue
        st.dataframe(
            pd.DataFrame(info['players'], columns=['Player', 'Status', 'Pts impact']),
            hide_index=True, use_container_width=True,
        )

# ---------- form trend ----------

section('Form over the season', 'Rolling 10-game average point margin.')

log = team_game_log()
fig = go.Figure()
for abbr in (away, home):
    g = log[log['team'] == abbr]
    color = team(abbr)['accent']
    fig.add_trace(go.Scatter(
        x=g['date'], y=g['rolling_margin'], mode='lines', name=abbr,
        line=dict(color=color, width=2),
        customdata=g[['opponent', 'margin']],
        hovertemplate=f'<b>{abbr}</b> %{{x|%b %d}}<br>vs %{{customdata[0]}}: '
                      '%{customdata[1]:+d}<br>10-game avg: %{y:+.1f}<extra></extra>',
    ))
    last = g.iloc[-1]
    add_logo(fig, abbr, last['date'] + pd.Timedelta(days=5), last['rolling_margin'],
             size=pd.Timedelta(days=9).total_seconds() * 1000, sizey=5, xanchor='left')
fig.add_hline(y=0, line=dict(color='rgba(255,255,255,0.25)', width=1))
x_max = log['date'].max() + pd.Timedelta(days=16)
fig.update_xaxes(range=[log['date'].min(), x_max], showgrid=False)
fig.update_yaxes(title='Point margin', ticksuffix='')
show(style_fig(fig, height=380, legend=True))

# ---------- today's slate ----------

slate = predictor.load_games_to_predict()
if slate:
    section('Slate', f"Games listed in {config.GAMES_TO_PREDICT_FILE}, predicted live.")
    results = [r for r in (predict(g['home_team'], g['away_team']) for g in slate) if r]
    cols = st.columns(2, gap='medium')
    for i, r in enumerate(results):
        with cols[i % 2]:
            matchup_card(r, pill='Slate')
            st.write('')

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
