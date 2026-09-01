"""
Fetch current NBA injuries from ESPN's public API and save to
data/input/injuries.csv (columns: team, player, status, detail).

predict_games.py automatically applies these as a margin adjustment.

Usage:
    python scripts/fetch_injuries.py
"""

import pandas as pd
import requests

import config

ESPN_INJURIES_URL = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries'

TEAM_NAME_TO_ABBR = {
    'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
    'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
    'LA Clippers': 'LAC', 'Los Angeles Clippers': 'LAC', 'Los Angeles Lakers': 'LAL',
    'Memphis Grizzlies': 'MEM', 'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL',
    'Minnesota Timberwolves': 'MIN', 'New Orleans Pelicans': 'NOP',
    'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC', 'Orlando Magic': 'ORL',
    'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX', 'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS', 'Toronto Raptors': 'TOR',
    'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS',
}


def fetch_injuries():
    response = requests.get(ESPN_INJURIES_URL, timeout=30)
    response.raise_for_status()
    data = response.json()

    rows = []
    for team_entry in data.get('injuries', []):
        team_name = team_entry.get('displayName', '')
        abbr = TEAM_NAME_TO_ABBR.get(team_name)
        if abbr is None:
            print(f"⚠️  Unknown team name from ESPN: {team_name!r} — skipping")
            continue
        for injury in team_entry.get('injuries', []):
            athlete = injury.get('athlete', {})
            details = injury.get('details', {})
            rows.append({
                'team': abbr,
                'player': athlete.get('displayName', ''),
                'status': injury.get('status', ''),
                'detail': details.get('type', ''),
            })
    return pd.DataFrame(rows)


def main():
    print("🏥 Fetching NBA injuries from ESPN...")
    try:
        df = fetch_injuries()
    except Exception as e:
        print(f"❌ Error fetching injuries: {e}")
        print("   Check your internet connection and try again.")
        return

    if df.empty:
        print("✅ No injuries reported (or off-season). Nothing saved.")
        return

    df = df.sort_values(['team', 'player'])
    df.to_csv(config.INJURIES_FILE, index=False)
    print(f"✅ Saved {len(df)} injuries across {df['team'].nunique()} teams "
          f"to {config.INJURIES_FILE}")
    print("\nStatus counts:")
    for status, count in df['status'].value_counts().items():
        print(f"   {status:15s} {count}")
    print("\n💡 predict_games.py will apply these automatically.")


if __name__ == '__main__':
    main()
