"""Home page: the pitch, the court (every section plays a position), and the next game day."""

from html import escape

import math

import pandas as pd
import streamlit as st

from app.common import load_schedule, predict, team

# Each section plays a position: (number, label, position, x, y, link, label side)
POSITIONS = [
    (1, 'Predictions', 'Point guard', 250, 330, 'predictions', 'left'),
    (2, 'Matchups', 'Shooting guard', 430, 230, 'predictions#any-matchup', 'below'),
    (3, 'Teams', 'Small forward', 70, 230, 'teams', 'below'),
    (4, 'Players', 'Power forward', 146, 104, 'players', 'left'),
    (5, 'Model', 'Center', 354, 104, 'about#model', 'right'),
    (6, 'Data', 'Sixth man', 62, 420, 'about#data', 'right'),
]


def spot(n, label, position, x, y, href, side):
    if side == 'below':
        lx, ly, anchor = x, y + 44, 'middle'
    elif side == 'left':
        lx, ly, anchor = x - 24, y + 4, 'end'
    else:
        lx, ly, anchor = x + 26, y - 4, 'start'
    return (f'<a class="spot{" sixth" if n == 6 else ""}" href="{href}" target="_self">'
            f'<circle cx="{x}" cy="{y}" r="16"/><text class="n" x="{x}" y="{y + 6}">{n}</text>'
            f'<text class="lab" x="{lx}" y="{ly}" text-anchor="{anchor}">{label}</text>'
            f'<text class="where" x="{lx}" y="{ly + 17}" text-anchor="{anchor}">{position}</text></a>')


def zigzag(x1, y1, x2, y2, amp=5, step=9):
    """A dribble: a zigzag from (x1, y1) that ends in a straight run for the arrowhead."""
    length = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    points = [f'M{x1} {y1}']
    for i in range(1, int((length - 14) // step) + 1):
        side = amp if i % 2 else -amp
        points.append(f'L{x1 + ux * i * step - uy * side:.1f} {y1 + uy * i * step + ux * side:.1f}')
    return ' '.join(points + [f'L{x2} {y2}'])


# A pick-and-roll in play-diagram notation. Ball movement (pass, dribble) is blue;
# players moving without the ball (cuts, the screen) are chalk.
PLAY = f"""
  <path class="cut" d="M354 120L290 308"/>
  <path class="screen" d="M278.6 304.1L301.4 311.9"/>
  <path class="dribble" d="{zigzag(276, 344, 372, 322)}" marker-end="url(#ball-head)"/>
  <path class="cut" d="M282 296C238 236 232 160 256 98" marker-end="url(#cut-head)"/>
  <path class="pass" d="M372 308C352 220 312 152 270 110" marker-end="url(#ball-head)"/>
  <path class="cut" d="M444 214C462 170 470 120 468 70" marker-end="url(#cut-head)"/>
  <path class="cut" d="M56 214C38 170 30 120 34 70" marker-end="url(#cut-head)"/>
  <path class="cut" d="M158 118L182 180" marker-end="url(#cut-head)"/>
  <path class="cut" d="M4 420H40" marker-end="url(#cut-head)"/>"""

court = f"""
<svg class="court" viewBox="0 0 500 470" role="navigation" aria-label="Site sections drawn as players running a pick-and-roll">
  <path class="ln" d="M1 1H499V469H1Z"/>
  <path class="ln" d="M170 0V190H330V0"/>
  <circle class="ln" cx="250" cy="190" r="60"/>
  <path class="ln" d="M30 0V140A237.5 237.5 0 0 0 470 140V0"/>
  <path class="ln" d="M210 52.5A40 40 0 0 0 290 52.5"/>
  <path class="ln" d="M220 40H280" stroke-width="3"/>
  <circle class="ln" cx="250" cy="52.5" r="7.5"/>
  <path class="ln" d="M190 470A60 60 0 0 1 310 470"/>
  <defs>
    <marker id="ball-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1L9 5L1 9" fill="none" stroke="#7eaee8" stroke-width="2"/></marker>
    <marker id="cut-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1L9 5L1 9" fill="none" stroke="#d9cfbf" stroke-width="2"/></marker>
  </defs>
  {PLAY}
  <circle class="ball" cx="268" cy="346" r="7"/>
  {''.join(spot(*p) for p in POSITIONS)}
</svg>"""

# st.html sanitizes inline SVG away; this markup is ours, so render it as raw HTML
st.markdown(f"""
<section class="hero">
  <div>
    <h1>Win probabilities for <em>every</em> NBA game</h1>
    <p class="lede">Pick two teams and a date. You get a predicted margin and a calibrated win probability,
      built only from games played before tip-off.</p>
    <div class="drives">
      <svg viewBox="0 0 40 40" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M8 30L30 8M30 8H18M30 8V20"/></svg>
      <p><span class="mark">What drives the number</span>Average margin, last-ten form and home/road splits,
        adjusted for injuries by each player's minutes and PIE.</p>
    </div>
  </div>
  <div>{court}<p class="note court-cap">Every section plays a position. The play: 5 screens, 1 drives, 5 rolls, 1 finds him.</p></div>
</section>""", unsafe_allow_html=True)

# ---------- next game day ----------

schedule = load_schedule()
today = pd.Timestamp.now(tz='America/New_York').normalize().tz_localize(None)
upcoming = schedule[schedule['date'] >= today] if schedule is not None else None
if upcoming is not None and not upcoming.empty:
    day = upcoming['date'].iloc[0]
    games = upcoming[upcoming['date'] == day]
    label = 'Tonight' if day == today else f"{day:%A}"
    st.subheader(f"{label} · {day:%a, %b %-d}", anchor=False)
    cards = []
    for g in games.head(3).itertuples():
        r = predict(g.home_team, g.away_team, g.date)
        if r is None:
            continue
        away, home = team(g.away_team), team(g.home_team)
        home_pct = r['win_probability'] if r['predicted_winner'] == g.home_team else 100 - r['win_probability']
        winner = team(r['predicted_winner'])
        tv = f" · {escape(g.broadcast)}" if g.broadcast else ''
        cards.append(f"""
<a href="predictions" target="_self">
  <div class="t num">{escape(g.time_et)} ET{tv}</div>
  <div class="m">{escape(away['nickname'])} at {escape(home['nickname'])}</div>
  <div class="tug" role="img" aria-label="{escape(away['nickname'])} {100 - home_pct:.0f} percent, {escape(home['nickname'])} {home_pct:.0f} percent">
    <i style="width:{100 - home_pct}%;background:{away['accent']}"></i><i style="width:{home_pct}%;background:{home['accent']}"></i></div>
  <div class="mark">{escape(winner['nickname'])} {r['win_probability']:.0f}% · by {abs(r['predicted_margin']):.1f}</div>
</a>""")
    if cards:
        st.html(f'<div class="tonight">{"".join(cards)}</div>')
    more = len(games) - len(cards)
    st.page_link('app/predictions.py', icon=':material/arrow_forward:',
                 label=f"Full slate: all {len(games)} games" if more > 0 else 'Full slate and any matchup')
