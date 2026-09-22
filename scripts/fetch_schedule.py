"""
Fetch the full NBA schedule (preseason + regular season) from ESPN's public
scoreboard API and save it to data/input/nba_schedule_<season>.csv.

Each row has the game's date and tip-off time (Eastern), both teams, the
arena, and the TV broadcast. The demo app's daily slate reads this file.

Usage:
    python scripts/fetch_schedule.py
"""

import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests

import config
from teams import TEAM_ABBRS, team

ESPN_SCOREBOARD_URL = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard'
EASTERN = ZoneInfo('America/New_York')
SEASON_TYPES = {1: 'preseason', 2: 'regular', 3: 'playoffs', 5: 'play-in'}

# ESPN abbreviations differ for a few teams (GS, NY, NO, SA, UTAH, WSH)
ESPN_TO_ABBR = {team(abbr)['espn_slug'].upper(): abbr for abbr in TEAM_ABBRS}


def get_scoreboard(date=None):
    params = {'dates': date} if date else {}
    response = requests.get(ESPN_SCOREBOARD_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_game(event, game_date):
    comp = event['competitions'][0]
    sides = {c['homeAway']: ESPN_TO_ABBR.get(c['team']['abbreviation']) for c in comp['competitors']}
    if not sides.get('home') or not sides.get('away'):
        return None  # exhibition against a non-NBA club
    tip = datetime.fromisoformat(event['date'].replace('Z', '+00:00')).astimezone(EASTERN)
    venue = comp.get('venue', {})
    address = venue.get('address', {})
    networks = [name for b in comp.get('broadcasts', []) for name in b.get('names', [])]
    return {
        'game_id': event['id'],
        'date': game_date,
        'tip_et': tip.strftime('%Y-%m-%d %H:%M'),
        'time_et': tip.strftime('%-I:%M %p'),
        'season_type': SEASON_TYPES.get(event['season']['type'], 'other'),
        'home_team': sides['home'],
        'away_team': sides['away'],
        'venue': venue.get('fullName', ''),
        'city': ', '.join(p for p in (address.get('city'), address.get('state')) if p),
        'broadcast': ' / '.join(networks),
        'neutral_site': bool(comp.get('neutralSite')),
    }


def fetch_schedule():
    """Returns (season display name, schedule DataFrame)."""
    league = get_scoreboard()['leagues'][0]
    season = league['season']['displayName']
    # The calendar lists every date with games, as midnight Eastern in UTC
    dates = sorted({entry[:10] for entry in league.get('calendar', [])})
    print(f"Fetching {len(dates)} game dates for the {season} season...")

    rows, skipped = [], 0
    for i, day in enumerate(dates, 1):
        data = get_scoreboard(day.replace('-', ''))
        for event in data.get('events', []):
            game = parse_game(event, day)
            if game is None:
                skipped += 1
            else:
                rows.append(game)
        if i % 25 == 0:
            print(f"  {i}/{len(dates)} dates")
        time.sleep(0.1)  # be polite to ESPN's API

    if skipped:
        print(f"Skipped {skipped} exhibition games against non-NBA teams")
    schedule = pd.DataFrame(rows).drop_duplicates('game_id').sort_values(['date', 'tip_et'])
    return season, schedule


def main():
    try:
        season, schedule = fetch_schedule()
    except Exception as e:
        print(f"Error fetching schedule: {e}")
        print("   Check your internet connection and try again.")
        return

    if schedule.empty:
        print("No games found. Nothing saved.")
        return

    path = config.schedule_file(season)
    schedule.to_csv(path, index=False)
    print(f"\nSaved {len(schedule)} games to {path}")
    for season_type, count in schedule['season_type'].value_counts().items():
        print(f"   {season_type:12s} {count}")
    print(f"   {schedule['date'].min()} to {schedule['date'].max()}")


if __name__ == '__main__':
    main()
