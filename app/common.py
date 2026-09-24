"""
Shared helpers for the demo app pages: cached data loaders, team logos as
URLs, and a Plotly theme that matches the app's dark design.
"""

import os

import pandas as pd
import streamlit as st

# streamlit_app.py puts scripts/ on the path and runs from the repo root, so
# every data path below is repo-relative, the same as for the command-line scripts.
import config
import features
import player_pool
from predict_games import NBAPredictor, load_injury_impacts
from teams import team

# Design tokens, taken from the Figma matchup card
BG = '#09090b'
SURFACE = '#111118'
INK = 'rgba(255,255,255,0.92)'
INK_MUTED = 'rgba(255,255,255,0.45)'
GRID = 'rgba(255,255,255,0.07)'
NEUTRAL = '#52525b'
DISPLAY_FONT = "'Barlow Condensed', sans-serif"
BODY_FONT = "'Inter', system-ui, sans-serif"


# ---------- data ----------

@st.cache_resource
def load_predictor():
    predictor = NBAPredictor()
    if not predictor.load_model():
        return None
    return predictor


@st.cache_data
def load_games():
    return features.load_games()


@st.cache_resource
def load_builder():
    return features.FeatureBuilder(load_games())


@st.cache_resource
def load_injuries():
    return load_injury_impacts()


@st.cache_data
def load_player_stats():
    return pd.read_csv(config.player_stats_file())


@st.cache_data
def load_rosters():
    """(season, rosters) from fetch_rosters.py, or (None, None) if it hasn't been run."""
    path = config.latest_rosters_file()
    if path is None:
        return None, None
    season = os.path.basename(path)[len('nba_rosters_'):-len('.csv')]  # e.g. '2026-27'
    return season, pd.read_csv(path, dtype={'espn_id': str})


@st.cache_data
def load_espn_stats(season):
    path = config.espn_stats_file(season)
    return pd.read_csv(path, dtype={'espn_id': str}) if os.path.exists(path) else None


def clear_roster_caches():
    load_rosters.clear()
    load_espn_stats.clear()
    load_player_pool.clear()


@st.cache_data
def load_player_pool(use_current=True):
    """
    Players on current rosters averaging 15+ minutes, as a dict:
      pool       one row per player, current team in TEAM_ABBREVIATION
      season     the season the stats are from
      current    True if those are this season's (ESPN) stats
      has_current  whether this season's stats exist at all
      emerging   rookies/breakouts new to 15+ minutes this season (or None)
      rosters, roster_season, updated
    Falls back to last season's stats file, unfiltered by roster, when
    fetch_rosters.py hasn't been run.
    """
    last_stats = load_player_stats()
    roster_season, rosters = load_rosters()
    if rosters is None:
        pool = last_stats[last_stats['MIN'] >= player_pool.MIN_MINUTES].copy()
        pool['STATS_TEAM'] = pool['TEAM_ABBREVIATION']
        return {'pool': pool.reindex(columns=player_pool.COLUMNS), 'season': config.current_season(),
                'current': False, 'has_current': False, 'emerging': None, 'rosters': None,
                'roster_season': None, 'updated': None}

    espn = load_espn_stats(roster_season)
    has_current = espn is not None and not espn.empty
    current_pool = player_pool.from_current_season(rosters, espn) if has_current else None
    if use_current and has_current:
        pool, season = current_pool, roster_season
    else:
        pool, season = player_pool.from_previous_season(rosters, last_stats), config.previous_season(roster_season)
    return {
        'pool': pool, 'season': season, 'current': pool is current_pool,
        'has_current': has_current, 'rosters': rosters, 'roster_season': roster_season,
        'emerging': player_pool.emerging_players(current_pool, last_stats) if has_current else None,
        'updated': rosters['updated'].iloc[0] if 'updated' in rosters else None,
    }


