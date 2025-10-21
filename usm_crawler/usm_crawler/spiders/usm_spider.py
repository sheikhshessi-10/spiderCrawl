import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request
from trafilatura import extract
import json
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime


class UsmSpider(CrawlSpider):
    name = 'usm_spider'
    allowed_domains = ['usm.edu']
    start_urls = [
        'https://www.usm.edu/',
        'https://www.usm.edu/a-to-z-index.php',
        'https://www.usm.edu/academics/',
        'https://www.usm.edu/admissions/',
        'https://www.usm.edu/research/',
        'https://www.usm.edu/student-life/',
        'https://www.usm.edu/about-usm/',
        'https://www.usm.edu/news/',
        'https://www.usm.edu/events/',
        'https://www.usm.edu/faculty/',
        'https://www.usm.edu/staff/',
        'https://www.usm.edu/alumni/',
        'https://www.usm.edu/athletics/',
        'https://www.usm.edu/arts/',
        'https://www.usm.edu/libraries/',
        'https://www.usm.edu/online/',
        'https://www.usm.edu/graduate/',
        'https://www.usm.edu/undergraduate/',
        'https://www.usm.edu/international/',
        'https://www.usm.edu/financial-aid/',
        'https://www.usm.edu/housing/',
        'https://www.usm.edu/dining/',
        'https://www.usm.edu/health/',
        'https://www.usm.edu/career/',
        'https://www.usm.edu/registrar/',
        'https://www.usm.edu/bursar/',
        'https://www.usm.edu/technology/',
        'https://www.usm.edu/security/',
        'https://www.usm.edu/parking/',
        'https://www.usm.edu/transportation/',
    ]
    
    # Rules for following links
    rules = (
        # Follow all links within usm.edu domain
        Rule(LinkExtractor(
            allow_domains=['usm.edu'],
            deny=[
                r'.*\.pdf$', r'.*\.doc$', r'.*\.docx$', r'.*\.xls$', r'.*\.xlsx$',
                r'.*\.ppt$', r'.*\.pptx$', r'.*\.zip$', r'.*\.rar$', r'.*\.tar$',
                r'.*\.gz$', r'.*\.mp4$', r'.*\.avi$', r'.*\.mov$', r'.*\.wmv$',
                r'.*\.mp3$', r'.*\.wav$', r'.*\.jpg$', r'.*\.jpeg$', r'.*\.png$',
                r'.*\.gif$', r'.*\.bmp$', r'.*\.tiff$', r'.*\.svg$',
                r'.*mailto:', r'.*tel:', r'.*javascript:',
                r'.*facebook\.com', r'.*twitter\.com', r'.*instagram\.com',
                r'.*linkedin\.com', r'.*youtube\.com', r'.*vimeo\.com'
            ],
            unique=True
        ), callback='parse_page', follow=True),
    )
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 50,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 20,
        'DOWNLOAD_DELAY': 0.5,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
        'AUTOTHROTTLE_DEBUG': False,
        'ROBOTSTXT_OBEY': True,
        'USER_AGENT': 'USM Research Bot (+https://www.usm.edu)',
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'COOKIES_ENABLED': False,
        'TELNETCONSOLE_ENABLED': False,
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages_crawled = 0
        self.max_pages = int(kwargs.get('max_pages', 10000))
        self.output_file = f"usm_crawl_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.results = []
        
    def start_requests(self):
        """Override start_requests to add custom headers and meta"""
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse_page,
                meta={
                    'dont_cache': True,
                    'dont_redirect': False,
                    'handle_httpstatus_list': [301, 302, 303, 307, 308, 404, 500, 502, 503, 504]
                }
            )
    
    def parse_page(self, response):
        """Parse individual pages and extract content"""
        if self.pages_crawled >= self.max_pages:
            return
            
        self.pages_crawled += 1
        
        # Skip if not a successful response
        if response.status not in [200, 301, 302]:
            self.logger.warning(f"Skipping {response.url} - Status: {response.status}")
            return
        
        # Extract content using trafilatura
        clean_text = None
        try:
            clean_text = extract(response.text)
        except Exception as e:
            self.logger.warning(f"Trafilatura extraction failed for {response.url}: {e}")
        
        # Fallback to basic text extraction if trafilatura fails
        if not clean_text or len(clean_text.strip()) < 50:
            clean_text = self._extract_fallback_text(response)
        
        # Only process pages with substantial content
        if not clean_text or len(clean_text.strip()) < 100:
            self.logger.info(f"Skipping {response.url} - insufficient content")
            return
        
        # Extract metadata
        title = response.css('title::text').get()
        if title:
            title = title.strip()
        
        # Extract headings
        headings = []
        for i in range(1, 7):
            for heading in response.css(f'h{i}::text').getall():
                if heading.strip():
                    headings.append({
                        'level': i,
                        'text': heading.strip()
                    })
        
        # Extract links
        links = []
        for link in response.css('a[href]'):
            href = link.css('::attr(href)').get()
            text = link.css('::text').get()
            if href and text:
                absolute_url = urljoin(response.url, href)
                if 'usm.edu' in absolute_url:
                    links.append({
                        'url': absolute_url,
                        'text': text.strip()
                    })
        
        # Create page data
        page_data = {
            'url': response.url,
            'title': title or 'No title',
            'content': clean_text.strip(),
            'content_length': len(clean_text.strip()),
            'headings': headings,
            'links': links[:50],  # Limit links to avoid huge files
            'status_code': response.status,
            'timestamp': datetime.now().isoformat(),
            'meta': {
                'depth': response.meta.get('depth', 0),
                'referer': response.meta.get('referer', ''),
            }
        }
        
        self.results.append(page_data)
        
        # Log progress
        if self.pages_crawled % 100 == 0:
            self.logger.info(f"Crawled {self.pages_crawled} pages so far...")
        
        # Save results periodically
        if self.pages_crawled % 500 == 0:
            self._save_results()
    
    def _extract_fallback_text(self, response):
        """Fallback text extraction when trafilatura fails"""
        # Remove unwanted elements
        unwanted_selectors = [
            'script', 'style', 'nav', 'footer', 'header', 
            '.navigation', '.nav', '.menu', '.sidebar',
            '.breadcrumb', '.pagination', '.social-media',
            '.cookie-notice', '.popup', '.modal'
        ]
        
        # Create a copy of the response for manipulation
        from scrapy.http import HtmlResponse
        response_copy = response.replace(body=response.text)
        
        # Remove unwanted elements
        for selector in unwanted_selectors:
            for element in response_copy.css(selector):
                element.extract()
        
        # Extract text from main content areas
        main_content = response_copy.css('main, article, .content, .main-content, #content, #main')
        if main_content:
            text_parts = []
            for element in main_content:
                text = element.css('::text').getall()
                text_parts.extend(text)
            return ' '.join(text_parts)
        
        # Fallback to all text
        return ' '.join(response_copy.css('::text').getall())
    
    def _save_results(self):
        """Save current results to file"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'crawl_stats': {
                        'pages_crawled': self.pages_crawled,
                        'total_results': len(self.results),
                        'timestamp': datetime.now().isoformat()
                    },
                    'pages': self.results
                }, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(self.results)} results to {self.output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def closed(self, reason):
        """Called when spider closes"""
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Total pages crawled: {self.pages_crawled}")
        self.logger.info(f"Total results saved: {len(self.results)}")
        
        # Final save
        self._save_results()
        
        # Print summary
        if self.results:
            total_content = sum(len(page['content']) for page in self.results)
            avg_content = total_content / len(self.results)
            self.logger.info(f"Average content length: {avg_content:.0f} characters")
            self.logger.info(f"Total content: {total_content:,} characters")
