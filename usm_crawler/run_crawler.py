#!/usr/bin/env python3
"""
USM Website Crawler Runner
A comprehensive Scrapy-based crawler for the University of Southern Mississippi website.
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime


def run_crawler(max_pages=10000, concurrent_requests=50, download_delay=0.5):
    """
    Run the USM crawler with specified parameters
    
    Args:
        max_pages (int): Maximum number of pages to crawl
        concurrent_requests (int): Number of concurrent requests
        download_delay (float): Delay between requests in seconds
    """
    
    print(f"🕷️  Starting USM Website Crawler")
    print(f"📊 Max pages: {max_pages:,}")
    print(f"⚡ Concurrent requests: {concurrent_requests}")
    print(f"⏱️  Download delay: {download_delay}s")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # Build the scrapy command
    cmd = [
        'python', '-m', 'scrapy', 'crawl', 'usm_spider',
        '-a', f'max_pages={max_pages}',
        '-s', f'CONCURRENT_REQUESTS={concurrent_requests}',
        '-s', f'DOWNLOAD_DELAY={download_delay}',
        '-s', f'CONCURRENT_REQUESTS_PER_DOMAIN={min(concurrent_requests, 20)}',
        '-L', 'INFO'
    ]
    
    try:
        # Run the crawler
        result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)), 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ Crawling completed successfully!")
            print(f"🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"\n❌ Crawler failed with return code: {result.returncode}")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Crawling interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running crawler: {e}")


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description='USM Website Crawler - Comprehensive Scrapy-based crawler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_crawler.py                           # Default: 10,000 pages, 50 concurrent, 0.5s delay
  python run_crawler.py --max-pages 5000         # Crawl 5,000 pages
  python run_crawler.py --concurrent 100         # Use 100 concurrent requests
  python run_crawler.py --delay 0.2              # 0.2 second delay between requests
  python run_crawler.py --max-pages 20000 --concurrent 100 --delay 0.3  # Custom settings
        """
    )
    
    parser.add_argument('--max-pages', type=int, default=10000,
                       help='Maximum number of pages to crawl (default: 10000)')
    parser.add_argument('--concurrent', type=int, default=50,
                       help='Number of concurrent requests (default: 50)')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay between requests in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.max_pages < 1:
        print("❌ Error: max-pages must be at least 1")
        sys.exit(1)
    
    if args.concurrent < 1:
        print("❌ Error: concurrent requests must be at least 1")
        sys.exit(1)
    
    if args.delay < 0:
        print("❌ Error: delay must be non-negative")
        sys.exit(1)
    
    # Run the crawler
    run_crawler(
        max_pages=args.max_pages,
        concurrent_requests=args.concurrent,
        download_delay=args.delay
    )


if __name__ == '__main__':
    main()
