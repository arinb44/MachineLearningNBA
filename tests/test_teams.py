"""
Tests for the team metadata in scripts/teams.py that the demo app draws with.
"""

import os

import pandas as pd

import config
import teams

ROOT = os.path.join(os.path.dirname(__file__), '..')


def test_every_team_in_the_data_has_metadata():
    games = pd.read_csv(os.path.join(ROOT, config.game_results_file()))
    in_data = set(games['home_team']) | set(games['away_team'])
    assert in_data == set(teams.TEAM_ABBRS)


def test_every_team_has_a_logo_file():
    missing = [abbr for abbr in teams.TEAM_ABBRS
               if not os.path.exists(os.path.join(ROOT, teams.team(abbr)['logo_path']))]
    assert missing == [], f"run scripts/fetch_team_logos.py (missing: {missing})"


def test_accent_colors_are_visible_on_a_dark_background():
    # The accent falls back to the secondary color when the primary is too dark
    for abbr in teams.TEAM_ABBRS:
        info = teams.team(abbr)
        assert teams._luminance(info['accent']) > 0.045, abbr
        assert teams._luminance(info['label']) > 0.045, abbr