@st.cache_data
def load_schedule():
    """Newest schedule from fetch_schedule.py, or None if it hasn't been run."""
    path = config.latest_schedule_file()
    if path is None:
        return None
    schedule = pd.read_csv(path, parse_dates=['date'], dtype={'game_id': str})
    schedule['broadcast'] = schedule['broadcast'].fillna('')
    schedule['city'] = schedule['city'].fillna('')
    return schedule.sort_values('tip_et').reset_index(drop=True)


@st.cache_data
def team_game_log():
    """One row per team per game, with running record and rolling margin."""
    long = features._long_format(load_games())
    long = long.sort_values(['team', 'date']).reset_index(drop=True)
    grouped = long.groupby('team')
    long['game_no'] = grouped.cumcount() + 1
    long['wins'] = grouped['won'].cumsum()
    long['over_500'] = long['wins'] * 2 - long['game_no']
    long['rolling_margin'] = grouped['margin'].transform(
        lambda m: m.rolling(10, min_periods=1).mean())
    games = load_games()
    opponents = pd.concat([
        pd.DataFrame({'date': games['date'], 'team': games['home_team'], 'opponent': games['away_team']}),
        pd.DataFrame({'date': games['date'], 'team': games['away_team'], 'opponent': games['home_team']}),
    ])
    return long.merge(opponents, on=['date', 'team'], how='left')


@st.cache_data
def team_summary():
    """Season totals per team: record, points for/against, home/road margin."""
    log = team_game_log()
    rows = []
    for abbr, g in log.groupby('team'):
        rows.append({
            'team': abbr,
            'name': team(abbr)['name'],
            'gp': len(g),
            'wins': int(g['won'].sum()),
            'losses': int(len(g) - g['won'].sum()),
            'win_pct': g['won'].mean(),
            'pts_for': g['pts_for'].mean(),
            'pts_against': g['pts_against'].mean(),
            'margin': g['margin'].mean(),
            'home_margin': g.loc[g['is_home'], 'margin'].mean(),
            'road_margin': g.loc[~g['is_home'], 'margin'].mean(),
            'last10_margin': g.tail(10)['margin'].mean(),
        })
    return pd.DataFrame(rows)


# ---------- logos ----------

def logo_url(abbr):
    """URL of a team logo, served from static/logos (see .streamlit/config.toml)."""
    return f"app/static/logos/{abbr}.png"


def add_logo(fig, abbr, x, y, size, xref='x', yref='y', xanchor='center',
             yanchor='middle', opacity=1.0, sizey=None):
    """Place a team logo on a Plotly figure at (x, y), sized in axis units."""
    fig.add_layout_image(
        source=logo_url(abbr), x=x, y=y, xref=xref, yref=yref,
        sizex=size, sizey=sizey if sizey is not None else size,
        xanchor=xanchor, yanchor=yanchor, sizing='contain',
        opacity=opacity, layer='above',
    )


# ---------- chart theme ----------

def style_fig(fig, height=420, title=None, legend=False):
    fig.update_layout(
        height=height,
        title=dict(text=title or '', font=dict(family=DISPLAY_FONT, size=20, color=INK),
                   x=0, xanchor='left'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family=BODY_FONT, size=12, color=INK_MUTED),
        margin=dict(l=8, r=8, t=48 if title else 8, b=8),
        showlegend=legend,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0,
                    bgcolor='rgba(0,0,0,0)', font=dict(color=INK)),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor='rgba(255,255,255,0.15)',
                        font=dict(family=BODY_FONT, color=INK, size=12)),
        bargap=0.25,
    )
    axis = dict(gridcolor=GRID, zerolinecolor='rgba(255,255,255,0.18)',
                linecolor=GRID, tickfont=dict(color=INK_MUTED),
                title_font=dict(color=INK_MUTED, size=12))
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    return fig


def show(fig):
    # Charts fill the column width by default
    st.plotly_chart(fig, config={'displayModeBar': False, 'scrollZoom': False})


def team_label(abbr):
    return f"{abbr} - {team(abbr)['name']}"


def section(title, caption=None):
    st.markdown(f"<h3 class='section-title'>{title}</h3>", unsafe_allow_html=True)
    if caption:
        st.caption(caption)
