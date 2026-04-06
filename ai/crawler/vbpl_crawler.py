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

# --- CONFIG ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Tăng ID lên mức mới nhất của năm 2026
START_ID = 185000 
END_ID = 140000 # Lấy đến hết năm 2019/2020 là đẹp
WORKERS = 2 # Để thấp cho an toàn, không bị ban IP

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
        """Quét sạch Metadata từ tab Thuộc tính."""
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
        """Lấy text nội dung."""
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

        logger.info(f"🔍 Đang kiểm tra ID: {item_id}...") # Log ngay lúc bắt đầu
        
        try:
            content = self.fetch_document(item_id)
            if not content:
                logger.warning(f"❌ ID {item_id}: Không có nội dung (404 hoặc rỗng)")
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
            
            logger.info(f"✅ HỐT NGON ID: {item_id}")
            return "SUCCESS"

        except Exception as e:
            logger.error(f"💥 Lỗi nghiêm trọng tại ID {item_id}: {str(e)}")
            return "ERROR"

    def run(self):
        START_ID = 187328
        END_ID = 180000
        STEP = 1 # Chỉnh lên 10 nếu muốn dò nhanh
        
        logger.info(f"🚀 Chiến dịch TRUY QUÉT từ {START_ID} về {END_ID}")
        
        for i in range(START_ID, END_ID, -STEP):
            result = self.download_one(i)
            
            # Nếu thành công thì nghỉ ngắn, nếu rỗng thì nghỉ cực ngắn để dò tiếp
            if result == "SUCCESS":
                time.sleep(random.uniform(1, 2))
            else:
                time.sleep(0.5)
                
if __name__ == "__main__":
    crawler = VBPLBackwardCrawler()
    crawler.run()