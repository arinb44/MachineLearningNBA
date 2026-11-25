"""
Interactive demo for the NBA game predictor.

The Tip Off. Five pages: Home, Predictions, Players, Teams, and About. The
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

st.set_page_config(page_title='The Tip Off', page_icon='static/brand.svg', layout='wide')
st.logo('static/brand.svg', size='large')

with open('app/styles.css') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# The Home page's nav title doubles as the wordmark (styled in app/styles.css)
pages = st.navigation([
    st.Page('app/home.py', title='The Tip Off', default=True),
    st.Page('app/predictions.py', title='Predictions', url_path='predictions'),
    st.Page('app/players.py', title='Players', url_path='players'),
    st.Page('app/teams.py', title='Teams', url_path='teams'),
    st.Page('app/about.py', title='About', url_path='about'),
], position='top')
pages.run()
