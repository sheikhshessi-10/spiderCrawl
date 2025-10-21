#!/usr/bin/env python3
"""
Monitor the progress of the USM parallel crawler
"""

import os
import json
import glob
from datetime import datetime

def check_crawl_progress():
    """Check the progress of the crawling process"""
    print("🔍 Monitoring USM Parallel Crawler Progress")
    print("=" * 50)
    
    # Check for Python processes
    import subprocess
    try:
        result = subprocess.run(['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue'], 
                              capture_output=True, text=True)
        if 'python' in result.stdout:
            print("✅ Python processes are running")
        else:
            print("❌ No Python processes found")
    except:
        print("⚠️  Could not check Python processes")
    
    # Check for output files
    json_files = glob.glob("usm_parallel_crawl_*.json")
    md_files = glob.glob("usm_parallel_rag_*.md")
    
    if json_files:
        latest_json = max(json_files, key=os.path.getctime)
        print(f"📄 Latest JSON file: {latest_json}")
        
        try:
            with open(latest_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stats = data.get('crawl_stats', {})
                print(f"📊 Pages crawled: {stats.get('total_pages', 0):,}")
                print(f"✅ Successful: {stats.get('successful_pages', 0):,}")
                print(f"📝 Total content: {stats.get('total_content', 0):,} characters")
        except Exception as e:
            print(f"⚠️  Could not read JSON file: {e}")
    else:
        print("⏳ No output files created yet - crawler may still be starting")
    
    if md_files:
        latest_md = max(md_files, key=os.path.getctime)
        print(f"📝 Latest Markdown file: {latest_md}")
    
    # Check for any error logs
    log_files = glob.glob("*.log")
    if log_files:
        print(f"📋 Log files found: {log_files}")
    
    print("\n" + "=" * 50)
    print(f"🕐 Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    check_crawl_progress()
