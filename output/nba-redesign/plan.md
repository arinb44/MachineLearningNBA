# Plan: NBA Game Predictor redesign

**Project Title:** Bring the NBA predictor into the NFL/MLB site family

**Objective:** Redesign the Streamlit NBA app so it reads as the third sibling of "Fourth and Why" (NFL) and "Full Count" (MLB): warm dark palette, editorial type, a sport-pun name and a basketball section metaphor. The current app works but looks like a cold, generic dark dashboard that doesn't match the other two.

**Users & Context:** NBA fans checking today's win probabilities, and people browsing the three sites as a portfolio. Mostly desktop, often on mobile.

## Design Requirements
1. Warm dark background and cream text, in the same range as the siblings (bg around `#15120f`, text around `#f1e8da`)
2. One accent color distinct from NFL gold and MLB terracotta, so each sport is recognizable
3. A sport-pun site name and wordmark (candidates shown in the directions)
4. A home page: lede, "what drives the number" note, a numbered section grid using a basketball metaphor, one illustration
5. Predictions page keeps the matchup card, win-probability bar and tale of the tape, restyled
6. WCAG AA contrast; works at 375 / 768 / 1280px

## Scope
- **In:** visual design of Home (new), Predictions, Teams, Players; tokens; wordmark; illustration
- **Out:** model, data pipeline, which stats are shown, Figma

## Deliverables
| Deliverable | Format | Location |
|---|---|---|
| 3 directions (Home + Predictions each) | HTML/CSS | `output/nba-redesign/directions/` |
| Refinement rounds, all 4 pages | HTML/CSS | `output/nba-redesign/iterations/round-n/` |
| Tokens | CSS variables + Streamlit theme | `app/styles.css`, `.streamlit/config.toml` (after approval) |
| Wordmark + illustration | SVG | `static/` (after approval) |
| Design spec | Markdown | `output/nba-redesign/design-spec.md` |

## Design Process
Three directions, each a static HTML mockup of Home and Predictions with real team logos and sample game data. You pick one (or combine), then I refine it in rounds, adding Teams and Players. Once approved, I apply it to the Streamlit app.

**Lead skill:** `/impeccable` for directions and refinement (one lead skill only).

## Accessibility & Responsiveness
WCAG 2.2 AA, with real contrast ratios reported each round. Breakpoints are 375, 768 and 1280px. Dark mode only.

## Milestones
1. Directions (3) → you choose
2. Round 1: chosen direction, all 4 pages at desktop
3. Round 2: mobile + tablet, states (no games today, loading, injury notes)
4. Apply to the Streamlit app
5. Spec + final assets

## Decision Points
- Which direction, and the site name
- Accent color
- Whether to keep the current matchup card's glow look or flatten it to fit the family
- Final file paths before anything is written into the app

## Risks & Limitations
- Streamlit limits layout control; some mockup details may need simplifying when applied
- Google Fonts only; no paid typefaces

## Open Questions
- The site name (I'll propose candidates in the directions)
- GitHub repo and branch for commits (asked before the first commit)

**Status:** Approved on 2026-11-24
