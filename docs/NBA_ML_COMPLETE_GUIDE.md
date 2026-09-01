# NBA Game Prediction ML System - Complete Guide

## Overview
This system categorizes NBA player statistics into **offensive** and **defensive** metrics, aggregates them by team, and creates matchup features for machine learning game prediction.

---

## Data Structure

### 1. Player-Level Data (Input)
Individual player advanced statistics from NBA.com/stats:

#### Offensive Metrics
| Metric | Description | Importance |
|--------|-------------|------------|
| OFF_RATING | Points scored per 100 possessions | Primary offensive efficiency measure |
| TS_PCT | True Shooting % (includes 2PT, 3PT, FT) | Best overall shooting efficiency metric |
| EFG_PCT | Effective Field Goal % | Shooting efficiency without FT |
| AST_PCT | % of teammate FGs assisted while on court | Ball movement and playmaking |
| AST_RATIO | Assists per 100 possessions | Assist frequency |
| OREB_PCT | Offensive rebound % | Second-chance opportunities |
| USG_PCT | % of team plays used while on court | Player's offensive load |

#### Defensive Metrics
| Metric | Description | Importance |
|--------|-------------|------------|
| DEF_RATING | Points allowed per 100 possessions LOWER IS BETTER | Primary defensive efficiency measure |
| DREB_PCT | Defensive rebound % | Limiting opponent second chances |
| REB_PCT | Total rebound % | Overall rebounding impact |
| STL | Steals per game | Defensive disruption |
| BLK | Blocks per game | Rim protection |

#### Overall Impact
| Metric | Description | Importance |
|--------|-------------|------------|
| NET_RATING | OFF_RATING - DEF_RATING | Overall player impact |
| PIE | Player Impact Estimate (0-1 scale) | Holistic performance metric |
| PLUS_MINUS | Point differential when on court | Real impact measure |

---

### 2. Team-Level Data (Aggregated)
For each team, player stats are aggregated using multiple methods:

#### Aggregation Methods
- **Mean**: Simple average across all rotation players
- **Weighted**: Weighted by minutes played (more accurate)
- **Std Dev**: Measure of consistency/depth
- **Max/Min**: Best performer in that category
- **Star Power**: Average PIE of top 3 players

#### Example Team Record
```python
{
    'team': 'LAL',
    'off_off_rating_mean': 115.2,
    'off_off_rating_weighted': 116.1,  # Weighted by minutes
    'off_ts_pct_mean': 0.592,
    'def_def_rating_mean': 110.3,
    'net_rating_weighted': 5.8,
    'star_power': 0.185,
    'rotation_size': 8
}
```

---

### 3. Matchup-Level Data (ML Features)
For each potential game matchup:

#### Feature Categories

**1. Raw Team Stats**
- All home team aggregated stats with `home_` prefix
- All away team aggregated stats with `away_` prefix

**2. Differential Features** (Most Predictive!)
```python
# Offense vs Defense matchups
home_off_vs_away_def = home_off_rating - away_def_rating
away_off_vs_home_def = away_off_rating - home_def_rating

# Overall quality gap
net_rating_differential = home_net_rating - away_net_rating

# Specific advantages
ts_pct_differential = home_ts_pct - away_ts_pct
rebounding_advantage = home_reb_pct - away_reb_pct
star_power_differential = home_star_power - away_star_power
```

**3. Home Court Advantage**
- Binary indicator (1 for home team)
- Or constant value (~2.5 point historical advantage)

---

## Feature Importance Ranking

### Tier 1: Critical Features
1. **net_rating_differential** - Single best predictor of team quality gap
2. **home_off_vs_away_def** - Measures how well home offense matches up vs away defense
3. **away_off_vs_home_def** - Reverse matchup
4. **home_court_advantage** - Historical ~2.5 point advantage

### Tier 2: Strong Predictors
5. **ts_pct_differential** - Shooting efficiency gap
6. **def_rating_differential** - Defensive quality comparison
7. **star_power_differential** - Top-end talent gap
8. **rebounding_advantage** - Second-chance opportunities

### Tier 3: Supporting Features
9. **rotation_size** - Team depth indicator
10. **off_ast_pct** - Ball movement quality
11. **pace_differential** - Game speed preferences
12. **recent_form** - Last 5-10 game performance (if available)

---

## Advanced Feature Engineering

### 1. Four Factors Model
Dean Oliver's Four Factors of Basketball Success:

