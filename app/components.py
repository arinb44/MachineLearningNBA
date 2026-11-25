"""
HTML building blocks for the app: the slate game row, the win-probability
headline, the tale-of-the-tape comparison, and team and player headers.
Styles live in app/styles.css.
"""

from html import escape

import streamlit as st

from app.common import logo_url, team


def _split(result):
    """(away %, home %) win probabilities."""
    home = result['home_team']
    home_pct = result['win_probability'] if result['predicted_winner'] == home \
        else 100 - result['win_probability']
    return 100 - home_pct, home_pct


def _tug(away, home, away_pct, home_pct, style=''):
    return (f'<div class="tug" style="{style}" role="img" aria-label="{escape(team(away)["nickname"])} '
            f'{away_pct:.0f} percent, {escape(team(home)["nickname"])} {home_pct:.0f} percent">'
            f'<i style="width:{away_pct}%;background:{team(away)["accent"]}"></i>'
            f'<i style="width:{home_pct}%;background:{team(home)["accent"]}"></i></div>')


def _pick(result):
    return f"{escape(team(result['predicted_winner'])['nickname'])} by {abs(result['predicted_margin']):.1f}"


def _note(result):
    """A margin note for the row: close games and injury adjustments."""
    if result['win_probability'] < 60:
        return 'close to a coin flip'
    if abs(result['injury_adjustment']) >= 0.05:
        return f"injury adjustment {result['injury_adjustment']:+.1f} pts".replace('-', '\u2212')
    return ''


def matchup_card(result, game):
    """One row of the daily slate: tip-off, away team, home team, and the model's read."""
    away, home = result['away_team'], result['home_team']
    away_pct, home_pct = _split(result)
    network = game['broadcast'] or ''
    if game['season_type'] == 'preseason':
        network = f"Preseason · {network}" if network else 'Preseason'
    venue = game['venue'] if isinstance(game['venue'], str) else ''
    place = network or venue
    tip, _, ampm = game['time_et'].partition(' ')

    def side(abbr, where):
        t = team(abbr)
        at = '<span class="at">at</span>' if where == 'home' else ''
        return (f'<div class="team">{at}<img src="{logo_url(abbr)}" alt=""><div>'
                f'<div class="nm">{escape(t["nickname"])}</div>'
                f'<div class="ct">{escape(t["city"])} · {where}</div></div></div>')

    note = _note(result)
    fav_away = away_pct > home_pct
    st.html(f"""
<div class="game">
  <div class="tip num">{escape(tip)}<small>{escape(ampm)} ET · {escape(place)}</small></div>
  {side(away, 'away')}
  {side(home, 'home')}
  <div class="odds">
    <div class="row1 num"><span class="pc{' fav' if fav_away else ''}">{away_pct:.0f}</span><span class="pc{'' if fav_away else ' fav'}">{home_pct:.0f}</span></div>
    {_tug(away, home, away_pct, home_pct)}
    <div class="mark">{_pick(result)}</div>
    {f'<div class="note">{escape(note)}</div>' if note else ''}
  </div>
</div>""")


def win_probability_bar(result, game=None):
    """The headline for one matchup: the big win probability and the tug bar."""
    away, home = result['away_team'], result['home_team']
    away_pct, home_pct = _split(result)
    winner = team(result['predicted_winner'])
    if game is not None:
        venue = game['venue'] if isinstance(game['venue'], str) else ''
        when = (f"Next meeting: {game['date']:%a, %b %-d} · {escape(game['time_et'])} ET"
                + (f" · {escape(venue)}" if venue else ''))
    else:
        when = f"Not on the schedule: a neutral read with {escape(team(home)['nickname'])} at home."
    st.html(f"""
<div class="win">
  <div class="when">{when}</div>
  <div class="big"><span class="v num">{result['win_probability']:.0f}%</span><span class="k">{escape(winner['nickname'])}<br>win it</span></div>
  {_tug(away, home, away_pct, home_pct)}
  <div class="ends num"><span>{away} {away_pct:.0f}%</span><span>{home} {home_pct:.0f}%</span></div>
</div>""")


def tale_of_the_tape(away, home, rows):
    """
    Side-by-side comparison. rows: (label, away_value, home_value, fmt,
    league_min, league_max, higher_is_better); the league range is unused
    here. The side with the edge gets a marker circle.
    """
    body = []
    for label, a, h, fmt, _lo, _hi, higher_better in rows:
        a_edge = (a > h) if higher_better else (a < h)
        h_edge = (h > a) if higher_better else (h < a)

        def cell(value, edge):
            text = fmt.format(value).replace('-', '\u2212')
            return f'<td class="e"><span>{text}</span></td>' if edge else f'<td>{text}</td>'
        body.append(f'<tr>{cell(a, a_edge)}<th>{escape(label)}</th>{cell(h, h_edge)}</tr>')
    st.html(f"""
<table class="tape num">
  <thead><tr><th><img src="{logo_url(away)}" alt="{away}"></th><th></th><th><img src="{logo_url(home)}" alt="{home}"></th></tr></thead>
  <tbody>{''.join(body)}</tbody>
</table>""")


def team_header(abbr, title=None, subtitle=None):
    """Logo plus a two-line heading; defaults to the team's city and nickname."""
    t = team(abbr)
    st.html(f"""
<div class="team-head">
  <img src="{logo_url(abbr)}" alt="{escape(t['name'])} logo">
  <div>
    <div class="t-name">{escape(title or t['nickname'])}</div>
    <div class="t-city">{escape(subtitle or t['city'])}</div>
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
<div class="player-head">
  <div class="p-frame">{photo}<img class="p-logo" src="{logo_url(t['abbr'])}" alt="{t['abbr']}"></div>
  <div>
    <div class="t-name">{escape(player['PLAYER_NAME'])}</div>
    <div class="t-city">{escape(' · '.join(details))}</div>
  </div>
</div>""")
