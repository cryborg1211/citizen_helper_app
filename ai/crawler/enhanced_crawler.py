#!/usr/bin/env python3
"""
Enhanced Crawler - Discovers and crawls MORE Vietnamese legal content from all sources.

Targets:
- LuatVietnam: Category pages, news, guides, all bieu-mau
- ThuvienPhapLuat: More law categories
- Court cases: anle.toaan.gov.vn with broader search
- Government gazettes: congbao if accessible
"""

import re
import time
import json
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

try:
    import cloudscraper
except ImportError:
    print("pip install cloudscraper")
    exit(1)

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_BASE = PROJECT_ROOT / "raw"


class EnhancedLuatVietnamCrawler:
    """Crawl more content from LuatVietnam by discovering article links."""

    def __init__(self):
        self.output_dir = OUTPUT_BASE / "luatvietnam"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True},
            delay=5
        )

        # Category listing pages to crawl
        self.category_pages = [
            "https://luatvietnam.vn/bieu-mau.html",
            "https://luatvietnam.vn/lao-dong-tien-luong",
            "https://luatvietnam.vn/dat-dai-nha-o",
            "https://luatvietnam.vn/doanh-nghiep",
            "https://luatvietnam.vn/thue-phi-le-phi",
            "https://luatvietnam.vn/hinh-su",
            "https://luatvietnam.vn/dan-su",
            "https://luatvietnam.vn/hon-nhan-gia-dinh",
            "https://luatvietnam.vn/thuong-mai",
            "https://luatvietnam.vn/tin-phap-luat",
            "https://luatvietnam.vn/can-bo-cong-chuc",
            "https://luatvietnam.vn/giao-thong",
            "https://luatvietnam.vn/y-te",
            "https://luatvietnam.vn/giao-duc",
            "https://luatvietnam.vn/bao-hiem",
        ]

        self.stats = {"discovered": 0, "downloaded": 0, "failed": 0}

    def fetch(self, url: str) -> Optional[str]:
        """Fetch with cloudscraper."""
        try:
            resp = self.scraper.get(url, timeout=30)
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                return resp.text
        except Exception as e:
            logger.warning(f"Fetch error {url}: {e}")
        return None

    def discover_articles(self, category_url: str, max_pages: int = 5) -> List[Tuple[str, str]]:
        """Discover article URLs from a category page."""
        articles = []

        for page in range(1, max_pages + 1):
            url = f"{category_url}?page={page}" if page > 1 else category_url
            logger.info(f"Discovering: {url}")

            html = self.fetch(url)
            if not html:
                break

            soup = BeautifulSoup(html, 'html.parser')

            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)

                if '-article.html' in href and text and len(text) > 10:
                    full_url = href if href.startswith('http') else f"https://luatvietnam.vn{href}"
                    slug = re.sub(r'[^\w\-]', '_', text[:50])
                    if full_url not in [a[0] for a in articles]:
                        articles.append((full_url, slug))

            time.sleep(2)

        logger.info(f"Discovered {len(articles)} articles from {category_url}")
        return articles

    def extract_content(self, html: str) -> str:
        """Extract article content."""
        soup = BeautifulSoup(html, 'html.parser')

        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()

        # Content selectors
        selectors = ['div.the-article-body', 'div.article-body', 'div.entry', 'article', 'div.nd-bai-viet']

        for sel in selectors:
            div = soup.select_one(sel)
            if div:
                text = div.get_text(separator='\n', strip=True)
                if len(text) > 500:
                    return text

        # Fallback
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            if len(text) > 1000 and ('Điều' in text or 'quy định' in text.lower()):
                return div.get_text(separator='\n', strip=True)

        return ""

    def download_article(self, url: str, slug: str) -> bool:
        """Download a single article."""
        output_path = self.output_dir / f"{slug}.txt"

        if output_path.exists() and output_path.stat().st_size > 100:
            return True

        html = self.fetch(url)
        if not html:
            self.stats["failed"] += 1
            return False

        content = self.extract_content(html)
        if not content or len(content) < 300:
            self.stats["failed"] += 1
            return False

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Source: {url}\n")
            f.write(f"# Downloaded: {datetime.now().isoformat()}\n")
            f.write("#" + "=" * 60 + "\n\n")
            f.write(content)

        self.stats["downloaded"] += 1
        logger.info(f"Saved: {slug}.txt ({len(content)} chars)")
        return True

    def run(self):
        """Run the enhanced crawler."""
        logger.info("=== Enhanced LuatVietnam Crawler ===")

        all_articles = []

        for category in self.category_pages:
            articles = self.discover_articles(category, max_pages=3)
            all_articles.extend(articles)
            time.sleep(1)

        # Deduplicate
        seen = set()
        unique = []
        for url, slug in all_articles:
            if url not in seen:
                seen.add(url)
                unique.append((url, slug))

        self.stats["discovered"] = len(unique)
        logger.info(f"Total unique articles discovered: {len(unique)}")

        for url, slug in unique:
            self.download_article(url, slug)
            time.sleep(2)

        logger.info(f"LuatVietnam complete. Stats: {self.stats}")


