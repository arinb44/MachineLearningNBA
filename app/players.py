"""Players page: stat leaders, scoring efficiency, and player profiles."""

import plotly.graph_objects as go
import streamlit as st

import config
from app.common import (INK, add_logo, load_player_stats, section,
                        show, style_fig, team)
from app.components import team_header

COMPARE_COLOR = '#a1a1aa'

STATS = {
    'Points': ('PTS', '{:.1f}'),
    'Rebounds': ('REB', '{:.1f}'),
    'Assists': ('AST', '{:.1f}'),
    'Steals': ('STL', '{:.1f}'),
    'Blocks': ('BLK', '{:.1f}'),
    '3-pointers made': ('FG3M', '{:.1f}'),
    'True shooting %': ('TS_PCT', '{:.1%}'),
    '3-point %': ('FG3_PCT', '{:.1%}'),
    'Plus-minus': ('PLUS_MINUS', '{:+.1f}'),
    'Net rating': ('NET_RATING', '{:+.1f}'),
    'Player impact (PIE)': ('PIE', '{:.3f}'),
    'Usage %': ('USG_PCT', '{:.1%}'),
}

st.title('Players')
st.caption(f"Per-game stats for the {config.current_season()} season from the NBA stats API.")

players = load_player_stats()

f1, f2 = st.columns([1, 1])
min_games = f1.slider('Minimum games played', 1, int(players['GP'].max()), 20)
min_minutes = f2.slider('Minimum minutes per game', 0, 36, 15)
qualified = players[(players['GP'] >= min_games) & (players['MIN'] >= min_minutes)].copy()
st.caption(f"{len(qualified)} of {len(players)} players qualify.")
if qualified.empty:
    st.warning('No players match these filters.')
    st.stop()

# ---------- stat leaders ----------

section('Stat leaders')
s1, s2 = st.columns([2, 1])
stat_name = s1.selectbox('Stat', list(STATS))
top_n = s2.select_slider('Show', options=[10, 15, 20, 25], value=15)
col, fmt = STATS[stat_name]

leaders = qualified.nlargest(top_n, col).iloc[::-1].reset_index(drop=True)
lo = min(0, leaders[col].min())
hi = leaders[col].max()
fig = go.Figure(go.Bar(
    x=leaders[col], y=leaders['PLAYER_NAME'], orientation='h',
    marker=dict(color=[team(t)['accent'] for t in leaders['TEAM_ABBREVIATION']],
                opacity=0.9, cornerradius=4),
    text=[fmt.format(v) for v in leaders[col]], textposition='outside',
    textfont=dict(color=INK, size=12), cliponaxis=False,
    customdata=leaders[['TEAM_ABBREVIATION', 'GP', 'MIN']],
    hovertemplate='<b>%{y}</b> (%{customdata[0]})<br>' + stat_name +
                  ': %{text}<br>%{customdata[1]} games, %{customdata[2]:.1f} min<extra></extra>',
))
# Team logo at the start of each bar, just right of the player name
for i, abbr in enumerate(leaders['TEAM_ABBREVIATION']):
    add_logo(fig, abbr, 0.005, i, size=0.04, sizey=0.85, xref='paper', xanchor='left')
fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False,
                 range=[lo - (hi - lo) * 0.06, hi + (hi - lo) * 0.1])
fig.update_yaxes(tickfont=dict(color=INK, size=12), showgrid=False)
show(style_fig(fig, height=30 * len(leaders) + 40))

# ---------- efficiency scatter ----------

section('Scoring load vs. efficiency',
        'Usage rate (share of team plays a player finishes) against true shooting %. '
        'Each logo is a player; top-right players carry a big load efficiently.')

scorers = qualified[qualified['MIN'] >= max(min_minutes, 24)]
if len(scorers) < 5:
    scorers = qualified
x_rng = scorers['USG_PCT'].max() - scorers['USG_PCT'].min()
y_rng = scorers['TS_PCT'].max() - scorers['TS_PCT'].min()
fig = go.Figure(go.Scatter(
    x=scorers['USG_PCT'], y=scorers['TS_PCT'], mode='markers',
    marker=dict(size=22, color='rgba(0,0,0,0)'),
    customdata=scorers[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'PTS']],
    hovertemplate='<b>%{customdata[0]}</b> (%{customdata[1]})<br>%{customdata[2]:.1f} pts<br>'
                  'Usage %{x:.1%} · TS %{y:.1%}<extra></extra>',
))
for row in scorers.itertuples():
    add_logo(fig, row.TEAM_ABBREVIATION, row.USG_PCT, row.TS_PCT,
             size=x_rng * 0.035, sizey=y_rng * 0.05)