```python
# For each team
shooting_factor = TS_PCT
turnover_factor = TOV_PCT  # (turnovers / possessions)
rebounding_factor = OREB_PCT + DREB_PCT
freethrow_factor = FT_RATE  # (FT made / FG attempted)

# Create differentials for matchup
shooting_differential = home_shooting - away_shooting
# ... etc for each factor
```

### 2. Pace & Style Matchups
```python
# Pace clash
pace_differential = abs(home_pace - away_pace)
fast_vs_slow = (home_pace > 100) & (away_pace < 95)

# Style clash
iso_heavy_vs_switching_defense = home_usg_pct_max * away_def_rating
motion_offense_vs_zone = home_ast_pct * away_opponent_3pt_pct
```

### 3. Recent Performance Windows
```python
# Weighted recent form (more recent = higher weight)
last_5_games_weighted = (
    game_1 * 0.35 +
    game_2 * 0.25 +
    game_3 * 0.20 +
    game_4 * 0.12 +
    game_5 * 0.08
)
```

### 4. Contextual Features
```python
# Rest and travel
rest_days_advantage = home_rest_days - away_rest_days
back_to_back_penalty = -3 if team_back_to_back else 0
travel_distance = calculate_distance(prev_city, current_city)

# Injury impact
injured_player_pie_loss = sum(injured_players['PIE'])
```

---

## ML Model Recommendations

### 1. Gradient Boosting (Recommended)
**Best for:** Tabular data, feature interactions, non-linear relationships

```python
from xgboost import XGBRegressor

model = XGBRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=6,
    min_child_weight=3,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='reg:squarederror'
)

# Train on point differential
model.fit(X_train, y_train_point_diff)
```

**Key Hyperparameters:**
- `max_depth`: 4-8 (deeper = more complex interactions)
- `learning_rate`: 0.01-0.1 (lower = better but slower)
- `n_estimators`: 500-2000 (with early stopping)

### 2. Neural Network (For Complex Patterns)
```python
from tensorflow import keras

model = keras.Sequential([
    keras.layers.Dense(128, activation='relu', input_shape=(n_features,)),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(64, activation='relu'),
    keras.layers.Dropout(0.2),
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dense(1)  # Point differential output
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])
```

### 3. Ensemble Approach (Best Results)
```python
# Combine multiple models
predictions = (
    0.5 * xgboost_pred +
    0.3 * neural_net_pred +
    0.2 * random_forest_pred
)
```

---

## Target Variables

### 1. Point Differential (Regression)
```python
target = home_score - away_score
# Range: typically -40 to +40
```
**Use case:** Most accurate predictions, can derive win probability

### 2. Win/Loss (Classification)
```python
target = 1 if home_score > away_score else 0
# Binary: 0 or 1
```
**Use case:** Simpler interpretation, direct win probability

### 3. Total Points (Over/Under)
```python
target = home_score + away_score
# Range: typically 180-250
```
**Use case:** Betting market predictions

### 4. Margin Buckets (Multi-class)
```python
if point_diff < -10: target = 0  # Blowout loss
elif point_diff < -3: target = 1  # Loss
elif point_diff <= 3: target = 2  # Close game
elif point_diff <= 10: target = 3  # Win
else: target = 4  # Blowout win
```
**Use case:** Game script prediction

---

## Validation Strategy

### Critical: Avoid Lookahead Bias
NEVER train on future games to predict past games!

### Time-Based Split
```python
# Train on games from Oct-Jan
# Validate on Feb-Mar
# Test on Apr (playoffs separate)

train_mask = (df['date'] >= '2024-10-01') & (df['date'] <= '2025-01-31')
val_mask = (df['date'] >= '2025-02-01') & (df['date'] <= '2025-03-31')
test_mask = df['date'] >= '2025-04-01'
```

### Rolling Window Validation
```python
# Simulate real-time prediction
for month in range(12):
    train_data = df[df['month'] < month]
    test_data = df[df['month'] == month]
    model.fit(train_data)
    predictions = model.predict(test_data)
```

### Metrics to Track
- **MAE** (Mean Absolute Error): Average points off
- **RMSE**: Penalizes large errors
- **Win/Loss Accuracy**: % of games predicted correctly
- **Against Spread**: Beat betting lines?

---

## Implementation Workflow

### Step 1: Data Collection
```bash
# Fetch from NBA Stats API
curl "https://stats.nba.com/stats/leaguedashplayerstats?MeasureType=Advanced&Season=2024-25"
```

