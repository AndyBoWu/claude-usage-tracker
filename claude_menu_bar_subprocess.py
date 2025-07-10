#!/usr/bin/env python3
"""
Claude Usage Menu Bar App for macOS - Subprocess Version
Shows real-time Claude usage statistics in the macOS menu bar
This version uses subprocess to call the tracker script
"""

import rumps
import json
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta
import threading
import time
from pathlib import Path
from zoneinfo import ZoneInfo

class ClaudeUsageMenuBarApp(rumps.App):
    def __init__(self):
        super(ClaudeUsageMenuBarApp, self).__init__("Loading...", quit_button=None)
        # Clear any default menu items first
        self.menu.clear()
        self.menu = [
            "Today's Requests: Loading...",
            "Today's Cost: Loading...",
            None,  # Separator
            "30-Day Average: Loading...",
            "Monthly Total: Loading...",
            None,  # Separator
            "Refresh Now",
            "Auto-refresh: ON",
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        self.auto_refresh = True
        self.refresh_interval = 30  # 30 seconds
        
        # Start auto-refresh thread
        self.refresh_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
        self.refresh_thread.start()
        
        # Initial refresh
        self.refresh_stats()
    
    def auto_refresh_loop(self):
        """Background thread for auto-refreshing stats"""
        while True:
            if self.auto_refresh:
                self.refresh_stats()
            time.sleep(self.refresh_interval)
    
    def get_usage_stats(self):
        """Get usage statistics by running the tracker script"""
        try:
            # Try different locations for the tracker script
            tracker_locations = [
                # When running from app bundle
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'claude_usage_tracker.py'),
                # When running from source
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'claude_usage_tracker.py'),
                # Hardcoded fallback
                '/Users/andy/Repos/andybowu/claude-usage-tracker/claude_usage_tracker.py'
            ]
            
            tracker_path = None
            for path in tracker_locations:
                if os.path.exists(path):
                    tracker_path = path
                    break
            
            if not tracker_path:
                print(f"Error: Could not find claude_usage_tracker.py in any of these locations: {tracker_locations}")
                return None
            
            # Run the tracker script
            result = subprocess.run(
                ['python3', tracker_path, '--json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            print(f"Error running tracker: {e}")
            print(f"stderr: {e.stderr}")
            return None
        except Exception as e:
            print(f"Error getting usage stats: {e}")
            return None
    
    def parse_json_output(self, json_output):
        """Parse the JSON output to extract key metrics"""
        stats = {
            'total_requests': 'N/A',
            'total_cost': 'N/A',
            'daily_avg': 'N/A',
            'monthly_est': 'N/A',
            'today_requests': 'N/A',
            'today_cost': 'N/A'
        }
        
        if not json_output:
            return stats
        
        try:
            data = json.loads(json_output)
            
            # Extract 30-day summary stats
            thirty_day = data.get('30_days', {}).get('summary', {})
            stats['total_requests'] = f"{thirty_day.get('total_requests', 0):,}"
            stats['total_cost'] = f"${thirty_day.get('total_cost_usd', 0):.2f}"
            stats['daily_avg'] = f"${thirty_day.get('daily_avg_cost', 0):.2f}"
            stats['monthly_est'] = f"${thirty_day.get('monthly_est_cost', 0):.2f}"
            
            # Get today's stats from by_day data
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            # Check in 30_days by_day data
            by_day = data.get('30_days', {}).get('by_day', {})
            if today_str in by_day:
                today_data = by_day[today_str]
                stats['today_requests'] = f"{today_data.get('requests', 0):,}"
                stats['today_cost'] = f"${today_data.get('cost_usd', 0):.2f}"
            else:
                stats['today_requests'] = "0"
                stats['today_cost'] = "$0.00"
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"JSON output: {json_output}")
        except Exception as e:
            print(f"Error parsing output: {e}")
        
        return stats
    
    @rumps.clicked("Refresh Now")
    def refresh_clicked(self, _):
        """Manual refresh button"""
        self.refresh_stats()
    
    @rumps.clicked("Auto-refresh: ON", "Auto-refresh: OFF")
    def toggle_auto_refresh(self, sender):
        """Toggle auto-refresh on/off"""
        self.auto_refresh = not self.auto_refresh
        sender.title = f"Auto-refresh: {'ON' if self.auto_refresh else 'OFF'}"
    
    def quit_app(self, _):
        """Quit the application"""
        rumps.quit_application()
    
    def refresh_stats(self):
        """Refresh usage statistics from the tracker"""
        try:
            json_output = self.get_usage_stats()
            
            if json_output:
                stats = self.parse_json_output(json_output)
                
                # Update menu bar title with TODAY's cost only
                self.title = stats['today_cost']
                
                # Update menu items
                self.menu["Today's Requests: Loading..."].title = f"Today's Requests: {stats['today_requests']}"
                self.menu["Today's Cost: Loading..."].title = f"Today's Cost: {stats['today_cost']}"
                self.menu["30-Day Average: Loading..."].title = f"30-Day Average: {stats['daily_avg']}"
                self.menu["Monthly Total: Loading..."].title = f"Monthly Total: {stats['total_cost']}"
            else:
                self.title = "Error"
                print("Error: No output from tracker")
        
        except Exception as e:
            self.title = "Error"
            print(f"Exception in refresh_stats: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Check if rumps is installed
    try:
        import rumps
    except ImportError:
        print("Installing required package: rumps")
        import subprocess
        subprocess.run(['pip3', 'install', 'rumps'], check=True)
        import rumps
    
    app = ClaudeUsageMenuBarApp()
    app.run()