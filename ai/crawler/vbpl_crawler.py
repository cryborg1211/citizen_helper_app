import re
import time
import json
import logging
import random
from pathlib import Path
from typing import Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Logging and runtime configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


START_ID = 185000 
END_ID = 140000 
WORKERS = 2 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9",
}

class VBPLBackwardCrawler:
    def __init__(self):
        self.output_dir = Path("ai_engine/raw/vbpl")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def fetch_attributes(self, item_id: int) -> dict:
        url = f"https://vbpl.vn/TW/Pages/vbpq-thuoctinh.aspx?ItemID={item_id}&dvid=13"
        metadata = {}
        try:
            resp = self.session.get(url, timeout=45)
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'html.parser')
                container = soup.find('div', {'id': 'divThuocTinh'}) or soup
                table = container.find('table')
                if table:
                    for row in table.find_all('tr'):
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            key = cols[0].get_text(strip=True).replace(':', '')
                            val = cols[1].get_text(strip=True)
                            metadata[key] = val
        except: pass
        return metadata

    def fetch_document(self, item_id: int) -> Optional[str]:
        url = f"https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID={item_id}&dvid=13"
        try:
            resp = self.session.get(url, timeout=45)
            if resp.status_code != 200: return None
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            for sid in ['toanvancontent', 'divContent', 'fulltext', 'content1']:
                div = soup.find('div', id=sid) or soup.find('div', class_=sid)
                if div and len(div.get_text(strip=True)) > 200:
                    return div.get_text(separator='\n', strip=True)
        except: pass
        return None

    def download_one(self, item_id: int):
        output_path = self.output_dir / f"{item_id}.json"
        if output_path.exists():
            return "SKIPPED"

        # Record the processing start for each document ID.
        logger.info(f"Checking ItemID {item_id}...")
        
        try:
            content = self.fetch_document(item_id)
            if not content:
                logger.warning(f"ItemID {item_id}: no document content found (404 or empty body).")
                return "EMPTY"

            metadata = self.fetch_attributes(item_id)
            
            data = {
                "item_id": item_id,
                "metadata": metadata,
                "full_text": content,
                "crawled_at": datetime.now().isoformat()
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Completed ItemID {item_id}.")
            return "SUCCESS"

        except Exception as e:
            logger.error(f"Unhandled error while processing ItemID {item_id}: {str(e)}")
            return "ERROR"

    def run(self):
        START_ID = 187328
        END_ID = 180000
        STEP = 1 
        
        logger.info(f"Starting backward crawl from ItemID {START_ID} down to {END_ID}.")
        
        for i in range(START_ID, END_ID, -STEP):
            result = self.download_one(i)
            
            if result == "SUCCESS":
                time.sleep(random.uniform(1, 2))
            else:
                time.sleep(0.5)
                
if __name__ == "__main__":
    crawler = VBPLBackwardCrawler()
    crawler.run()