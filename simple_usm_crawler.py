#!/usr/bin/env python3
"""
Simple USM Website Crawler - No Unicode Issues
"""

import asyncio
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import time
import re

class SimpleUSMCrawler:
    def __init__(self):
        self.results = []
        self.visited_urls = set()
        self.start_urls = [
            'https://www.usm.edu/',
            'https://www.usm.edu/a-to-z-index.php',
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
            'https://www.usm.edu/athletics/',
            'https://www.usm.edu/arts/',
            'https://www.usm.edu/libraries/',
            'https://www.usm.edu/faculty/',
            'https://www.usm.edu/staff/',
            'https://www.usm.edu/alumni/',
        ]
        
    def extract_content(self, html, url):
        """Extract clean content from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No Title"
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') and 'usm.edu' in href:
                    links.append(href)
                elif href.startswith('/'):
                    links.append('https://www.usm.edu' + href)
            
            return {
                'title': title_text,
                'content': text,
                'links': list(set(links))  # Remove duplicates
            }
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None
    
    def crawl_page(self, url, depth=0, max_depth=2):
        """Crawl a single page"""
        if url in self.visited_urls or depth > max_depth:
            return []
            
        self.visited_urls.add(url)
        print(f"Crawling: {url} (depth: {depth})")
        
        try:
            # Add headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Extract content
            extracted = self.extract_content(response.text, url)
            
            if extracted and len(extracted['content']) > 100:  # Only save substantial content
                page_data = {
                    'url': url,
                    'title': extracted['title'],
                    'content': extracted['content'],
                    'content_length': len(extracted['content']),
                    'links_found': len(extracted['links']),
                    'depth': depth,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }
                
                self.results.append(page_data)
                print(f"Extracted {len(extracted['content'])} characters from {url}")
                
                # Return new links for further crawling
                new_links = [link for link in extracted['links'] if link not in self.visited_urls]
                return new_links[:20]  # Limit to 20 links per page
            else:
                print(f"Skipped {url} - insufficient content")
                return []
                
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            self.results.append({
                'url': url,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            })
            return []
    
    def crawl_website(self):
        """Crawl the entire USM website"""
        print("Starting Simple USM Website Crawler")
        print("Target: Extract content from USM website")
        print("=" * 60)
        
        # Start with initial URLs
        current_level_urls = self.start_urls.copy()
        depth = 0
        max_depth = 2
        
        while current_level_urls and depth <= max_depth:
            print(f"\nLevel {depth}: Processing {len(current_level_urls)} URLs...")
            
            new_links = []
            for url in current_level_urls:
                found_links = self.crawl_page(url, depth, max_depth)
                new_links.extend(found_links)
                
                # Small delay to be respectful
                time.sleep(0.5)
            
            # Move to next level
            current_level_urls = list(set(new_links))  # Remove duplicates
            depth += 1
            
            # Progress update
            successful_pages = [r for r in self.results if r.get('success', False)]
            total_content = sum(len(r.get('content', '')) for r in successful_pages)
            print(f"Progress: {len(self.results)} pages, {len(successful_pages)} successful, {total_content:,} characters")
        
        # Save results
        self.save_results()
        
        # Print final summary
        successful_pages = [r for r in self.results if r.get('success', False)]
        total_content = sum(len(r.get('content', '')) for r in successful_pages)
        
        print("\n" + "=" * 60)
        print("Simple USM Website Crawling Finished!")
        print(f"Pages crawled: {len(self.results):,}")
        print(f"Successful: {len(successful_pages):,}")
        print(f"Total content: {total_content:,} characters")
        print(f"Average content: {total_content/len(successful_pages) if successful_pages else 0:.0f} characters")
        print("=" * 60)
    
    def save_results(self):
        """Save results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed JSON
        json_filename = f"usm_simple_crawl_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'crawl_stats': {
                    'total_pages': len(self.results),
                    'successful_pages': len([r for r in self.results if r.get('success', False)]),
                    'total_content': sum(len(r.get('content', '')) for r in self.results),
                    'timestamp': datetime.now().isoformat()
                },
                'pages': self.results
            }, f, indent=2, ensure_ascii=False)
        
        # Save clean text for RAG
        txt_filename = f"usm_simple_rag_{timestamp}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            for i, page in enumerate(self.results, 1):
                if page.get('success', False) and page.get('content'):
                    f.write(f"=== PAGE {i}: {page.get('title', 'No Title')} ===\n")
                    f.write(f"URL: {page['url']}\n")
                    f.write(f"Depth: {page.get('depth', 0)}\n")
                    f.write(f"Links Found: {page.get('links_found', 0)}\n\n")
                    f.write(page['content'])
                    f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Results saved to:")
        print(f"   JSON: {json_filename}")
        print(f"   Text: {txt_filename}")

def main():
    """Main function to run the simple crawler"""
    print("Initializing Simple USM Crawler...")
    crawler = SimpleUSMCrawler()
    crawler.crawl_website()

if __name__ == '__main__':
    main()

