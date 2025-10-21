#!/usr/bin/env python3
"""
Quick Results Checker for USM Crawler
Shows where results are stored and current progress
"""

import os
import json
import glob
from datetime import datetime

def check_results():
    """Check the current crawling results"""
    print("📁 USM CRAWLER RESULTS LOCATION")
    print("=" * 50)
    
    # Check the main results directory
    results_dir = "usm_crawler"
    if not os.path.exists(results_dir):
        print(f"❌ Results directory not found: {results_dir}")
        return
    
    print(f"📂 Results Directory: {os.path.abspath(results_dir)}")
    
    # Find all JSON files
    json_files = glob.glob(f"{results_dir}/*.json")
    if not json_files:
        print("⏳ No results files found yet...")
        return
    
    # Sort by modification time
    json_files.sort(key=os.path.getmtime, reverse=True)
    
    print(f"\n📄 Found {len(json_files)} result files:")
    for i, file in enumerate(json_files[:5]):  # Show last 5 files
        file_size = os.path.getsize(file)
        mod_time = datetime.fromtimestamp(os.path.getmtime(file))
        print(f"  {i+1}. {os.path.basename(file)}")
        print(f"     Size: {file_size:,} bytes")
        print(f"     Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check the latest file
    latest_file = json_files[0]
    print(f"\n🔍 Latest Results: {os.path.basename(latest_file)}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stats = data.get('crawl_stats', {})
        pages = data.get('pages', [])
        
        print(f"📊 Pages crawled: {stats.get('pages_crawled', 0):,}")
        print(f"💾 Results saved: {len(pages):,}")
        
        if pages:
            total_content = sum(len(page.get('content', '')) for page in pages)
            avg_content = total_content / len(pages) if pages else 0
            max_content = max(len(page.get('content', '')) for page in pages)
            
            print(f"📝 Total content: {total_content:,} characters")
            print(f"📊 Average content: {avg_content:.0f} characters")
            print(f"📈 Max content: {max_content:,} characters")
            
            # Show recent URLs
            print(f"\n🔗 Recent pages:")
            for page in pages[-3:]:
                url = page.get('url', 'Unknown')
                title = page.get('title', 'No title')[:50]
                content_len = len(page.get('content', ''))
                print(f"  • {title} ({content_len:,} chars)")
                print(f"    {url}")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error reading results: {e}")

if __name__ == '__main__':
    check_results()
