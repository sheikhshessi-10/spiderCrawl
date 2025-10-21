#!/usr/bin/env python3
"""
RAG-Optimized USM Website Crawler
Specifically designed for maximum content extraction for RAG systems
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
from trafilatura import extract
import concurrent.futures
from collections import deque


class RAGOptimizedCrawler:
    def __init__(self, max_pages=10000, max_workers=50, delay=0.1):
        self.max_pages = max_pages
        self.max_workers = max_workers
        self.delay = delay
        self.visited_urls = set()
        self.results = []
        self.url_queue = deque()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RAG Research Bot (+https://www.usm.edu)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # RAG-optimized starting URLs - focus on content-rich pages
        self.start_urls = [
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
        
        # Content quality filters for RAG
        self.min_content_length = 500  # Minimum 500 characters
        self.min_paragraphs = 3       # Minimum 3 paragraphs
        self.content_keywords = [
            'program', 'degree', 'course', 'curriculum', 'requirement',
            'admission', 'application', 'tuition', 'scholarship', 'financial',
            'research', 'faculty', 'department', 'academic', 'student',
            'campus', 'housing', 'dining', 'library', 'technology'
        ]
    
    def is_content_rich(self, content, title):
        """Check if content is rich enough for RAG"""
        if len(content) < self.min_content_length:
            return False
        
        # Check for content keywords
        content_lower = content.lower()
        keyword_count = sum(1 for keyword in self.content_keywords if keyword in content_lower)
        
        # Check for paragraph structure
        paragraphs = content.split('\n\n')
        if len(paragraphs) < self.min_paragraphs:
            return False
        
        # Check for substantial sentences
        sentences = content.split('.')
        long_sentences = [s for s in sentences if len(s.strip()) > 50]
        
        return keyword_count >= 2 and len(long_sentences) >= 3
    
    def extract_content(self, url, html):
        """Extract content using trafilatura with RAG optimization"""
        try:
            # Use trafilatura for clean extraction
            clean_text = extract(html)
            if clean_text and len(clean_text) > 200:
                return clean_text.strip()
        except:
            pass
        
        # Fallback to BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if main_content:
            return main_content.get_text(separator='\n', strip=True)
        
        # Fallback to body
        return soup.get_text(separator='\n', strip=True)
    
    def get_links(self, url, html):
        """Extract relevant links for further crawling"""
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
                len(text) > 3 and
                absolute_url not in self.visited_urls):
                
                links.append((absolute_url, text))
        
        return links
    
    def crawl_page(self, url):
        """Crawl a single page with RAG optimization"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract content
            content = self.extract_content(url, response.text)
            
            if not content or len(content) < 200:
                return None
            
            # Check if content is rich enough for RAG
            title = BeautifulSoup(response.text, 'html.parser').find('title')
            title_text = title.get_text(strip=True) if title else 'No title'
            
            if not self.is_content_rich(content, title_text):
                return None
            
            # Extract metadata
            soup = BeautifulSoup(response.text, 'html.parser')
            headings = []
            for i in range(1, 7):
                for heading in soup.find_all(f'h{i}'):
                    headings.append({
                        'level': i,
                        'text': heading.get_text(strip=True)
                    })
            
            # Extract links for further crawling
            links = self.get_links(url, response.text)
            
            page_data = {
                'url': url,
                'title': title_text,
                'content': content,
                'content_length': len(content),
                'headings': headings,
                'links': links[:20],  # Limit links to avoid huge files
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'rag_score': self.calculate_rag_score(content, title_text)
            }
            
            return page_data
            
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None
    
    def calculate_rag_score(self, content, title):
        """Calculate RAG relevance score"""
        score = 0
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Content length score
        score += min(len(content) / 1000, 10)  # Max 10 points for length
        
        # Keyword score
        keyword_count = sum(1 for keyword in self.content_keywords if keyword in content_lower)
        score += keyword_count * 2  # 2 points per keyword
        
        # Title relevance
        title_keywords = sum(1 for keyword in self.content_keywords if keyword in title_lower)
        score += title_keywords * 3  # 3 points per title keyword
        
        # Structure score
        paragraphs = content.split('\n\n')
        score += min(len(paragraphs) / 5, 5)  # Max 5 points for structure
        
        return round(score, 2)
    
    def crawl_website(self):
        """Main crawling function with RAG optimization"""
        print("🚀 Starting RAG-Optimized USM Website Crawler")
        print(f"📊 Max pages: {self.max_pages:,}")
        print(f"⚡ Workers: {self.max_workers}")
        print(f"⏱️  Delay: {self.delay}s")
        print(f"🎯 Target: Content-rich pages for RAG")
        print("=" * 60)
        
        # Initialize queue with start URLs
        for url in self.start_urls:
            self.url_queue.append(url)
        
        start_time = datetime.now()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.url_queue and len(self.visited_urls) < self.max_pages:
                # Get batch of URLs to process
                batch_size = min(50, len(self.url_queue))
                batch_urls = [self.url_queue.popleft() for _ in range(batch_size)]
                
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
                        result = future.result()
                        if result:
                            self.results.append(result)
                            
                            # Add new links to queue
                            for link_url, link_text in result.get('links', []):
                                if link_url not in self.visited_urls:
                                    self.url_queue.append(link_url)
                            
                            # Progress update
                            if len(self.results) % 10 == 0:
                                elapsed = (datetime.now() - start_time).total_seconds()
                                print(f"📄 Crawled: {len(self.results):,} pages | "
                                      f"Queue: {len(self.url_queue):,} | "
                                      f"Time: {elapsed:.1f}s")
                        
                    except Exception as e:
                        print(f"Error processing {url}: {e}")
                    
                    # Respect delay
                    time.sleep(self.delay)
        
        # Save results
        self.save_results()
        
        # Print summary
        elapsed = (datetime.now() - start_time).total_seconds()
        total_content = sum(len(page['content']) for page in self.results)
        avg_content = total_content / len(self.results) if self.results else 0
        
        print("\n" + "=" * 60)
        print("✅ RAG-Optimized Crawling Completed!")
        print(f"📄 Pages crawled: {len(self.results):,}")
        print(f"📝 Total content: {total_content:,} characters")
        print(f"📊 Average content: {avg_content:.0f} characters")
        print(f"⏱️  Time elapsed: {elapsed:.1f} seconds")
        print(f"🎯 RAG Score: {sum(page['rag_score'] for page in self.results):.1f}")
        print("=" * 60)
    
    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"rag_optimized_crawl_{timestamp}.json"
        
        # Sort by RAG score
        sorted_results = sorted(self.results, key=lambda x: x['rag_score'], reverse=True)
        
        data = {
            'crawl_stats': {
                'pages_crawled': len(self.results),
                'total_content': sum(len(page['content']) for page in self.results),
                'average_content': sum(len(page['content']) for page in self.results) / len(self.results) if self.results else 0,
                'max_rag_score': max(page['rag_score'] for page in self.results) if self.results else 0,
                'avg_rag_score': sum(page['rag_score'] for page in self.results) / len(self.results) if self.results else 0,
                'timestamp': datetime.now().isoformat()
            },
            'pages': sorted_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filename}")


if __name__ == '__main__':
    # RAG-optimized settings
    crawler = RAGOptimizedCrawler(
        max_pages=5000,      # Focus on quality over quantity
        max_workers=30,      # Moderate concurrency
        delay=0.2           # Respectful delay
    )
    
    crawler.crawl_website()
