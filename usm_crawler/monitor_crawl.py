#!/usr/bin/env python3
"""
USM Crawl Monitor
Monitor the progress of the USM website crawler
"""

import os
import json
import time
import glob
from datetime import datetime


def monitor_crawl():
    """Monitor the crawling progress"""
    print("🔍 USM Crawl Monitor")
    print("=" * 50)
    
    while True:
        try:
            # Find the latest results file
            json_files = glob.glob("usm_crawl_results_*.json")
            if not json_files:
                print("⏳ No results files found yet...")
                time.sleep(5)
                continue
            
            latest_file = max(json_files, key=os.path.getctime)
            
            # Read and display stats
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stats = data.get('crawl_stats', {})
            pages = data.get('pages', [])
            
            print(f"\n📊 CRAWL PROGRESS - {datetime.now().strftime('%H:%M:%S')}")
            print(f"📄 Pages crawled: {stats.get('pages_crawled', 0):,}")
            print(f"💾 Results saved: {len(pages):,}")
            print(f"📁 File: {latest_file}")
            
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
                for page in pages[-3:]:
                    url = page.get('url', 'Unknown')
                    title = page.get('title', 'No title')[:50]
                    content_len = len(page.get('content', ''))
                    print(f"  • {title} ({content_len:,} chars)")
                    print(f"    {url}")
            
            print("-" * 50)
            time.sleep(10)  # Update every 10 seconds
            
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"❌ Error monitoring: {e}")
            time.sleep(5)


if __name__ == '__main__':
    monitor_crawl()
