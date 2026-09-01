"""
Central configuration: one place for the season and every data file path.

The season can be set three ways (highest priority first):
  1. --season 2026-27 on any fetch script
  2. NBA_SEASON environment variable
  3. DEFAULT_SEASON below
"""

import os

DEFAULT_SEASON = '2025-26'


def current_season():
    return os.environ.get('NBA_SEASON', DEFAULT_SEASON)


def game_results_file(season=None):
    return f"data/tracking/nba_game_results_{season or current_season()}.csv"


def player_stats_file(season=None):
    return f"data/input/nba_player_stats_{season or current_season()}.csv"


def player_stats_std_file(season=None):
    return f"data/input/nba_player_stats_with_std_{season or current_season()}.csv"


INJURIES_FILE = 'data/input/injuries.csv'
MODEL_FILE = 'models/nba_predictor.pkl'
GAMES_TO_PREDICT_FILE = 'data/input/games_to_predict.txt'
PREDICTIONS_CSV = 'data/output/predictions.csv'
PREDICTIONS_TXT = 'data/output/predictions_output.txt'


def add_season_arg(parser):
    """Attach the standard --season argument to an argparse parser."""
    parser.add_argument(
        '--season', default=current_season(),
        help=f"NBA season, e.g. 2025-26 (default: {current_season()}; "
             f"also settable via NBA_SEASON env var)")
    return parser
