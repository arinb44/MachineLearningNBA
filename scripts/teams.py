"""
Team metadata shared by the demo app and the logo fetcher: names, colors,
and where each team's logo lives on disk.
"""

import os

LOGO_DIR = 'assets/logos'

# abbr: (city, nickname, primary color, secondary color, ESPN logo slug, home city)
_TEAMS = {
    'ATL': ('Atlanta', 'Hawks', '#E03A3E', '#C1D32F', 'atl', 'Atlanta, GA'),
    'BOS': ('Boston', 'Celtics', '#007A33', '#BA9653', 'bos', 'Boston, MA'),
    'BKN': ('Brooklyn', 'Nets', '#000000', '#A1A1A4', 'bkn', 'Brooklyn, NY'),
    'CHA': ('Charlotte', 'Hornets', '#1D1160', '#00788C', 'cha', 'Charlotte, NC'),
    'CHI': ('Chicago', 'Bulls', '#CE1141', '#000000', 'chi', 'Chicago, IL'),
    'CLE': ('Cleveland', 'Cavaliers', '#860038', '#FDBB30', 'cle', 'Cleveland, OH'),
    'DAL': ('Dallas', 'Mavericks', '#00538C', '#B8C4CA', 'dal', 'Dallas, TX'),
    'DEN': ('Denver', 'Nuggets', '#0E2240', '#FEC524', 'den', 'Denver, CO'),
    'DET': ('Detroit', 'Pistons', '#C8102E', '#1D42BA', 'det', 'Detroit, MI'),
    'GSW': ('Golden State', 'Warriors', '#1D428A', '#FFC72C', 'gs', 'San Francisco, CA'),
    'HOU': ('Houston', 'Rockets', '#CE1141', '#C4CED4', 'hou', 'Houston, TX'),
    'IND': ('Indiana', 'Pacers', '#002D62', '#FDBB30', 'ind', 'Indianapolis, IN'),
    'LAC': ('LA', 'Clippers', '#C8102E', '#1D428A', 'lac', 'Inglewood, CA'),
    'LAL': ('Los Angeles', 'Lakers', '#552583', '#FDB927', 'lal', 'Los Angeles, CA'),
    'MEM': ('Memphis', 'Grizzlies', '#5D76A9', '#12173F', 'mem', 'Memphis, TN'),
    'MIA': ('Miami', 'Heat', '#98002E', '#F9A01B', 'mia', 'Miami, FL'),
    'MIL': ('Milwaukee', 'Bucks', '#00471B', '#EEE1C6', 'mil', 'Milwaukee, WI'),
    'MIN': ('Minnesota', 'Timberwolves', '#0C2340', '#78BE20', 'min', 'Minneapolis, MN'),
    'NOP': ('New Orleans', 'Pelicans', '#0C2340', '#C8102E', 'no', 'New Orleans, LA'),
    'NYK': ('New York', 'Knicks', '#006BB6', '#F58426', 'ny', 'New York, NY'),
    'OKC': ('Oklahoma City', 'Thunder', '#007AC1', '#EF3B24', 'okc', 'Oklahoma City, OK'),
    'ORL': ('Orlando', 'Magic', '#0077C0', '#C4CED4', 'orl', 'Orlando, FL'),
    'PHI': ('Philadelphia', '76ers', '#006BB6', '#ED174C', 'phi', 'Philadelphia, PA'),
    'PHX': ('Phoenix', 'Suns', '#1D1160', '#E56020', 'phx', 'Phoenix, AZ'),
    'POR': ('Portland', 'Trail Blazers', '#E03A3E', '#000000', 'por', 'Portland, OR'),
    'SAC': ('Sacramento', 'Kings', '#5A2D81', '#63727A', 'sac', 'Sacramento, CA'),
    'SAS': ('San Antonio', 'Spurs', '#C4CED4', '#000000', 'sa', 'San Antonio, TX'),
    'TOR': ('Toronto', 'Raptors', '#CE1141', '#000000', 'tor', 'Toronto, ON'),
    'UTA': ('Utah', 'Jazz', '#753BBD', '#000000', 'utah', 'Salt Lake City, UT'),
    'WAS': ('Washington', 'Wizards', '#002B5C', '#E31837', 'wsh', 'Washington, DC'),
}

TEAM_ABBRS = sorted(_TEAMS)


def _luminance(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def team(abbr):
    """Everything the app needs to draw a team, as a dict."""
    city, nickname, primary, secondary, espn_slug, home_city = _TEAMS[abbr]
    # Very dark primaries (navy, black) vanish on a dark background, so the
    # accent used for glows and highlights falls back to the secondary color.
    accent = primary if _luminance(primary) > 0.045 else secondary
    # Secondary text color on the card, with the same fallback for black
    label = secondary if _luminance(secondary) > 0.045 else '#A1A1AA'
    return {
        'abbr': abbr,
        'city': city,
        'nickname': nickname,
        'name': f"{city} {nickname}",
        'primary': primary,
        'secondary': secondary,
        'accent': accent,
        'label': label,
        'espn_slug': espn_slug,
        'home_city': home_city,
        'logo_path': os.path.join(LOGO_DIR, f"{abbr}.png"),
    }
