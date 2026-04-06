import re
import time
import json
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry 
import random

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VBPLIDCrawler:
    """Class cào dữ liệu VBPL kết hợp Toàn văn và Thuộc tính (Labels)."""
    
    BASE_URL = "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx"
    ATTR_URL = "https://vbpl.vn/TW/Pages/vbpq-thuoctinh.aspx"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9",
    }

    def __init__(self, output_dir: Path, metadata_dir: Path, checkpoint_file: Path, workers: int = 1):
        self.output_dir = output_dir
        self.metadata_dir = metadata_dir
        self.checkpoint_file = checkpoint_file
        self.workers = workers
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

        retry_strategy = Retry(
            total=5, # Thử lại tối đa 5 lần
            backoff_factor=1, # Đợi 1s, 2s, 4s, 8s... giữa các lần thử
            status_forcelist=[429, 500, 502, 503, 504], # Thử lại nếu gặp các lỗi này
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.checkpoint = self._load_checkpoint()
        self.stats = {"checked": 0, "downloaded": 0, "skipped": 0, "empty": 0}

    def _load_checkpoint(self) -> dict:
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Lỗi load checkpoint: {e}")
        return {"downloaded_ids": [], "last_id": 0}

    def _save_checkpoint(self):
        self.checkpoint["last_updated"] = datetime.now().isoformat()
        self.checkpoint["stats"] = self.stats
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoint, f, ensure_ascii=False, indent=2)

    def fetch_attributes(self, item_id: int) -> dict:
        # Thêm dvid=13 để truy cập đúng phân vùng dữ liệu trung ương
        url = f"{self.ATTR_URL}?ItemID={item_id}&dvid=13"
        metadata = {}
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                # Ép kiểu encoding về utf-8 để tránh lỗi font tiếng Việt
                response.encoding = 'utf-8' 
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # CÁCH 1: Tìm vùng chứa div có id là 'divThuocTinh' (Cái này cực chuẩn)
                attr_container = soup.find('div', {'id': 'divThuocTinh'})
            
                # Nếu không thấy div đó, tìm đại cái table nào có text 'Số ký hiệu'
                if not attr_container:
                    attr_container = soup
            
                # Quét tất cả các bảng trong container này
                tables = attr_container.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                                # Lấy key và value, dọn dẹp khoảng trắng rác
                            key = cols[0].get_text(strip=True).replace(':', '')
                            val = cols[1].get_text(strip=True)
                            if key and val:
                                metadata[key] = val
                            
        except Exception as e:
            logger.error(f"Lỗi lấy attributes ID {item_id}: {e}")
    
        # Debug nhẹ: Nếu vẫn rỗng thì in ra log để mình soi
        if not metadata:
            logger.warning(f"ID {item_id}: Metadata vẫn rỗng sau khi quét!")
        
        return metadata

    def fetch_document(self, item_id: int) -> Optional[str]:
        """Lấy Toàn văn văn bản."""
        url = f"{self.BASE_URL}?ItemID={item_id}&dvid=13"
        try:
            response = self.session.get(url, timeout=60)
            if response.status_code != 200:
                return None
            response.encoding = 'utf-8'
            return self._extract_content(response.text)
        except Exception as e:
            logger.error(f"Lỗi lấy document ID {item_id}: {e}")
            return None

    def _extract_content(self, html: str) -> str:
        """Xử lý HTML để lấy text sạch."""
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        selectors = [{'class': 'content1'}, {'class': 'toanvancontent'}, {'id': 'toanvancontent'}]
        for sel in selectors:
            div = soup.find('div', sel)
            if div and len(div.get_text(strip=True)) > 300:
                text = div.get_text(separator='\n', strip=True)
                return '\n'.join([l.strip() for l in text.split('\n') if l.strip()])

        # Fallback
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            if any(ind in text for ind in ['Điều 1', 'ĐIỀU 1', 'Căn cứ']) and len(text) > 500:
                lines = [l.strip() for l in div.get_text(separator='\n').split('\n') if l.strip()]
                return '\n'.join(lines)
        return ""

    def download_by_id(self, item_id: int) -> bool:
        """Quy trình tải và lưu trữ 1 văn bản."""
        time.sleep(random.uniform(0.1, 0.5))
        self.stats["checked"] += 1
        output_path = self.output_dir / f"{item_id}.json"
        
        # Kiểm tra nếu đã tải rồi
        if output_path.exists() or str(item_id) in self.checkpoint.get("downloaded_ids", []):
            self.stats["skipped"] += 1
            return True

        # 1. Fetch Text
        content = self.fetch_document(item_id)
        if not content or len(content) < 100:
            self.stats["empty"] += 1
            return False

        # 2. Fetch Labels
        labels = self.fetch_attributes(item_id)

        # 3. Save as Structured JSON
        data_to_save = {
            "item_id": item_id,
            "source": "vbpl.vn",
            "downloaded_at": datetime.now().isoformat(),
            "metadata": labels,
            "full_text": content
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            
            self.checkpoint["downloaded_ids"].append(str(item_id))
            self.stats["downloaded"] += 1
            return True
        except Exception as e:
            logger.error(f"Lỗi lưu file {item_id}: {e}")
            return False

    def crawl_range(self, start_id: int, end_id: int, batch_size: int = 100):
        """Chạy crawler theo dải ID với đa luồng."""
        logger.info(f"Đang cào dải ID từ {start_id} đến {end_id}")
        current = start_id
        while current < end_id:
            batch_end = min(current + batch_size, end_id)
            ids = list(range(current, batch_end))

            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = {executor.submit(self.download_by_id, id): id for id in ids}
                for future in as_completed(futures):
                    future.result()

            logger.info(f"Đã xong IDs {current}-{batch_end}. Tổng đã tải: {self.stats['downloaded']}")
            self.checkpoint["last_id"] = batch_end
            self._save_checkpoint()
            current = batch_end
            time.sleep(1) # Nghỉ chút cho web đỡ chặn


def main():
    import argparse

    PROJECT_ROOT = Path(__file__).parent.parent
    OUTPUT_DIR   = PROJECT_ROOT / "raw" / "vbpl"
    METADATA_DIR = PROJECT_ROOT / "metadata"
    CHECKPOINT   = METADATA_DIR / "vbpl_id_checkpoint.json"

    parser = argparse.ArgumentParser(description='VBPL ID-Range Crawler')
    parser.add_argument('--start',   type=int, default=1,       help='ID bắt đầu')
    parser.add_argument('--end',     type=int, default=185000,  help='ID kết thúc')
    parser.add_argument('--workers', type=int, default=5,       help='Số luồng song song')
    parser.add_argument('--batch',   type=int, default=100,     help='Kích thước mỗi batch')
    args = parser.parse_args()

    crawler = VBPLIDCrawler(
        output_dir      = OUTPUT_DIR,
        metadata_dir    = METADATA_DIR,
        checkpoint_file = CHECKPOINT,
        workers         = args.workers,
    )
    crawler.crawl_range(args.start, args.end, args.batch)


if __name__ == "__main__":
    main()
