#!/usr/bin/env python3
"""
Claude Usage Floating Window
A small, always-on-top floating window showing real-time Claude usage
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import re
import threading
import time
import os

class ClaudeFloatingWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude Usage")
        
        # Window settings
        self.root.geometry("250x100+20+50")  # width x height + x + y
        self.root.attributes('-topmost', True)  # Always on top
        self.root.attributes('-alpha', 0.9)  # Slight transparency
        
        # Make window frameless and draggable
        self.root.overrideredirect(True)
        
        # Variables
        self.auto_refresh = True
        self.refresh_interval = 60  # 1 minute
        self.script_path = os.path.join(os.path.dirname(__file__), "claude_usage_tracker.py")
        
        # Create UI
        self.create_widgets()
        
        # Make window draggable
        self.make_draggable()
        
        # Start refresh thread
        self.refresh_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
        self.refresh_thread.start()
        
        # Initial refresh
        self.refresh_stats()
    
    def create_widgets(self):
        # Main frame with border
        main_frame = ttk.Frame(self.root, relief=tk.RAISED, borderwidth=2)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Title bar
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        title_label = ttk.Label(title_frame, text="Claude Usage", font=('Arial', 12, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = ttk.Button(title_frame, text="×", width=3, command=self.root.quit)
        close_btn.pack(side=tk.RIGHT)
        
        # Stats frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Requests label
        self.requests_label = ttk.Label(stats_frame, text="Requests: Loading...", font=('Arial', 11))
        self.requests_label.pack(anchor=tk.W)
        
        # Cost label
        self.cost_label = ttk.Label(stats_frame, text="Cost: Loading...", font=('Arial', 11))
        self.cost_label.pack(anchor=tk.W)
        
        # Daily average label
        self.daily_label = ttk.Label(stats_frame, text="Daily avg: Loading...", font=('Arial', 9))
        self.daily_label.pack(anchor=tk.W)
    
    def make_draggable(self):
        """Make the window draggable"""
        def on_drag_start(event):
            self.x = event.x
            self.y = event.y
        
        def on_drag_motion(event):
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")
        
        self.root.bind("<Button-1>", on_drag_start)
        self.root.bind("<B1-Motion>", on_drag_motion)
    
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
            'daily_avg': 'N/A'
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
        
        return stats
    
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
                
                # Update labels
                self.requests_label.config(text=f"Requests: {stats['total_requests']}")
                self.cost_label.config(text=f"Cost: {stats['total_cost']}")
                self.daily_label.config(text=f"Daily avg: {stats['daily_avg']}")
            else:
                self.requests_label.config(text="Error loading stats")
                print(f"Error running tracker: {result.stderr}")
        
        except Exception as e:
            self.requests_label.config(text="Error loading stats")
            print(f"Exception: {e}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ClaudeFloatingWindow()
    app.run()