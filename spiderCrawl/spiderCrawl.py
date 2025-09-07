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

class LocalWebSpider(scrapy.Spider):
    name = 'local_web_spider'
    
    def __init__(self, start_url, max_pages=100, concurrent_requests=16, 
                 download_delay=0.5, *args, **kwargs):
        super(LocalWebSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.MAX_PAGES = max_pages
        self.pages_crawled = 0
        self.visited_urls = set()
        self.homepage_links = set()
        
        # Breadth-first traversal queues
        self.current_level_urls = []  # URLs to crawl in current level
        self.next_level_urls = []     # URLs to crawl in next level
        self.current_level = 0
        self.is_processing_level = False
        self.level_complete = False
        
        self.custom_settings = {
            'ROBOTSTXT_OBEY': False,
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'LOG_LEVEL': 'INFO',
            'CONCURRENT_REQUESTS': concurrent_requests,
            'CONCURRENT_REQUESTS_PER_DOMAIN': concurrent_requests,
            'DOWNLOAD_DELAY': download_delay,
            'COOKIES_ENABLED': False,
            'DOWNLOAD_TIMEOUT': 5,  # Very short timeout
            'HTTPCACHE_ENABLED': True,
            'HTTPCACHE_EXPIRATION_SECS': 3600,
            'RETRY_TIMES': 1,  # Only retry once
            'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
            'DOWNLOAD_MAXSIZE': 10485760,  # 10MB max page size
        }

    def start_requests(self):
        """Initialize crawling with custom headers"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        for url in self.start_urls:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse_homepage)

    def parse_homepage(self, response):
        """Special parser for homepage to ensure all main sections are captured"""
        logging.info("\nProcessing Homepage...")

        links = response.css('a::attr(href)').getall()
        for link in links:
            if link:
                absolute_url = urljoin(response.url, link)
                if self.allowed_domains[0] in absolute_url and absolute_url not in self.visited_urls:
                    self.homepage_links.add(absolute_url)
                    yield scrapy.Request(
                        url=absolute_url,
                        callback=self.parse,
                        priority=100,
                        errback=self.handle_error
                    )

        logging.info(f"Found {len(self.homepage_links)} main sections on homepage")
        yield from self.parse(response)

    def parse(self, response):
        """Parse pages and follow all links"""
        if self.pages_crawled >= self.MAX_PAGES:
            raise scrapy.exceptions.CloseSpider(reason='Reached maximum pages')

        if response.url in self.visited_urls:
            return

        self.visited_urls.add(response.url)
        self.pages_crawled += 1

        # Update global stats
        crawl_stats['pages_crawled'] = self.pages_crawled
        crawl_stats['total_urls'] = len(self.visited_urls)

        print(f"📄 Crawling page {self.pages_crawled}/{self.MAX_PAGES}: {response.url}")
        
        # Show progress every 10 pages
        if self.pages_crawled % 10 == 0:
            print(f"⏳ Progress: {self.pages_crawled}/{self.MAX_PAGES} pages ({self.pages_crawled/self.MAX_PAGES*100:.1f}%)")
        
        # Debug: Show what content types we found
        if self.pages_crawled <= 3:  # Only for first 3 pages
            tables_found = len(response.css('table').getall())
            columns_found = len(response.css('.columns__item').getall())
            print(f"🔍 Debug - Tables: {tables_found}, Column divs: {columns_found}")

        # Extract comprehensive content for RAG
        content_data = self.extract_comprehensive_content(response)

        # Store results
        page_data = {
            'url': response.url,
            'title': content_data.get('title', ''),
            'content': content_data.get('full_text', ''),
            'content_length': len(content_data.get('full_text', '')),
            'headings': content_data.get('headings', []),
            'links': content_data.get('links', []),
            'timestamp': datetime.now().isoformat()
        }
        crawl_results.append(page_data)

        # Follow links - prioritize content links over navigation
        all_links = response.css('a[href]')
        
        # First, get content links (from main content area)
        content_links = []
        nav_links = []
        
        for link in all_links:
            href = link.css('::attr(href)').get()
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                absolute_url = urljoin(response.url, href)
                if self.allowed_domains[0] in absolute_url and absolute_url not in self.visited_urls:
                    # Check if it's a navigation link by looking at parent elements
                    is_nav_link = False
                    # Check if link is inside nav, header, or navigation elements
                    if (link.xpath('ancestor::nav') or 
                        link.xpath('ancestor::header') or 
                        link.xpath('ancestor::*[contains(@class, "navigation")]') or
                        link.xpath('ancestor::*[contains(@class, "nav")]')):
                        is_nav_link = True
                    
                    if is_nav_link:
                        nav_links.append(absolute_url)
                    else:
                        content_links.append(absolute_url)
        
        # Follow content links first, then navigation links
        for url in content_links + nav_links:
            if self.pages_crawled < self.MAX_PAGES:
                    yield scrapy.Request(
                    url=url,
                        callback=self.parse,
                        errback=self.handle_error
                    )

    def extract_comprehensive_content(self, response):
        """Extract comprehensive content for RAG with safety limits"""
        content_data = {}
        
        try:
            # Extract page title
            title = response.css('title::text').get()
            content_data['title'] = title.strip() if title else ''
            
            # Get main content area with safety limits
            main_content = response.css('body')
            
            # Extract headings (h1-h6) with hierarchy - limit to 50 headings
            headings = []
            for i in range(1, 7):
                heading_texts = main_content.css(f'h{i}::text').getall()[:10]  # Limit per level
                for heading in heading_texts:
                    if heading.strip() and len(headings) < 50:
                        headings.append({
                            'level': i,
                            'text': heading.strip()
                        })
            content_data['headings'] = headings
            
            # Extract text content with limits
            text_elements = []
            
            # Paragraphs - limit to 100 paragraphs
            paragraphs = main_content.css('p::text').getall()[:100]
            text_elements.extend([('p', p.strip()) for p in paragraphs if p.strip()])
            
            # List items - limit to 200 items
            list_items = main_content.css('li::text').getall()[:200]
            text_elements.extend([('li', li.strip()) for li in list_items if li.strip()])
            
            # Extract table content properly
            tables = main_content.css('table')
            for table in tables[:10]:  # Limit to 10 tables
                table_text = self.extract_table_content(table)
                if table_text:
                    text_elements.append(('table', table_text))
            
            # Extract content from specific div classes (like columns__item)
            column_divs = main_content.css('.columns__item, .content, .main-content, .article-content')
            for div in column_divs[:20]:  # Limit to 20 content divs
                div_text = self.extract_div_content(div)
                if div_text:
                    text_elements.append(('content_div', div_text))
            
            # Div content - limit to 50 divs
            divs = main_content.css('div::text').getall()[:50]
            text_elements.extend([('div', div.strip()) for div in divs if div.strip() and len(div.strip()) > 20])
            
            # Combine all text with structure
            full_text_parts = []
            for element_type, text in text_elements:
                if text and len(text) > 5 and len(full_text_parts) < 500:  # Limit total elements
                    full_text_parts.append(text)
            
            # Join all text content with better structure
            full_text = '\n\n'.join(full_text_parts)
            
            # Add proper line breaks for better readability
            full_text = full_text.replace('Table:', '\n\nTable:')
            full_text = full_text.replace('Section:', '\n\nSection:')
            
            # Limit total content length to prevent memory issues
            if len(full_text) > 50000:  # 50KB limit
                full_text = full_text[:50000] + "... [Content truncated]"
            
            # Clean up the text
            full_text = self.clean_text_for_rag(full_text)
            
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
        """Extract structured content from HTML tables in RAG-friendly format"""
        try:
            table_text = []
            
            # Extract headers
            headers = table.css('thead th::text, th::text').getall()
            if headers:
                header_text = " | ".join([h.strip() for h in headers if h.strip()])
                table_text.append(f"Table: {header_text}")
            
            # Extract rows with better formatting
            rows = table.css('tbody tr, tr')
            for row in rows[:50]:  # Limit to 50 rows
                cells = row.css('td::text, th::text').getall()
                if cells:
                    # Create more natural language format
                    if len(cells) == 2:
                        # For 2-column tables, use "X: Y" format
                        row_text = f"{cells[0].strip()}: {cells[1].strip()}"
                    else:
                        # For multi-column tables, use pipe format
                        row_text = " | ".join([cell.strip() for cell in cells if cell.strip()])
                    
                    if row_text:
                        table_text.append(f"  {row_text}")
            
            return "\n".join(table_text) if table_text else ""
            
        except Exception as e:
            print(f"⚠️  Error extracting table: {str(e)}")
            return ""
    
    def extract_div_content(self, div):
        """Extract content from structured divs like columns__item"""
        try:
            content_parts = []
            
            # Extract headings within the div
            headings = div.css('h1::text, h2::text, h3::text, h4::text, h5::text, h6::text').getall()
            for heading in headings:
                if heading.strip():
                    content_parts.append(f"Section: {heading.strip()}")
            
            # Extract paragraphs
            paragraphs = div.css('p::text').getall()
            for p in paragraphs:
                if p.strip():
                    content_parts.append(p.strip())
            
            # Extract tables within the div
            tables = div.css('table')
            for table in tables:
                table_text = self.extract_table_content(table)
                if table_text:
                    content_parts.append(table_text)
            
            # Extract list items
            list_items = div.css('li::text').getall()
            for li in list_items:
                if li.strip():
                    content_parts.append(f"• {li.strip()}")
            
            return "\n".join(content_parts) if content_parts else ""
            
        except Exception as e:
            print(f"⚠️  Error extracting div content: {str(e)}")
            return ""
    
    def clean_text_for_rag(self, text):
        """Clean and format text for RAG"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'Cookie\s*policy',
            r'Privacy\s*policy',
            r'Terms\s*of\s*service',
            r'Subscribe\s*to\s*newsletter',
            r'Follow\s*us\s*on',
            r'Share\s*this',
            r'Read\s*more',
            r'Click\s*here',
            r'Learn\s*more',
        ]
        
        import re
        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove multiple consecutive newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    def structure_content_for_rag(self, content, title):
        """Structure content for better RAG understanding"""
        try:
            # Add document header
            structured = f"Document: {title}\n"
            structured += "=" * 50 + "\n\n"
            
            # Remove duplicates and organize content
            seen_tables = set()
            sections = content.split('\n\n')
            current_section = ""
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                # Handle table content - avoid duplicates
                if section.startswith('Table:'):
                    # Create a hash of the table content to detect duplicates
                    table_hash = hash(section)
                    if table_hash not in seen_tables:
                        seen_tables.add(table_hash)
                        if current_section:
                            structured += current_section + "\n\n"
                        structured += section + "\n"
                        current_section = ""
                    continue
                
                # Handle section headers
                if section.startswith('Section:'):
                    if current_section:
                        structured += current_section + "\n\n"
                    structured += section + "\n"
                    current_section = ""
                    continue
                
                # Regular text content
                if current_section:
                    structured += current_section + "\n\n"
                current_section = section
            
            # Add any remaining section
            if current_section:
                structured += current_section + "\n\n"
            
            return structured.strip()
            
        except Exception as e:
            print(f"⚠️  Error structuring content: {str(e)}")
        return content

    def safe_extract_list(self, selector):
        """Safely extract list of text elements"""
        try:
            return [text.strip() for text in selector.getall() if text.strip()]
        except:
            return []

    def handle_error(self, failure):
        """Handle request errors"""
        print(f"❌ Request failed: {failure.request.url}")
        crawl_stats['errors'] += 1

    def closed(self, reason):
        """Called when spider is closed"""
        crawl_stats['end_time'] = datetime.now().isoformat()
        print(f"\n✅ Crawling completed!")
        print(f"📊 Total pages crawled: {self.pages_crawled}")
        print(f"🔗 Total unique URLs: {len(self.visited_urls)}")
        print(f"❌ Errors: {crawl_stats['errors']}")
        print(f"⏱️  Reason: {reason}")

