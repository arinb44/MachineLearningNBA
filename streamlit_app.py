"""
Interactive demo for the NBA game predictor.

Three pages: matchup predictions, team charts, and player charts. The
Predictions page reuses the exact prediction code path from
scripts/predict_games.py, so the demo can never drift from the
command-line tool or the trained model.

Run locally:  streamlit run streamlit_app.py
"""

import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)  # data paths in scripts/config.py are repo-relative
sys.path[:0] = [ROOT, os.path.join(ROOT, 'scripts')]  # for app/ and scripts/ imports

st.set_page_config(page_title='NBA Game Predictor', page_icon='🏀', layout='wide')

with open('app/styles.css') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

pages = st.navigation([
    st.Page('app/predictions.py', title='Predictions', icon=':material/sports_basketball:', default=True),
    st.Page('app/teams.py', title='Teams', icon=':material/groups:'),
    st.Page('app/players.py', title='Players', icon=':material/person:'),
])
pages.run()
