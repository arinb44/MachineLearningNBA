"""
Fetch current NBA rosters and this season's per-game player stats from
ESPN's public API (the data behind espn.com/nba/players).

Saves:
  data/input/nba_rosters_<season>.csv        every player on a current roster
  data/input/espn_player_stats_<season>.csv  per-game stats, once games are played

The demo's Players page builds its player pool from these: current teams from
the rosters, and only players averaging at least 15 minutes. Re-run this (or
use Refresh on the Players page) during the season to pick up rookies and
breakout players as their minutes climb.

Usage:
    python scripts/fetch_rosters.py
"""

import time
from datetime import datetime, timezone

import pandas as pd
import requests

import config
from teams import TEAM_ABBRS, team

ESPN_TEAMS_URL = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams'
ESPN_ROSTER_URL = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster'
ESPN_STATS_URL = 'https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/statistics/byathlete'

# ESPN abbreviations differ for a few teams (GS, NY, NO, SA, UTAH, WSH)
ESPN_TO_ABBR = {team(abbr)['espn_slug'].upper(): abbr for abbr in TEAM_ABBRS}

# ESPN stat name -> our column name (per-game values unless noted)
STAT_COLUMNS = {
    'gamesPlayed': 'GP', 'avgMinutes': 'MIN', 'avgPoints': 'PTS', 'avgRebounds': 'REB',
    'avgAssists': 'AST', 'avgSteals': 'STL', 'avgBlocks': 'BLK', 'avgTurnovers': 'TOV',
    'avgFieldGoalsMade': 'FGM', 'avgFieldGoalsAttempted': 'FGA', 'fieldGoalPct': 'FG_PCT',
    'avgThreePointFieldGoalsMade': 'FG3M', 'avgThreePointFieldGoalsAttempted': 'FG3A',
    'threePointFieldGoalPct': 'FG3_PCT', 'avgFreeThrowsMade': 'FTM',
    'avgFreeThrowsAttempted': 'FTA', 'freeThrowPct': 'FT_PCT',
}


def _get(url, **params):
    response = requests.get(url, params=params or None, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_roster(data, abbr):
    rows = []
    for athlete in data.get('athletes', []):
        rows.append({
            'espn_id': athlete['id'],
            'player': athlete['displayName'],
            'team': abbr,
            'position': athlete.get('position', {}).get('abbreviation', ''),
            'age': athlete.get('age'),
            'experience': athlete.get('experience', {}).get('years'),
            'jersey': athlete.get('jersey', ''),
            'headshot': athlete.get('headshot', {}).get('href', ''),
        })
    return rows


def fetch_rosters(progress=None):
    """Every player on a current NBA roster. progress(i, n) is called per team."""
    league = _get(ESPN_TEAMS_URL)['sports'][0]['leagues'][0]['teams']
    espn_teams = [(t['team']['id'], ESPN_TO_ABBR[t['team']['abbreviation']]) for t in league]
    rows = []
    for i, (team_id, abbr) in enumerate(espn_teams, 1):
        rows += parse_roster(_get(ESPN_ROSTER_URL.format(team_id=team_id)), abbr)
        if progress:
            progress(i, len(espn_teams))
        time.sleep(0.05)
    return pd.DataFrame(rows)


def parse_stats(data):
    """Flatten ESPN's byathlete response into one row per player."""
    names = {cat['name']: cat['names'] for cat in data.get('categories', [])}
    rows = []
    for entry in data.get('athletes', []):
        athlete = entry['athlete']
        row = {
            'espn_id': athlete['id'],
            'player': athlete['displayName'],
            'stats_team': ESPN_TO_ABBR.get(athlete.get('teamShortName', ''), ''),
        }
        for cat in entry['categories']:
            for name, value in zip(names.get(cat['name'], []), cat.get('totals', [])):
                if name in STAT_COLUMNS:
                    row[STAT_COLUMNS[name]] = pd.to_numeric(value, errors='coerce')
        rows.append(row)
    stats = pd.DataFrame(rows)
    if not stats.empty:
        # ESPN reports percentages as 0-100; the app uses fractions like the NBA API
        for col in ('FG_PCT', 'FG3_PCT', 'FT_PCT'):
            stats[col] = stats[col] / 100
    return stats


def espn_season_year(season):
    """'2026-27' -> 2027, the year ESPN files the season under."""
    return int(season[:4]) + 1


def fetch_season_stats(season):
    """Per-game regular-season stats for every player who has played."""
    data = _get(ESPN_STATS_URL, region='us', lang='en', contentorigin='espn',
                isqualified='false', page=1, limit=1000, sort='general.avgMinutes:desc',
                season=espn_season_year(season), seasontype=2)
    return parse_stats(data)


def current_season():
    """ESPN's current season, e.g. '2026-27'."""
    return _get(ESPN_ROSTER_URL.format(team_id=1))['season']['displayName']


def refresh(progress=None):
    """Fetch rosters and current-season stats and save both. Returns a summary."""
    season = current_season()
    rosters = fetch_rosters(progress)
    rosters['updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    rosters.to_csv(config.rosters_file(season), index=False)

    stats = fetch_season_stats(season)
    if not stats.empty:
        stats.to_csv(config.espn_stats_file(season), index=False)
    return {'season': season, 'players': len(rosters), 'with_stats': len(stats)}


def main():
    print("Fetching current rosters and player stats from ESPN...")
    try:
        summary = refresh(lambda i, n: print(f"  {i}/{n} teams") if i % 10 == 0 else None)
    except Exception as e:
        print(f"Error fetching rosters: {e}")
        print("   Check your internet connection and try again.")
        return

    print(f"\nSaved {summary['players']} rostered players to "
          f"{config.rosters_file(summary['season'])}")
    if summary['with_stats']:
        print(f"Saved {summary['season']} stats for {summary['with_stats']} players to "
              f"{config.espn_stats_file(summary['season'])}")
    else:
        print(f"No {summary['season']} regular-season games yet; the app uses last "
              "season's stats until they start.")


if __name__ == '__main__':
    main()