def crawl_website(url: str, max_pages: int = 100, concurrent_requests: int = 16, download_delay: float = 0.5):
    """Start crawling a website"""
    global crawl_results, crawl_stats
    
    # Reset global variables
    crawl_results = []
    crawl_stats = {
        'pages_crawled': 0,
        'total_urls': 0,
        'errors': 0,
        'start_time': datetime.now().isoformat(),
        'end_time': None
    }
    
    print(f"🕷️  Starting to crawl: {url}")
    print(f"📊 Max pages: {max_pages}")
    print(f"⚡ Concurrent requests: {concurrent_requests}")
    print(f"⏱️  Download delay: {download_delay}s")
    print("-" * 50)
    
    process = CrawlerProcess(get_project_settings())
    process.crawl(
        LocalWebSpider,
        start_url=url,
        max_pages=max_pages,
        concurrent_requests=concurrent_requests,
        download_delay=download_delay
    )
    
    try:
        process.start()
    except Exception as e:
        print(f"❌ Crawling failed: {str(e)}")
        return False
    
    return True

def save_results_to_file(filename: str = None):
    """Save crawling results to a JSON file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawl_results_{timestamp}.json"
    
    results = {
        'crawl_stats': crawl_stats,
        'pages': crawl_results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: {filename}")

def display_summary():
    """Display a summary of crawling results"""
    print("\n" + "="*60)
    print("📋 CRAWLING SUMMARY")
    print("="*60)
    
    if crawl_stats['start_time']:
        start_time = datetime.fromisoformat(crawl_stats['start_time'])
        end_time = datetime.fromisoformat(crawl_stats['end_time']) if crawl_stats['end_time'] else datetime.now()
        duration = end_time - start_time
        print(f"⏱️  Duration: {duration}")
    
    print(f"📄 Pages crawled: {crawl_stats['pages_crawled']}")
    print(f"🔗 Unique URLs: {crawl_stats['total_urls']}")
    print(f"❌ Errors: {crawl_stats['errors']}")
    
    if crawl_results:
        total_content = sum(page.get('content_length', 0) for page in crawl_results)
        print(f"📝 Total content length: {total_content:,} characters")
        
        print(f"\n📋 Sample pages:")
        for i, page in enumerate(crawl_results[:5]):  # Show first 5 pages
            title = page.get('title', 'No title')[:50]
            print(f"  {i+1}. {title}...")
            print(f"     URL: {page['url']}")
            print(f"     Content: {page.get('content_length', 0):,} characters")
            if page.get('headings'):
                print(f"     Headings: {len(page['headings'])} found")
            print()

def get_user_input():
    """Get website URL and settings from user"""
    print("🕷️  Local Web Crawler")
    print("="*30)
    
    try:
        # Get URL
        print("Enter website URL to crawl: ", end='', flush=True)
        url = input().strip()
        if not url:
            print("❌ No URL provided!")
            return None
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Get settings
        try:
            print("Max pages to crawl (default: 100): ", end='', flush=True)
            max_pages_input = input().strip()
            max_pages = int(max_pages_input) if max_pages_input else 100
            
            print("Concurrent requests (default: 16): ", end='', flush=True)
            concurrent_input = input().strip()
            concurrent_requests = int(concurrent_input) if concurrent_input else 16
            
            print("Download delay in seconds (default: 0.5): ", end='', flush=True)
            delay_input = input().strip()
            download_delay = float(delay_input) if delay_input else 0.5
            
        except ValueError:
            print("❌ Invalid input! Using default values.")
            max_pages, concurrent_requests, download_delay = 100, 16, 0.5
    
    return {
            'url': url,
            'max_pages': max_pages,
            'concurrent_requests': concurrent_requests,
            'download_delay': download_delay
        }
        
    except (EOFError, KeyboardInterrupt):
        print("\n❌ Input cancelled!")
        return None

if __name__ == "__main__":
    # Option 1: Interactive mode
    if len(sys.argv) == 1:
        print("🕷️  Local Web Crawler")
        print("="*30)
        print("If you can't enter input, use command line mode instead:")
        print("python spiderCrawl.py <url> [max_pages] [concurrent] [delay]")
        print("Example: python spiderCrawl.py https://example.com 10 4 0.5")
        print()
        
        settings = get_user_input()
        if settings:
            success = crawl_website(**settings)
            if success:
                display_summary()
                # Auto-save results by default
                print("\n💾 Auto-saving results...")
                save_results_to_file()
        else:
            print("❌ No valid input provided. Exiting.")
    
    # Option 2: Command line mode
    elif len(sys.argv) >= 2:
        url = sys.argv[1]
        max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        concurrent_requests = int(sys.argv[3]) if len(sys.argv) > 3 else 16
        download_delay = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        save_results = sys.argv[5].lower() != 'nosave' if len(sys.argv) > 5 else True
        
        success = crawl_website(url, max_pages, concurrent_requests, download_delay)
        if success:
            display_summary()
            if save_results:
                save_results_to_file()
            else:
                print("\n💾 Results not saved (nosave option used)")
    
    else:
        print("Usage:")
        print("  python spiderCrawl.py                    # Interactive mode (auto-saves)")
        print("  python spiderCrawl.py <url> [max_pages] [concurrent] [delay] [nosave]")
        print("  Example: python spiderCrawl.py https://example.com 50 8 1.0")
        print("  Example: python spiderCrawl.py https://example.com 50 8 1.0 nosave")


