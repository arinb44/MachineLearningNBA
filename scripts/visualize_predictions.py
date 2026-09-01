#!/usr/bin/env python3
"""
NBA Prediction Visualization
Creates TWO sets of visualizations:
1. Historical visualizations (all predictions over time)
2. Session visualizations (current session only)

Auto-opens generated images in default viewer
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os
import sys
import subprocess
import platform

class PredictionVisualizer:
    def __init__(self):
        self.historical_file = "data/tracking/prediction_tracking.csv"
        self.session_file = "data/tracking/session_results.csv"
        self.created_images = []  # Track created images to open them later
    
    def open_image(self, filepath):
        """Open image file in default viewer (cross-platform)"""
        try:
            if not os.path.exists(filepath):
                print(f"⚠️  Image not found: {filepath}")
                return False
            
            system = platform.system()
            
            if system == 'Darwin':  # macOS
                subprocess.run(['open', filepath], check=True)
            elif system == 'Windows':
                os.startfile(filepath)
            else:  # Linux and others
                subprocess.run(['xdg-open', filepath], check=True)
            
            return True
        except Exception as e:
            print(f"⚠️  Could not auto-open {filepath}: {e}")
            print(f"   Please open manually: {os.path.abspath(filepath)}")
            return False
        
    def load_data(self, filename):
        """Load prediction data from CSV"""
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return None
            
        try:
            df = pd.read_csv(filename)
            
            # Remove duplicates - keep the last occurrence of each unique game
            # (in case predictions were run multiple times for the same game)
            original_count = len(df)
            df = df.drop_duplicates(subset=['home_team', 'away_team', 'date'], keep='last')
            duplicates_removed = original_count - len(df)
            
            if duplicates_removed > 0:
                print(f"🧹 Removed {duplicates_removed} duplicate game(s)")
            
            # Calculate signed error
            # Positive = predicted winner won (correct)
            # Negative = predicted winner lost (incorrect)
            df['signed_error'] = df.apply(lambda row: 
                (row['actual_margin'] - row['predicted_margin']) if row['correct'] == 1
                else -(row['actual_margin'] - row['predicted_margin']),
                axis=1
            )
            
            return df
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
            return None
    
    def create_main_accuracy_graph(self, df, output_file):
        """Create main accuracy graph with signed errors"""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Sort by date for better visualization
        df = df.sort_values('date')
        
        # Create game labels (matchup only — dates cluttered the axis)
        df['game_label'] = df.apply(lambda row:
            f"{row['away_team']}@{row['home_team']}",
            axis=1
        )
        
        # Colors: Green for correct, Red for incorrect
        colors = ['green' if correct == 1 else 'red' for correct in df['correct']]
        
        # Create bar plot
        x_pos = np.arange(len(df))
        bars = ax.bar(x_pos, df['signed_error'], color=colors, alpha=0.6, edgecolor='black')
        
        # Add error bars showing margin prediction accuracy
        ax.errorbar(x_pos, df['signed_error'], 
                   yerr=df['margin_error'],
                   fmt='none', 
                   ecolor='gray', 
                   alpha=0.5,
                   capsize=3)
        
        # Formatting
        ax.set_xlabel('Games', fontsize=12, fontweight='bold')
        ax.set_ylabel('Signed Error (Predicted - Actual Margin)', fontsize=12, fontweight='bold')
        ax.set_title('NBA Prediction Accuracy: Game-by-Game Performance\n' + 
                    'Green = Correct Winner | Red = Incorrect Winner | Error Bars = Margin Accuracy',
                    fontsize=14, fontweight='bold')
        
        # Add horizontal line at y=0
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
        
        # Per-game matchup labels are only readable for small sets;
        # with many games, use a clean numeric axis instead
        if len(df) <= 25:
            ax.set_xticks(x_pos)
            ax.set_xticklabels(df['game_label'], rotation=45, ha='right', fontsize=8)
        else:
            ax.set_xlabel('Games (chronological)', fontsize=12, fontweight='bold')
            ax.margins(x=0.01)
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='green', alpha=0.6, label='Correct Prediction'),
            Patch(facecolor='red', alpha=0.6, label='Incorrect Prediction')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        # Add statistics text box
        accuracy = (df['correct'].sum() / len(df)) * 100
        avg_margin_error = df['margin_error'].mean()
        stats_text = f'Overall Accuracy: {accuracy:.1f}%\n'
        stats_text += f'Avg Margin Error: {avg_margin_error:.1f} pts\n'
        stats_text += f'Total Games: {len(df)}'
        
        ax.text(0.02, 0.98, stats_text,
               transform=ax.transAxes,
               fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file
    
    def create_dashboard(self, df, output_file):
        """Create comprehensive 4-panel dashboard"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Sort by date
        df = df.sort_values('date')
        
        # Panel 1: Cumulative Accuracy Over Time
        df['cumulative_correct'] = df['correct'].cumsum()
        df['cumulative_total'] = range(1, len(df) + 1)
        df['cumulative_accuracy'] = (df['cumulative_correct'] / df['cumulative_total']) * 100
        
        ax1.plot(df['cumulative_total'], df['cumulative_accuracy'], 
                linewidth=2, color='blue', marker='o', markersize=4)
        ax1.set_xlabel('Games Predicted', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Cumulative Accuracy (%)', fontsize=11, fontweight='bold')
        ax1.set_title('Accuracy Evolution Over Time', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([0, 105])
        
        # Add final accuracy annotation
        final_acc = df['cumulative_accuracy'].iloc[-1]
        ax1.axhline(y=final_acc, color='red', linestyle='--', alpha=0.5)
        ax1.text(len(df)/2, final_acc + 3, f'Final: {final_acc:.1f}%', 
                ha='center', fontsize=10, color='red', fontweight='bold')
        
        # Panel 2: Confidence vs Margin Error Scatter
        colors = ['green' if c == 1 else 'red' for c in df['correct']]
        scatter = ax2.scatter(df['confidence'], df['margin_error'], 
                            c=colors,
                            alpha=0.6, s=100, edgecolors='black')
        ax2.set_xlabel('Prediction Confidence (%)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Margin Error (points)', fontsize=11, fontweight='bold')
        ax2.set_title('Confidence vs Margin Error', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add trend line
        z = np.polyfit(df['confidence'], df['margin_error'], 1)
        p = np.poly1d(z)
        ax2.plot(df['confidence'], p(df['confidence']), 
                "r--", alpha=0.5, linewidth=2, label='Trend')
        ax2.legend()
        
        # Panel 3: Error Distribution
        correct_errors = df[df['correct'] == 1]['margin_error']
        incorrect_errors = df[df['correct'] == 0]['margin_error']
        
        if len(correct_errors) > 0:
            ax3.hist(correct_errors, bins=15, 
                    alpha=0.6, color='green', label='Correct Predictions', edgecolor='black')
        if len(incorrect_errors) > 0:
            ax3.hist(incorrect_errors, bins=15, 
                    alpha=0.6, color='red', label='Incorrect Predictions', edgecolor='black')
        ax3.set_xlabel('Margin Error (points)', fontsize=11, fontweight='bold')
        ax3.set_ylabel('Frequency', fontsize=11, fontweight='bold')
        ax3.set_title('Distribution of Margin Errors', fontsize=12, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Panel 4: Accuracy by Confidence Bins
        confidence_bins = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
        df['confidence_bin'] = pd.cut(df['confidence'], bins=confidence_bins)
        
        bin_accuracy = df.groupby('confidence_bin', observed=True).agg({
            'correct': ['sum', 'count', 'mean']
        })
        bin_accuracy.columns = ['correct', 'total', 'accuracy']
        bin_accuracy['accuracy'] = bin_accuracy['accuracy'] * 100
        
        # Only plot bins with data
        bin_accuracy = bin_accuracy[bin_accuracy['total'] > 0]
        
        x_pos = np.arange(len(bin_accuracy))
        bars = ax4.bar(x_pos, bin_accuracy['accuracy'], 
                      color='skyblue', edgecolor='black', alpha=0.7)
        
        # Add counts on bars
        for i, (idx, row) in enumerate(bin_accuracy.iterrows()):
            ax4.text(i, row['accuracy'] + 2, 
                    f"n={int(row['total'])}", 
                    ha='center', fontsize=9, fontweight='bold')
        
        ax4.set_xlabel('Confidence Range (%)', fontsize=11, fontweight='bold')
        ax4.set_ylabel('Accuracy (%)', fontsize=11, fontweight='bold')
        ax4.set_title('Accuracy by Confidence Level', fontsize=12, fontweight='bold')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels([str(idx) for idx in bin_accuracy.index], 
                           rotation=45, ha='right', fontsize=9)
        ax4.set_ylim([0, 105])
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.axhline(y=50, color='red', linestyle='--', alpha=0.3, label='Coin Flip')
        ax4.legend()
        
        # Overall title
        fig.suptitle('NBA Prediction Model - Comprehensive Performance Dashboard', 
                    fontsize=16, fontweight='bold', y=0.995)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file
    
    def visualize_dataset(self, filename, prefix):
        """Create visualizations for a specific dataset"""
        print(f"\n📊 Creating {prefix} visualizations...")
        
        # Load data
        df = self.load_data(filename)
        if df is None or df.empty:
            print(f"❌ No data found in {filename}")
            return False
        
        print(f"✅ Loaded {len(df)} predictions")
        
        # Create visualizations
        os.makedirs("reports", exist_ok=True)
        main_graph = f"reports/{prefix}_accuracy_graph.png"
        dashboard = f"reports/{prefix}_dashboard.png"
        
        print(f"📈 Creating main accuracy graph...")
        self.create_main_accuracy_graph(df, main_graph)
        print(f"✅ Saved: {main_graph}")
        self.created_images.append(main_graph)  # Track for opening later
        
        print(f"📊 Creating comprehensive dashboard...")
        self.create_dashboard(df, dashboard)
        print(f"✅ Saved: {dashboard}")
        self.created_images.append(dashboard)  # Track for opening later
        
        return True
    
    def run(self):
        """Run visualization for both historical and session data"""
        print("🎨 NBA Prediction Visualization Tool")
        print("="*60)
        
        success_count = 0
        
        # Visualize Historical Data
        if os.path.exists(self.historical_file):
            print(f"\n📚 HISTORICAL DATA ({self.historical_file})")
            print("-"*60)
            if self.visualize_dataset(self.historical_file, "historical"):
                success_count += 1
        else:
            print(f"\n⚠️  Historical file not found: {self.historical_file}")
            print("   Run track_accuracy.py first to generate data")
        
        # Visualize Session Data
        if os.path.exists(self.session_file):
            print(f"\n📝 SESSION DATA ({self.session_file})")
            print("-"*60)
            if self.visualize_dataset(self.session_file, "session"):
                success_count += 1
        else:
            print(f"\n⚠️  Session file not found: {self.session_file}")
            print("   Run track_accuracy.py first to generate data")
        
        print("\n" + "="*60)
        
        if success_count > 0:
            print("✅ Visualization complete!")
            print("\n📂 Files created:")
            if os.path.exists(self.historical_file):
                print("\n   HISTORICAL VISUALIZATIONS:")
                print("   • historical_accuracy_graph.png")
                print("     └─ Game-by-game performance over entire season")
                print("   • historical_dashboard.png")
                print("     └─ Comprehensive 4-panel analysis")
            
            if os.path.exists(self.session_file):
                print("\n   SESSION VISUALIZATIONS:")
                print("   • session_accuracy_graph.png")
                print("     └─ Performance for current prediction batch")
                print("   • session_dashboard.png")
                print("     └─ Analysis of current session only")
            
            print("\n💡 Use historical charts to see long-term trends")
            print("💡 Use session charts for quick current batch analysis")
            
            # Open all created images
            if self.created_images:
                print("\n" + "="*60)
                print("🖼️  Opening images...")
                print("="*60)
                
                for img in self.created_images:
                    print(f"Opening: {img}")
                    self.open_image(img)
                
                print(f"\n✅ Opened {len(self.created_images)} image(s) in default viewer")
        else:
            print("❌ No visualizations created")
            print("\n💡 Next steps:")
            print("   1. Run: python predict_games.py")
            print("   2. Run: python track_accuracy.py")
            print("   3. Run: python visualize_predictions.py")
        
        return success_count > 0

def main():
    # Check for matplotlib
    try:
        import matplotlib
    except ImportError:
        print("❌ matplotlib not installed!")
        print("\n📦 Install it with:")
        print("   pip install matplotlib --break-system-packages")
        return
    
    visualizer = PredictionVisualizer()
    visualizer.run()

if __name__ == "__main__":
    main()