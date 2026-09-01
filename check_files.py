"""
Debug script to check prediction and result files
"""

import os
import pandas as pd

def check_files():
    """Check if required files exist and preview their contents."""
    
    print("🔍 NBA Accuracy Tracker - File Checker\n")
    print("="*60)
    
    # Check predictions file
    predictions_file = 'predictions_output.txt'
    print(f"\n1️⃣  Checking: {predictions_file}")
    
    if os.path.exists(predictions_file):
        print(f"   ✅ File exists")
        
        # Get file size
        size = os.path.getsize(predictions_file)
        print(f"   📏 Size: {size} bytes")
        
        # Preview first 20 lines
        with open(predictions_file, 'r') as f:
            lines = f.readlines()
        
        print(f"   📄 Total lines: {len(lines)}")
        print(f"\n   Preview (first 20 lines):")
        print("   " + "-"*56)
        for i, line in enumerate(lines[:20], 1):
            print(f"   {i:2d}: {line.rstrip()}")
        
        if len(lines) > 20:
            print(f"   ... ({len(lines) - 20} more lines)")
    else:
        print(f"   ❌ File NOT found")
        print(f"   💡 Run 'python predict_games.py' to create this file")
    
    # Check results file
    results_file = 'nba_game_results_2025-26.csv'
    print(f"\n2️⃣  Checking: {results_file}")
    
    if os.path.exists(results_file):
        print(f"   ✅ File exists")
        
        try:
            df = pd.read_csv(results_file)
            print(f"   📊 Rows: {len(df)}")
            print(f"   📊 Columns: {list(df.columns)}")
            
            # Show first few games
            if not df.empty:
                print(f"\n   Preview (first 5 games):")
                print("   " + "-"*56)
                preview_cols = ['date', 'home_team', 'away_team', 'home_score', 'away_score']
                available_cols = [col for col in preview_cols if col in df.columns]
                
                for _, row in df.head(5).iterrows():
                    row_str = " | ".join([f"{col}: {row[col]}" for col in available_cols])
                    print(f"   {row_str}")
                
                if len(df) > 5:
                    print(f"   ... ({len(df) - 5} more games)")
        except Exception as e:
            print(f"   ⚠️  Error reading CSV: {e}")
    else:
        print(f"   ❌ File NOT found")
        print(f"   💡 Run 'python fetch_nba_games_2025-26.py' to create this file")
    
    # Check tracking file (if it exists)
    tracking_file = 'prediction_tracking.csv'
    print(f"\n3️⃣  Checking: {tracking_file}")
    
    if os.path.exists(tracking_file):
        print(f"   ✅ File exists")
        try:
            df = pd.read_csv(tracking_file)
            print(f"   📊 Tracked predictions: {len(df)}")
            
            if not df.empty:
                correct = df['correct'].sum()
                accuracy = (correct / len(df)) * 100
                print(f"   🎯 Current accuracy: {correct}/{len(df)} ({accuracy:.1f}%)")
        except Exception as e:
            print(f"   ⚠️  Error reading CSV: {e}")
    else:
        print(f"   ℹ️  File does not exist yet (will be created after first run)")
    
    print("\n" + "="*60)
    print("\n✅ File check complete!")
    print("\n💡 Next steps:")
    print("   1. If predictions file is missing: python predict_games.py")
    print("   2. If results file is missing: python fetch_nba_games_2025-26.py")
    print("   3. Then run: python track_accuracy.py")


if __name__ == "__main__":
    check_files()
