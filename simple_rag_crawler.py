#!/usr/bin/env python3
"""
Simple RAG-Optimized Crawler
Just extracts clean text content - no JSON overhead, no links, no metadata
Perfect for RAG systems
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
from trafilatura import extract
import concurrent.futures
from collections import deque


class SimpleRAGCrawler:
    def __init__(self, max_pages=2000, max_workers=20, delay=0.2):
        self.max_pages = max_pages
        self.max_workers = max_workers
        self.delay = delay
        self.visited_urls = set()
        self.content_pages = []  # Just store clean text content
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RAG Research Bot (+https://www.usm.edu)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        # Start with content-rich pages
        self.start_urls = [
            'https://www.usm.edu/academics/',
            'https://www.usm.edu/admissions/',
            'https://www.usm.edu/research/',
            'https://www.usm.edu/student-life/',
            'https://www.usm.edu/about-usm/',
            'https://www.usm.edu/news/',
            'https://www.usm.edu/graduate/',
            'https://www.usm.edu/undergraduate/',
            'https://www.usm.edu/financial-aid/',
            'https://www.usm.edu/housing/',
        ]
        
        # Content quality filters
        self.min_content_length = 800  # Minimum 800 characters
        self.content_keywords = [
            'program', 'degree', 'course', 'curriculum', 'requirement',
            'admission', 'application', 'tuition', 'scholarship', 'financial',
            'research', 'faculty', 'department', 'academic', 'student',
            'campus', 'housing', 'dining', 'library', 'technology'
        ]
    
    def is_meaningful_content(self, content, title):
        """Check if content is meaningful for RAG"""
        if len(content) < self.min_content_length:
            return False
        
        # Check for content keywords
        content_lower = content.lower()
        keyword_count = sum(1 for keyword in self.content_keywords if keyword in content_lower)
        
        # Check for substantial sentences
        sentences = content.split('.')
        long_sentences = [s for s in sentences if len(s.strip()) > 30]
        
        # Must have keywords and substantial sentences
        return keyword_count >= 3 and len(long_sentences) >= 5
    
    def extract_clean_content(self, url, html):
        """Extract just clean text content"""
        try:
            # Use trafilatura for clean extraction
            clean_text = extract(html)
            if clean_text and len(clean_text) > 200:
                return clean_text.strip()
        except:
            pass
        
        # Fallback to BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove all unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'menu', 'sidebar']):
            element.decompose()
        
        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if main_content:
            return main_content.get_text(separator='\n', strip=True)
        
        # Fallback to body
        return soup.get_text(separator='\n', strip=True)
    
    def get_content_links(self, url, html):
        """Get only content-rich links"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            
            # Filter for USM domain and content-rich pages
            if ('usm.edu' in absolute_url and 
                not any(ext in absolute_url.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz', '.mp4', '.avi', '.mov', '.wmv', '.mp3', '.wav', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg']) and
                not any(social in absolute_url for social in ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com', 'vimeo.com']) and
                len(text) > 5 and
                absolute_url not in self.visited_urls and
                # Only follow links that look like content pages
                any(keyword in text.lower() for keyword in ['program', 'course', 'degree', 'admission', 'academic', 'student', 'faculty', 'research', 'news', 'event'])):
                
                links.append(absolute_url)
        
        return links
    
    def crawl_page(self, url):
        """Crawl a single page and extract just content"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract clean content
            content = self.extract_clean_content(url, response.text)
            
            if not content or len(content) < 200:
                return None, []
            
            # Check if content is meaningful
            title = BeautifulSoup(response.text, 'html.parser').find('title')
            title_text = title.get_text(strip=True) if title else 'No title'
            
            if not self.is_meaningful_content(content, title_text):
                return None, []
            
            # Get content links for further crawling
            links = self.get_content_links(url, response.text)
            
            # Return just the content and links
            return content, links
            
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None, []
    
    def crawl_website(self):
        """Main crawling function - just extract content"""
        print("🚀 Simple RAG-Optimized USM Crawler")
        print(f"📊 Max pages: {self.max_pages:,}")
        print(f"⚡ Workers: {self.max_workers}")
        print(f"⏱️  Delay: {self.delay}s")
        print(f"🎯 Target: Just clean text content for RAG")
        print("=" * 60)
        
        # Initialize queue with start URLs
        url_queue = deque(self.start_urls)
        
        start_time = datetime.now()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while url_queue and len(self.visited_urls) < self.max_pages:
                # Get batch of URLs to process
                batch_size = min(20, len(url_queue))
                batch_urls = [url_queue.popleft() for _ in range(batch_size)]
                
                # Filter out already visited URLs
                new_urls = [url for url in batch_urls if url not in self.visited_urls]
                
                if not new_urls:
                    continue
                
                # Process batch concurrently
                future_to_url = {
                    executor.submit(self.crawl_page, url): url 
                    for url in new_urls
                }
                
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    self.visited_urls.add(url)
                    
                    try:
                        content, links = future.result()
                        if content:
                            self.content_pages.append(content)
                            
                            # Add new links to queue
                            for link_url in links:
                                if link_url not in self.visited_urls:
                                    url_queue.append(link_url)
                            
                            # Progress update
                            if len(self.content_pages) % 20 == 0:
                                elapsed = (datetime.now() - start_time).total_seconds()
                                print(f"📄 Content pages: {len(self.content_pages):,} | "
                                      f"Queue: {len(url_queue):,} | "
                                      f"Time: {elapsed:.1f}s")
                        
                    except Exception as e:
                        print(f"Error processing {url}: {e}")
                    
                    # Respect delay
                    time.sleep(self.delay)
        
        # Save results
        self.save_results()
        
        # Print summary
        elapsed = (datetime.now() - start_time).total_seconds()
        total_content = sum(len(page) for page in self.content_pages)
        avg_content = total_content / len(self.content_pages) if self.content_pages else 0
        
        print("\n" + "=" * 60)
        print("✅ RAG-Optimized Crawling Completed!")
        print(f"📄 Content pages: {len(self.content_pages):,}")
        print(f"📝 Total content: {total_content:,} characters")
        print(f"📊 Average content: {avg_content:.0f} characters")
        print(f"⏱️  Time elapsed: {elapsed:.1f} seconds")
        print("=" * 60)
    
    def save_results(self):
        """Save results as simple text file for RAG"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"usm_rag_content_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            for i, content in enumerate(self.content_pages, 1):
                f.write(f"=== PAGE {i} ===\n")
                f.write(content)
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"💾 RAG content saved to: {filename}")


if __name__ == '__main__':
    # Simple RAG-optimized settings
    crawler = SimpleRAGCrawler(
        max_pages=1000,      # Focus on quality
        max_workers=15,       # Moderate concurrency
        delay=0.3            # Respectful delay
    )
    
    crawler.crawl_website()
