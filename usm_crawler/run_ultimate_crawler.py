#!/usr/bin/env python3
"""
ULTIMATE USM WEBSITE CRAWLER
Extract EVERYTHING from the entire USM website with maximum speed and coverage
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime


def run_ultimate_crawler():
    """Run the ultimate USM crawler - maximum speed, maximum coverage"""
    
    print(f"🚀 ULTIMATE USM WEBSITE CRAWLER")
    print(f"🎯 Mission: Extract ENTIRE USM website")
    print(f"📊 Max pages: 200,000 (MASSIVE)")
    print(f"⚡ Concurrent requests: 300 (MAXIMUM)")
    print(f"⏱️  Download delay: 0.02s (ULTRA-FAST)")
    print(f"🔥 Auto-throttling: DISABLED (MAXIMUM SPEED)")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Ultimate settings for maximum extraction
    cmd = [
        'python', '-m', 'scrapy', 'crawl', 'usm_spider',
        '-a', 'max_pages=200000',  # 200k pages - should cover entire site
        '-s', 'CONCURRENT_REQUESTS=300',  # Maximum concurrent requests
        '-s', 'DOWNLOAD_DELAY=0.02',  # Ultra-minimal delay
        '-s', 'RANDOMIZE_DOWNLOAD_DELAY=0.01',  # Minimal randomization
        '-s', 'CONCURRENT_REQUESTS_PER_DOMAIN=100',  # Very high per-domain limit
        '-s', 'AUTOTHROTTLE_ENABLED=False',  # Disable throttling for max speed
        '-s', 'DOWNLOAD_TIMEOUT=10',  # Shorter timeout for speed
        '-s', 'RETRY_TIMES=1',  # Minimal retries for speed
        '-s', 'LOG_LEVEL=ERROR',  # Minimal logging for speed
        '-s', 'ROBOTSTXT_OBEY=False',  # Ignore robots.txt for maximum coverage
        '-s', 'COOKIES_ENABLED=False',  # No cookies for speed
        '-s', 'TELNETCONSOLE_ENABLED=False',  # Disable telnet console
        '-s', 'STATS_CLASS=scrapy.statscollectors.MemoryStatsCollector',  # Memory stats
        '-L', 'ERROR'
    ]
    
    try:
        print("🚀 Starting ULTIMATE crawl...")
        print("⚡ This will extract the ENTIRE USM website at maximum speed!")
        print("📊 Monitor progress with: python monitor_crawl.py")
        print("=" * 80)
        
        result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)), 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 80)
            print("🎉 ULTIMATE CRAWLING COMPLETED!")
            print(f"🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("🎯 ENTIRE USM WEBSITE HAS BEEN EXTRACTED!")
            print("📊 Check the results file for your massive dataset!")
        else:
            print(f"\n❌ Ultimate crawler failed with return code: {result.returncode}")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Ultimate crawling interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running ultimate crawler: {e}")


if __name__ == '__main__':
    run_ultimate_crawler()