### Step 2: Data Processing
```python
# 1. Load player data
players_df = pd.read_csv('player_stats.csv')

# 2. Filter rotation players (>15 MPG)
players_df = players_df[players_df['MIN'] > 15]

# 3. Aggregate by team
team_stats = aggregate_team_stats(players_df)

# 4. Create matchup features
matchups = create_matchup_features(team_stats)

# 5. Add historical game results
matchups = matchups.merge(game_results, on=['home_team', 'away_team', 'date'])
```

### Step 3: Feature Engineering
```python
# Add differential features
matchups['net_rating_diff'] = (
    matchups['home_net_rating'] - matchups['away_net_rating']
)

# Add contextual features
matchups['rest_advantage'] = (
    matchups['home_rest_days'] - matchups['away_rest_days']
)

# Add interaction features
matchups['offense_defense_interaction'] = (
    matchups['home_off_rating'] * matchups['away_def_rating']
)
```

### Step 4: Model Training
```python
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor

# Features
feature_cols = [col for col in matchups.columns
                if col not in ['home_score', 'away_score', 'date']]
X = matchups[feature_cols]
y = matchups['home_score'] - matchups['away_score']

# Time-based split
tscv = TimeSeriesSplit(n_splits=5)

# Train with cross-validation
for train_idx, val_idx in tscv.split(X):
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

    model = XGBRegressor(n_estimators=1000, learning_rate=0.05)
    model.fit(X_train, y_train,
              eval_set=[(X_val, y_val)],
              early_stopping_rounds=50,
              verbose=False)
```

### Step 5: Prediction & Evaluation
```python
# Predict next games
predictions = model.predict(upcoming_games)

# Convert to win probability
win_prob = norm.cdf(predictions / std_dev)

# Evaluate
mae = mean_absolute_error(y_true, predictions)
accuracy = (predictions > 0) == (y_true > 0).mean()
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Data Leakage
**Problem:** Using future information to predict past
**Solution:** Strict time-based validation, no lookahead features

### Pitfall 2: Ignoring Context
**Problem:** Treating all games equally
**Solution:** Add rest days, travel, injuries, playoff flag

### Pitfall 3: Overfitting Recent Games
**Problem:** Model too sensitive to last 1-2 games
**Solution:** Use longer windows (10-20 games) or exponential weighting

### Pitfall 4: Ignoring Home Court
**Problem:** Underestimating venue advantage
**Solution:** Always include home indicator, consider altitude (DEN), etc.

### Pitfall 5: Using Raw Stats Instead of Differentials
**Problem:** Model struggles to compare teams
**Solution:** Create differential features (home - away) for key metrics

---

## Expected Performance

### Realistic Benchmarks
- **Point Spread MAE:** 8-10 points (professional models: 5-7)
- **Win/Loss Accuracy:** 65-70% (coin flip: 50%, vegas: ~70%)
- **Beat the Spread:** 52-54% (breakeven: 52.4% with juice)

### What Affects Accuracy
- Regular season games: More predictable
- Early season: Less historical data
- Playoff games: Different intensity/strategy
- Injured stars: Major impact not in stats
- Trade deadline: New team chemistry

---

## Next Steps & Enhancements

### Phase 1: Basic Model
- [x] Collect advanced stats
- [x] Aggregate by team (offense/defense)
- [x] Create matchup features
- [ ] Train gradient boosting model
- [ ] Validate with time-based splits

### Phase 2: Enhanced Features
- [ ] Add injury data (scrape injury reports)
- [ ] Include rest days & travel distance
- [ ] Add betting market data (lines, totals)
- [ ] Include head-to-head history
- [ ] Add referee assignments (some refs favor home/away)

### Phase 3: Advanced Modeling
- [ ] Ensemble multiple models
- [ ] Deep learning with attention mechanisms
- [ ] Bayesian updating during games
- [ ] Player-level Monte Carlo simulations
- [ ] Real-time prediction updates

### Phase 4: Production
- [ ] Automate daily data pipeline
- [ ] Build API for predictions
- [ ] Create monitoring dashboard
- [ ] A/B test against baseline models
- [ ] Track ROI vs betting markets

---

## Resources

### Data Sources
- NBA.com/stats - Official advanced stats
- Basketball-Reference.com - Historical data
- ESPN API - Real-time updates
- Covers.com - Betting lines

### Libraries
```bash
pip install pandas numpy scikit-learn xgboost lightgbm tensorflow
```

### Further Reading
- Dean Oliver's "Basketball on Paper"
- Ken Pomeroy's adjusted efficiency metrics
- FiveThirtyEight's NBA predictions methodology
- Nate Silver's "The Signal and the Noise"

---

**Good luck with your NBA ML predictions! **
