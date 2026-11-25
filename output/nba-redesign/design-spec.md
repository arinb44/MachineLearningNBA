# The Tip Off: Design Specification

**Prepared by:** Courtside, the NBA redesign agent
**Date:** 2026-11-24
**Status:** Final

## 1. Overview

This is a redesign of the NBA Game Predictor Streamlit app. The app is now **The Tip Off**, and it sits alongside the NFL site ("Fourth and Why") and the MLB site ("Full Count") as a family. It is for fans who want a win probability and a predicted margin for any NBA game.

The design combines two of the original directions. The layout comes from direction A (Court Map): the home page is a half court, and each section of the site is a player on it. The look comes from direction C (Whiteboard): a dark board, chalk lines, a marker-blue accent and handwritten notes.

## 2. Design Rationale

- **Family fit.** All three sites use a sport-pun name, a dark warm background, cream text, a single accent color, and a home page where each section of the site is part of the sport. The NFL site names sections after positions and the MLB site after pitches. Here the sections play positions 1–5, plus a sixth man.
- **A real play.** The court is drawn as a pick-and-roll in standard play-diagram notation, so basketball fans can read it:
  - 5 screens for 1.
  - 1 drives.
  - 5 rolls to the rim.
  - 1 passes to 5.
- **A coach's whiteboard.** The look explains the model like a coach at a whiteboard. Marker circles show which team has the edge, and handwritten notes carry the asides. The data itself stays in a clean condensed sans.
- **Data pages stay plain.** Predictions, Teams and Players follow familiar patterns: lists, tables and charts. The whiteboard look shows in the details, not in the structure.

## 3. Visual Foundations

### Color

Contrast ratios are measured against the background (`--bg`) unless another surface is named. Text needs 4.5:1 to pass WCAG AA.

| Token | Hex | Use | Contrast |
|---|---|---|---|
| `--bg` | `#1a1714` | Page background (the board) | — |
| `--surface` | `#221e1a` | Cards, chart areas, Streamlit secondary background | — |
| `--line` | `#3d3630` | Rules, table borders, control outlines | Decorative |
| `--line-soft` | `#2c2722` | Row dividers | Decorative |
| `--court` | `#4d443b` | Court lines on the home page | Decorative |
| `--text` | `#efe7da` | Body text and headings | 14.5:1 |
| `--muted` | `#b0a596` | Secondary text and captions | 7.4:1 |
| `--faint` | `#8d8275` | Labels, meta text, handwritten notes | 4.7:1 |
| `--chalk` | `#d9cfbf` | Player circles, cuts, the comparison series in charts | 10.7:1 on surface |
| `--accent` | `#7eaee8` | Marker blue: links, the edge circle, ball movement, chart bars | 7.7:1 |
| `--accent-ink` | `#0b1626` | Text on an accent fill | 7.9:1 on accent |
| `--accent-wash` | `#1f2a38` | Hover fill for the court spots | — |
| `--red` | `#e46a5a` | Losses and negative values | 5.5:1 |
| `--ball` | `#e8873f` | The ball on the court (the only orange) | Decorative |

**Team colors** appear only in the tug-of-war bars, where they are the data. Plotly charts use `ACCENT` for the main series, `#d9cfbf` for comparison and road, and `RED` for negative values.

### Typography

- **Archivo**, a variable font with width from 62 to 125, is used for everything except notes:
  - Headings are uppercase at width 62% and weight 900:
    - h1: `clamp(48px, 6vw, 80px)`, line-height 0.9.
    - h3 (section titles): 40px, or 34px under 600px wide.
  - Numbers are at width 70–75% and weight 800. They use tabular figures (`.num`).
  - Body text is set by Streamlit, at 16px and weight 400.
- **Kalam** is the handwriting font:
  - `.mark` is 700 20px in accent blue. It is for the call ("Celtics 64% · by 4.5").
  - `.note` is 400 18px in faint. It is for asides.
