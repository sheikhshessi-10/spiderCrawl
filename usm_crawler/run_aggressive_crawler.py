#!/usr/bin/env python3
"""
AGGRESSIVE USM Website Crawler
Maximum speed, maximum coverage - extract EVERYTHING from USM website
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime


def run_aggressive_crawler():
    """Run the most aggressive USM crawler possible"""
    
    print(f"🔥 AGGRESSIVE USM WEBSITE CRAWLER")
    print(f"📊 Max pages: 100,000 (UNLIMITED)")
    print(f"⚡ Concurrent requests: 200 (MAXIMUM)")
    print(f"⏱️  Download delay: 0.05s (MINIMAL)")
    print(f"🎯 Target: ENTIRE USM WEBSITE")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Ultra-aggressive settings
    cmd = [
        'python', '-m', 'scrapy', 'crawl', 'usm_spider',
        '-a', 'max_pages=100000',  # 100k pages - should cover entire site
        '-s', 'CONCURRENT_REQUESTS=200',  # Maximum concurrent requests
        '-s', 'DOWNLOAD_DELAY=0.05',  # Minimal delay
        '-s', 'RANDOMIZE_DOWNLOAD_DELAY=0.02',  # Small randomization
        '-s', 'CONCURRENT_REQUESTS_PER_DOMAIN=50',  # High per-domain limit
        '-s', 'AUTOTHROTTLE_ENABLED=False',  # Disable throttling for max speed
        '-s', 'DOWNLOAD_TIMEOUT=15',  # Shorter timeout for speed
        '-s', 'RETRY_TIMES=2',  # Fewer retries for speed
        '-s', 'LOG_LEVEL=WARNING',  # Less logging for speed
        '-L', 'WARNING'
    ]
    
    try:
        print("🚀 Starting aggressive crawl...")
        result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)), 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 80)
            print("✅ AGGRESSIVE CRAWLING COMPLETED!")
            print(f"🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("🎯 Entire USM website should now be extracted!")
        else:
            print(f"\n❌ Crawler failed with return code: {result.returncode}")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Aggressive crawling interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running aggressive crawler: {e}")


if __name__ == '__main__':
    run_aggressive_crawler()
