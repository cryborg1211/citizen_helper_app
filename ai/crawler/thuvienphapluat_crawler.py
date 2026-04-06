#!/usr/bin/env python3
"""
ThuvienPhapLuat Crawler - Crawls legal documents from thuvienphapluat.vn

This is one of the largest Vietnamese legal databases with 100,000+ documents.
Uses cloudscraper to bypass Cloudflare protection.

Categories:
- Bo-luat (Codes): Civil Code, Labor Code, Criminal Code, etc.
- Luat (Laws): Various laws by topic
- Nghi-dinh (Decrees)
- Thong-tu (Circulars)
"""

import re
import time
import json
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import cloudscraper
except ImportError:
    print("Please install cloudscraper: pip install cloudscraper")
    exit(1)

from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://thuvienphapluat.vn"
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "raw" / "thuvienphapluat"
METADATA_DIR = PROJECT_ROOT / "metadata"
CHECKPOINT_FILE = METADATA_DIR / "tvpl_checkpoint.json"

# Known important legal document URLs (verified Dec 2025)
SEED_DOCUMENTS = [
    # Major Codes (Bộ luật)
    ("Bo-luat-dan-su-2015-296215", "Bộ luật Dân sự 2015"),
    ("Bo-luat-lao-dong-2019-430702", "Bộ luật Lao động 2019"),
    ("Bo-luat-hinh-su-2015-296211", "Bộ luật Hình sự 2015"),
    ("Bo-luat-to-tung-dan-su-2015-296213", "Bộ luật Tố tụng dân sự 2015"),
    ("Bo-luat-to-tung-hinh-su-2015-296220", "Bộ luật Tố tụng hình sự 2015"),

    # Important Laws (Luật)
    ("Luat-Dat-dai-2024-597866", "Luật Đất đai 2024"),
    ("Luat-Nha-o-2023-586367", "Luật Nhà ở 2023"),
    ("Luat-Doanh-nghiep-2020-450977", "Luật Doanh nghiệp 2020"),
    ("Luat-Dau-tu-2020-450976", "Luật Đầu tư 2020"),
    ("Luat-Thuong-mai-2005-8550", "Luật Thương mại 2005"),
    ("Luat-Hon-nhan-va-gia-dinh-2014-238640", "Luật Hôn nhân và gia đình 2014"),
    ("Luat-Bao-hiem-xa-hoi-2024-599988", "Luật Bảo hiểm xã hội 2024"),
    ("Luat-Thue-thu-nhap-ca-nhan-2007-19734", "Luật Thuế TNCN"),
    ("Luat-Thue-gia-tri-gia-tang-2008-74067", "Luật Thuế GTGT"),
    ("Luat-Bao-ve-quyen-loi-nguoi-tieu-dung-2023-586332", "Luật Bảo vệ quyền lợi người tiêu dùng 2023"),

    # Key Decrees (Nghị định) - 2024-2025
    ("Nghi-dinh-145-2020-ND-CP-huong-dan-Bo-luat-Lao-dong-ve-dieu-kien-lao-dong-quan-he-lao-dong-456564", "NĐ 145/2020 hướng dẫn BLLĐ"),
    ("Nghi-dinh-35-2021-ND-CP-huong-dan-Luat-Dau-tu-479714", "NĐ 35/2021 hướng dẫn Luật Đầu tư"),
    ("Nghi-dinh-01-2021-ND-CP-dang-ky-doanh-nghiep-461774", "NĐ 01/2021 đăng ký doanh nghiệp"),

    # Circulars (Thông tư)
    ("Thong-tu-200-2014-TT-BTC-huong-dan-che-do-ke-toan-doanh-nghiep-262336", "TT 200/2014 chế độ kế toán DN"),
]

# Category listing pages for discovery
CATEGORY_PAGES = [
    "/van-ban/Bo-luat",
    "/van-ban/Luat",
    "/van-ban/Nghi-dinh",
    "/van-ban/Thong-tu",
    "/van-ban/Lao-dong-Tien-luong",
    "/van-ban/Doanh-nghiep",
    "/van-ban/Dat-dai-Nha-o",
    "/van-ban/Thue-Phi-Le-Phi",
    "/van-ban/Thuong-mai",
    "/van-ban/Hinh-su",
    "/van-ban/Quyen-dan-su",
]