- Both fonts load from Google Fonts at the top of `app/styles.css`.

### Spacing and layout

- The content column is at most 1200px wide, with 4.5rem of space above it for the top navigation.
- Section titles have 2.5rem of space above them.
- Each slate row is a four-column grid (`96px 1fr 1fr 260px`), with 22px of padding above and below and a soft divider.
- The home hero has two columns (`1fr 1.05fr`) with a 56px gap.

### Icons and imagery

- **Logo:** `static/brand.svg`, a ball mark drawn in line.
- **Team logos:** served from `app/static/logos/`.
- **Player headshots:** from ESPN, cropped into a chalk-ringed circle with the team logo as a badge.
- **Other icons:** Streamlit Material icons, for example the arrow on page links.
- **Play-diagram notation:**
  - A cut is a solid chalk line.
  - A pass is a dashed blue line.
  - A dribble is a blue zigzag.
  - A screen is a chalk T-bar.

## 4. Screens

Each screen has a static mockup in `final/` and a live page in the app.

| Screen | Mockup | App | Notes |
|---|---|---|---|
| Home | `final/home.html` | `app/home.py` | See below. |
| Predictions | `final/predictions.html` | `app/predictions.py` | See below. |
| Teams | `final/teams.html` | `app/teams.py` | See below. |
| Players | `final/players.html` | `app/players.py` | See below. |
| About | (none) | `app/about.py` | The Model section has a feature-importance chart and metrics table. The Data section lists the sources and the Monday 6 AM ET refresh. |

**Home.**
- The hero has the lede, a "What drives the number" note, and the court.
- Each court spot is a link. On hover or keyboard focus, the circle fills with the accent wash and the label turns blue.
- Below the hero, the next game day's first three games appear, each with a real prediction, followed by a link to the full slate.
- If there is no upcoming schedule, the game list is hidden.

**Predictions.**
- The slate is one list with a row per game. A day switcher moves between dates.
- The "Any matchup" section shows the big win percentage, the tug bar and the next meeting, then the tale of the tape. In the tape, the side with the edge is circled.

States for Predictions, from the round-2 mockups:
- **No games that day** (for example, Thanksgiving): a note, with a link to the next day that has games.
- **Loading:** a skeleton.
- **Off-season:** a note.
- **Model not built:** a message to run the training script.
- **ESPN unreachable:** an error message.

**Teams.**
- The header shows the team's name, with the city handwritten beneath it.
- Power rankings: bars are blue for positive values and red for negative ones.
- Game by game: bars are blue for wins and red for losses.
- Home and road splits: home in blue, road in chalk.

**Players.**
- The header shows the headshot with the team logo as a badge.
- The stat leaders chart uses blue bars.
- The comparison player is drawn in chalk, and all other players are muted dots.
- If the filters are too strict to match anyone, a "filters too strict" state appears.

## 5. Components and Tokens

| Piece | Where |
|---|---|
| CSS tokens (`:root`) and Streamlit chrome overrides | `app/styles.css` (copy: `final/tipoff.css`) |
| Streamlit theme | `.streamlit/config.toml` |
| Python tokens (`BG`, `SURFACE`, `INK`, `INK_MUTED`, `GRID`, `NEUTRAL`, `ACCENT`, `RED`, fonts) and the `style_fig` chart theme | `app/common.py` |
| `section()`: a section title with its URL anchor (`#any-matchup`, `#model`, `#data`) | `app/common.py` |
| `predict()`, shared by Home and Predictions | `app/common.py` |
| `matchup_card` (slate row), `win_probability_bar` (big number, tug bar, next meeting), `tale_of_the_tape` (edge circle), team and player headers | `app/components.py` |
| Court: `POSITIONS`, `spot()`, `zigzag()`, `PLAY` | `app/home.py` |
| Logo | `static/brand.svg` (copy: `final/brand.svg`) |

The CSS classes, all in `app/styles.css`:

