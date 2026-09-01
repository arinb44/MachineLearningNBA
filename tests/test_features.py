"""
Tests for the point-in-time feature engineering in scripts/features.py.

The most important property under test: no data leakage. Features for a
game must depend only on games played strictly before it.
"""

import pandas as pd
import pytest

import features


def make_games():
    """Small synthetic season with known margins, rest patterns, venues."""
    rows = [
        # date, home, away, home_score, away_score
        ('2025-01-01', 'AAA', 'BBB', 100, 90),   # AAA +10 at home
        ('2025-01-02', 'CCC', 'AAA', 80, 100),   # AAA +20 on road (back-to-back)
        ('2025-01-05', 'BBB', 'CCC', 95, 85),    # BBB +10 at home
        ('2025-01-06', 'AAA', 'CCC', 110, 100),  # AAA +10 at home
        ('2025-01-08', 'BBB', 'AAA', 90, 95),    # AAA +5 on road
    ]
    games = pd.DataFrame(rows, columns=[
        'date', 'home_team', 'away_team', 'home_score', 'away_score'])
    games['date'] = pd.to_datetime(games['date'])
    games['game_id'] = range(len(games))
    games['home_win'] = (games['home_score'] > games['away_score']).astype(int)
    return games.sort_values('date').reset_index(drop=True)


def test_team_form_uses_only_prior_games():
    builder = features.FeatureBuilder(make_games())
    form = builder.team_form('AAA', pd.Timestamp('2025-01-06'))
    # AAA has played exactly 2 games before Jan 6 (Jan 1 and Jan 2)
    assert form['gp'] == 2
    assert form['win_pct'] == 1.0
    assert form['avg_margin'] == pytest.approx(15.0)  # +10 and +20
    assert form['home_margin'] == pytest.approx(10.0)
    assert form['road_margin'] == pytest.approx(20.0)


def test_no_future_leakage():
    """Features must be identical whether or not later games exist."""
    games = make_games()
    cutoff = pd.Timestamp('2025-01-06')
    full = features.FeatureBuilder(games)
    truncated = features.FeatureBuilder(games[games['date'] < cutoff])
    assert (full.game_features('AAA', 'CCC', cutoff)
            == truncated.game_features('AAA', 'CCC', cutoff))


def test_rest_days_and_back_to_back():
    builder = features.FeatureBuilder(make_games())
    # AAA played on Jan 2; on Jan 3 that's a back-to-back
    form = builder.team_form('AAA', pd.Timestamp('2025-01-03'))
    assert form['rest_days'] == 1
    assert form['b2b'] == 1.0
    # By Jan 6, AAA has had 4 days off
    form = builder.team_form('AAA', pd.Timestamp('2025-01-06'))
    assert form['rest_days'] == 4
    assert form['b2b'] == 0.0


def test_rest_days_capped():
    builder = features.FeatureBuilder(make_games())
    form = builder.team_form('CCC', pd.Timestamp('2025-03-01'))
    assert form['rest_days'] == 7  # capped, not ~50


def test_unknown_team_returns_none():
    builder = features.FeatureBuilder(make_games())
    assert builder.team_form('ZZZ', pd.Timestamp('2025-01-06')) is None
    assert builder.game_features('ZZZ', 'AAA', pd.Timestamp('2025-01-06')) is None


def test_first_game_has_no_features():
    """A team's first game has no history — must return None, not zeros."""
    builder = features.FeatureBuilder(make_games())
    assert builder.game_features('AAA', 'BBB', pd.Timestamp('2025-01-01')) is None


def test_training_table_min_gp_and_targets():
    table = features.build_training_table(make_games(), min_gp=2)
    # Only the Jan 6 and Jan 8 games have both teams with >= 2 prior games
    assert len(table) == 2
    assert list(table['home_margin']) == [10, -5]
    assert list(table['home_win']) == [1, 0]
    # Chronological order is required for walk-forward validation
    assert table['date'].is_monotonic_increasing


def test_feature_columns_complete_and_ordered():
    builder = features.FeatureBuilder(make_games())
    feats = builder.game_features('AAA', 'CCC', pd.Timestamp('2025-01-08'))
    assert set(feats) == set(features.FEATURE_COLUMNS)


def test_differentials_signed_from_home_perspective():
    games = make_games()
    builder = features.FeatureBuilder(games)
    # As of Jan 8: AAA is 3-0, CCC is 0-3
    feats = builder.game_features('AAA', 'CCC', pd.Timestamp('2025-01-08'))
    assert feats['win_pct_diff'] == pytest.approx(1.0)
    assert feats['avg_margin_diff'] > 0  # the stronger team is at home
