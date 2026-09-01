#!/usr/bin/env python3
"""
MANUAL NBA INJURY TRACKER
Dead simple - just enter injuries and get adjusted predictions
Takes 90 seconds per day
"""

import pandas as pd
import os
from datetime import datetime

# Star player impact values (points they're worth to the spread)
STAR_IMPACTS = {
    # MVP Tier (9-11 points)
    'Luka Doncic': 11.0,
    'Nikola Jokic': 11.0,
    'Giannis Antetokounmpo': 10.5,
    'Shai Gilgeous-Alexander': 9.5,
    'Joel Embiid': 9.5,
    
    # Superstar Tier (7-9 points)
    'Kevin Durant': 9.0,
    'LeBron James': 8.5,
    'Stephen Curry': 8.5,
    'Anthony Davis': 8.0,
    'Victor Wembanyama': 8.0,
    'Kawhi Leonard': 8.0,
    'Jayson Tatum': 7.5,
    'Damian Lillard': 7.0,
    'Ja Morant': 7.0,
    'Zion Williamson': 7.0,
    'Jalen Brunson': 7.0,
    'Anthony Edwards': 7.0,
    
    # All-Star Tier (5-7 points)
    'Tyrese Maxey': 6.5,
    'Donovan Mitchell': 6.5,
    'Devin Booker': 6.5,
    "De'Aaron Fox": 6.5,
    'Tyrese Haliburton': 6.5,
    'Josh Giddey': 6.5,
    'Trae Young': 6.5,
    'LaMelo Ball': 6.5,
    'Pascal Siakam': 6.5,
    'Karl-Anthony Towns': 6.0,
    'Jalen Williams': 6.0,
    'Jimmy Butler': 6.0,
    'Paul George': 6.0,
    'Jalen Johnson': 6.0,
    'Jamal Murray': 6.0,
    'Deni Avdija': 6.0,
    'Jrue Holiday': 5.5,
    'Cade Cunningham': 5.5,
    'Darius Garland': 5.5,
    'Brandon Miller': 5.5,
    'Walker Kessler': 5.5,
    'Tyler Herro': 5.5,
    
    # Key Players Tier (3-5 points)
    'Benedict Mathurin': 5.5,
    'Austin Reaves': 5.5,
    'Lauri Markkanen': 5.0,
    'Domantas Sabonis': 5.0,
    'Nikola Vucevic': 5.0,
    'Bam Adebayo': 5.0,
    'DeMar DeRozan': 5.0,
    'Paolo Banchero': 5.0,
    'Aaron Gordon': 5.0,
    'Cam Thomas': 5.0,
    'Zach LaVine': 4.5,
    'Kristaps Porzingis': 4.5,
    'Stephon Castle': 4.5,
    'Scottie Barnes': 4.5,
    'Jrue Holiday': 4.5,
    'Rj Barret': 4.0,
    'Jarrett Allen': 4.0,
    'Isaiah Stewart': 4.0,
    'Miles Bridges': 4.0,
}

# Team abbreviations
TEAMS = [
    'ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET',
    'GSW', 'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN',
    'NOP', 'NYK', 'OKC', 'ORL', 'PHI', 'PHX', 'POR', 'SAC', 'SAS',
    'TOR', 'UTA', 'WAS'
]

