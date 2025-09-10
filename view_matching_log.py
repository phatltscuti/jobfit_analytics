#!/usr/bin/env python3
"""
Script to view matching debug log
"""

import os
import sys
from datetime import datetime

def view_log():
    """View the matching debug log"""
    log_file = 'matching_debug.log'
    
    if not os.path.exists(log_file):
        print("❌ Log file not found: matching_debug.log")
        return
    
    print("📋 JobFit Analytics - Matching Debug Log")
    print("=" * 50)
    print(f"📅 Last updated: {datetime.fromtimestamp(os.path.getmtime(log_file))}")
    print(f"📏 File size: {os.path.getsize(log_file)} bytes")
    print("=" * 50)
    print()
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.strip():
                print(content)
            else:
                print("📝 Log file is empty")
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

def clear_log():
    """Clear the matching debug log"""
    log_file = 'matching_debug.log'
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"# JobFit Analytics - Matching Debug Log\n")
            f.write(f"# Log cleared at: {datetime.now()}\n")
            f.write(f"# This file contains detailed logs for matching functionality debugging\n\n")
            f.write("=== LOG CLEARED ===\n")
        print("✅ Log file cleared successfully")
    except Exception as e:
        print(f"❌ Error clearing log file: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == 'clear':
        clear_log()
    else:
        view_log()

if __name__ == "__main__":
    main()