class EnhancedToanCrawler:
    """Crawl more court cases by trying different án lệ IDs."""

    def __init__(self):
        self.output_dir = OUTPUT_BASE / "toaan" / "anle"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )

        # Try a range of document IDs
        self.doc_id_patterns = [
            "TAND%06d" % i for i in range(50000, 60000, 500)  # Sample IDs
        ] + [
            "TAND332626", "TAND332640", "TAND057418", "TAND055215",
            "TAND053214", "TAND054328", "TAND056127", "TAND052876",
        ]

        self.stats = {"checked": 0, "downloaded": 0, "failed": 0}

    def fetch(self, url: str) -> Optional[str]:
        """Fetch with SSL handling."""
        try:
            resp = self.scraper.get(url, timeout=30, verify=False)
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                return resp.text
        except Exception as e:
            pass
        return None

    def extract_anle(self, html: str) -> str:
        """Extract court case content."""
        soup = BeautifulSoup(html, 'html.parser')

        for tag in soup.find_all(['script', 'style']):
            tag.decompose()

        # Look for án lệ content
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            if 'Án lệ' in text and len(text) > 500:
                return div.get_text(separator='\n', strip=True)

        return ""

    def download_anle(self, doc_id: str) -> bool:
        """Try to download an án lệ."""
        self.stats["checked"] += 1

        output_path = self.output_dir / f"{doc_id}.txt"
        if output_path.exists():
            return True

        url = f"https://anle.toaan.gov.vn/webcenter/portal/anle/chitietanle?dDocName={doc_id}"
        html = self.fetch(url)

        if not html:
            return False

        content = self.extract_anle(html)
        if not content or len(content) < 300:
            self.stats["failed"] += 1
            return False

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Document ID: {doc_id}\n")
            f.write(f"# Source: anle.toaan.gov.vn\n")
            f.write("#" + "=" * 60 + "\n\n")
            f.write(content)

        self.stats["downloaded"] += 1
        logger.info(f"Downloaded án lệ: {doc_id}")
        return True

    def run(self):
        """Run the court case crawler."""
        logger.info("=== Enhanced Toaan Án Lệ Crawler ===")

        import urllib3
        urllib3.disable_warnings()

        for doc_id in self.doc_id_patterns:
            self.download_anle(doc_id)
            time.sleep(1)

        logger.info(f"Toaan complete. Stats: {self.stats}")


class EnhancedMOJCrawler:
    """Crawl more MOJ content."""

    def __init__(self):
        self.output_dir = OUTPUT_BASE / "moj"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.scraper = cloudscraper.create_scraper()

        # Try different MOJ portals
        self.base_urls = [
            "https://htpldn.moj.gov.vn",
            "https://moj.gov.vn",
            "https://pbgdpl.moj.gov.vn",  # Legal dissemination
        ]

        self.stats = {"checked": 0, "downloaded": 0}

    def fetch(self, url: str) -> Optional[str]:
        try:
            resp = self.scraper.get(url, timeout=30)
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                return resp.text
        except:
            pass
        return None

    def discover_links(self, base_url: str) -> List[Tuple[str, str]]:
        """Discover legal document links."""
        links = []

        html = self.fetch(base_url)
        if not html:
            return links

        soup = BeautifulSoup(html, 'html.parser')

        keywords = ['mẫu', 'biểu', 'hợp đồng', 'văn bản', 'hướng dẫn', 'quy định']

        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)

            if text and any(kw in text.lower() for kw in keywords):
                full_url = href if href.startswith('http') else f"{base_url}{href}"
                slug = re.sub(r'[^\w\-]', '_', text[:40])
                links.append((full_url, slug))

        return links[:20]  # Limit

    def run(self):
        """Run MOJ crawler."""
        logger.info("=== Enhanced MOJ Crawler ===")

        for base_url in self.base_urls:
            logger.info(f"Checking: {base_url}")
            links = self.discover_links(base_url)
            logger.info(f"Found {len(links)} potential links")

            for url, slug in links:
                self.stats["checked"] += 1
                html = self.fetch(url)
                if html:
                    soup = BeautifulSoup(html, 'html.parser')
                    text = soup.get_text(separator='\n', strip=True)
                    if len(text) > 500:
                        output_path = self.output_dir / f"moj_{slug}.txt"
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(text[:50000])
                        self.stats["downloaded"] += 1
                time.sleep(1)

        logger.info(f"MOJ complete. Stats: {self.stats}")


def main():
    """Run all enhanced crawlers."""
    # LuatVietnam - more articles
    luatvietnam = EnhancedLuatVietnamCrawler()
    luatvietnam.run()

    # Toaan - more court cases
    toaan = EnhancedToanCrawler()
    toaan.run()

    # MOJ - more templates
    moj = EnhancedMOJCrawler()
    moj.run()

    logger.info("=== All enhanced crawlers complete ===")


if __name__ == "__main__":
    main()