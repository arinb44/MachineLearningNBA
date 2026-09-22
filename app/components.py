"""
HTML building blocks for the app: the Figma matchup card, the
win-probability bar, the tale-of-the-tape comparison, and a team header.
Styles live in app/styles.css.
"""

from html import escape

import streamlit as st

from app.common import logo_uri, team


def _side(abbr, side):
    t = team(abbr)
    logo = logo_uri(abbr, 256) or ''
    return f"""
<div class="mc-side {side}">
  <div class="mc-inner">
    <div class="mc-radial" style="--c:{t['accent']}55"></div>
    <div class="mc-logo-zone"><img class="mc-logo" src="{logo}" alt="{escape(t['name'])} logo" style="--glow:{t['accent']}88"></div>
    <div class="mc-text">
      <span class="mc-city" style="color:{t['label']}">{escape(t['city'])}</span>
      <span class="mc-name">{escape(t['nickname'])}</span>
      <span class="mc-abbr" style="color:{t['accent']};filter:drop-shadow(0 0 8px {t['accent']})">{abbr}</span>
    </div>
  </div>
</div>"""


def matchup_card(result, pill='Model pick'):
    """The Figma matchup card: away team on the left, home team on the right."""
    away, home = result['away_team'], result['home_team']
    winner = team(result['predicted_winner'])
    html = f"""
<div class="mc-wrap">
  <div class="mc" style="--away-glow:{team(away)['accent']}22;--home-glow:{team(home)['accent']}22">
    <div class="mc-noise"></div>
    <div class="mc-divider"></div>
    {_side(away, 'away')}
    {_side(home, 'home')}
    <div class="mc-center">
      <div class="mc-pill">{escape(pill)}</div>
      <div class="mc-pick">
        <span class="mc-pick-main">{escape(winner['nickname'])} by {abs(result['predicted_margin']):.1f}</span>
        <span class="mc-pick-sub">{result['win_probability']:.0f}% WIN PROBABILITY</span>
      </div>
    </div>
    <div class="mc-footer">Home court · {escape(team(home)['home_city'])}</div>
  </div>
</div>"""
    st.html(html)


def win_probability_bar(result):
    away, home = result['away_team'], result['home_team']
    home_pct = result['win_probability'] if result['predicted_winner'] == home \
        else 100 - result['win_probability']
    away_pct = 100 - home_pct
    st.html(f"""
<div class="wp">
  <div class="wp-row">
    <img src="{logo_uri(away, 96)}" alt="{away}">
    <div class="wp-bar" role="img" aria-label="{away} {away_pct:.0f}%, {home} {home_pct:.0f}%">
      <div style="width:{away_pct}%;background:{team(away)['accent']}"></div>
      <div style="width:{home_pct}%;background:{team(home)['accent']}"></div>
    </div>
    <img src="{logo_uri(home, 96)}" alt="{home}">
  </div>
  <div class="wp-labels">
    <span>{away} {away_pct:.0f}% <span class="muted">away</span></span>
    <span><span class="muted">home</span> {home} {home_pct:.0f}%</span>
  </div>
</div>""")


def tale_of_the_tape(away, home, rows):
    """
    Side-by-side comparison. rows: (label, away_value, home_value, fmt,
    league_min, league_max, higher_is_better). Each bar is scaled to where
    the value sits in the league range for that stat, so every row reads on
    its own scale; the better side of each row is drawn in its team color.
    """
    def fill(value, lo, hi):
        share = 0.08 + 0.92 * (value - lo) / (hi - lo) if hi > lo else 0.5
        share = max(0.05, min(1.0, share))
        return share * 100

    body = []
    for label, a, h, fmt, lo, hi, higher_better in rows:
        a_better = (a > h) if higher_better else (a < h)
        h_better = (h > a) if higher_better else (h < a)
        # "Lower is better" stats: a lower value earns the longer bar
        a_len = fill(a if higher_better else lo + hi - a, lo, hi)
        h_len = fill(h if higher_better else lo + hi - h, lo, hi)
        a_color = team(away)['accent'] if a_better else 'rgba(255,255,255,0.14)'
        h_color = team(home)['accent'] if h_better else 'rgba(255,255,255,0.14)'
        body.append(f"""
<div class="tape-row">
  <div class="tape-val left">{fmt.format(a)}</div>
  <div class="tape-track left"><div style="width:{a_len:.0f}%;background:{a_color}"></div></div>
  <div class="tape-label">{escape(label)}</div>
  <div class="tape-track"><div style="width:{h_len:.0f}%;background:{h_color}"></div></div>
  <div class="tape-val right">{fmt.format(h)}</div>
</div>""")

    st.html(f"""
<div class="tape">
  <div class="tape-head">
    <img src="{logo_uri(away, 96)}" alt="{away}">
    <img src="{logo_uri(home, 96)}" alt="{home}">
  </div>
  {''.join(body)}
</div>""")


def team_header(abbr, title=None, subtitle=None):
    """Logo plus a two-line heading; defaults to the team's city and nickname."""
    t = team(abbr)
    st.html(f"""
<div class="team-head">
  <img src="{logo_uri(abbr, 128)}" alt="{escape(t['name'])} logo">
  <div>
    <div class="t-city">{escape(subtitle or t['city'])}</div>
    <div class="t-name">{escape(title or t['nickname'])}</div>
  </div>
</div>""")
