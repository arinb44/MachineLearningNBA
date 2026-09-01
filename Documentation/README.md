# NBA Game Predictor 🏀

Machine learning system for predicting NBA game outcomes using XGBoost.

## Quick Start

### 1. Update Data (Weekly)
```bash
# Fetch latest player stats
python fetch_nba_player_stats_2025-26.py

# Fetch latest game results
python fetch_nba_games_2025-26.py
```

### 2. Make Predictions
Edit `games_to_predict.txt`:
```txt
DET vs CLE
PHI vs ORL
GSW vs BOS
```

Run predictions:
```bash
python predict_games.py
```

Check `predictions_output.txt` for results.

### 3. Train Model (Optional)
```bash
python train_model.py
```

## Files You Need

**Data:**
- `nba_player_stats_2025-26.csv` - Player statistics
- `nba_game_results_2025-26.csv` - Game results for training

**Scripts:**
- `predict_games.py` - Main prediction script
- `train_model.py` - View training stats
- `nba_ml_model_template.py` - Core ML model

**Input/Output:**
- `games_to_predict.txt` - Games to predict (edit this)
- `predictions_output.txt` - Predictions (read this)

## Requirements

```bash
pip install pandas numpy scikit-learn xgboost nba_api
```

## Team Abbreviations

| Team | Code | Team | Code |
|------|------|------|------|
| Atlanta Hawks | ATL | Memphis Grizzlies | MEM |
| Boston Celtics | BOS | Miami Heat | MIA |
| Brooklyn Nets | BKN | Milwaukee Bucks | MIL |
| Charlotte Hornets | CHA | Minnesota Timberwolves | MIN |
| Chicago Bulls | CHI | New Orleans Pelicans | NOP |
| Cleveland Cavaliers | CLE | New York Knicks | NYK |
| Dallas Mavericks | DAL | Oklahoma City Thunder | OKC |
| Denver Nuggets | DEN | Orlando Magic | ORL |
| Detroit Pistons | DET | Philadelphia 76ers | PHI |
| Golden State Warriors | GSW | Phoenix Suns | PHX |
| Houston Rockets | HOU | Portland Trail Blazers | POR |
| Indiana Pacers | IND | Sacramento Kings | SAC |
| LA Clippers | LAC | San Antonio Spurs | SAS |
| LA Lakers | LAL | Toronto Raptors | TOR |
| Memphis Grizzlies | MEM | Utah Jazz | UTA |
| Washington Wizards | WAS | | |

## Understanding Confidence

- **0-30%**: Very close game (3 points or less)
- **30-50%**: Moderate advantage (3-7 points)
- **50-80%**: Strong favorite (7-12 points)
- **80-100%**: Heavy favorite (12+ points)

**Low confidence is normal early in the season** (only ~40 games played). Confidence improves as more games are played.

## Troubleshooting

**"ModuleNotFoundError: No module named 'nba_api'"**
```bash
pip install nba_api
```

**"ModuleNotFoundError: No module named 'xgboost'"**
```bash
brew install libomp
pip install xgboost
```

**Low confidence scores?**
- Normal with only 40 games of data
- Fetch data weekly to improve predictions
- Wait for 100+ games (around January) for best results

**Wrong predictions?**
- Model doesn't account for injuries, rest, or travel
- Early season performance is less predictive
- Use predictions as one factor, not the only factor

## Tips

- ✅ Update data weekly for best results
- ✅ Low confidence = close game (good for betting unders)
- ✅ Check injury reports before using predictions
- ✅ Model improves as season progresses
- ❌ Don't bet your life savings on this
- ❌ Don't use for playoff games (different dynamics)

---

**That's it!** Simple NBA predictions with machine learning.
