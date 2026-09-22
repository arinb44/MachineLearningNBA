"""
Download all 30 NBA team logos from ESPN's CDN into static/logos/<ABBR>.png.

Uses ESPN's dark-background variants (the demo app has a dark theme) and
downsizes them to 256px so the repo stays small.

Usage:
    python scripts/fetch_team_logos.py
"""

import io
import os

import requests
from PIL import Image

from teams import LOGO_DIR, TEAM_ABBRS, team

ESPN_LOGO_URL = 'https://a.espncdn.com/i/teamlogos/nba/500-dark/{slug}.png'
LOGO_SIZE = 256


def fetch_logo(abbr):
    info = team(abbr)
    response = requests.get(ESPN_LOGO_URL.format(slug=info['espn_slug']), timeout=30)
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content)).convert('RGBA')
    image.thumbnail((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
    image.save(info['logo_path'], optimize=True)


def main():
    os.makedirs(LOGO_DIR, exist_ok=True)
    print(f"Downloading {len(TEAM_ABBRS)} team logos to {LOGO_DIR}/...")
    failed = []
    for abbr in TEAM_ABBRS:
        try:
            fetch_logo(abbr)
            print(f"  {abbr}")
        except (requests.RequestException, OSError) as exc:
            print(f"  {abbr}: failed ({exc})")
            failed.append(abbr)
    if failed:
        print(f"\n{len(failed)} logos failed: {', '.join(failed)}")
    else:
        print("\nAll logos downloaded.")


if __name__ == '__main__':
    main()
