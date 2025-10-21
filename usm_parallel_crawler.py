#!/usr/bin/env python3
"""
Parallel USM Website Crawler using Crawl4AI
Follows ALL links found on each page in parallel
"""

import asyncio
import json
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.chunking_strategy import RegexChunking
import re


class ParallelUSMCrawler:
    def __init__(self):
        self.results = []
        self.visited_urls = set()
        self.start_urls = [
            'https://www.usm.edu/',
            'https://www.usm.edu/a-to-z-index.php',  # Comprehensive directory
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
        self.max_concurrent = 50  # Process up to 50 pages simultaneously
        
    async def crawl_page(self, crawler, url, depth=0, max_depth=3):
        """Crawl a single page with all details"""
        if url in self.visited_urls or depth > max_depth:
            return []
            
        self.visited_urls.add(url)
        print(f"Crawling: {url} (depth: {depth})")
        
        try:
            # Configure extraction strategy for comprehensive content
            extraction_strategy = LLMExtractionStrategy(
                provider="ollama/llama3.2",  # Use local LLM
                api_token="",  # No API key needed for local
                instruction="Extract all meaningful content including: academic programs, courses, requirements, faculty information, research details, student services, news articles, and any other relevant information. Focus on substantive content, not navigation or boilerplate."
            )
            
            # Run the crawler
            result = await crawler.arun(
                url=url,
                extraction_strategy=extraction_strategy,
                chunking_strategy=RegexChunking(patterns=[r'\n\n', r'\. ']),
                word_count_threshold=50,  # Only extract pages with substantial content
                bypass_cache=True,
                wait_for="networkidle",
                delay_before_return_html=2.0,  # Wait for dynamic content
                js_code=[
                    "window.scrollTo(0, document.body.scrollHeight);",  # Scroll to load content
                    "await new Promise(resolve => setTimeout(resolve, 2000));"  # Wait for content
                ]
            )
            
            if result.success and result.markdown:
                # Extract all links for further crawling
                links = result.links
                usm_links = [link for link in links if 'usm.edu' in link and link not in self.visited_urls]
                
                # Store comprehensive results
                page_data = {
                    'url': url,
                    'title': result.metadata.get('title', ''),
                    'content': result.markdown,
                    'content_length': len(result.markdown),
                    'extracted_content': result.extracted_content,
                    'links_found': len(usm_links),
                    'depth': depth,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }
                
                self.results.append(page_data)
                print(f"Extracted {len(result.markdown)} characters from {url} (found {len(usm_links)} new links)")
                
                # Return links for parallel processing
                return usm_links
                    
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            self.results.append({
                'url': url,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            })
        
        return []
    
    async def crawl_level_parallel(self, crawler, urls, depth, max_depth):
        """Crawl a level of URLs in parallel"""
        if not urls or depth > max_depth:
            return []
        
        print(f"\nLevel {depth}: Processing {len(urls)} URLs in parallel...")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def crawl_with_semaphore(url):
            async with semaphore:
                return await self.crawl_page(crawler, url, depth, max_depth)
        
        # Process all URLs in parallel
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all new links found
        all_new_links = []
        for result in results:
            if isinstance(result, list):
                all_new_links.extend(result)
        
        # Remove duplicates while preserving order
        unique_links = list(dict.fromkeys(all_new_links))
        
        print(f"Level {depth} complete: Found {len(unique_links)} unique new links")
        return unique_links
    
    async def crawl_entire_website(self):
        """Crawl the entire USM website with parallel processing"""
        print("Starting Parallel USM Website Crawler")
        print("Target: Extract every detail from the entire USM website")
        print("Processing: ALL links in parallel at each level")
        print("=" * 60)
        
        async with AsyncWebCrawler(
            headless=True,
            browser_type="chromium",
            verbose=True
        ) as crawler:
            
            # Start with initial URLs
            current_level_urls = self.start_urls.copy()
            depth = 0
            max_depth = 3
            
            while current_level_urls and depth <= max_depth:
                print(f"\n{'='*20} LEVEL {depth} {'='*20}")
                print(f"📄 Processing {len(current_level_urls)} URLs...")
                
                # Process current level in parallel
                new_links = await self.crawl_level_parallel(
                    crawler, current_level_urls, depth, max_depth
                )
                
                # Move to next level
                current_level_urls = new_links
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
            print("Parallel USM Website Crawling Finished!")
            print(f"Pages crawled: {len(self.results):,}")
            print(f"Successful: {len(successful_pages):,}")
            print(f"Total content: {total_content:,} characters")
            print(f"Average content: {total_content/len(successful_pages) if successful_pages else 0:.0f} characters")
            print("=" * 60)
    
    def save_results(self):
        """Save comprehensive results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed JSON
        json_filename = f"usm_parallel_crawl_{timestamp}.json"
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
        
        # Save clean markdown for RAG
        md_filename = f"usm_parallel_rag_{timestamp}.md"
        with open(md_filename, 'w', encoding='utf-8') as f:
            for i, page in enumerate(self.results, 1):
                if page.get('success', False) and page.get('content'):
                    f.write(f"# Page {i}: {page.get('title', 'No Title')}\n")
                    f.write(f"**URL:** {page['url']}\n")
                    f.write(f"**Depth:** {page.get('depth', 0)}\n")
                    f.write(f"**Links Found:** {page.get('links_found', 0)}\n\n")
                    f.write(page['content'])
                    f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Results saved to:")
        print(f"   JSON: {json_filename}")
        print(f"   Markdown: {md_filename}")


async def main():
    """Main function to run the parallel crawler"""
    crawler = ParallelUSMCrawler()
    await crawler.crawl_entire_website()


if __name__ == '__main__':
    asyncio.run(main())