class ThuvienPhapLuatCrawler:
    """Crawler for thuvienphapluat.vn using cloudscraper."""

    def __init__(self, workers: int = 3):
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        METADATA_DIR.mkdir(parents=True, exist_ok=True)

        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True,
            },
            delay=5,
        )
        self.scraper.headers.update({
            "Accept-Language": "vi-VN,vi;q=0.9",
        })

        self.workers = workers
        self.checkpoint = self._load_checkpoint()
        self.stats = {"checked": 0, "downloaded": 0, "skipped": 0, "failed": 0}

    def _load_checkpoint(self) -> dict:
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"downloaded_ids": [], "discovered_urls": []}

    def _save_checkpoint(self):
        self.checkpoint["last_updated"] = datetime.now().isoformat()
        self.checkpoint["stats"] = self.stats
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(self.checkpoint, f, ensure_ascii=False, indent=2)

    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch a page with cloudscraper."""
        for attempt in range(max_retries):
            try:
                response = self.scraper.get(url, timeout=30)
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    return response.text
                elif response.status_code == 403:
                    logger.warning(f"Cloudflare blocked: {url}")
                    time.sleep(5)
                else:
                    logger.warning(f"Status {response.status_code}: {url}")
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                time.sleep(2 ** attempt)
        return None

    def extract_content(self, html: str) -> Tuple[str, str]:
        """Extract title and content from document page."""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted elements
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()

        # Extract title
        title = ""
        title_selectors = [
            {'class': 'title-vb'},
            {'class': 'ten-van-ban'},
            {'tag': 'h1'},
        ]
        for sel in title_selectors:
            if 'tag' in sel:
                elem = soup.find(sel['tag'])
            else:
                elem = soup.find('div', sel) or soup.find('span', sel)
            if elem:
                title = elem.get_text(strip=True)
                break

        # Extract main content
        content_selectors = [
            {'class': 'content1'},
            {'class': 'noi-dung-van-ban'},
            {'class': 'toanvancontent'},
            {'class': 'fulltext'},
            {'id': 'toanvancontent'},
            {'class': 'noidung'},
        ]

        content = ""
        for sel in content_selectors:
            div = soup.find('div', sel)
            if div:
                text = div.get_text(separator='\n', strip=True)
                if len(text) > 500:
                    content = text
                    break

        # Fallback: look for legal indicators
        if not content or len(content) < 500:
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                indicators = ['Điều 1', 'ĐIỀU 1', 'Căn cứ', 'QUỐC HỘI', 'THỦ TƯỚNG']
                if any(ind in text for ind in indicators) and len(text) > 1000:
                    content = div.get_text(separator='\n', strip=True)
                    break

        return title, content

    def download_document(self, doc_id: str, title: str) -> bool:
        """Download a single document."""
        self.stats["checked"] += 1

        # Check if already downloaded
        safe_id = re.sub(r'[^\w\-]', '_', doc_id)[:100]
        output_path = self.output_dir / f"{safe_id}.txt"

        if output_path.exists() and output_path.stat().st_size > 100:
            self.stats["skipped"] += 1
            return True

        if doc_id in self.checkpoint.get("downloaded_ids", []):
            self.stats["skipped"] += 1
            return True

        # Build URL
        url = f"{BASE_URL}/van-ban/{doc_id}.aspx"

        logger.info(f"Downloading: {title[:50]}...")
        html = self.fetch_page(url)

        if not html:
            self.stats["failed"] += 1
            return False

        extracted_title, content = self.extract_content(html)

        if not content or len(content) < 200:
            # Try alternative URL format
            url = f"{BASE_URL}/van-ban/EN/{doc_id}.aspx"
            html = self.fetch_page(url)
            if html:
                extracted_title, content = self.extract_content(html)

        if not content or len(content) < 200:
            logger.warning(f"Insufficient content for {doc_id}")
            self.stats["failed"] += 1
            return False

        # Filter out "attached file only" documents
        if 'Văn bản này hiện chưa có nội dung' in content or 'file kèm theo' in content.lower():
            if len(content) < 1000:
                self.stats["failed"] += 1
                return False

        # Save
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Title: {extracted_title or title}\n")
            f.write(f"# Source: thuvienphapluat.vn\n")
            f.write(f"# ID: {doc_id}\n")
            f.write(f"# Downloaded: {datetime.now().isoformat()}\n")
            f.write("#" + "=" * 60 + "\n\n")
            f.write(content)

        self.checkpoint["downloaded_ids"].append(doc_id)
        self.stats["downloaded"] += 1
        logger.info(f"Saved: {safe_id}.txt ({len(content)} chars)")
        return True

    def discover_documents(self, category_url: str, max_pages: int = 5) -> List[Tuple[str, str]]:
        """Discover document URLs from a category listing page."""
        discovered = []

        for page in range(1, max_pages + 1):
            url = f"{BASE_URL}{category_url}?page={page}"
            logger.info(f"Discovering from: {url}")

            html = self.fetch_page(url)
            if not html:
                break

            soup = BeautifulSoup(html, 'html.parser')

            # Find document links
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)

                # Match document URL pattern
                match = re.search(r'/van-ban/([^/]+\.aspx)', href)
                if match and text and len(text) > 10:
                    doc_id = match.group(1).replace('.aspx', '')
                    if doc_id not in [d[0] for d in discovered]:
                        discovered.append((doc_id, text[:100]))

            time.sleep(2)

        logger.info(f"Discovered {len(discovered)} documents from {category_url}")
        return discovered

    def crawl_seed_documents(self):
        """Crawl the seed documents."""
        logger.info(f"Crawling {len(SEED_DOCUMENTS)} seed documents...")

        for doc_id, title in SEED_DOCUMENTS:
            self.download_document(doc_id, title)
            time.sleep(3)  # Polite delay

        self._save_checkpoint()
        logger.info(f"Seed docs complete. Stats: {self.stats}")

    def crawl_categories(self, max_pages_per_category: int = 3):
        """Discover and crawl documents from category pages."""
        all_docs = []

        for category in CATEGORY_PAGES:
            docs = self.discover_documents(category, max_pages_per_category)
            all_docs.extend(docs)
            time.sleep(2)

        # Remove duplicates
        seen = set()
        unique_docs = []
        for doc_id, title in all_docs:
            if doc_id not in seen:
                seen.add(doc_id)
                unique_docs.append((doc_id, title))

        logger.info(f"Total unique documents discovered: {len(unique_docs)}")

        # Download discovered documents
        for doc_id, title in unique_docs:
            self.download_document(doc_id, title)
            time.sleep(3)

        self._save_checkpoint()
        logger.info(f"Category crawl complete. Stats: {self.stats}")

    def run(self):
        """Run the full crawl."""
        logger.info("Starting ThuvienPhapLuat crawler")

        # First crawl seed documents
        self.crawl_seed_documents()

        # Then discover and crawl from categories
        self.crawl_categories()

        self._save_checkpoint()
        logger.info(f"Crawl complete! Total stats: {self.stats}")


def main():
    crawler = ThuvienPhapLuatCrawler(workers=3)
    crawler.run()


if __name__ == "__main__":
    main()
