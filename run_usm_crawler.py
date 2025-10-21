#!/usr/bin/env python3
"""
Run USM Parallel Crawler with real-time output
"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from usm_parallel_crawler import ParallelUSMCrawler
    print("Successfully imported ParallelUSMCrawler")
except ImportError as e:
    print(f"❌ Error importing crawler: {e}")
    print("Make sure usm_parallel_crawler.py is in the current directory")
    sys.exit(1)

async def main():
    """Run the crawler with real-time output"""
    print("Starting USM Parallel Crawler")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        crawler = ParallelUSMCrawler()
        await crawler.crawl_entire_website()
        
        print("\n" + "=" * 60)
        print("Crawler completed successfully!")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\nCrawler interrupted by user (Ctrl+C)")
        print("Partial results may have been saved")
    except Exception as e:
        print(f"\nError running crawler: {e}")
        print("Check the error message above for details")

if __name__ == '__main__':
    print("Initializing crawler...")
    asyncio.run(main())
