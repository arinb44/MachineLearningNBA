"""Players page: rotation players on current rosters, their stats, and who's emerging."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import fetch_rosters
import player_pool
from app.common import (INK, INK_MUTED, NEUTRAL, SURFACE, Calibrating, add_logo,
                        clear_roster_caches, load_player_pool, section, show, style_fig,
                        team, team_label)
from app.components import player_header

COMPARE_COLOR = '#a1a1aa'

STATS = {
    'Points': ('PTS', '{:.1f}'),
    'Rebounds': ('REB', '{:.1f}'),
    'Assists': ('AST', '{:.1f}'),
    'Steals': ('STL', '{:.1f}'),
    'Blocks': ('BLK', '{:.1f}'),
    '3-pointers made': ('FG3M', '{:.1f}'),
    'True shooting %': ('TS_PCT', '{:.1%}'),
    'Field goal %': ('FG_PCT', '{:.1%}'),
    '3-point %': ('FG3_PCT', '{:.1%}'),
    'Free throw %': ('FT_PCT', '{:.1%}'),
    'Plus-minus': ('PLUS_MINUS', '{:+.1f}'),
    'Net rating': ('NET_RATING', '{:+.1f}'),
    'Player impact (PIE)': ('PIE', '{:.3f}'),
    'Usage %': ('USG_PCT', '{:.1%}'),
    'Minutes': ('MIN', '{:.1f}'),
}
MIN_MINUTES = player_pool.MIN_MINUTES

st.title('Players')
calib = Calibrating()

# ---------- roster refresh ----------

top1, top2 = st.columns([3, 1], vertical_alignment='bottom')
if top2.button('Refresh rosters', icon=':material/refresh:', width='stretch',
               help='Pull the latest rosters and this season\'s stats from ESPN'):
    try:
        summary = fetch_rosters.refresh(lambda i, n: calib.to(5 + 80 * i // n))
        clear_roster_caches()
        st.toast(f"Rosters refreshed: {summary['players']} players"
                 + (f", {summary['with_stats']} with {summary['season']} stats"
                    if summary['with_stats'] else ''), icon=':material/check_circle:')
    except Exception as exc:  # network trouble shouldn't take the page down
        st.error(f"Couldn't reach ESPN to refresh rosters ({exc}). Showing the last saved rosters.")

info = load_player_pool(use_current=True)
if info['has_current']:
    choice = top1.radio('Stats from', [info['roster_season'], 'Last season'], horizontal=True)
    if choice == 'Last season':
        info = load_player_pool(use_current=False)
players = info['pool']
calib.to(25)

source = 'ESPN' if info['current'] else 'the NBA stats API'
if info['rosters'] is not None:
    top1.caption(
        f"{len(players)} players on current rosters averaging {MIN_MINUTES}+ minutes, with "
        f"{info['season']} per-game stats from {source}. "
        f"Rosters updated {info['updated'] or 'recently'}.")
else:
    top1.caption(f"{info['season']} per-game stats for players averaging {MIN_MINUTES}+ minutes. "
                 'Run `python scripts/fetch_rosters.py` for current rosters.')

# ---------- new in the rotation ----------

if info['rosters'] is not None:
    section('New in the rotation',
            f"Rookies and breakout players who now average {MIN_MINUTES}+ minutes "
            f"but didn't last season.")
    emerging = info['emerging']
    if emerging is None:
        st.info(f"Rookies and breakout players appear here once {info['roster_season']} "
                f"games are played and they average {MIN_MINUTES}+ minutes. Press "
                '**Refresh rosters** during the season to pull the latest.')
        rookies = info['rosters'][info['rosters']['experience'] == 0]
        with st.expander(f"Rookies on current rosters ({len(rookies)})"):
            st.dataframe(
                rookies[['headshot', 'player', 'team', 'position', 'age']].sort_values(['team', 'player']),
                hide_index=True, width='stretch', row_height=48,
                column_config={'headshot': st.column_config.ImageColumn('', width='small'),
                               'player': 'Player', 'team': 'Team', 'position': 'Pos', 'age': 'Age'},
            )
    elif emerging.empty:
        st.caption('No new rotation players yet.')
    else:
        table = emerging.assign(
            LAST_MIN=emerging['LAST_MIN'].map(lambda m: '-' if pd.isna(m) else f"{m:.1f}"))
        st.dataframe(
            table[['HEADSHOT', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'KIND', 'GP', 'MIN',
                   'LAST_MIN', 'PTS', 'REB', 'AST']],
            hide_index=True, width='stretch', row_height=48,
            column_config={
                'HEADSHOT': st.column_config.ImageColumn('', width='small'),
                'PLAYER_NAME': 'Player', 'TEAM_ABBREVIATION': 'Team', 'KIND': 'Type',
                'GP': 'Games', 'MIN': st.column_config.NumberColumn('Min', format='%.1f'),
                'LAST_MIN': 'Min last season',
                'PTS': st.column_config.NumberColumn('Pts', format='%.1f'),
                'REB': st.column_config.NumberColumn('Reb', format='%.1f'),
                'AST': st.column_config.NumberColumn('Ast', format='%.1f'),
            },
        )

# ---------- filters ----------

max_gp = int(players['GP'].max()) if not players.empty else 1
f1, f2 = st.columns([1, 1])
min_games = f1.slider('Minimum games played', 1, max_gp, min(20, max(1, max_gp // 4)))
min_minutes = f2.slider('Minimum minutes per game', MIN_MINUTES, 36, MIN_MINUTES)
qualified = players[(players['GP'] >= min_games) & (players['MIN'] >= min_minutes)].copy()
st.caption(f"{len(qualified)} of {len(players)} players match these filters.")
if qualified.empty:
    calib.done()
    st.warning('No players match these filters.')
    st.stop()

# Only offer stats this season's source actually has (ESPN has no PIE or net rating)
STATS = {name: spec for name, spec in STATS.items() if qualified[spec[0]].notna().any()}

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
    customdata=leaders[['TEAM_ABBREVIATION', 'GP', 'MIN', 'STATS_TEAM']],
    hovertemplate='<b>%{y}</b> (%{customdata[0]})<br>' + stat_name +
                  ': %{text}<br>%{customdata[1]} games, %{customdata[2]:.1f} min'
                  '<br>Stats with %{customdata[3]}<extra></extra>',
))
# Team logo at the start of each bar, just right of the player name
for i, abbr in enumerate(leaders['TEAM_ABBREVIATION']):
    add_logo(fig, abbr, 0.005, i, size=0.04, sizey=0.85, xref='paper', xanchor='left')
fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False,
                 range=[lo - (hi - lo) * 0.06, hi + (hi - lo) * 0.1])
fig.update_yaxes(tickfont=dict(color=INK, size=12), showgrid=False)
show(style_fig(fig, height=30 * len(leaders) + 40))

calib.to(40)

# ---------- efficiency scatter ----------

section('Scoring load vs. efficiency',
        'Usage rate (share of team plays a player finishes) against true shooting %. '
        'Top-right players carry a big load efficiently. Pick teams or players to highlight them.')

scorers = qualified[qualified['MIN'] >= max(min_minutes, 24)]
if len(scorers) < 5:
    scorers = qualified
h1, h2 = st.columns(2)
hl_teams = h1.multiselect('Highlight teams', sorted(scorers['TEAM_ABBREVIATION'].unique()),
                          format_func=team_label, placeholder='Choose teams')
hl_players = h2.multiselect('Highlight players',
                            scorers.sort_values('PTS', ascending=False)['PLAYER_NAME'].tolist(),
                            placeholder='Choose players')

highlighted = scorers['TEAM_ABBREVIATION'].isin(hl_teams) | scorers['PLAYER_NAME'].isin(hl_players)
hover = ('<b>%{customdata[0]}</b> (%{customdata[1]})<br>%{customdata[2]:.1f} pts<br>'
         'Usage %{x:.1%} · TS %{y:.1%}<extra></extra>')
cols = ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'PTS']
fig = go.Figure()

# Everyone not highlighted: a quiet gray field (brighter when nothing is picked)
rest = scorers[~highlighted]
fig.add_trace(go.Scatter(
    x=rest['USG_PCT'], y=rest['TS_PCT'], mode='markers', name='Other players',
    marker=dict(size=9, color=NEUTRAL if highlighted.any() else '#a1a1aa',
                opacity=0.45 if highlighted.any() else 0.8,
                line=dict(color=SURFACE, width=1)),
    customdata=rest[cols], hovertemplate=hover, showlegend=bool(highlighted.any()),
))
# Highlighted players: one trace per team, in team colors, drawn on top
picked = scorers[highlighted]
for abbr, group in picked.groupby('TEAM_ABBREVIATION'):
    fig.add_trace(go.Scatter(
        x=group['USG_PCT'], y=group['TS_PCT'], mode='markers', name=team(abbr)['name'],
        marker=dict(size=13, color=team(abbr)['accent'], line=dict(color=SURFACE, width=2)),
        customdata=group[cols], hovertemplate=hover,
    ))

# Name the highlighted players (or the top scorers when nothing is picked)
labeled = picked if highlighted.any() else scorers.nlargest(8, 'PTS')
if len(labeled) <= 25:
    for row in labeled.itertuples():
        fig.add_annotation(x=row.USG_PCT, y=row.TS_PCT, text=row.PLAYER_NAME, showarrow=False,
                           yshift=14, font=dict(color=INK if highlighted.any() else INK_MUTED, size=11))

x_rng = scorers['USG_PCT'].max() - scorers['USG_PCT'].min()
y_rng = scorers['TS_PCT'].max() - scorers['TS_PCT'].min()
avg_line = dict(color='rgba(255,255,255,0.22)', width=1, dash='dash')
fig.add_vline(x=scorers['USG_PCT'].mean(), line=avg_line)
fig.add_hline(y=scorers['TS_PCT'].mean(), line=avg_line)
fig.update_xaxes(title='Usage rate', tickformat='.0%',
                 range=[scorers['USG_PCT'].min() - x_rng * 0.05, scorers['USG_PCT'].max() + x_rng * 0.05])
fig.update_yaxes(title='True shooting %', tickformat='.0%',
                 range=[scorers['TS_PCT'].min() - y_rng * 0.06, scorers['TS_PCT'].max() + y_rng * 0.08])
show(style_fig(fig, height=560, legend=bool(highlighted.any())))
calib.to(70)

# ---------- player profile ----------

section('Player profile', 'Percentile rank among qualified players (100 = best in the league).')

by_pts = qualified.sort_values('PTS', ascending=False)
names = by_pts['PLAYER_NAME'].tolist()
p1, p2 = st.columns(2)
name = p1.selectbox('Player', names, index=0)
compare = p2.selectbox('Compare with', ['(none)'] + [n for n in names if n != name])

PROFILE = [c for c in ('PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'TS_PCT', 'USG_PCT', 'NET_RATING', 'PIE')
           if qualified[c].notna().any()]
PROFILE_LABELS = {v[0]: k for k, v in STATS.items()}
pct = qualified[PROFILE].rank(pct=True) * 100
pct.index = qualified['PLAYER_NAME']

by_name = qualified.set_index('PLAYER_NAME')
player = by_name.loc[name]
player_header({**player.to_dict(), 'PLAYER_NAME': name})

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
st.caption('Dashed line = league median. Percentiles recompute when you change the filters above.'
           + (' Usage % is estimated from ESPN box-score totals.' if info['current'] else ''))
calib.done()
