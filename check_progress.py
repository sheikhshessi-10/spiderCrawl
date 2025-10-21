#!/usr/bin/env python3
"""
Quick progress checker for USM crawler
"""

import os
import json
import glob
from datetime import datetime

def check_progress():
    """Check the current crawling progress"""
    print("🔍 USM Crawl Progress Check")
    print("=" * 50)
    
    # Find the latest results file
    json_files = glob.glob("usm_crawler/usm_crawl_results_*.json")
    if not json_files:
        print("⏳ No results files found yet...")
        return
    
    latest_file = max(json_files, key=os.path.getctime)
    
    try:
        # Read and display stats
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stats = data.get('crawl_stats', {})
        pages = data.get('pages', [])
        
        print(f"📁 Latest file: {latest_file}")
        print(f"📄 Pages crawled: {stats.get('pages_crawled', 0):,}")
        print(f"💾 Results saved: {len(pages):,}")
        print(f"🕐 Last updated: {datetime.fromtimestamp(os.path.getmtime(latest_file)).strftime('%H:%M:%S')}")
        
        if pages:
            # Calculate content stats
            total_content = sum(len(page.get('content', '')) for page in pages)
            avg_content = total_content / len(pages) if pages else 0
            max_content = max(len(page.get('content', '')) for page in pages)
            
            print(f"📝 Total content: {total_content:,} characters")
            print(f"📊 Average content: {avg_content:.0f} characters")
            print(f"📈 Max content: {max_content:,} characters")
            
            # Show recent URLs
            print(f"\n🔗 Recent pages:")
            for page in pages[-5:]:
                url = page.get('url', 'Unknown')
                title = page.get('title', 'No title')[:60]
                content_len = len(page.get('content', ''))
                print(f"  • {title} ({content_len:,} chars)")
                print(f"    {url}")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error reading results: {e}")

if __name__ == '__main__':
    check_progress()
