"""
Smoke test: every page of the Streamlit demo runs without raising.
"""

import os

import pytest
from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(__file__), '..', 'streamlit_app.py')


@pytest.mark.parametrize('page', ['app/predictions.py', 'app/teams.py', 'app/players.py'])
def test_page_runs(page):
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    at.switch_page(page).run()
    assert not at.exception, [e.value for e in at.exception]


def test_slate_filters_to_one_team():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    team_box = next(box for box in at.selectbox if box.label == 'Team')
    team_box.select('BOS').run()
    assert not at.exception, [e.value for e in at.exception]
    # Either the Celtics' upcoming games or the no-games message, never other teams'
    shown = [c.value for c in at.caption] + [i.value for i in at.info]
    assert any(text.startswith('Boston Celtics') for text in shown)
