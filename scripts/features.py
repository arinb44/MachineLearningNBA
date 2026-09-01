"""
Point-in-time feature engineering shared by train_model.py and predict_games.py.

Every feature for a game is computed ONLY from games played strictly before
that game's date, so training never sees information from the future.
All features are built from dated game results (data/tracking/*.csv).
"""

import pandas as pd

import config

# Canonical feature order — the model is trained and queried with exactly this.
FEATURE_COLUMNS = [
    'win_pct_diff',        # season-to-date win% (home - away)
    'avg_margin_diff',     # season-to-date avg point margin (home - away)
    'pts_for_diff',        # avg points scored (home - away)
    'pts_against_diff',    # avg points allowed (away - home; positive favors home)
    'last10_win_pct_diff', # recent form: win% over last 10 games
    'last10_margin_diff',  # recent form: avg margin over last 10 games
    'venue_margin_diff',   # home team's avg margin AT HOME - away team's avg margin ON ROAD
    'rest_diff',           # rest days (home - away), capped at 7
    'home_b2b',            # 1 if home team played yesterday
    'away_b2b',            # 1 if away team played yesterday
    'min_games_played',    # fewer prior games = less reliable stats
]


def load_games(path=None):
    """Load game results sorted chronologically."""
    games = pd.read_csv(path or config.game_results_file(), parse_dates=['date'])
    return games.sort_values('date').reset_index(drop=True)


def _long_format(games):
    """One row per team per game: date, team, pts_for, pts_against, won, is_home."""
    home = pd.DataFrame({
        'date': games['date'], 'team': games['home_team'],
        'pts_for': games['home_score'], 'pts_against': games['away_score'],
        'is_home': True,
    })
    away = pd.DataFrame({
        'date': games['date'], 'team': games['away_team'],
        'pts_for': games['away_score'], 'pts_against': games['home_score'],
        'is_home': False,
    })
    long = pd.concat([home, away]).sort_values('date').reset_index(drop=True)
    long['margin'] = long['pts_for'] - long['pts_against']
    long['won'] = (long['margin'] > 0).astype(int)
    return long


class FeatureBuilder:
    """Builds team form features as of any date, using only earlier games."""

    def __init__(self, games):
        self.long = _long_format(games)
        self.by_team = {team: grp for team, grp in self.long.groupby('team')}

    def team_form(self, team, as_of_date, last_n=10):
        """Form stats for a team using games strictly before as_of_date."""
        history = self.by_team.get(team)
        if history is None:
            return None
        prior = history[history['date'] < as_of_date]
        if prior.empty:
            return None

        recent = prior.tail(last_n)
        home_games = prior[prior['is_home']]
        road_games = prior[~prior['is_home']]
        days_since_last = (as_of_date - prior['date'].iloc[-1]).days

        return {
            'gp': len(prior),
            'win_pct': prior['won'].mean(),
            'avg_margin': prior['margin'].mean(),
            'pts_for': prior['pts_for'].mean(),
            'pts_against': prior['pts_against'].mean(),
            'last_win_pct': recent['won'].mean(),
            'last_margin': recent['margin'].mean(),
            # fall back to overall margin until a team has home/road samples
            'home_margin': home_games['margin'].mean() if len(home_games) else prior['margin'].mean(),
            'road_margin': road_games['margin'].mean() if len(road_games) else prior['margin'].mean(),
            'rest_days': min(days_since_last, 7),
            'b2b': 1.0 if days_since_last <= 1 else 0.0,
        }

    def game_features(self, home_team, away_team, as_of_date, min_gp=1):
        """Feature dict for one matchup, or None if either team lacks history."""
        home = self.team_form(home_team, as_of_date)
        away = self.team_form(away_team, as_of_date)
        if home is None or away is None:
            return None
        if home['gp'] < min_gp or away['gp'] < min_gp:
            return None

        return {
            'win_pct_diff': home['win_pct'] - away['win_pct'],
            'avg_margin_diff': home['avg_margin'] - away['avg_margin'],
            'pts_for_diff': home['pts_for'] - away['pts_for'],
            'pts_against_diff': away['pts_against'] - home['pts_against'],
            'last10_win_pct_diff': home['last_win_pct'] - away['last_win_pct'],
            'last10_margin_diff': home['last_margin'] - away['last_margin'],
            'venue_margin_diff': home['home_margin'] - away['road_margin'],
            'rest_diff': home['rest_days'] - away['rest_days'],
            'home_b2b': home['b2b'],
            'away_b2b': away['b2b'],
            'min_games_played': min(home['gp'], away['gp']),
        }


def build_training_table(games, min_gp=5):
    """
    One row per game with point-in-time features and targets.
    Games where either team has fewer than min_gp prior games are skipped
    (their stats are too noisy to train on).
    Rows come out in chronological order — required for walk-forward validation.
    """
    builder = FeatureBuilder(games)
    rows = []
    for game in games.itertuples():
        features = builder.game_features(
            game.home_team, game.away_team, game.date, min_gp=min_gp
        )
        if features is None:
            continue
        features['date'] = game.date
        features['home_margin'] = game.home_score - game.away_score
        features['home_win'] = int(game.home_score > game.away_score)
        rows.append(features)
    return pd.DataFrame(rows)
