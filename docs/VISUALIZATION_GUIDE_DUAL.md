# NBA Prediction Visualization Guide - Dual Output System

## Overview
The visualization tool now creates **TWO separate sets of visualizations** to match your dual CSV tracking system:

## Visualization Sets

### 1. Historical Visualizations (Season-Long Analysis)
**Source Data:** `prediction_tracking.csv` (all cumulative predictions)

**Files Created:**
- `historical_accuracy_graph.png` - All predictions over time
- `historical_dashboard.png` - Comprehensive 4-panel analysis

**What You'll See:**
Your model's evolution throughout the entire season
Long-term accuracy trends
Cumulative performance metrics
How your model improves (or regresses) over time

**Best For:**
- Tracking model improvement over weeks/months
- Comparing different model versions
- Season-end reporting
- Identifying long-term patterns

---

### 2. Session Visualizations (Current Batch Only)
**Source Data:** `session_results.csv` (current run only)

**Files Created:**
- `session_accuracy_graph.png` - Just this batch of predictions
- `session_dashboard.png` - Analysis of current session

**What You'll See:**
Performance of just the predictions you ran today
Quick snapshot without historical noise
Focused analysis on specific game set

**Best For:**
- Quick performance check after prediction run
- Analyzing specific game batches
- Testing new strategies
- Daily/weekly reports

## Visual Explanations

### Main Accuracy Graph (Both Versions)

```
     Signed Error

    +15  |     ████ Green bars = Correct prediction
         |
    +10  |     |
         |     | Error bars = Margin accuracy
     +5  |
    ════════════════════════════════> Games
     -5  |
         |     |
    -10  |     ████ Red bars = Incorrect prediction
         |
    -15  |
```

**Reading the Graph:**
- **Y-axis (Signed Error):**
  - Positive values = Predicted winner actually won
  - Negative values = Predicted winner lost
  - Distance from 0 = How wrong the margin prediction was

- **Bar Colors:**
  - Green = Correct winner prediction
  - Red = Incorrect winner prediction

- **Error Bars:**
  - Show margin prediction accuracy
  - Smaller error bars = Better margin predictions

**Example Interpretation:**
```
Game: LAL vs GSW
Bar: +8 (green)
└─ Predicted winner: Won
└─ Margin off by 8 points

Game: BOS vs MIA
Bar: -12 (red)
└─ Predicted winner: Lost
└─ Margin off by 12 points
```

### Dashboard (4 Panels)

#### Panel 1: Cumulative Accuracy Over Time
Shows how accuracy changes as more games are predicted

**Historical Dashboard:**
```
Accuracy %
   100 |     ╱─────╲
       |    ╱       ╲___
    80 |   ╱            ╲___
       |  ╱                 ────
    60 | ╱
       |╱___________________
    40 |
       └─────────────────────> Games
        1   10   20   30   40
```
- Shows model evolution
- Identifies when model improves/declines
- Useful for finding optimal retraining points

**Session Dashboard:**
```
Accuracy %
   100 |    ────────
       |
    80 |   ╱
       |  ╱
    60 | ╱
       |╱___________
    40 |
       └───────────> Games
        1    5    10
```
- Shows just current batch trend
- Quick check if this batch was good

#### Panel 2: Confidence vs Margin Error
Shows relationship between your confidence and accuracy

```
Margin Error

   20 |  ○     ○
      |    ○ ○   ○
   15 |  ○   ●     ○
      |    ●   ●
   10 |  ●   ●   ●
      |    ●
    5 |  ●───────── Trend line
      |
    0 └─────────────> Confidence %
      50   60   70   80

  ● = Correct prediction
  ○ = Incorrect prediction
```

**What to Look For:**
- Downward trend = Higher confidence Lower error (good!)
- Upward trend = Higher confidence Higher error (overconfident!)
- Scattered = Confidence doesn't match accuracy

#### Panel 3: Error Distribution
Shows how often you make errors of different sizes

```
Frequency

 15 |     █
    |     █
 10 |   █ █ █
    | █ █ █ █ █
  5 | █ █ █ █ █
    |_█_█_█_█_█_ Margin Error (pts)
      0 5 10 15 20

  █ Green = Correct predictions
  █ Red = Incorrect predictions
```

**What to Look For:**
- Peak near 0 = Most predictions have low error
- Spread out = Inconsistent margin predictions
- Separate peaks for correct/incorrect = Different error patterns

#### Panel 4: Accuracy by Confidence Level
Shows how accurate you are at different confidence levels

```
Accuracy %
   100 |        n=14
       |    █    █
    80 |    █    █
       |    █  n=5█  n=23
    60 |    █    █    █
       |    █    █    █
    40 |____|____|____|___
       └──────────────────> Confidence
        50-55 65-75  75+
```

**What to Look For:**
- Rising bars = Higher confidence Higher accuracy (well-calibrated!)
- Flat bars = Confidence doesn't predict accuracy
- Small n values = Not enough data in that range

## Usage Workflow

### Scenario 1: Daily Prediction Routine
```bash
# Make today's predictions
python predict_games.py

# Track accuracy
python track_accuracy.py

# Visualize today's results
python visualize_predictions.py

# Check session graphs for today's performance
# historical graphs update automatically
```

