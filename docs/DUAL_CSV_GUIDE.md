# Dual CSV Output Guide

## Overview
The accuracy tracker now outputs **TWO CSV files** with different purposes:

## File 1: `prediction_tracking.csv` (Historical Data)
**Purpose:** Cumulative tracking of ALL predictions across all sessions

**Behavior:**
- First run: Creates new file with current predictions
- Subsequent runs: APPENDS new predictions to existing data
- Never overwrites - keeps growing with each run
- Contains complete historical record

**Use Cases:**
Long-term performance analysis
Tracking model improvement over time
Season-long accuracy trends
Comparing different model versions
Creating charts showing performance evolution

**Example Data After 3 Sessions:**
```csv
date,home_team,away_team,predicted_winner,actual_winner,correct,confidence,tracked_at
2025-10-27,LAL,GSW,GSW,GSW,True,65.5,2025-10-27 10:00:00
2025-10-27,OKC,HOU,OKC,OKC,True,72.3,2025-10-27 10:00:00
2025-10-28,BOS,MIL,BOS,BOS,True,68.1,2025-10-28 15:30:00 Session 2
2025-10-28,NYK,CLE,CLE,CLE,True,71.2,2025-10-28 15:30:00 Session 2
2025-10-29,MIA,CHI,MIA,MIA,True,63.4,2025-10-29 09:15:00 Session 3
```

## File 2: `session_results.csv` (Current Session Only)
**Purpose:** Contains ONLY the predictions from the most recent run

**Behavior:**
- Every run: OVERWRITES previous file completely
- Only contains predictions from THIS execution
- Lightweight and focused on current analysis

**Use Cases:**
Quick review of today's predictions
Importing into other tools for immediate analysis
Creating session-specific reports
Testing new prediction batches
Sharing results without full history

**Example Data (Single Session):**
```csv
date,home_team,away_team,predicted_winner,actual_winner,correct,confidence,tracked_at
2025-10-29,MIA,CHI,MIA,MIA,True,63.4,2025-10-29 09:15:00
2025-10-29,GSW,LAC,GSW,LAC,False,58.7,2025-10-29 09:15:00
```

## Workflow Example

### Day 1: Make First Predictions
```bash
python predict_games.py  # Predict 10 games
python track_accuracy.py
```
**Result:**
- `prediction_tracking.csv` 10 rows
- `session_results.csv` 10 rows

### Day 2: Make More Predictions
```bash
python predict_games.py  # Predict 8 new games
python track_accuracy.py
```
**Result:**
- `prediction_tracking.csv` 18 rows (10 + 8 appended)
- `session_results.csv` 8 rows (overwritten with just Day 2)

### Day 3: Make More Predictions
```bash
python predict_games.py  # Predict 12 new games
python track_accuracy.py
```
**Result:**
- `prediction_tracking.csv` 30 rows (18 + 12 appended)
- `session_results.csv` 12 rows (overwritten with just Day 3)

## Use Case Examples

### Example 1: Weekly Performance Report
```python
import pandas as pd

# Load all historical data
historical = pd.read_csv('prediction_tracking.csv')

# Group by week
historical['week'] = pd.to_datetime(historical['date']).dt.isocalendar().week
weekly_accuracy = historical.groupby('week')['correct'].mean()

print("Weekly Accuracy:")
print(weekly_accuracy)
```

### Example 2: Today's Predictions Only
```python
import pandas as pd

# Just look at today's results
today = pd.read_csv('session_results.csv')

print(f"Today's Accuracy: {today['correct'].mean():.1%}")
print(f"Games Predicted: {len(today)}")
```

### Example 3: Compare Model Versions
```python
import pandas as pd

# Historical data shows model evolution
all_data = pd.read_csv('prediction_tracking.csv')

# Compare accuracy before and after model update
before = all_data[all_data['tracked_at'] < '2025-11-01']
after = all_data[all_data['tracked_at'] >= '2025-11-01']

print(f"Accuracy before update: {before['correct'].mean():.1%}")
print(f"Accuracy after update: {after['correct'].mean():.1%}")
```

## Which File Should You Use?

| Task | Use This File |
|------|---------------|
| Track long-term trends | `prediction_tracking.csv` |
| See if model is improving | `prediction_tracking.csv` |
| Create season visualizations | `prediction_tracking.csv` |
| Quick check today's results | `session_results.csv` |
| Share today's performance | `session_results.csv` |
| Import to spreadsheet for today | `session_results.csv` |
| Test specific prediction batch | `session_results.csv` |

## Pro Tips

1. **Backup Historical Data**
   ```bash
   cp prediction_tracking.csv prediction_tracking_backup.csv
   ```

2. **Reset Historical Data**
   ```bash
   # Start fresh (delete old historical data)
   rm prediction_tracking.csv
   # Next run will create new file
   ```

3. **Export Session for Analysis**
   ```bash
   # Rename session file before next run
   cp session_results.csv results_2025-10-29.csv
   ```

4. **Combine Multiple Sessions**
   ```python
   import pandas as pd
   import glob

   # Combine all saved session files
   files = glob.glob('results_*.csv')
   combined = pd.concat([pd.read_csv(f) for f in files])
   combined.to_csv('combined_results.csv', index=False)
   ```

## Sample Analysis Script

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load historical data
df = pd.read_csv('prediction_tracking.csv')

# Convert date column
df['date'] = pd.to_datetime(df['date'])

# Calculate rolling accuracy (10-game window)
df = df.sort_values('date')
df['rolling_accuracy'] = df['correct'].rolling(window=10).mean()

# Plot
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['rolling_accuracy'] * 100)
plt.title('Model Accuracy Over Time (10-Game Rolling Average)')
plt.xlabel('Date')
plt.ylabel('Accuracy (%)')
plt.grid(True)
plt.savefig('accuracy_trend.png')
print(" Saved accuracy_trend.png")
```

## Summary

- **Historical File** = Complete record of all predictions (cumulative)
- **Session File** = Just this run's predictions (overwrites each time)
- Both files have identical structure
- Use historical for trends, session for quick analysis
- Both are created automatically on every run
