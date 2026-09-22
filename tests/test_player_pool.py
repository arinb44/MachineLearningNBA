"""
Tests for the Players page pool in scripts/player_pool.py and the ESPN
stats parsing in scripts/fetch_rosters.py.
"""

import pandas as pd
import pytest

import player_pool
from fetch_rosters import parse_stats


def make_rosters():
    return pd.DataFrame([
        # espn_id, player, current team, experience
        ('1', 'Star Guard', 'BOS', 6),
        ('2', 'Traded Wing', 'ATL', 4),       # played for OKC last season
        ('3', 'Deep Bench', 'BOS', 3),        # under 15 minutes
        ('4', 'Big Rookie', 'ATL', 0),        # no NBA minutes last season
        ('5', 'Late Bloomer', 'BOS', 2),      # 9 minutes last season
        ('6', 'Mouhamed Gueye', 'ATL', 2),    # spelled differently by the NBA API
    ], columns=['espn_id', 'player', 'team', 'experience']).assign(
        position='G', age=25, headshot='', updated='2026-09-22 20:00 UTC')


def make_last_season():
    return pd.DataFrame([
        # name, team last season, GP, MIN, PTS, AGE
        ('Star Guard', 'BOS', 70, 34.0, 25.0, 27),
        ('Traded Wing', 'OKC', 65, 28.0, 14.0, 25),
        ('Deep Bench', 'BOS', 40, 8.0, 2.0, 24),
        ('Late Bloomer', 'BOS', 30, 9.0, 3.0, 22),
        ('Mouhamadou Gueye', 'ATL', 60, 22.7, 8.0, 23),
        ('Unsigned Vet', 'MIA', 50, 25.0, 11.0, 35),  # not on any current roster
    ], columns=['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', 'PTS', 'AGE'])


def make_espn_stats():
    return pd.DataFrame([
        # espn_id, name, stats team, GP, MIN, PTS, FGA, FTA, TOV
        ('1', 'Star Guard', 'BOS', 10, 35.0, 27.0, 19.0, 7.0, 3.0),
        ('3', 'Deep Bench', 'BOS', 6, 10.0, 3.0, 3.0, 0.5, 0.4),
        ('4', 'Big Rookie', 'ATL', 10, 29.0, 16.0, 13.0, 4.0, 2.5),
        ('5', 'Late Bloomer', 'BOS', 10, 24.0, 11.0, 9.0, 2.0, 1.0),
    ], columns=['espn_id', 'player', 'stats_team', 'GP', 'MIN', 'PTS', 'FGA', 'FTA', 'TOV'])


def test_previous_season_pool_uses_current_teams_and_rosters():
    pool = player_pool.from_previous_season(make_rosters(), make_last_season())
    teams = dict(zip(pool['PLAYER_NAME'], pool['TEAM_ABBREVIATION']))
    # 15+ minute players on a current roster only; the bench player and the
    # unsigned veteran are out, and the NBA API's spelling still matches
    assert set(teams) == {'Star Guard', 'Traded Wing', 'Mouhamed Gueye'}
    assert teams['Traded Wing'] == 'ATL'
    traded = pool.set_index('PLAYER_NAME').loc['Traded Wing']
    assert traded['STATS_TEAM'] == 'OKC'
    assert traded['AGE'] == 25  # age from the current roster, not last season's file


def test_current_season_pool_filters_minutes_and_adds_shooting():
    pool = player_pool.from_current_season(make_rosters(), make_espn_stats())
    assert set(pool['PLAYER_NAME']) == {'Star Guard', 'Big Rookie', 'Late Bloomer'}
    star = pool.set_index('PLAYER_NAME').loc['Star Guard']
    assert star['TS_PCT'] == pytest.approx(27.0 / (2 * (19.0 + 0.44 * 7.0)))
    assert 0 < star['USG_PCT'] < 1


def test_emerging_players_are_rookies_and_breakouts():
    pool = player_pool.from_current_season(make_rosters(), make_espn_stats())
    new = player_pool.emerging_players(pool, make_last_season()).set_index('PLAYER_NAME')
    assert set(new.index) == {'Big Rookie', 'Late Bloomer'}
    assert new.loc['Big Rookie', 'KIND'] == 'Rookie'
    assert new.loc['Late Bloomer', 'KIND'] == 'Breakout'
    assert new.loc['Late Bloomer', 'LAST_MIN'] == 9.0


def test_parse_stats_maps_teams_and_scales_percentages():
    data = {
        'categories': [
            {'name': 'general', 'names': ['gamesPlayed', 'avgMinutes']},
            {'name': 'offensive', 'names': ['avgPoints', 'fieldGoalPct', 'threePointFieldGoalPct', 'freeThrowPct']},
        ],
        'athletes': [{
            'athlete': {'id': '9', 'displayName': 'Some Guard', 'teamShortName': 'GS'},
            'categories': [
                {'name': 'general', 'totals': ['12', '31.5']},
                {'name': 'offensive', 'totals': ['22.4', '47.5', '38.0', '88.0']},
            ],
        }],
    }
    row = parse_stats(data).iloc[0]
    assert row['stats_team'] == 'GSW'
    assert (row['GP'], row['MIN'], row['PTS']) == (12, 31.5, 22.4)
    assert row['FG_PCT'] == pytest.approx(0.475)
