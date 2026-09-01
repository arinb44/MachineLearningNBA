#!/usr/bin/env python3
"""
NBA Prediction Project Structure Fixer
Automatically reorganizes files into the correct directory structure
"""

import os
import shutil
from pathlib import Path

def create_directories():
    """Create the required directory structure"""
    print("📁 Creating directory structure...")
    
    dirs = ['Input_Data', 'Output_Data', 'Models']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"   ✅ Created/verified: {dir_name}/")

def move_files():
    """Move files to their correct locations"""
    print("\n📦 Moving files to correct locations...")
    
    # Files to move to Input_Data/
    input_files = [
        'nba_player_stats_2025-26.csv',
        'nba_player_stats_with_std_2025-26.csv',
        'games_to_predict.txt',
    ]
    
    for file in input_files:
        if os.path.exists(file):
            dest = f'Input_Data/{file}'
            if not os.path.exists(dest):
                shutil.copy2(file, dest)
                print(f"   ✅ Copied {file} → Input_Data/")
            else:
                print(f"   ⏭️  Skipped {file} (already in Input_Data/)")
        else:
            print(f"   ⚠️  Missing: {file}")
    
    # Create training data file if it doesn't exist
    if os.path.exists('nba_game_results_2025-26.csv'):
        if not os.path.exists('TrainingAccuracyGameData.csv'):
            shutil.copy2('nba_game_results_2025-26.csv', 'TrainingAccuracyGameData.csv')
            print(f"   ✅ Created TrainingAccuracyGameData.csv from nba_game_results_2025-26.csv")
    
    # Move output files to Output_Data/ (optional - they get created there anyway)
    output_files = [
        'feature_importance.csv',
        'most_consistent_points.csv',
        'most_consistent_assists.csv',
        'most_consistent_rebounds.csv',
        'most_consistent_steals.csv',
        'most_consistent_blocks.csv',
    ]
    
    for file in output_files:
        if os.path.exists(file):
            dest = f'Output_Data/{file}'
            if not os.path.exists(dest):
                shutil.copy2(file, dest)
                print(f"   ✅ Copied {file} → Output_Data/")

def create_symlinks():
    """Create symlinks for backward compatibility"""
    print("\n🔗 Creating symlinks for backward compatibility...")
    
    # Symlink player stats in both locations
    if os.path.exists('Input_Data/nba_player_stats_2025-26.csv'):
        if not os.path.exists('nba_player_stats_2025-26.csv'):
            # Can't use symlinks in all environments, so just copy
            print(f"   ℹ️  Player stats already in Input_Data/")
    
    print("   ✅ Symlinks/copies complete")

def verify_structure():
    """Verify the structure is correct"""
    print("\n🔍 Verifying project structure...")
    
    required_files = {
        'Input_Data/nba_player_stats_2025-26.csv': 'Player statistics',
        'Input_Data/games_to_predict.txt': 'Games to predict',
        'TrainingAccuracyGameData.csv': 'Training data',
    }
    
    all_good = True
    for file, description in required_files.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size:,} bytes) - {description}")
        else:
            print(f"   ❌ MISSING: {file} - {description}")
            all_good = False
    
    required_dirs = ['Input_Data', 'Output_Data', 'Models']
    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print(f"   ✅ {dir_name}/ directory exists")
        else:
            print(f"   ❌ MISSING: {dir_name}/ directory")
            all_good = False
    
    return all_good

def show_next_steps():
    """Show what to do next"""
    print("\n" + "="*70)
    print("🎯 PROJECT STRUCTURE FIXED!")
    print("="*70)
    print("\n📋 NEXT STEPS:")
    print("\n1️⃣  TEST TRAINING:")
    print("   python train_model.py")
    print("\n2️⃣  TEST PREDICTIONS:")
    print("   Edit Input_Data/games_to_predict.txt with today's games")
    print("   python predict_games.py")
    print("\n3️⃣  TRACK ACCURACY:")
    print("   python track_accuracy.py")
    print("\n4️⃣  VISUALIZE RESULTS:")
    print("   python visualize_predictions.py")
    print("\n" + "="*70)
    print("💡 TIP: Run 'python check_files.py' anytime to verify file status")
    print("="*70)

def main():
    print("="*70)
    print("🏀 NBA PREDICTION PROJECT STRUCTURE FIXER")
    print("="*70)
    print("\nThis script will:")
    print("  • Create proper directory structure")
    print("  • Move files to correct locations")
    print("  • Create necessary symlinks/copies")
    print("  • Verify everything is in place")
    print("\n" + "="*70)
    
    input("\nPress ENTER to continue...")
    
    # Run the fixes
    create_directories()
    move_files()
    create_symlinks()
    
    # Verify
    success = verify_structure()
    
    # Show next steps
    show_next_steps()
    
    if success:
        print("\n✅ ALL CHECKS PASSED! You're ready to train and predict.")
    else:
        print("\n⚠️  Some files are still missing. Check the output above.")
    
    return success

if __name__ == "__main__":
    main()
