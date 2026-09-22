"""Teams page: league-wide team charts, with logos marking every team."""

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.common import (INK, INK_MUTED, NEUTRAL, add_logo, load_player_stats,
                        section, show, style_fig, team, team_game_log,
                        team_label, team_summary)
from app.components import team_header

HOME_COLOR = '#f58426'
ROAD_COLOR = '#5b9cf5'

st.title('Teams')
st.caption('How all 30 teams stack up this season, from every game result so far.')

summary = team_summary()
log = team_game_log()

if os.path.exists('data/input/adjusted_team_rankings.csv'):
    power = pd.read_csv('data/input/adjusted_team_rankings.csv')[['team', 'power_rating']]
    summary = summary.merge(power, on='team', how='left')

# ---------- power rankings ----------

section('Power rankings')
metrics = {
    'Avg point margin': ('margin', '{:+.1f}'),
    'Win %': ('win_pct', '{:.3f}'),
    'Last 10 games margin': ('last10_margin', '{:+.1f}'),
    'Points scored per game': ('pts_for', '{:.1f}'),
    'Points allowed per game': ('pts_against', '{:.1f}'),
}
if 'power_rating' in summary:
    metrics['Injury-adjusted power rating'] = ('power_rating', '{:.1f}')
metric_name = st.selectbox('Rank by', list(metrics), label_visibility='collapsed')
col, fmt = metrics[metric_name]
# Best team first; for points allowed, fewer is better
ranked = summary.dropna(subset=[col]).sort_values(col, ascending=(col == 'pts_against'))
ranked = ranked.reset_index(drop=True)
order = ranked['team'].tolist()[::-1]  # plotly draws the first category at the bottom

# Win% and ratings are all-positive; margins straddle zero
baseline = 0 if col in ('margin', 'last10_margin') else ranked[col].min() * 0.97
span = ranked[col].max() - min(baseline, ranked[col].min())
fig = go.Figure(go.Bar(
    x=ranked[col] - baseline, base=baseline, y=ranked['team'], orientation='h',
    marker=dict(color=[team(t)['accent'] for t in ranked['team']], opacity=0.9,
                cornerradius=4),
    customdata=ranked[['name', 'wins', 'losses']],
    text=[fmt.format(v) for v in ranked[col]], textposition='outside',
    textfont=dict(color=INK, size=12), cliponaxis=False,
    hovertemplate='<b>%{customdata[0]}</b> (%{customdata[1]}-%{customdata[2]})<br>'
                  + metric_name + ': %{text}<extra></extra>',
))
for i, abbr in enumerate(order):
    add_logo(fig, abbr, -0.005, i, size=0.05, sizey=0.9, xref='paper', xanchor='right')
fig.update_yaxes(categoryorder='array', categoryarray=order, showticklabels=False,
                 showgrid=False)
fig.update_xaxes(range=[min(baseline, ranked[col].min()) - span * 0.07,
                        ranked[col].max() + span * 0.12], zeroline=col in ('margin', 'last10_margin'))
style_fig(fig, height=30 * len(ranked) + 40)
fig.update_layout(margin=dict(l=44, r=8, t=8, b=8), bargap=0.3)
show(fig)

# ---------- offense vs defense ----------

section('Offense vs. defense', 'Points scored against points allowed per game. '
        'Up and to the right is better; the dashed lines are league averages.')

x_avg, y_avg = summary['pts_for'].mean(), summary['pts_against'].mean()
fig = go.Figure(go.Scatter(
    x=summary['pts_for'], y=summary['pts_against'], mode='markers',
    marker=dict(size=34, color='rgba(0,0,0,0)'),
    customdata=summary[['name', 'wins', 'losses', 'margin']],
    hovertemplate='<b>%{customdata[0]}</b> (%{customdata[1]}-%{customdata[2]})<br>'
                  'Scored %{x:.1f} · Allowed %{y:.1f}<br>Margin %{customdata[3]:+.1f}<extra></extra>',
))
x_pad = (summary['pts_for'].max() - summary['pts_for'].min()) * 0.08
y_pad = (summary['pts_against'].max() - summary['pts_against'].min()) * 0.08
logo_size = max(summary['pts_for'].max() - summary['pts_for'].min(),
                summary['pts_against'].max() - summary['pts_against'].min()) * 0.075
for row in summary.itertuples():
    add_logo(fig, row.team, row.pts_for, row.pts_against, size=logo_size)
avg_line = dict(color='rgba(255,255,255,0.22)', width=1, dash='dash')
fig.add_vline(x=x_avg, line=avg_line)
fig.add_hline(y=y_avg, line=avg_line)
x_lo, x_hi = summary['pts_for'].min() - x_pad, summary['pts_for'].max() + x_pad
y_lo, y_hi = summary['pts_against'].min() - y_pad, summary['pts_against'].max() + y_pad
corner = dict(showarrow=False, font=dict(color=INK_MUTED, size=11, family="'Barlow Condensed'"))
fig.add_annotation(x=x_hi, y=y_lo, text='GOOD OFFENSE · GOOD DEFENSE', xanchor='right', yanchor='top', **corner)
fig.add_annotation(x=x_lo, y=y_hi, text='POOR OFFENSE · POOR DEFENSE', xanchor='left', yanchor='bottom', **corner)
fig.update_xaxes(title='Points scored per game', range=[x_lo, x_hi])
# Reversed so that stingier defenses sit higher up
fig.update_yaxes(title='Points allowed per game', range=[y_hi, y_lo])
show(style_fig(fig, height=560))

# ---------- season race ----------

section('Season race', 'Games above or below .500 after every game played.')

top = summary.sort_values('win_pct', ascending=False)['team'].tolist()
picked = st.multiselect('Teams', sorted(summary['team']), default=top[:5],
                        format_func=team_label, max_selections=8)