# Name the top scorers directly; everyone else is on hover
for row in scorers.nlargest(8, 'PTS').itertuples():
    fig.add_annotation(x=row.USG_PCT, y=row.TS_PCT, text=row.PLAYER_NAME.split(' ', 1)[-1],
                       showarrow=False, yshift=16, font=dict(color=INK, size=11))
avg_line = dict(color='rgba(255,255,255,0.22)', width=1, dash='dash')
fig.add_vline(x=scorers['USG_PCT'].mean(), line=avg_line)
fig.add_hline(y=scorers['TS_PCT'].mean(), line=avg_line)
fig.update_xaxes(title='Usage rate', tickformat='.0%',
                 range=[scorers['USG_PCT'].min() - x_rng * 0.05, scorers['USG_PCT'].max() + x_rng * 0.05])
fig.update_yaxes(title='True shooting %', tickformat='.0%',
                 range=[scorers['TS_PCT'].min() - y_rng * 0.06, scorers['TS_PCT'].max() + y_rng * 0.08])
show(style_fig(fig, height=560))

# ---------- player profile ----------

section('Player profile', 'Percentile rank among qualified players (100 = best in the league).')

by_pts = qualified.sort_values('PTS', ascending=False)
names = by_pts['PLAYER_NAME'].tolist()
p1, p2 = st.columns(2)
name = p1.selectbox('Player', names, index=0)
compare = p2.selectbox('Compare with', ['(none)'] + [n for n in names if n != name])

PROFILE = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'TS_PCT', 'USG_PCT', 'NET_RATING', 'PIE']
PROFILE_LABELS = {v[0]: k for k, v in STATS.items()}
pct = qualified[PROFILE].rank(pct=True) * 100
pct.index = qualified['PLAYER_NAME']

by_name = qualified.set_index('PLAYER_NAME')
player = by_name.loc[name]
team_header(player['TEAM_ABBREVIATION'], title=name, subtitle=team(player['TEAM_ABBREVIATION'])['name'])

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric('Points', f"{player['PTS']:.1f}")
k2.metric('Rebounds', f"{player['REB']:.1f}")
k3.metric('Assists', f"{player['AST']:.1f}")
k4.metric('True shooting', f"{player['TS_PCT']:.1%}")
k5.metric('Games · min', f"{int(player['GP'])} · {player['MIN']:.0f}")

labels = [PROFILE_LABELS[c] for c in PROFILE][::-1]
fig = go.Figure()
series = [(name, team(player['TEAM_ABBREVIATION'])['accent'])]
if compare != '(none)':
    other_color = team(by_name.loc[compare, 'TEAM_ABBREVIATION'])['accent']
    # Two players from similar-colored teams would be indistinguishable
    series.append((compare, other_color if other_color != series[0][1] else COMPARE_COLOR))
for player_name, color in series:
    values = pct.loc[player_name]
    raw = by_name.loc[player_name]
    fig.add_trace(go.Bar(
        x=values[PROFILE][::-1], y=labels, orientation='h', name=player_name,
        marker=dict(color=color, cornerradius=4),
        customdata=[STATS[l][1].format(raw[c]) for l, c in zip(labels, PROFILE[::-1])],
        hovertemplate='<b>' + player_name + '</b><br>%{y}: %{customdata}<br>'
                      '%{x:.0f}th percentile<extra></extra>',
    ))
fig.add_vline(x=50, line=dict(color='rgba(255,255,255,0.22)', width=1, dash='dash'))
fig.update_xaxes(range=[0, 100], title='Percentile', ticksuffix='')
fig.update_yaxes(tickfont=dict(color=INK, size=12), showgrid=False)
style_fig(fig, height=460, legend=len(series) > 1)
fig.update_layout(barmode='group', bargap=0.3, bargroupgap=0.08)
show(fig)
st.caption("Dashed line = league median. Percentiles recompute when you change the filters above.")