| Class | Component |
|---|---|
| `.tug` | Tug-of-war bar |
| `.game` | Slate row |
| `.win` | Big win number |
| `.tape`, `td.e span` | Tale of the tape, and the edge circle |
| `.team-head`, `.player-head` | Team and player headers |
| `.hero`, `.drives`, `.court`, `.spot`, `.tonight` | Home page |
| `.cut`, `.pass`, `.dribble`, `.screen` | Play-diagram lines |

## 6. Accessibility and Responsiveness

**Contrast.** Every text token passes WCAG AA (4.5:1). The lowest is `--faint` at 4.7:1. The ratios are in the color table above.

**Labels for screen readers.**
- Tug bars have `role="img"` and an aria-label with both teams' percentages.
- The court SVG has `role="navigation"` and a description.
- Each court spot is a real link with visible text.

**Keyboard and motion.**
- Court spots show a focus style as well as a hover style.
- A `prefers-reduced-motion` rule turns off all transitions.

**Screen widths.**
- **900px and below:**
  - The hero becomes one column.
  - The next-games strip stacks.
  - Slate rows wrap the odds onto their own line.
- **820px and below:** the top navigation wraps under the wordmark.
- **600px and below:**
  - Section titles shrink to 34px.
  - Court labels grow so they stay readable when the court scales down.
  - Each slate row shows just the two teams, with the tip-off time on top.
  - The big win number drops to 96px.

**Theme.** The app is dark only, like the NFL and MLB sites, and is set as a dark theme in the Streamlit config.

**Tests.** `tests/test_app.py` loads all five pages through AppTest. All 24 tests pass.

## 7. Files and Links

**In `output/nba-redesign/`:**
- Documents: `designAgent.md`, `plan.md`, `progress.md`, `decisions.md`, `design-spec.md`.
- `directions/`: `a-court-map.html`, `b-box-score.html`, `c-whiteboard.html`.
- `iterations/round-1/` and `iterations/round-2/`: `home.html`, `predictions.html`, `teams.html`, `players.html` and `tipoff.css` in each.
- `final/`: `home.html`, `predictions.html`, `teams.html`, `players.html`, `tipoff.css`, `brand.svg`.

**In the project:**
- Changed: `.streamlit/config.toml`, `streamlit_app.py`, `app/styles.css`, `app/common.py`, `app/components.py`, `app/predictions.py`, `app/teams.py`, `app/players.py`, `tests/test_app.py`.
- New: `app/home.py`, `app/about.py`, `static/brand.svg`.

**Repository:** https://github.com/arinb44/MachineLearningNBA, branch `design/the-tip-off`. The redesign is commit 88d4fc7, which is pushed.

**Figma:** none. The mockups are static HTML.

## 8. Decision Log

Every decision below was the user's.

- Skipped the setup interview. The defaults came from the NFL and MLB sites.
- Named the site "The Tip Off".
- Picked direction C (Whiteboard), then asked to combine A's court-map layout with C's look.
- Asked for the court spots to be real basketball positions (1–5 plus the sixth man) rather than places on the floor.
- Approved round 2 and had it applied to the app.
- Chose to link court sections to what already exists:
  - Matchups goes to Predictions → "Any matchup".
  - Model and Data go to a new About page.
- Asked for more arrows, so the court reads as a real pick-and-roll.
- Had the work committed and pushed to `arinb44/MachineLearningNBA` on `design/the-tip-off`.

The full log is in `decisions.md`.

## 9. Known Issues and Next Steps

- **Not yet checked:**
  - The live app at phone widths. Only the mockups were checked at 375px.
  - Clicking through every court link in the live app.
- **Duplicate number:** on Predictions, the Streamlit "Win probability" metric repeats the big number above it. It could be removed.
- **Fonts:** load from Google Fonts at runtime, so with no network the app falls back to system fonts.
- **Open:** a pull request from `design/the-tip-off` into `main`.
