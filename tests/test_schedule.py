"""
Tests for parsing ESPN scoreboard events in scripts/fetch_schedule.py.
"""

from fetch_schedule import parse_game


def make_event(home='GS', away='NY', when='2026-10-21T02:30Z', season_type=2):
    return {
        'id': '401900001',
        'date': when,
        'season': {'type': season_type},
        'competitions': [{
            'competitors': [
                {'homeAway': 'home', 'team': {'abbreviation': home}},
                {'homeAway': 'away', 'team': {'abbreviation': away}},
            ],
            'venue': {'fullName': 'Chase Center',
                      'address': {'city': 'San Francisco', 'state': 'CA'}},
            'broadcasts': [{'names': ['ESPN']}],
            'neutralSite': False,
        }],
    }


def test_maps_espn_abbreviations_and_converts_to_eastern_time():
    game = parse_game(make_event(), '2026-10-20')
    assert (game['home_team'], game['away_team']) == ('GSW', 'NYK')
    # 02:30 UTC on Oct 21 is 10:30 PM Eastern on Oct 20
    assert game['time_et'] == '10:30 PM'
    assert game['tip_et'] == '2026-10-20 22:30'
    assert game['venue'] == 'Chase Center'
    assert game['city'] == 'San Francisco, CA'
    assert game['broadcast'] == 'ESPN'
    assert game['season_type'] == 'regular'


def test_skips_exhibitions_against_non_nba_teams():
    assert parse_game(make_event(away='RMA', season_type=1), '2026-10-05') is None
