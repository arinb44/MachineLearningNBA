"""
HTML building blocks for the app: the Figma matchup card, the
win-probability bar, the tale-of-the-tape comparison, and a team header.
Styles live in app/styles.css.
"""

from html import escape

import streamlit as st

from app.common import logo_url, team


def _side(abbr, side):
    t = team(abbr)
    return f"""
<div class="mc-side {side}">
  <div class="mc-inner">
    <div class="mc-radial" style="--c:{t['accent']}55"></div>
    <div class="mc-logo-zone"><img class="mc-logo" src="{logo_url(abbr)}" alt="{escape(t['name'])} logo" style="--glow:{t['accent']}88"></div>
    <div class="mc-text">
      <span class="mc-city" style="color:{t['label']}">{escape(t['city'])}</span>
      <span class="mc-name">{escape(t['nickname'])}</span>
      <span class="mc-abbr" style="color:{t['accent']};filter:drop-shadow(0 0 8px {t['accent']})">{abbr}</span>
    </div>
  </div>
</div>"""


def _game_pill(game):
    network = game['broadcast'] or ('NBA' if game['season_type'] == 'regular' else '')
    if game['season_type'] == 'preseason':
        return f"Preseason · {network}" if network else 'Preseason'
    return network


def matchup_card(result, game=None):
    """
    The Figma matchup card: away team on the left, home team on the right.
    With a scheduled game (a row from the schedule), the center shows the
    network, date and tip-off time and the footer shows the arena, as in the
    design; the model's pick sits underneath. Without one, the pick is the
    headline.
    """
    away, home = result['away_team'], result['home_team']
    winner = team(result['predicted_winner'])
    pick = f"{escape(winner['nickname'])} by {abs(result['predicted_margin']):.1f}"
    prob = f"{result['win_probability']:.0f}%"
    if game is not None:
        center = f"""
      <div class="mc-pill">{escape(_game_pill(game))}</div>
      <div class="mc-pick">
        <span class="mc-pick-main">{game['date']:%a · %b %-d}</span>
        <span class="mc-pick-sub">{escape(game['time_et'])} ET</span>
      </div>
      <div class="mc-pick-line">{pick} · {prob}</div>"""
        place = ' · '.join(p for p in (game['venue'], game['city']) if p)
    else:
        center = f"""
      <div class="mc-pill">Model pick</div>
      <div class="mc-pick">
        <span class="mc-pick-main">{pick}</span>
        <span class="mc-pick-sub">{prob} WIN PROBABILITY</span>
      </div>"""
        place = f"Home court · {team(home)['home_city']}"
    html = f"""
<div class="mc-wrap">
  <div class="mc" style="--away-glow:{team(away)['accent']}22;--home-glow:{team(home)['accent']}22">
    <div class="mc-noise"></div>
    <div class="mc-divider"></div>
    {_side(away, 'away')}
    {_side(home, 'home')}
    <div class="mc-center">{center}
    </div>
    <div class="mc-footer">{escape(place)}</div>
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
    <img src="{logo_url(away)}" alt="{away}">
    <div class="wp-bar" role="img" aria-label="{away} {away_pct:.0f}%, {home} {home_pct:.0f}%">
      <div style="width:{away_pct}%;background:{team(away)['accent']}"></div>
      <div style="width:{home_pct}%;background:{team(home)['accent']}"></div>
    </div>
    <img src="{logo_url(home)}" alt="{home}">
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
    <img src="{logo_url(away)}" alt="{away}">
    <img src="{logo_url(home)}" alt="{home}">
  </div>
  {''.join(body)}
</div>""")


def team_header(abbr, title=None, subtitle=None):
    """Logo plus a two-line heading; defaults to the team's city and nickname."""
    t = team(abbr)
    st.html(f"""
<div class="team-head">
  <img src="{logo_url(abbr)}" alt="{escape(t['name'])} logo">
  <div>
    <div class="t-city">{escape(subtitle or t['city'])}</div>
    <div class="t-name">{escape(title or t['nickname'])}</div>
  </div>
</div>""")


def player_header(player):
    """Headshot, name, and team for a row of the player pool."""
    t = team(player['TEAM_ABBREVIATION'])
    details = [t['name']]
    if isinstance(player.get('POSITION'), str) and player['POSITION']:
        details.append(player['POSITION'])
    if player.get('AGE') == player.get('AGE'):  # not NaN
        details.append(f"Age {int(player['AGE'])}")
    if player.get('STATS_TEAM') and player['STATS_TEAM'] != player['TEAM_ABBREVIATION']:
        details.append(f"Stats below with {player['STATS_TEAM']}")
    headshot = player.get('HEADSHOT') if isinstance(player.get('HEADSHOT'), str) else ''
    photo = (f'<img class="p-photo" src="{escape(headshot)}" alt="">' if headshot
             else f'<img class="p-photo" src="{logo_url(t["abbr"])}" alt="">')
    st.html(f"""
<div class="player-head" style="--c:{t['accent']}">
  <div class="p-frame">{photo}<img class="p-logo" src="{logo_url(t['abbr'])}" alt="{t['abbr']}"></div>
  <div>
    <div class="t-city">{escape(' · '.join(details))}</div>
    <div class="t-name">{escape(player['PLAYER_NAME'])}</div>
  </div>
</div>""")
