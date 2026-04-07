import requests
from bs4 import BeautifulSoup
import json
import time
import random
import logging
import urllib3
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

# 1. Disable SSL warnings for a cleaner terminal output
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CongBaoHybridCrawler:
    BASE_URL = "https://congbao.chinhphu.vn"
    LIST_PATH = "/van-ban-dang-cong-bao/trang-{}.htm"

    def __init__(self, workers=3):
        # Define and create the output directory
        self.output_dir = Path("ai_engine/raw/congbao_files")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.workers = workers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
        # Important: Disable SSL verification for the entire session
        self.session.verify = False
        
        # Scan the existing folder for deduplication to prevent re-downloading
        self.downloaded_ids = {f.stem for f in self.output_dir.glob("*.json")}
        logger.info(f"💾 Found {len(self.downloaded_ids)} existing files. Only new files will be downloaded.")

    def download_file(self, url, title, vanban_id, referer, ext):
        """Download the actual file using the Referer header to bypass CDN restrictions."""
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_')).strip()
        file_path = self.output_dir / f"{safe_title[:80]}{ext}"
        
        # Smart Skip: If the physical file (docx/pdf) already exists, bypass the download
        if file_path.exists():
            return True

        headers = self.session.headers.copy()
        headers['Referer'] = referer # Use the detail page link as the Referer
        
        try:
            r = self.session.get(url, stream=True, timeout=60, headers=headers)
            if r.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                logger.warning(f"❌ ID {vanban_id} encountered HTTP error {r.status_code} while downloading {ext}")
        except Exception as e:
            logger.error(f"💥 Error downloading file {vanban_id}: {e}")
        return False

    def process_link(self, detail_url):
        """Process the detail page: Extract Docx/PDF links and Metadata."""
        try:
            # Quickly extract the ID from the URL to check for duplicates
            v_id_match = detail_url.split('-')[-1].replace('.htm', '')
            if v_id_match in self.downloaded_ids:
                return

            # Introduce a random delay to simulate human behavior
            time.sleep(random.uniform(0.5, 1.5))
            
            resp = self.session.get(detail_url, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Extract metadata from hidden input fields
            input_title = soup.find('input', {'id': 'hdVanBanTitle'})
            input_id = soup.find('input', {'id': 'hdVanBanId'})
            
            if not input_title or not input_id:
                return

            title = input_title['value']
            vanban_id = input_id['value']

            # Scan the entire page for Docx and PDF download links
            links_found = {}
            for a in soup.find_all('a', href=True):
                href = a['href'].lower()
                if 'download' in href or 'tai-file' in href:
                    if '.docx' in href:
                        links_found['docx'] = urljoin(self.BASE_URL, a['href'])
                    elif '.pdf' in href:
                        links_found['pdf'] = urljoin(self.BASE_URL, a['href'])

            # Hybrid Logic: Prioritize Docx -> PDF -> Fallback Docx
            final_url = links_found.get('docx') or links_found.get('pdf')
            extension = ".docx" if final_url == links_found.get('docx') else ".pdf"

            if not final_url:
                final_url = f"https://congbao.chinhphu.vn/tai-file-docx/{vanban_id}.htm"
                extension = ".docx"

            # Execute the file download process
            if self.download_file(final_url, title, vanban_id, detail_url, extension):
                # Save metadata as a JSON file
                meta = {
                    "id": vanban_id,
                    "title": title,
                    "extension": extension,
                    "url": detail_url,
                    "crawled_at": datetime.now().isoformat()
                }
                with open(self.output_dir / f"{vanban_id}.json", 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
                
                self.downloaded_ids.add(vanban_id)
                logger.info(f"✅ SUCCESSFULLY RETRIEVED ({extension[1:]}): {title[:50]}...")
                
        except Exception as e:
            logger.error(f"💥 Error processing link {detail_url}: {e}")

    def run_bruteforce(self, start_p=1, end_p=10):
        """Systematically scrape from the starting page to the ending page."""
        logger.info(f"🚜 COMMENCING COMPREHENSIVE SCRAPE: Pages {start_p} -> {end_p}")
        
        for p in range(start_p, end_p + 1):
            page_url = self.BASE_URL + self.LIST_PATH.format(p)
            logger.info(f"--- 🚜 Processing list page {p} ---")
            
            try:
                resp = self.session.get(page_url, timeout=30)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Restrict link extraction to the 'p-content' area to avoid sidebar noise
                main_area = soup.find('div', class_='p-content') or soup
                links = []
                for a in main_area.find_all('a', href=True):
                    href = a['href']
                    if '/van-ban/' in href and '.htm' in href:
                        clean_href = href.split('#')[0] # Remove URL anchors like #print, #comment
                        links.append(urljoin(self.BASE_URL, clean_href))
                
                unique_links = list(set(links))
                logger.info(f"🚜 Page {p}: Identified {len(unique_links)} potential documents.")
                
                # Utilize ThreadPool for concurrent processing of links on the page
                with ThreadPoolExecutor(max_workers=self.workers) as executor:
                    executor.map(self.process_link, unique_links)
                
                # Implement a pause between major page requests to prevent IP blocking
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error processing list page {p}: {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    # It is recommended to maintain workers=3 to ensure stability and avoid rate limits
    crawler = CongBaoHybridCrawler(workers=3)
    
    # Define the required page range for the scraping operation (e.g., 1 to 2500)
    crawler.run_bruteforce(start_p=1, end_p=2500)
    
    logger.info("🏁 OPERATION SUCCESSFULLY COMPLETED! Please review the raw/congbao_files directory.")