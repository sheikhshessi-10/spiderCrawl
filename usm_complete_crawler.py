#!/usr/bin/env python3
"""
Complete USM Website Crawler using Crawl4AI
Extracts every detail from the entire USM website
"""

import asyncio
import json
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.chunking_strategy import RegexChunking
import re


class CompleteUSMCrawler:
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
        
    async def crawl_page(self, crawler, url, depth=0, max_depth=3):
        """Crawl a single page with all details"""
        if url in self.visited_urls or depth > max_depth:
            return
            
        self.visited_urls.add(url)
        print(f"🔍 Crawling: {url} (depth: {depth})")
        
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
                    'links': usm_links[:20],  # Limit to avoid infinite loops
                    'depth': depth,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }
                
                self.results.append(page_data)
                print(f"✅ Extracted {len(result.markdown)} characters from {url}")
                
                # Recursively crawl found links
                for link in usm_links[:10]:  # Limit concurrent crawling
                    await self.crawl_page(crawler, link, depth + 1, max_depth)
                    
        except Exception as e:
            print(f"❌ Error crawling {url}: {e}")
            self.results.append({
                'url': url,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            })
    
    async def crawl_entire_website(self):
        """Crawl the entire USM website"""
        print("🚀 Starting Complete USM Website Crawler")
        print("🎯 Target: Extract every detail from the entire USM website")
        print("=" * 60)
        
        async with AsyncWebCrawler(
            headless=True,
            browser_type="chromium",
            verbose=True
        ) as crawler:
            
            # Crawl all starting URLs
            for url in self.start_urls:
                await self.crawl_page(crawler, url)
            
            # Save results
            self.save_results()
            
            # Print summary
            successful_pages = [r for r in self.results if r.get('success', False)]
            total_content = sum(len(r.get('content', '')) for r in successful_pages)
            
            print("\n" + "=" * 60)
            print("✅ Complete USM Website Crawling Finished!")
            print(f"📄 Pages crawled: {len(self.results):,}")
            print(f"✅ Successful: {len(successful_pages):,}")
            print(f"📝 Total content: {total_content:,} characters")
            print(f"📊 Average content: {total_content/len(successful_pages) if successful_pages else 0:.0f} characters")
            print("=" * 60)
    
    def save_results(self):
        """Save comprehensive results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed JSON
        json_filename = f"usm_complete_crawl_{timestamp}.json"
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
        md_filename = f"usm_rag_content_{timestamp}.md"
        with open(md_filename, 'w', encoding='utf-8') as f:
            for i, page in enumerate(self.results, 1):
                if page.get('success', False) and page.get('content'):
                    f.write(f"# Page {i}: {page.get('title', 'No Title')}\n")
                    f.write(f"**URL:** {page['url']}\n\n")
                    f.write(page['content'])
                    f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"💾 Results saved to:")
        print(f"   📄 JSON: {json_filename}")
        print(f"   📝 Markdown: {md_filename}")


async def main():
    """Main function to run the complete crawler"""
    crawler = CompleteUSMCrawler()
    await crawler.crawl_entire_website()


if __name__ == '__main__':
    asyncio.run(main())
