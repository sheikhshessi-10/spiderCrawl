#!/usr/bin/env python3
"""
Real-time monitoring of the USM parallel crawler
"""

import os
import time
import subprocess
import glob
from datetime import datetime

def watch_crawler():
    """Watch the crawler in real-time"""
    print("🔍 Real-time USM Crawler Monitor")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 50)
    
    start_time = datetime.now()
    
    try:
        while True:
            # Clear screen (works on most terminals)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("🔍 Real-time USM Crawler Monitor")
            print(f"⏰ Started monitoring: {start_time.strftime('%H:%M:%S')}")
            print(f"🕐 Current time: {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 50)
            
            # Check Python processes
            try:
                result = subprocess.run(['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue | Measure-Object'], 
                                      capture_output=True, text=True, timeout=5)
                if 'Count' in result.stdout:
                    count = result.stdout.split('Count')[1].split()[0]
                    print(f"🐍 Python processes running: {count}")
                else:
                    print("❌ No Python processes found")
            except:
                print("⚠️  Could not check processes")
            
            # Check for new files
            json_files = glob.glob("usm_parallel_crawl_*.json")
            md_files = glob.glob("usm_parallel_rag_*.md")
            
            if json_files:
                latest_json = max(json_files, key=os.path.getctime)
                file_time = datetime.fromtimestamp(os.path.getctime(latest_json))
                print(f"📄 Latest JSON: {latest_json}")
                print(f"📅 Created: {file_time.strftime('%H:%M:%S')}")
                
                # Try to read progress
                try:
                    with open(latest_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        stats = data.get('crawl_stats', {})
                        print(f"📊 Pages: {stats.get('total_pages', 0):,}")
                        print(f"✅ Success: {stats.get('successful_pages', 0):,}")
                        print(f"📝 Content: {stats.get('total_content', 0):,} chars")
                except:
                    print("📄 JSON file exists but not readable yet")
            else:
                print("⏳ No output files yet - crawler initializing...")
            
            if md_files:
                latest_md = max(md_files, key=os.path.getctime)
                print(f"📝 Latest MD: {latest_md}")
            
            # Check for any new files in the last minute
            recent_files = []
            for file in glob.glob("*"):
                if os.path.isfile(file):
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file))
                    if (datetime.now() - mod_time).seconds < 60:
                        recent_files.append(f"{file} ({mod_time.strftime('%H:%M:%S')})")
            
            if recent_files:
                print(f"🆕 Recent files: {', '.join(recent_files[:3])}")
            
            print("\n" + "=" * 50)
            print("🔄 Refreshing in 10 seconds... (Ctrl+C to stop)")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    watch_crawler()