def load_predictions():
    """Load today's predictions"""
    predictions_file = 'Output_Data/predictions_output.txt'
    
    if not os.path.exists(predictions_file):
        print(f"❌ Can't find {predictions_file}")
        print("   Run predict_games.py first!")
        return None
    
    predictions = []
    
    with open(predictions_file, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for game matchups with "GAME X:" prefix
        if line.startswith('GAME') and (':' in line):
            # Extract the matchup part after "GAME X:"
            matchup = line.split(':', 1)[1].strip()
            
            # Check if it's in "vs" or "@" format
            if ' vs ' in matchup.lower():
                separator = ' vs ' if ' vs ' in matchup else ' VS '
                teams = matchup.split(separator)
                
                if len(teams) == 2:
                    home_team = teams[0].strip()
                    away_team = teams[1].strip()
                    
                    # Extract margin and confidence from following lines
                    # Stop when we hit the next GAME line or end of relevant section
                    margin = 0
                    confidence = 0
                    winner = None
                    
                    for j in range(i+1, min(i+10, len(lines))):
                        current_line = lines[j].strip()
                        
                        # Stop if we hit another GAME line
                        if current_line.startswith('GAME') and ':' in current_line:
                            break
                        
                        # Stop if we hit the betting tips section
                        if 'BETTING TIPS' in current_line or current_line.startswith('='):
                            break
                        
                        # Look for "Margin:" (not "Predicted Margin:")
                        if 'Margin:' in lines[j] and 'Predicted Winner' not in lines[j]:
                            margin_str = lines[j].split(':')[1].strip().split()[0]
                            try:
                                margin = float(margin_str)
                            except ValueError:
                                margin = 0
                        
                        # Look for "Confidence:"
                        if 'Confidence:' in lines[j]:
                            conf_str = lines[j].split(':')[1].strip().replace('%', '')
                            try:
                                confidence = float(conf_str)
                            except ValueError:
                                confidence = 0
                        
                        # Look for winner to determine margin sign
                        if 'Predicted Winner:' in lines[j]:
                            if '(HOME)' in lines[j]:
                                winner = 'home'
                            elif '(AWAY)' in lines[j]:
                                winner = 'away'
                    
                    # Adjust margin sign based on winner
                    # Positive margin = home team favored
                    # Negative margin = away team favored
                    if winner == 'away':
                        margin = -abs(margin)
                    else:
                        margin = abs(margin)
                    
                    predictions.append({
                        'home_team': home_team,
                        'away_team': away_team,
                        'base_margin': margin,
                        'confidence': confidence
                    })
        i += 1
    
    return predictions

def manual_injury_entry():
    """Simple manual injury entry"""
    print("\n🏥 INJURY ENTRY")
    print("="*80)
    print("Format: TEAM PLAYER STATUS")
    print("Example: LAL LeBron James OUT")
    print("")
    print("STATUS OPTIONS:")
    print("  OUT       = Definitely not playing (100% impact)")
    print("  DTD  = Probably not playing (70% impact)")
    print("  GTD       = Game-time decision (40% impact)")
    print("")
    print("Type 'done' when finished")
    print("Type 'skip' to use base predictions without adjustments")
    print("="*80)
    print()
    
    injuries = []
    
    while True:
        entry = input(">> ").strip()
        
        if entry.lower() == 'done':
            break
        
        if entry.lower() == 'skip':
            print("\n⏭️  Skipping injury adjustments")
            return None
        
        if not entry:
            continue
        
        # Parse entry
        parts = entry.split()
        if len(parts) < 3:
            print("❌ Format: TEAM PLAYER STATUS")
            print("   Example: LAL LeBron James OUT")
            continue
        
        team = parts[0].upper()
        status = parts[-1].upper()
        player_name = ' '.join(parts[1:-1])
        
        # Validate team
        if team not in TEAMS:
            print(f"❌ Invalid team: {team}")
            print(f"   Valid teams: {', '.join(TEAMS)}")
            continue
        
        # Validate status
        if status not in ['OUT', 'DTD', 'GTD', 'QUESTIONABLE']:
            print(f"❌ Invalid status: {status}")
            print("   Use: OUT, DTD, or GTD")
            continue
        
        # Get player impact
        base_impact = STAR_IMPACTS.get(player_name, 0)
        
        # Adjust based on status
        if status == 'OUT':
            impact = base_impact
        elif status == 'DTD':
            impact = base_impact * 0.7
        elif status in ['GTD', 'QUESTIONABLE']:
            impact = base_impact * 0.4
        else:
            impact = 0
        
        injuries.append({
            'team': team,
            'player': player_name,
            'status': status,
            'impact': round(impact, 1)
        })
        
        if base_impact > 0:
            print(f"✅ {player_name} ({team}) - {status}")
            print(f"   Impact: -{impact:.1f} points")
        else:
            print(f"⚠️  {player_name} ({team}) - {status}")
            print(f"   Unknown player (not in database) - impact: 0 points")
            print(f"   Note: Add high-impact players to STAR_IMPACTS dict")
    
    return injuries

def adjust_predictions(predictions, injuries):
    """Adjust predictions based on injuries"""
    
    if not injuries:
        print("\n✅ No injuries to adjust for - using base predictions")
        return predictions
    
    print("\n🔧 ADJUSTING PREDICTIONS FOR INJURIES")
    print("="*80)
    
    for pred in predictions:
        home = pred['home_team']
        away = pred['away_team']
        base = pred['base_margin']
        
        # Calculate injury impacts
        home_impact = sum([inj['impact'] for inj in injuries if inj['team'] == home])
        away_impact = sum([inj['impact'] for inj in injuries if inj['team'] == away])
        
        # Adjust margin
        # If home team loses a star (home_impact > 0), margin shifts negative
        net_adjustment = away_impact - home_impact
        adjusted = base + net_adjustment
        
        pred['adjusted_margin'] = adjusted
        pred['injury_adjustment'] = net_adjustment
        pred['home_injuries'] = home_impact
        pred['away_injuries'] = away_impact
        
        # Print if there's an adjustment
        if abs(net_adjustment) > 0.5:
            print(f"\n{home} vs {away}:")
            print(f"  Base prediction: {base:+.1f} pts")
            
            if home_impact > 0:
                home_players = [inj['player'] for inj in injuries if inj['team'] == home]
                print(f"  {home} injuries: {', '.join(home_players)} (Total: -{home_impact:.1f} pts)")
            
            if away_impact > 0:
                away_players = [inj['player'] for inj in injuries if inj['team'] == away]
                print(f"  {away} injuries: {', '.join(away_players)} (Total: -{away_impact:.1f} pts)")
            
            print(f"  → ADJUSTED: {adjusted:+.1f} pts")
            
            if abs(net_adjustment) > 5:
                print(f"  🔥 MAJOR ADJUSTMENT: {net_adjustment:+.1f} pts")
    
    return predictions

def print_betting_report(predictions):
    """Print betting recommendations"""
    print("\n" + "="*80)
    print("💰 INJURY-ADJUSTED BETTING REPORT")
    print("="*80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)
    
    # Sort by confidence
    sorted_preds = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
    
    for pred in sorted_preds:
        home = pred['home_team']
        away = pred['away_team']
        margin = pred.get('adjusted_margin', pred['base_margin'])
        base = pred['base_margin']
        adj = pred.get('injury_adjustment', 0)
        conf = pred['confidence']
        
        print(f"\n{home} vs {away}")
        
        # Pick
        if margin > 0:
            pick = f"{home} by {abs(margin):.1f}"
        else:
            pick = f"{away} by {abs(margin):.1f}"
        
        print(f"  PICK: {pick}")
        print(f"  Confidence: {conf:.1f}%")
        
        # Show adjustment if any
        if abs(adj) > 0.5:
            print(f"  Injury adjustment: {adj:+.1f} pts (from {base:+.1f})")
        
        # Betting recommendation
        if conf >= 80:
            print(f"  💵 HIGH CONFIDENCE - Bet 2-3% of bankroll ($10-15)")
            if abs(margin) > 10:
                print(f"  🔥 STRONG FAVORITE - Look for value if Vegas line is less")
        elif conf >= 60:
            print(f"  💵 MEDIUM CONFIDENCE - Bet 1-2% of bankroll ($5-10)")
        elif conf >= 40:
            print(f"  💵 LOW CONFIDENCE - Bet 0.5-1% of bankroll ($2.50-5) or skip")
        else:
            print(f"  ❌ SKIP - Too uncertain")
        
        # Special note for injury-adjusted games
        if abs(adj) > 5:
            print(f"  ⚠️  LINE MIGHT NOT HAVE MOVED YET - CHECK VEGAS QUICKLY!")

def save_results(predictions):
    """Save adjusted predictions to formatted TXT file"""
    output_dir = 'Output_Data'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'injury_adjusted_predictions.txt')
    
    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("🏥 INJURY-ADJUSTED NBA PREDICTIONS\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Games: {len(predictions)}\n")
        f.write("="*80 + "\n\n")
        
        for i, pred in enumerate(predictions, 1):
            home = pred['home_team']
            away = pred['away_team']
            margin = pred.get('adjusted_margin', pred['base_margin'])
            base_margin = pred['base_margin']
            confidence = pred['confidence']
            adjustment = pred.get('injury_adjustment', 0)
            
            # Determine winner and margin
            if margin > 0:
                winner = home
                winner_location = "HOME"
                margin_value = abs(margin)
            else:
                winner = away
                winner_location = "AWAY"
                margin_value = abs(margin)
            
            # Calculate win probability (from margin)
            win_probability = min(95, 50 + (margin_value * 2))
            
            f.write(f"GAME {i}: {home} vs {away}\n")
            f.write("-"*80 + "\n")
            f.write(f"🏆 Predicted Winner: {winner} ({winner_location})\n")
            f.write(f"   Margin: {margin_value:.1f} points\n")
            f.write(f"   Win Probability: {win_probability:.1f}%\n")
            f.write(f"   Confidence: {confidence:.1f}%\n")
            
            # Show injury adjustment if significant
            if abs(adjustment) > 0.5:
                f.write(f"\n   📊 INJURY IMPACT:\n")
                f.write(f"   Base prediction: {base_margin:+.1f} pts\n")
                f.write(f"   Injury adjustment: {adjustment:+.1f} pts\n")
                f.write(f"   Final prediction: {margin:+.1f} pts\n")
                
                if abs(adjustment) > 5:
                    f.write(f"   🔥 MAJOR ADJUSTMENT - Line may not have moved yet!\n")
            
            f.write("\n")
        
        f.write("="*80 + "\n")
        f.write("💡 BETTING NOTES:\n")
        f.write("="*80 + "\n")
        f.write("• Positive margin = home team favored\n")
        f.write("• Negative margin = away team favored\n")
        f.write("• Focus on high confidence games (>60%)\n")
        f.write("• Major adjustments (>5 pts) = potential value bets\n")
        f.write("• Always compare with current Vegas lines\n")
        f.write("="*80 + "\n")
    
    print(f"\n💾 Saved to: {output_file}")

def main():
    print("🏀 NBA MANUAL INJURY TRACKER")
    print("="*80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Step 1: Load predictions
    print("\n📊 Loading predictions...")
    predictions = load_predictions()
    
    if not predictions:
        return
    
    print(f"✅ Loaded {len(predictions)} predictions")
    
    # Step 2: Manual injury entry
    print("\n💡 TIP: Check rotowire.com/basketball/nba-lineups.php for injuries")
    injuries = manual_injury_entry()
    
    # Step 3: Adjust predictions
    predictions = adjust_predictions(predictions, injuries)
    
    # Step 4: Print betting report
    print_betting_report(predictions)
    
    # Step 5: Save results
    save_results(predictions)
    
    print("\n" + "="*80)
    print("✅ DONE!")
    print("="*80)
    print("\n📋 NEXT STEPS:")
    print("1. Check Vegas lines at covers.com")
    print("2. Look for games where your adjusted line differs by 3+ points")
    print("3. Bet on value (only games with edge)")
    print("4. Log bets in bet_tracker.csv")
    print("5. Profit! 💰")

if __name__ == "__main__":
    main()