**Look at:**
- `session_accuracy_graph.png` - How did today go?
- `session_dashboard.png` - Quick analysis

### Scenario 2: Weekly Performance Review
```bash
# After a week of predictions
python visualize_predictions.py

# Check historical graphs for weekly trends
```

**Look at:**
- `historical_accuracy_graph.png` - Week-over-week performance
- `historical_dashboard.png` - Panel 1: Is accuracy trending up?

### Scenario 3: Model Update Testing
```bash
# Before model update
python visualize_predictions.py
cp historical_accuracy_graph.png before_update.png

# Update model...

# After model update
python predict_games.py
python track_accuracy.py
python visualize_predictions.py

# Compare:
# - before_update.png vs historical_accuracy_graph.png
```

## Interpreting Results

### Historical Graphs - What to Look For:

**Good Signs:**
- Accuracy increasing over time (upward trend in Panel 1)
- High-confidence predictions more accurate (Panel 4 rising)
- Error bars getting smaller (margin predictions improving)
- Errors clustering near 0 (Panel 3)

**Warning Signs:**
- Accuracy declining over time (need retraining)
- Random relationship between confidence and accuracy
- Large error bars (inconsistent predictions)
- High confidence but low accuracy (overconfident model)

### Session Graphs - What to Look For:

**Good Session:**
- Most bars are green
- Error bars are small
- Accuracy > 60%
- High confidence games mostly correct

**Bad Session:**
- Many red bars
- Large error bars
- Accuracy < 55%
- High confidence games incorrect (rethink model)

## Pro Tips

### 1. Compare Historical vs Session
```python
# Quick comparison script
import matplotlib.pyplot as plt
from PIL import Image

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

historical = Image.open('historical_accuracy_graph.png')
session = Image.open('session_accuracy_graph.png')

ax1.imshow(historical)
ax1.set_title('Historical (All Time)', fontsize=16)
ax1.axis('off')

ax2.imshow(session)
ax2.set_title('Session (Today)', fontsize=16)
ax2.axis('off')

plt.savefig('comparison.png', dpi=300, bbox_inches='tight')
```

### 2. Track Best Sessions
```bash
# Save today's session if it was exceptional
cp session_accuracy_graph.png best_sessions/session_2025-10-29.png
```

### 3. Identify Problem Games
Look at historical graph - which games have the longest red bars?
Those teams might need special handling in your model.

### 4. Monitor Confidence Calibration
Check Panel 2 in both dashboards:
- Historical: Are you generally well-calibrated?
- Session: Was today's confidence appropriate?

## Quick Decision Guide

| Question | Look At This |
|----------|-------------|
| How am I doing overall? | Historical accuracy graph |
| Is my model improving? | Historical dashboard - Panel 1 |
| Did today's predictions work? | Session accuracy graph |
| Should I retrain my model? | Historical dashboard - Panel 1 (declining?) |
| Am I overconfident? | Either dashboard - Panel 2 |
| Which teams do I struggle with? | Historical accuracy graph (red bars) |
| Is this batch worth tracking? | Session dashboard - overall accuracy |

## File Summary

| File | Source | Purpose | Overwrites? |
|------|--------|---------|-------------|
| `historical_accuracy_graph.png` | prediction_tracking.csv | Season trends | Yes (updates) |
| `historical_dashboard.png` | prediction_tracking.csv | Full analysis | Yes (updates) |
| `session_accuracy_graph.png` | session_results.csv | Today's results | Yes |
| `session_dashboard.png` | session_results.csv | Today's analysis | Yes |

## Installation & Usage

### First Time Setup:
```bash
pip install matplotlib --break-system-packages
```

### Regular Use:
```bash
python visualize_predictions.py
```

### Expected Output:
```
NBA Prediction Visualization Tool
============================================================

HISTORICAL DATA (prediction_tracking.csv)
------------------------------------------------------------
Creating historical visualizations...
Loaded 42 predictions
Creating main accuracy graph...
Saved: historical_accuracy_graph.png
Creating comprehensive dashboard...
Saved: historical_dashboard.png

SESSION DATA (session_results.csv)
------------------------------------------------------------
Creating session visualizations...
Loaded 10 predictions
Creating main accuracy graph...
Saved: session_accuracy_graph.png
Creating comprehensive dashboard...
Saved: session_dashboard.png

============================================================
Visualization complete!

Files created:

   HISTORICAL VISUALIZATIONS:
   • historical_accuracy_graph.png
     └─ Game-by-game performance over entire season
   • historical_dashboard.png
     └─ Comprehensive 4-panel analysis

   SESSION VISUALIZATIONS:
   • session_accuracy_graph.png
     └─ Performance for current prediction batch
   • session_dashboard.png
     └─ Analysis of current session only

Use historical charts to see long-term trends
Use session charts for quick current batch analysis
```

## Complete Workflow Example

```bash
# Monday: Predict games
python predict_games.py
python track_accuracy.py
python visualize_predictions.py
# Check session_accuracy_graph.png

# Tuesday: More predictions
python predict_games.py
python track_accuracy.py
python visualize_predictions.py
# Check both session (today) and historical (all time)

# Sunday: Weekly review
python visualize_predictions.py
# Analyze historical_dashboard.png for weekly trends
```

That's it! You now have powerful dual visualization tracking for both daily analysis and long-term trends!
