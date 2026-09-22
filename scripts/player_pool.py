"""
Builds the player pool the demo's Players page draws from: everyone on a
current roster (fetch_rosters.py) who averages at least MIN_MINUTES, with
their current team and per-game stats.

Stats come from one season at a time:
  - the current season, from ESPN, once games have been played
  - otherwise last season, from the NBA stats API file (fetch_player_stats.py),
    which also carries the advanced stats (PIE, net rating, plus-minus)
"""

import numpy as np

from predict_games import _norm_name

MIN_MINUTES = 15

# NBA stats API spelling -> ESPN spelling, where normalizing isn't enough
NAME_ALIASES = {
    'mouhamadou gueye': 'mouhamed gueye',
}

COLUMNS = [
    'PLAYER_NAME', 'TEAM_ABBREVIATION', 'STATS_TEAM', 'POSITION', 'AGE', 'EXPERIENCE',
    'HEADSHOT', 'GP', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FG_PCT',
    'FG3_PCT', 'FT_PCT', 'TS_PCT', 'USG_PCT', 'PLUS_MINUS', 'NET_RATING', 'PIE',
]


def true_shooting(pts, fga, fta):
    attempts = 2 * (fga + 0.44 * fta)
    return (pts / attempts).where(attempts > 0)


def estimate_usage(stats):
    """
    Usage rate (share of team possessions a player finishes while on the
    floor), from season totals. Team totals are summed from every player's
    line for that team, since ESPN's player feed has no team totals.
    """
    totals = stats[['FGA', 'FTA', 'TOV', 'MIN']].mul(stats['GP'], axis=0)
    totals['team'] = stats['stats_team']
    team = totals.groupby('team')[['FGA', 'FTA', 'TOV', 'MIN']].transform('sum')
    player_poss = totals['FGA'] + 0.44 * totals['FTA'] + totals['TOV']
    team_poss = team['FGA'] + 0.44 * team['FTA'] + team['TOV']
    usage = player_poss * (team['MIN'] / 5) / (totals['MIN'] * team_poss)
    return usage.where(totals['MIN'] > 0).replace([np.inf, -np.inf], np.nan)


def _key(name):
    key = _norm_name(name)
    return NAME_ALIASES.get(key, key)


def _roster_fields(rosters):
    return rosters.rename(columns={
        'player': 'PLAYER_NAME', 'team': 'TEAM_ABBREVIATION', 'position': 'POSITION',
        'age': 'AGE', 'experience': 'EXPERIENCE', 'headshot': 'HEADSHOT',
    })


def _finish(pool, min_minutes):
    # Names key the app's pickers, so keep one row per name
    pool = pool[pool['MIN'] >= min_minutes].sort_values('MIN', ascending=False)
    pool = pool.drop_duplicates('PLAYER_NAME')
    return pool.reindex(columns=COLUMNS).reset_index(drop=True)


def from_current_season(rosters, espn_stats, min_minutes=MIN_MINUTES):
    """Pool from this season's ESPN stats, matched to rosters by ESPN id."""
    stats = espn_stats.copy()
    stats['espn_id'] = stats['espn_id'].astype(str)
    stats['TS_PCT'] = true_shooting(stats['PTS'], stats['FGA'], stats['FTA'])
    stats['USG_PCT'] = estimate_usage(stats)
    stats = stats.rename(columns={'stats_team': 'STATS_TEAM'}).drop(columns=['player'])

    roster = _roster_fields(rosters).assign(espn_id=rosters['espn_id'].astype(str))
    pool = roster.merge(stats, on='espn_id', how='inner')
    return _finish(pool, min_minutes)


def from_previous_season(rosters, nba_stats, min_minutes=MIN_MINUTES):
    """Pool from last season's NBA stats file, matched to rosters by name."""
    stats = nba_stats.copy()
    stats['key'] = stats['PLAYER_NAME'].map(_key)
    stats = stats.drop_duplicates('key').rename(columns={'TEAM_ABBREVIATION': 'STATS_TEAM'})
    # Name and age come from the current roster instead
    stats = stats.drop(columns=['PLAYER_NAME', 'AGE'], errors='ignore')

    roster = _roster_fields(rosters)
    roster['key'] = roster['PLAYER_NAME'].map(_key)
    pool = roster.merge(stats, on='key', how='inner')
    return _finish(pool, min_minutes)


def emerging_players(current_pool, nba_stats, min_minutes=MIN_MINUTES):
    """
    Players in this season's pool who weren't rotation players last season:
    rookies, and breakouts who averaged under min_minutes (or didn't play).
    """
    last = nba_stats.assign(key=nba_stats['PLAYER_NAME'].map(_key))
    last_min = last.drop_duplicates('key').set_index('key')['MIN']
    pool = current_pool.copy()
    pool['LAST_MIN'] = pool['PLAYER_NAME'].map(_key).map(last_min)
    new = pool[pool['LAST_MIN'].isna() | (pool['LAST_MIN'] < min_minutes)].copy()
    new['KIND'] = np.where(new['EXPERIENCE'].fillna(1) == 0, 'Rookie', 'Breakout')
    return new.sort_values('MIN', ascending=False).reset_index(drop=True)