fig = go.Figure()
max_game = log['game_no'].max()
for abbr in picked:
    g = log[log['team'] == abbr]
    fig.add_trace(go.Scatter(
        x=g['game_no'], y=g['over_500'], mode='lines', name=abbr,
        line=dict(color=team(abbr)['accent'], width=2),
        customdata=g[['wins', 'opponent', 'margin']].assign(losses=g['game_no'] - g['wins']),
        hovertemplate=f'<b>{abbr}</b> game %{{x}}: %{{customdata[0]}}-%{{customdata[3]}}<br>'
                      'vs %{customdata[1]} (%{customdata[2]:+d})<extra></extra>',
    ))
    last = g.iloc[-1]
    y_span = max(log['over_500'].abs().max(), 10)
    add_logo(fig, abbr, last['game_no'] + 1, last['over_500'], size=5,
             sizey=y_span * 0.14, xanchor='left')
fig.add_hline(y=0, line=dict(color='rgba(255,255,255,0.25)', width=1))
fig.update_xaxes(title='Games played', range=[0, max_game + 8], showgrid=False)
fig.update_yaxes(title='Games over .500')
show(style_fig(fig, height=440, legend=True))

# ---------- home vs road ----------

section('Home court', 'Average point margin at home vs. on the road, sorted by the size of the gap.')

hr = summary.assign(gap=summary['home_margin'] - summary['road_margin'])
hr = hr.sort_values('gap').reset_index(drop=True)
fig = go.Figure()
for row in hr.itertuples():
    fig.add_trace(go.Scatter(
        x=[row.road_margin, row.home_margin], y=[row.team, row.team], mode='lines',
        line=dict(color='rgba(255,255,255,0.18)', width=2), hoverinfo='skip',
        showlegend=False,
    ))
for label, col, color in (('Road', 'road_margin', ROAD_COLOR), ('Home', 'home_margin', HOME_COLOR)):
    fig.add_trace(go.Scatter(
        x=hr[col], y=hr['team'], mode='markers', name=label,
        marker=dict(size=10, color=color, line=dict(color='#09090b', width=2)),
        customdata=hr[['name', 'gap']],
        hovertemplate='<b>%{customdata[0]}</b><br>' + label +
                      ' margin %{x:+.1f}<br>Home edge %{customdata[1]:+.1f}<extra></extra>',
    ))
for i, abbr in enumerate(hr['team']):
    add_logo(fig, abbr, -0.005, i, size=0.05, sizey=0.9, xref='paper', xanchor='right')
fig.update_yaxes(categoryorder='array', categoryarray=hr['team'].tolist(),
                 showticklabels=False, showgrid=False)
fig.update_xaxes(title='Average point margin', zeroline=True)
style_fig(fig, height=30 * len(hr) + 60, legend=True)
fig.update_layout(margin=dict(l=44, r=8, t=30, b=8))
show(fig)

# ---------- team drill-down ----------

section('Team detail')
abbr = st.selectbox('Team', sorted(summary['team']), index=sorted(summary['team']).index('OKC'),
                    format_func=team_label, label_visibility='collapsed')
row = summary.set_index('team').loc[abbr]
rank = summary['margin'].rank(ascending=False).astype(int).set_axis(summary['team'])[abbr]
team_header(abbr, subtitle=f"{team(abbr)['city']} · #{rank} by point margin")

c1, c2, c3, c4 = st.columns(4)
c1.metric('Record', f"{int(row.wins)}-{int(row.losses)}")
c2.metric('Avg margin', f"{row.margin:+.1f}")
c3.metric('Scored / allowed', f"{row.pts_for:.0f} / {row.pts_against:.0f}")
c4.metric('Last 10 margin', f"{row.last10_margin:+.1f}")

g = log[log['team'] == abbr]
fig = go.Figure(go.Bar(
    x=g['date'], y=g['margin'],
    marker=dict(color=[team(abbr)['accent'] if w else NEUTRAL for w in g['won']],
                cornerradius=2),
    customdata=g[['opponent', 'pts_for', 'pts_against']].assign(
        venue=g['is_home'].map({True: 'vs', False: '@'})),
    hovertemplate='%{x|%b %d} %{customdata[3]} %{customdata[0]}<br>'
                  '%{customdata[1]}-%{customdata[2]} (%{y:+d})<extra></extra>',
))
fig.update_xaxes(showgrid=False)
fig.update_yaxes(title='Point margin')
style_fig(fig, height=300, title='Game by game (wins in team color, losses in gray)')
fig.update_layout(bargap=0.15)
show(fig)

players = load_player_stats()
roster = players[players['TEAM_ABBREVIATION'] == abbr].sort_values('PTS', ascending=False).head(10)
if not roster.empty:
    roster = roster.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=roster['PTS'], y=roster['PLAYER_NAME'], orientation='h',
        marker=dict(color=team(abbr)['accent'], cornerradius=4),
        text=roster['PTS'].map('{:.1f}'.format), textposition='outside',
        textfont=dict(color=INK), cliponaxis=False,
        customdata=roster[['REB', 'AST', 'GP', 'MIN']],
        hovertemplate='<b>%{y}</b><br>%{x:.1f} pts · %{customdata[0]:.1f} reb · '
                      '%{customdata[1]:.1f} ast<br>%{customdata[2]} games, '
                      '%{customdata[3]:.1f} min<extra></extra>',
    ))
    fig.update_xaxes(showgrid=False, showticklabels=False, range=[0, roster['PTS'].max() * 1.15])
    fig.update_yaxes(tickfont=dict(color=INK, size=12))
    show(style_fig(fig, height=34 * len(roster) + 60, title='Top scorers (points per game)'))
