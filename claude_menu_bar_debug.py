#!/usr/bin/env python3
"""
Claude Usage Menu Bar App for macOS - Debug Version
Shows real-time Claude usage statistics in the macOS menu bar
This version includes debug output to diagnose issues
"""

import rumps
import json
import os
import re
from datetime import datetime, timezone, timedelta
import threading
import time
from io import StringIO
import sys
from pathlib import Path
import glob
from collections import defaultdict, namedtuple
from typing import Dict, List, Tuple, Optional
from zoneinfo import ZoneInfo
import traceback

# Import the tracker module directly
from claude_usage_tracker import ClaudeUsageTracker, Usage

class ClaudeUsageMenuBarApp(rumps.App):
    def __init__(self):
        super(ClaudeUsageMenuBarApp, self).__init__("Claude: Loading...", quit_button=None)
        
        # Debug: Print Claude directory
        print(f"DEBUG: Looking for Claude logs in: {os.path.expanduser('~/.claude')}")
        print(f"DEBUG: Directory exists: {os.path.exists(os.path.expanduser('~/.claude'))}")
        
        # Clear the menu completely
        self.menu.clear()
        
        # Create menu items
        self.menu_items = {
            'today_requests': rumps.MenuItem("Today's Requests: Loading..."),
            'today_cost': rumps.MenuItem("Today's Cost: Loading..."),
            'sep1': None,
            'daily_avg': rumps.MenuItem("30-Day Average: Loading..."),
            'monthly_total': rumps.MenuItem("Monthly Total: Loading..."),
            'sep2': None,
            'refresh': rumps.MenuItem("Refresh Now", callback=self.refresh_clicked),
            'auto_refresh': rumps.MenuItem("Auto-refresh: ON", callback=self.toggle_auto_refresh),
            'sep3': None,
            'debug': rumps.MenuItem("Show Debug Info", callback=self.show_debug),
            'quit': rumps.MenuItem("Quit", callback=self.quit_app)
        }
        
        # Build menu
        self.menu = [
            self.menu_items['today_requests'],
            self.menu_items['today_cost'],
            self.menu_items['sep1'],
            self.menu_items['daily_avg'],
            self.menu_items['monthly_total'],
            self.menu_items['sep2'],
            self.menu_items['refresh'],
            self.menu_items['auto_refresh'],
            self.menu_items['sep3'],
            self.menu_items['debug'],
            self.menu_items['quit']
        ]
        
        self.auto_refresh = True
        self.refresh_interval = 30  # 30 seconds
        self.last_error = None
        
        # Initialize the tracker
        try:
            self.tracker = ClaudeUsageTracker()
            print(f"DEBUG: Tracker initialized successfully")
            print(f"DEBUG: Projects dir: {self.tracker.projects_dir}")
        except Exception as e:
            self.last_error = f"Failed to initialize tracker: {str(e)}"
            print(f"DEBUG ERROR: {self.last_error}")
            self.title = "Claude: Init Error"
        
        # Start auto-refresh thread
        self.refresh_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
        self.refresh_thread.start()
        
        # Initial refresh
        self.refresh_stats()
    
    def show_debug(self, _):
        """Show debug information"""
        debug_info = f"""Debug Information:
        
Claude Directory: {os.path.expanduser('~/.claude')}
Directory Exists: {os.path.exists(os.path.expanduser('~/.claude'))}
Projects Directory: {os.path.expanduser('~/.claude/projects')}
Projects Dir Exists: {os.path.exists(os.path.expanduser('~/.claude/projects'))}

Last Error: {self.last_error or 'None'}

Python Version: {sys.version}
Working Directory: {os.getcwd()}
"""
        rumps.alert("Debug Info", debug_info)
    
    def auto_refresh_loop(self):
        """Background thread for auto-refreshing stats"""
        while True:
            if self.auto_refresh:
                self.refresh_stats()
            time.sleep(self.refresh_interval)
    
    def get_usage_stats(self):
        """Get usage statistics directly from the tracker"""
        try:
            # Capture the output that would normally go to stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # Run the tracker's main analysis
            conversation_files = self.tracker.get_all_conversation_files()
            print(f"DEBUG: Found {len(conversation_files)} conversation files")
            
            all_usage = []
            for file_path in conversation_files:
                usage_data = self.tracker.extract_usage_from_file(file_path)
                all_usage.extend(usage_data)
            
            print(f"DEBUG: Total usage entries: {len(all_usage)}")
            
            # Generate the summary
            self.tracker.print_summary(all_usage)
            
            # Get the output
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            return output, all_usage
            
        except Exception as e:
            sys.stdout = old_stdout
            self.last_error = f"Error getting usage stats: {str(e)}\n{traceback.format_exc()}"
            print(f"DEBUG ERROR: {self.last_error}")
            return None, []
    
    def parse_usage_output(self, output, all_usage):
        """Parse the CLI output to extract key metrics"""
        stats = {
            'total_requests': 'N/A',
            'total_cost': 'N/A',
            'daily_avg': 'N/A',
            'monthly_est': 'N/A',
            'today_requests': 'N/A',
            'today_cost': 'N/A'
        }
        
        if not output:
            return stats
        
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
        
        # Calculate today's stats directly from usage data
        try:
            pst = ZoneInfo('America/Los_Angeles')
            today_start = datetime.now(pst).replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            today_usage = [u for u in all_usage if today_start <= u.timestamp.astimezone(pst) < today_end]
            
            if today_usage:
                today_requests = len(today_usage)
                today_cost = sum(u.cost_usd for u in today_usage)
                stats['today_requests'] = f"{today_requests:,}"
                stats['today_cost'] = f"${today_cost:.2f}"
            else:
                stats['today_requests'] = "0"
                stats['today_cost'] = "$0.00"
        except Exception as e:
            self.last_error = f"Error calculating today's stats: {str(e)}"
            print(f"DEBUG ERROR: {self.last_error}")
        
        return stats
    
    def refresh_clicked(self, _):
        """Manual refresh button"""
        self.refresh_stats()
    
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
            print("DEBUG: Starting refresh_stats")
            output, all_usage = self.get_usage_stats()
            
            if output:
                stats = self.parse_usage_output(output, all_usage)
                
                # Update menu bar title with TODAY's requests and cost
                self.title = f"Claude: {stats['today_requests']} reqs | {stats['today_cost']}"
                
                # Update menu items
                self.menu_items['today_requests'].title = f"Today's Requests: {stats['today_requests']}"
                self.menu_items['today_cost'].title = f"Today's Cost: {stats['today_cost']}"
                self.menu_items['daily_avg'].title = f"30-Day Average: {stats['daily_avg']}"
                self.menu_items['monthly_total'].title = f"Monthly Total: {stats['total_cost']}"
                
                print("DEBUG: Stats updated successfully")
            else:
                self.title = "Claude: Error"
                print("DEBUG: No output from tracker")
        
        except Exception as e:
            self.title = "Claude: Error"
            self.last_error = f"Exception in refresh_stats: {str(e)}\n{traceback.format_exc()}"
            print(f"DEBUG ERROR: {self.last_error}")

if __name__ == "__main__":
    app = ClaudeUsageMenuBarApp()
    app.run()