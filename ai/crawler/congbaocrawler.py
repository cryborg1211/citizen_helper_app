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

# 1. Tắt cảnh báo SSL cho sạch Terminal
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
        # Folder lưu trữ
        self.output_dir = Path("ai_engine/raw/congbao_files")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.workers = workers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
        # Quan trọng: Tắt xác thực SSL cho toàn bộ session của Chính phủ
        self.session.verify = False 
        
        # Quét folder cũ để Deduplication (Chống tải trùng)
        self.downloaded_ids = {f.stem for f in self.output_dir.glob("*.json")}
        logger.info(f"💾 Đã tìm thấy {len(self.downloaded_ids)} file trong máy. Sẽ chỉ tải cái mới.")

    def download_file(self, url, title, vanban_id, referer, ext):
        """Tải file thực tế với Referer header để vượt rào CDN."""
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_')).strip()
        file_path = self.output_dir / f"{safe_title[:80]}{ext}"
        
        # Smart Skip: Nếu file vật lý (docx/pdf) đã tồn tại thì không tải lại
        if file_path.exists():
            return True

        headers = self.session.headers.copy()
        headers['Referer'] = referer # Link trang chi tiết làm Referer
        
        try:
            r = self.session.get(url, stream=True, timeout=60, headers=headers)
            if r.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                logger.warning(f"❌ ID {vanban_id} lỗi HTTP {r.status_code} khi tải {ext}")
        except Exception as e:
            logger.error(f"💥 Lỗi tải file {vanban_id}: {e}")
        return False

    def process_link(self, detail_url):
        """Xử lý trang chi tiết: Tìm link Docx/PDF và Metadata."""
        try:
            # Lấy ID từ URL nhanh để check trùng
            v_id_match = detail_url.split('-')[-1].replace('.htm', '')
            if v_id_match in self.downloaded_ids:
                return

            # Nghỉ xíu cho giống người dùng thật
            time.sleep(random.uniform(0.5, 1.5))
            
            resp = self.session.get(detail_url, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Móc Metadata từ hidden inputs
            input_title = soup.find('input', {'id': 'hdVanBanTitle'})
            input_id = soup.find('input', {'id': 'hdVanBanId'})
            
            if not input_title or not input_id:
                return

            title = input_title['value']
            vanban_id = input_id['value']

            # Dò link tải Docx và PDF trong toàn bộ trang
            links_found = {}
            for a in soup.find_all('a', href=True):
                href = a['href'].lower()
                if 'download' in href or 'tai-file' in href:
                    if '.docx' in href:
                        links_found['docx'] = urljoin(self.BASE_URL, a['href'])
                    elif '.pdf' in href:
                        links_found['pdf'] = urljoin(self.BASE_URL, a['href'])

            # Logic Hybrid: Ưu tiên Docx -> PDF -> Fallback Docx
            final_url = links_found.get('docx') or links_found.get('pdf')
            extension = ".docx" if final_url == links_found.get('docx') else ".pdf"

            if not final_url:
                final_url = f"https://congbao.chinhphu.vn/tai-file-docx/{vanban_id}.htm"
                extension = ".docx"

            # Tiến hành tải file
            if self.download_file(final_url, title, vanban_id, detail_url, extension):
                # Lưu JSON metadata
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
                logger.info(f"✅ HỐT NGON ({extension[1:]}): {title[:50]}...")
                
        except Exception as e:
            logger.error(f"💥 Lỗi tại link {detail_url}: {e}")

    def run_bruteforce(self, start_p=1, end_p=10):
        """Ủi sạch từ trang đầu đến trang cuối."""
        logger.info(f"🚜 CHIẾN DỊCH TỔNG LỰC: Trang {start_p} -> {end_p}")
        
        for p in range(start_p, end_p + 1):
            page_url = self.BASE_URL + self.LIST_PATH.format(p)
            logger.info(f"--- 🚜 Đang 'ủi' trang danh sách {p} ---")
            
            try:
                resp = self.session.get(page_url, timeout=30)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Chỉ lấy link trong vùng p-content để tránh sidebar
                main_area = soup.find('div', class_='p-content') or soup
                links = []
                for a in main_area.find_all('a', href=True):
                    href = a['href']
                    if '/van-ban/' in href and '.htm' in href:
                        clean_href = href.split('#')[0] # Bỏ các neo #print, #comment
                        links.append(urljoin(self.BASE_URL, clean_href))
                
                unique_links = list(set(links))
                logger.info(f"🚜 Trang {p}: Tìm thấy {len(unique_links)} văn bản tiềm năng.")
                
                # Dùng ThreadPool để ủi song song các link trong trang
                with ThreadPoolExecutor(max_workers=self.workers) as executor:
                    executor.map(self.process_link, unique_links)
                
                # Nghỉ giữa các trang lớn để tránh bị Ban IP
                time.sleep(2)
            except Exception as e:
                logger.error(f"Lỗi tại trang danh sách {p}: {e}")

# --- KHỞI CHẠY ---
if __name__ == "__main__":
    # Khuyên Khương để workers=3 cho an toàn, thà chậm mà chắc bro ạ!
    crawler = CongBaoHybridCrawler(workers=3)
    
    # Khương muốn hốt bao nhiêu trang thì chỉnh ở đây nhé (ví dụ 1 đến 2500)
    crawler.run_bruteforce(start_p=1, end_p=2500)
    
    logger.info("🏁 PHÁ ĐẢO THÀNH CÔNG! Check folder raw/congbao_files nha bro!")