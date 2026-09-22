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
