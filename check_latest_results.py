#!/usr/bin/env python3
"""
Check the latest crawl results
"""

import json
import os
from datetime import datetime

def check_latest_results():
    """Check the latest crawl results"""
    print("📊 LATEST CRAWL RESULTS ANALYSIS")
    print("=" * 50)
    
    # Find the latest results file
    json_files = [f for f in os.listdir('.') if f.startswith('crawl_results_') and f.endswith('.json')]
    if not json_files:
        print("❌ No results files found")
        return
    
    latest_file = max(json_files, key=os.path.getmtime)
    print(f"📁 Latest file: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stats = data.get('crawl_stats', {})
        pages = data.get('pages', [])
        
        print(f"📄 Pages crawled: {stats.get('pages_crawled', 0):,}")
        print(f"❌ Errors: {stats.get('errors', 0):,}")
        print(f"⏱️  Start time: {stats.get('start_time', 'Unknown')}")
        print(f"⏱️  End time: {stats.get('end_time', 'Unknown')}")
        
        if pages:
            total_content = sum(len(page.get('content', '')) for page in pages)
            avg_content = total_content / len(pages) if pages else 0
            max_content = max(len(page.get('content', '')) for page in pages)
            
            print(f"\n📝 Content Analysis:")
            print(f"   Total content: {total_content:,} characters")
            print(f"   Average content: {avg_content:.0f} characters")
            print(f"   Max content: {max_content:,} characters")
            
            # Show content length distribution
            content_lengths = [len(page.get('content', '')) for page in pages]
            content_lengths.sort(reverse=True)
            
            print(f"\n📈 Content Distribution:")
            print(f"   Top 10 pages by content length:")
            for i, length in enumerate(content_lengths[:10]):
                print(f"   {i+1:2d}. {length:,} characters")
            
            # Show recent pages
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
    check_latest_results()
