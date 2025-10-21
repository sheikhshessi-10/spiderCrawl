import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from datetime import datetime
import os
import json
from urllib.parse import urljoin, urlparse
import logging
from typing import Dict, List, Set
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Global variables to store crawling results
crawl_results = []
crawl_stats = {
    'pages_crawled': 0,
    'total_urls': 0,
    'errors': 0,
    'start_time': None,
    'end_time': None
}

class BreadthFirstWebSpider(scrapy.Spider):
    name = 'breadth_first_web_spider'
    
    def __init__(self, start_url, max_pages=100, concurrent_requests=16, 
                 download_delay=0.5, *args, **kwargs):
        super(BreadthFirstWebSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.MAX_PAGES = max_pages
        self.pages_crawled = 0
        self.visited_urls = set()
        
        # Breadth-first traversal queues
        self.current_level_urls = []  # URLs to crawl in current level
        self.next_level_urls = []     # URLs to crawl in next level
        self.current_level = 0
        self.is_processing_level = False
        self.level_complete = False
        self.level_urls_processed = 0
        
        self.custom_settings = {
            'ROBOTSTXT_OBEY': False,
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'LOG_LEVEL': 'INFO',
            'CONCURRENT_REQUESTS': concurrent_requests,
            'CONCURRENT_REQUESTS_PER_DOMAIN': concurrent_requests,
            'DOWNLOAD_DELAY': download_delay,
            'COOKIES_ENABLED': False,
            'DOWNLOAD_TIMEOUT': 5,
            'HTTPCACHE_ENABLED': True,
            'HTTPCACHE_EXPIRATION_SECS': 3600,
            'RETRY_TIMES': 1,
            'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
            'DOWNLOAD_MAXSIZE': 10 * 1024 * 1024,  # 10MB
        }

    def start_requests(self):
        """Start with the initial URL"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.handle_error,
                meta={'level': 0}
            )

    def parse(self, response):
        """Main parsing method with breadth-first traversal"""
        if self.pages_crawled >= self.MAX_PAGES:
            return
            
        level = response.meta.get('level', 0)
        self.pages_crawled += 1
        self.visited_urls.add(response.url)
        
        # Update global stats
        crawl_stats['pages_crawled'] = self.pages_crawled
        crawl_stats['total_urls'] = len(self.visited_urls)
        
        # Progress reporting
        print(f"📄 Crawling page {self.pages_crawled}/{self.MAX_PAGES} (Level {level}): {response.url}")
        if self.pages_crawled % 10 == 0:
            print(f"⏳ Progress: {self.pages_crawled}/{self.MAX_PAGES} pages ({(self.pages_crawled/self.MAX_PAGES)*100:.1f}%)")
        
        # Extract comprehensive content
        content_data = self.extract_comprehensive_content(response)
        
        # Store page data
        page_data = {
            'url': response.url,
            'title': content_data.get('title', ''),
            'content': content_data.get('full_text', ''),
            'content_length': len(content_data.get('full_text', '')),
            'headings': content_data.get('headings', []),
            'links': content_data.get('links', []),
            'level': level,
            'timestamp': datetime.now().isoformat()
        }
        crawl_results.append(page_data)

        # Collect all links from this page for next level
        all_links = response.css('a[href]')
        page_links = []
        
        for link in all_links:
            href = link.css('::attr(href)').get()
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                absolute_url = urljoin(response.url, href)
                if (self.allowed_domains[0] in absolute_url and 
                    absolute_url not in self.visited_urls):
                    page_links.append(absolute_url)
        
        # Add links to next level queue (avoid duplicates)
        for url in page_links:
            if url not in self.next_level_urls:
                self.next_level_urls.append(url)
        
        # Check if we should start processing next level
        if not self.is_processing_level and self.next_level_urls and self.pages_crawled < self.MAX_PAGES:
            yield from self.start_next_level()

    def start_next_level(self):
        """Start processing the next level of URLs"""
        if not self.next_level_urls or self.pages_crawled >= self.MAX_PAGES:
            return
            
        self.current_level += 1
        self.is_processing_level = True
        
        print(f"🔄 Starting Level {self.current_level} with {len(self.next_level_urls)} URLs")
        
        # Process all URLs in next level
        for url in self.next_level_urls:
            if self.pages_crawled < self.MAX_PAGES:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    errback=self.handle_error,
                    meta={'level': self.current_level}
                )
        
        # Clear the next level queue
        self.next_level_urls = []
        self.is_processing_level = False

    def extract_comprehensive_content(self, response):
        """Extract comprehensive content for RAG with safety limits"""
        content_data = {}
        
        try:
            # Extract title
            title = response.css('title::text').get()
            if title:
                title = title.strip()
            content_data['title'] = title or 'No title found'
            
            # Get main content area, excluding unwanted elements
            unwanted_selectors = [
                'script', 'style', 'nav', 'footer', 'header', 
                '.navigation', '.nav', '.menu', '.sidebar',
                '.advertisement', '.ads', '.social-media'
            ]
            
            # Remove unwanted elements
            main_content = response.css('body')
            for selector in unwanted_selectors:
                main_content = main_content.css(f'body:not({selector})')
            
            # Extract headings with levels
            headings = []
            for i in range(1, 7):  # h1 to h6
                heading_elements = main_content.css(f'h{i}::text').getall()
                for heading in heading_elements:
                    if heading.strip():
                        headings.append({
                            'level': i,
                            'text': heading.strip()
                        })
            content_data['headings'] = headings
            
            # Extract paragraphs
            paragraphs = []
            para_elements = main_content.css('p::text').getall()
            for para in para_elements[:100]:  # Limit to 100 paragraphs
                if para.strip() and len(para.strip()) > 10:
                    paragraphs.append(para.strip())
            
            # Extract list items
            list_items = []
            li_elements = main_content.css('li::text').getall()
            for li in li_elements[:200]:  # Limit to 200 list items
                if li.strip() and len(li.strip()) > 5:
                    list_items.append(li.strip())
            
            # Extract div content (for structured content)
            div_content = []
            div_elements = main_content.css('div::text').getall()
            for div in div_elements[:50]:  # Limit to 50 divs
                if div.strip() and len(div.strip()) > 20:
                    div_content.append(div.strip())
            
            # Combine all text content
            full_text = ""
            
            # Add headings
            for heading in headings:
                full_text += f"\n\n{'#' * heading['level']} {heading['text']}\n"
            
            # Add paragraphs
            for para in paragraphs:
                full_text += f"\n{para}\n"
            
            # Add list items
            for li in list_items:
                full_text += f"\n• {li}\n"
            
            # Add div content
            for div in div_content:
                full_text += f"\n{div}\n"
            
            # Extract tables
            tables = main_content.css('table')
            for table in tables[:10]:  # Limit to 10 tables
                table_content = self.extract_table_content(table)
                if table_content:
                    full_text += f"\n\nTable:\n{table_content}\n"
            
            # Extract content from specific divs (like .columns__item)
            content_divs = main_content.css('.columns__item, .content, .main-content, .page-content')
            for div in content_divs[:20]:  # Limit to 20 content divs
                div_content = self.extract_div_content(div)
                if div_content:
                    full_text += f"\n\nSection: {div_content}\n"
            
            # Clean and limit text
            full_text = self.clean_text_for_rag(full_text)
            
            # Safety limit: 50KB of text
            if len(full_text) > 50000:
                full_text = full_text[:50000] + "\n\n[Content truncated due to length limit]"
            
            # Add document structure for better RAG understanding
            structured_content = self.structure_content_for_rag(full_text, content_data.get('title', ''))
            content_data['full_text'] = structured_content
            
            # Extract links for context - prioritize A to Z content links
            links = []
            
            # For A to Z index page, look for links in the main content area
            if 'a-to-z-index' in response.url:
                # Look for A to Z links in various content containers
                content_selectors = [
                    'main a[href]',
                    '.content a[href]', 
                    '.main-content a[href]',
                    '#maincontent a[href]',
                    '.page-content a[href]',
                    'article a[href]',
                    '.columns a[href]',
                    '.grid a[href]'
                ]
                
                for selector in content_selectors:
                    content_links = response.css(selector)
                    for link in content_links:
                        href = link.css('::attr(href)').get()
                        text = link.css('::text').get()
                        if href and text and text.strip():
                            # Skip navigation, anchor, and external links
                            if (not href.startswith('#') and 
                                not href.startswith('javascript:') and
                                'usm.edu' in href and
                                len(text.strip()) > 1):  # Avoid single character links
                                links.append({
                                    'url': urljoin(response.url, href),
                                    'text': text.strip()
                                })
                                if len(links) >= 100:  # Limit for A to Z page
                                    break
                    if len(links) >= 100:
                        break
            else:
                # For other pages, use the original logic
                content_links = main_content.css('a[href]')
                for link in content_links[:50]:
                    href = link.css('::attr(href)').get()
                    text = link.css('::text').get()
                    if href and text and text.strip():
                        if not href.startswith('#') and not href.startswith('javascript:'):
                            links.append({
                                'url': urljoin(response.url, href),
                                'text': text.strip()
                            })
            
            content_data['links'] = links[:50]  # Limit to 50 total links
            
        except Exception as e:
            print(f"⚠️  Error extracting content from {response.url}: {str(e)}")
            content_data = {
                'title': 'Error extracting title',
                'full_text': f'Error extracting content: {str(e)}',
                'headings': [],
                'links': []
            }
        
        return content_data

    def extract_table_content(self, table):
        """Extract content from table elements"""
        try:
            # Get table headers
            headers = table.css('th::text').getall()
            header_text = ' | '.join([h.strip() for h in headers if h.strip()])
            
            # Get table rows
            rows = table.css('tr')
            table_content = ""
            
            if header_text:
                table_content += f"Table: {header_text}\n"
            
            for row in rows[1:]:  # Skip header row
                cells = row.css('td::text').getall()
                if len(cells) == 2:
                    # Two-column table - use Key: Value format
                    key = cells[0].strip()
                    value = cells[1].strip()
                    if key and value:
                        table_content += f"{key}: {value}\n"
                elif len(cells) > 2:
                    # Multi-column table - use pipe format
                    row_text = ' | '.join([cell.strip() for cell in cells if cell.strip()])
                    if row_text:
                        table_content += f"{row_text}\n"
            
            return table_content.strip()
        except Exception as e:
            return f"Error extracting table: {str(e)}"

    def extract_div_content(self, div):
        """Extract content from specific div elements"""
        try:
            # Get heading from div
            heading = div.css('h1::text, h2::text, h3::text, h4::text, h5::text, h6::text').get()
            if heading:
                heading = heading.strip()
            
            # Get paragraphs
            paragraphs = div.css('p::text').getall()
            para_text = ' '.join([p.strip() for p in paragraphs if p.strip()])
            
            # Get tables
            tables = div.css('table')
            table_content = ""
            for table in tables:
                table_text = self.extract_table_content(table)
                if table_text:
                    table_content += f"\n{table_text}\n"
            
            # Get list items
            list_items = div.css('li::text').getall()
            list_text = ' '.join([li.strip() for li in list_items if li.strip()])
            
            # Combine content
            content = ""
            if heading:
                content += f"{heading}\n"
            if para_text:
                content += f"{para_text}\n"
            if table_content:
                content += f"{table_content}\n"
            if list_text:
                content += f"{list_text}\n"
            
            return content.strip()
        except Exception as e:
            return f"Error extracting div content: {str(e)}"

    def clean_text_for_rag(self, text):
        """Clean text for better RAG processing"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
        text = text.strip()
        
        return text

    def structure_content_for_rag(self, content, title):
        """Structure content for better RAG understanding"""
        if not content:
            return ""
        
        # Add document header
        structured = f"Document: {title}\n"
        structured += "=" * (len(title) + 10) + "\n\n"
        
        # Remove duplicate table content
        seen_tables = set()
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            if line.startswith('Table:'):
                if line not in seen_tables:
                    seen_tables.add(line)
                    filtered_lines.append(line)
            else:
                filtered_lines.append(line)
        
        content = '\n'.join(filtered_lines)
        
        # Ensure proper line breaks for markers
        content = content.replace('Table:', '\n\nTable:')
        content = content.replace('Section:', '\n\nSection:')
        
        structured += content
        return structured

    def handle_error(self, failure):
        """Handle request errors"""
        crawl_stats['errors'] += 1
        print(f"❌ Error crawling {failure.request.url}: {failure.value}")

    def closed(self, reason):
        """Called when spider closes"""
        crawl_stats['end_time'] = datetime.now().isoformat()
        print(f"\n✅ Crawling completed!")
        print(f"📊 Total pages crawled: {crawl_stats['pages_crawled']}")
        print(f"🔗 Total unique URLs: {crawl_stats['total_urls']}")
        print(f"❌ Errors: {crawl_stats['errors']}")
        print(f"⏱️  Reason: {reason}")

def crawl_website(start_url, max_pages=50, concurrent_requests=4, download_delay=1.0):
    """Main function to crawl website with breadth-first approach"""
    global crawl_stats
    crawl_stats['start_time'] = datetime.now().isoformat()
    
    print(f"\n🕷️  Starting breadth-first crawl: {start_url}")
    print(f"📊 Max pages: {max_pages}")
    print(f"⚡ Concurrent requests: {concurrent_requests}")
    print(f"⏱️  Download delay: {download_delay}s")
    print("-" * 50)
    
    # Configure Scrapy settings
    settings = get_project_settings()
    settings.update({
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'LOG_LEVEL': 'INFO',
        'CONCURRENT_REQUESTS': concurrent_requests,
        'CONCURRENT_REQUESTS_PER_DOMAIN': concurrent_requests,
        'DOWNLOAD_DELAY': download_delay,
        'COOKIES_ENABLED': False,
        'DOWNLOAD_TIMEOUT': 5,
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 3600,
        'RETRY_TIMES': 1,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'DOWNLOAD_MAXSIZE': 10 * 1024 * 1024,  # 10MB
    })
    
    # Run crawler
    process = CrawlerProcess(settings)
    process.crawl(
        BreadthFirstWebSpider,
        start_url=start_url,
        max_pages=max_pages,
        concurrent_requests=concurrent_requests,
        download_delay=download_delay
    )
    process.start()

def save_results_to_file():
    """Save crawling results to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"crawl_results_bfs_{timestamp}.json"
    
    results = {
        'crawl_stats': crawl_stats,
        'pages': crawl_results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: {filename}")
    return filename

def display_summary():
    """Display crawling summary"""
    print("\n" + "=" * 60)
    print("📋 CRAWLING SUMMARY")
    print("=" * 60)
    
    if crawl_stats['start_time'] and crawl_stats['end_time']:
        start = datetime.fromisoformat(crawl_stats['start_time'])
        end = datetime.fromisoformat(crawl_stats['end_time'])
        duration = end - start
        print(f"⏱️  Duration: {duration}")
    
    print(f"📄 Pages crawled: {crawl_stats['pages_crawled']}")
    print(f"🔗 Unique URLs: {crawl_stats['total_urls']}")
    print(f"❌ Errors: {crawl_stats['errors']}")
    
    total_content = sum(page.get('content_length', 0) for page in crawl_results)
    print(f"📝 Total content length: {total_content:,} characters")
    
    print(f"\n📋 Sample pages:")
    for i, page in enumerate(crawl_results[:5], 1):
        title = page.get('title', 'No title')[:50] + "..." if len(page.get('title', '')) > 50 else page.get('title', 'No title')
        level = page.get('level', 0)
        print(f"  {i}. {title}")
        print(f"     URL: {page.get('url', 'No URL')}")
        print(f"     Content: {page.get('content_length', 0)} characters")
        print(f"     Level: {level}")
        print(f"     Headings: {len(page.get('headings', []))} found")
        print()

def get_user_input():
    """Get user input for crawling parameters"""
    try:
        print("🕷️  Breadth-First Web Crawler")
        print("=" * 40)
        
        start_url = input("Enter website URL: ").strip()
        if not start_url:
            start_url = "https://www.usm.edu/a-to-z-index.php"
            print(f"Using default: {start_url}")
        
        max_pages = input("Max pages to crawl (default 50): ").strip()
        max_pages = int(max_pages) if max_pages.isdigit() else 50
        
        concurrent_requests = input("Concurrent requests (default 4): ").strip()
        concurrent_requests = int(concurrent_requests) if concurrent_requests.isdigit() else 4
        
        download_delay = input("Download delay in seconds (default 1.0): ").strip()
        download_delay = float(download_delay) if download_delay.replace('.', '').isdigit() else 1.0
        
        return start_url, max_pages, concurrent_requests, download_delay
        
    except (EOFError, KeyboardInterrupt):
        print("\n\n⚠️  Input cancelled. Using default values.")
        return "https://www.usm.edu/a-to-z-index.php", 50, 4, 1.0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        start_url = sys.argv[1]
        max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        concurrent_requests = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        download_delay = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
        
        print(f"Command line mode: {start_url} {max_pages} {concurrent_requests} {download_delay}")
    else:
        # Interactive mode
        try:
            start_url, max_pages, concurrent_requests, download_delay = get_user_input()
        except:
            print("⚠️  Interactive input failed. Using command line mode.")
            print("Usage: python spiderCrawl_bfs.py <URL> [max_pages] [concurrent_requests] [download_delay]")
            print("Example: python spiderCrawl_bfs.py https://www.usm.edu/a-to-z-index.php 100 4 0.5")
            sys.exit(1)
    
    # Run crawler
    crawl_website(start_url, max_pages, concurrent_requests, download_delay)
    
    # Save results and display summary
    save_results_to_file()
    display_summary()
