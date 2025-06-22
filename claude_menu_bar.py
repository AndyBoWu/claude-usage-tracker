#!/usr/bin/env python3
"""
Claude Usage Menu Bar App for macOS
Shows real-time Claude usage statistics in the macOS menu bar
"""

import rumps
import subprocess
import json
import os
import re
from datetime import datetime
import threading
import time

class ClaudeUsageMenuBarApp(rumps.App):
    def __init__(self):
        super(ClaudeUsageMenuBarApp, self).__init__("Claude: Loading...")
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
            "Quit"
        ]
        self.auto_refresh = True
        self.refresh_interval = 30  # 30 seconds
        self.script_path = os.path.join(os.path.dirname(__file__), "claude_usage_tracker.py")
        
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
    
    def parse_usage_output(self, output):
        """Parse the CLI output to extract key metrics"""
        stats = {
            'total_requests': 'N/A',
            'total_cost': 'N/A',
            'daily_avg': 'N/A',
            'monthly_est': 'N/A',
            'today_requests': 'N/A',
            'today_cost': 'N/A'
        }
        
        # Parse total requests
        requests_match = re.search(r'Total requests:\s*([\d,]+)', output)
        if requests_match:
            stats['total_requests'] = requests_match.group(1)
        
        # Parse API equivalent cost
        cost_match = re.search(r'API equivalent:\s*\$([\d,]+\.?\d*)', output)
        if cost_match:
            stats['total_cost'] = f"${cost_match.group(1)}"
        
        # Parse daily average
        daily_match = re.search(r'Daily average:\s*\$([\d,]+\.?\d*)', output)
        if daily_match:
            stats['daily_avg'] = f"${daily_match.group(1)}"
        
        # Parse monthly estimate
        monthly_match = re.search(r'Monthly estimate:\s*\$([\d,]+\.?\d*)', output)
        if monthly_match:
            stats['monthly_est'] = f"${monthly_match.group(1)}"
        
        # Parse today's stats from the daily table
        # The tracker now shows dates in PST, so use local PST time
        today = datetime.now().strftime('%m-%d')
            
        today_pattern = rf'│\s*{today}\s*│\s*([\d,]+)\s*│\s*\$\s*([\d,]+\.?\d*)'
        today_match = re.search(today_pattern, output)
        if today_match:
            stats['today_requests'] = today_match.group(1).strip()
            stats['today_cost'] = f"${today_match.group(2).strip()}"
        
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
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        """Quit the application"""
        rumps.quit_application()
    
    def refresh_stats(self):
        """Refresh usage statistics from the tracker script"""
        try:
            # Run the usage tracker script
            result = subprocess.run(
                ['python3', self.script_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                stats = self.parse_usage_output(result.stdout)
                
                # Update menu bar title with TODAY's requests and cost
                if stats['today_requests'] != 'N/A':
                    self.title = f"Claude: {stats['today_requests']} reqs | {stats['today_cost']}"
                else:
                    # When no data for today, show 0 instead of total
                    self.title = f"Claude: 0 reqs | $0.00"
                
                # Update menu items
                self.menu["Today's Requests: Loading..."].title = f"Today's Requests: {stats['today_requests']}"
                self.menu["Today's Cost: Loading..."].title = f"Today's Cost: {stats['today_cost']}"
                self.menu["30-Day Average: Loading..."].title = f"30-Day Average: {stats['daily_avg']}"
                self.menu["Monthly Total: Loading..."].title = f"Monthly Total: {stats['total_cost']}"
            else:
                self.title = "Claude: Error"
                print(f"Error running tracker: {result.stderr}")
        
        except Exception as e:
            self.title = "Claude: Error"
            print(f"Exception: {e}")

if __name__ == "__main__":
    # Check if rumps is installed
    try:
        import rumps
    except ImportError:
        print("Installing required package: rumps")
        subprocess.run(['pip3', 'install', 'rumps'], check=True)
        import rumps
    
    app = ClaudeUsageMenuBarApp()
    app.run()