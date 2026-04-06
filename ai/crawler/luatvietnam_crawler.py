#!/usr/bin/env python3
"""
LuatVietnam Crawler - Fetches sample contracts and legal forms from LuatVietnam.vn.

This crawler uses Selenium with undetected-chromedriver to bypass Cloudflare protection.
Falls back to cloudscraper if Selenium is not available.

Source: https://luatvietnam.vn/bieu-mau.html (verified Dec 2025)

Dependencies:
    pip install selenium undetected-chromedriver cloudscraper beautifulsoup4
"""

import re
import time
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://luatvietnam.vn"
BIEU_MAU_URL = "https://luatvietnam.vn/bieu-mau.html"

# Target URLs - contracts, legal guides, and articles (verified Dec 2025)
TARGET_TEMPLATES = [
    # === Hợp đồng (Contracts) ===
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-thue-nha-571-19399-article.html", "hop-dong-thue-nha"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-lao-dong-571-19352-article.html", "hop-dong-lao-dong"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-kinh-te-571-24970-article.html", "hop-dong-kinh-te"),
    ("https://luatvietnam.vn/bieu-mau/hop-dong-thue-mat-bang-571-32242-article.html", "hop-dong-thue-mat-bang"),
    ("https://luatvietnam.vn/dat-dai-nha-o/hop-dong-mua-ban-nha-dat-567-25348-article.html", "hop-dong-mua-ban-nha-dat"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-cong-tac-vien-moi-nhat-571-19507-article.html", "hop-dong-cong-tac-vien"),
    ("https://luatvietnam.vn/bieu-mau/mau-bien-ban-ghi-nho-571-89473-article.html", "bien-ban-ghi-nho"),
    ("https://luatvietnam.vn/bieu-mau/mau-bien-ban-thoa-thuan-hop-tac-571-34061-article.html", "thoa-thuan-hop-tac"),
    ("https://luatvietnam.vn/bieu-mau/mau-thong-bao-cham-dut-hop-dong-lao-dong-571-19832-article.html", "thong-bao-cham-dut-hdld"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-moi-gioi-mua-ban-hang-hoa-571-99612-article.html", "hop-dong-moi-gioi"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-xuat-khau-lao-dong-571-95397-article.html", "hop-dong-xuat-khau-lao-dong"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-van-chuyen-hanh-khach-571-101961-article.html", "hop-dong-van-chuyen"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-cho-thue-nha-xuong-va-kho-bai-571-101919-article.html", "hop-dong-thue-nha-xuong"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-dat-coc-571-19366-article.html", "hop-dong-dat-coc"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-uy-thac-571-19461-article.html", "hop-dong-uy-thac"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-dai-ly-571-19377-article.html", "hop-dong-dai-ly"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-bao-hiem-571-19498-article.html", "hop-dong-bao-hiem"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-dich-vu-571-19389-article.html", "hop-dong-dich-vu"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-xay-dung-571-19417-article.html", "hop-dong-xay-dung"),
    ("https://luatvietnam.vn/bieu-mau/mau-hop-dong-chuyen-nhuong-quyen-su-dung-dat-571-19428-article.html", "hop-dong-chuyen-nhuong-dat"),

    # === Đơn từ (Applications/Petitions) ===
    ("https://luatvietnam.vn/bieu-mau/mau-don-xin-viec-571-19341-article.html", "don-xin-viec"),
    ("https://luatvietnam.vn/bieu-mau/mau-don-xin-nghi-phep-571-34072-article.html", "don-xin-nghi-phep"),
    ("https://luatvietnam.vn/bieu-mau/mau-don-xin-thoi-viec-571-19843-article.html", "don-xin-thoi-viec"),
    ("https://luatvietnam.vn/bieu-mau/mau-don-khieu-nai-571-19876-article.html", "don-khieu-nai"),
    ("https://luatvietnam.vn/bieu-mau/mau-don-to-cao-571-19887-article.html", "don-to-cao"),

    # === Giấy tờ doanh nghiệp (Business Documents) ===
    ("https://luatvietnam.vn/bieu-mau/mau-giay-uy-quyen-571-19450-article.html", "giay-uy-quyen"),
    ("https://luatvietnam.vn/bieu-mau/mau-bien-ban-hop-571-34083-article.html", "bien-ban-hop"),
    ("https://luatvietnam.vn/bieu-mau/mau-bien-ban-ban-giao-571-34094-article.html", "bien-ban-ban-giao"),
    ("https://luatvietnam.vn/bieu-mau/mau-quyet-dinh-bo-nhiem-571-34105-article.html", "quyet-dinh-bo-nhiem"),
    ("https://luatvietnam.vn/bieu-mau/mau-dieu-le-cong-ty-571-25337-article.html", "dieu-le-cong-ty"),

    # === Lao động (Labor) ===
    ("https://luatvietnam.vn/lao-dong/muc-luong-toi-thieu-vung-2024-223-94617-article.html", "luong-toi-thieu-vung-2024"),
    ("https://luatvietnam.vn/lao-dong/che-do-thai-san-223-25326-article.html", "che-do-thai-san"),
    ("https://luatvietnam.vn/lao-dong/bao-hiem-xa-hoi-tu-nguyen-223-29876-article.html", "bhxh-tu-nguyen"),
    ("https://luatvietnam.vn/lao-dong/nghi-phep-nam-223-25348-article.html", "nghi-phep-nam"),
    ("https://luatvietnam.vn/lao-dong/tro-cap-that-nghiep-223-25359-article.html", "tro-cap-that-nghiep"),

    # === Đất đai - Nhà ở (Land & Housing) ===
    ("https://luatvietnam.vn/dat-dai-nha-o/thu-tuc-sang-ten-so-do-567-25370-article.html", "thu-tuc-sang-ten-so-do"),
    ("https://luatvietnam.vn/dat-dai-nha-o/cap-so-do-lan-dau-567-25381-article.html", "cap-so-do-lan-dau"),
    ("https://luatvietnam.vn/dat-dai-nha-o/thu-tuc-tach-thua-567-25392-article.html", "thu-tuc-tach-thua"),
    ("https://luatvietnam.vn/dat-dai-nha-o/thue-dat-567-25403-article.html", "thue-dat"),

    # === Doanh nghiệp (Business) ===
    ("https://luatvietnam.vn/doanh-nghiep/thanh-lap-cong-ty-569-25414-article.html", "thanh-lap-cong-ty"),
    ("https://luatvietnam.vn/doanh-nghiep/thay-doi-dang-ky-kinh-doanh-569-25425-article.html", "thay-doi-dkkd"),
    ("https://luatvietnam.vn/doanh-nghiep/giai-the-doanh-nghiep-569-25436-article.html", "giai-the-dn"),
    ("https://luatvietnam.vn/doanh-nghiep/pha-san-doanh-nghiep-569-25447-article.html", "pha-san-dn"),

    # === Hôn nhân gia đình (Marriage & Family) ===
    ("https://luatvietnam.vn/hon-nhan-gia-dinh/dang-ky-ket-hon-570-25458-article.html", "dang-ky-ket-hon"),
    ("https://luatvietnam.vn/hon-nhan-gia-dinh/thu-tuc-ly-hon-570-25469-article.html", "thu-tuc-ly-hon"),
    ("https://luatvietnam.vn/hon-nhan-gia-dinh/quyen-nuoi-con-570-25480-article.html", "quyen-nuoi-con"),
    ("https://luatvietnam.vn/hon-nhan-gia-dinh/chia-tai-san-khi-ly-hon-570-25491-article.html", "chia-tai-san-ly-hon"),

    # === Thuế (Tax) ===
    ("https://luatvietnam.vn/thue/thue-thu-nhap-ca-nhan-568-25502-article.html", "thue-tncn"),
    ("https://luatvietnam.vn/thue/thue-gia-tri-gia-tang-568-25513-article.html", "thue-gtgt"),
    ("https://luatvietnam.vn/thue/thue-thu-nhap-doanh-nghiep-568-25524-article.html", "thue-tndn"),

    # === Hình sự (Criminal) ===
    ("https://luatvietnam.vn/hinh-su/toi-trom-cap-tai-san-572-25535-article.html", "toi-trom-cap"),
    ("https://luatvietnam.vn/hinh-su/toi-lua-dao-572-25546-article.html", "toi-lua-dao"),
    ("https://luatvietnam.vn/hinh-su/toi-co-y-gay-thuong-tich-572-25557-article.html", "toi-gay-thuong-tich"),

    # === Dân sự (Civil) ===
    ("https://luatvietnam.vn/dan-su/boi-thuong-thiet-hai-573-25568-article.html", "boi-thuong-thiet-hai"),
    ("https://luatvietnam.vn/dan-su/thua-ke-tai-san-573-25579-article.html", "thua-ke-tai-san"),
    ("https://luatvietnam.vn/dan-su/quyen-so-huu-tai-san-573-25590-article.html", "quyen-so-huu-tai-san"),
]

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "raw" / "luatvietnam"


class CloudflareBypass:
    """
    Cloudflare bypass handler using multiple strategies:
    1. undetected-chromedriver (Selenium)
    2. cloudscraper (requests-based)
    3. Standard requests (fallback)
    """

    def __init__(self):
        self.driver = None
        self.scraper = None
        self.method = None
        self._init_bypass()

    def _init_bypass(self):
        """Initialize the best available bypass method."""
        # Try undetected-chromedriver first (best for Cloudflare v2/v3)
        try:
            import undetected_chromedriver as uc
            from selenium.webdriver.chrome.options import Options

            options = uc.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--lang=vi-VN')

            self.driver = uc.Chrome(options=options, version_main=None)
            self.method = 'selenium'
            logger.info("Using undetected-chromedriver for Cloudflare bypass")
            return
        except ImportError:
            logger.warning("undetected-chromedriver not installed, trying cloudscraper")
        except Exception as e:
            logger.warning(f"Failed to init undetected-chromedriver: {e}")

        # Try cloudscraper as fallback
        try:
            import cloudscraper
            self.scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True,
                },
                delay=10,
            )
            self.method = 'cloudscraper'
            logger.info("Using cloudscraper for Cloudflare bypass")
            return
        except ImportError:
            logger.warning("cloudscraper not installed, using standard requests")
        except Exception as e:
            logger.warning(f"Failed to init cloudscraper: {e}")

        # Fallback to standard requests
        import requests
        self.scraper = requests.Session()
        self.scraper.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.method = 'requests'
        logger.info("Using standard requests (Cloudflare bypass not available)")

    def fetch(self, url: str, wait_time: int = 5) -> Optional[str]:
        """
        Fetch a URL with Cloudflare bypass.

        Args:
            url: URL to fetch
            wait_time: Time to wait for page load (Selenium only)

        Returns:
            HTML content or None if failed
        """
        if self.method == 'selenium' and self.driver:
            return self._fetch_selenium(url, wait_time)
        elif self.scraper:
            return self._fetch_scraper(url)
        return None

    def _fetch_selenium(self, url: str, wait_time: int) -> Optional[str]:
        """Fetch using Selenium with undetected-chromedriver."""
        try:
            logger.info(f"Fetching with Selenium: {url}")
            self.driver.get(url)

            # Wait for Cloudflare challenge to complete
            time.sleep(wait_time)

            # Check if we're still on Cloudflare challenge page
            page_source = self.driver.page_source
            if 'Just a moment' in page_source or 'Checking your browser' in page_source:
                logger.info("Cloudflare challenge detected, waiting longer...")
                time.sleep(10)
                page_source = self.driver.page_source

            # Additional wait for dynamic content
            time.sleep(2)
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Selenium fetch error: {e}")
            return None

    def _fetch_scraper(self, url: str) -> Optional[str]:
        """Fetch using cloudscraper or requests."""
        try:
            logger.info(f"Fetching with {self.method}: {url}")
            response = self.scraper.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return None

    def close(self):
        """Close browser/session."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


def extract_article_content(html: str) -> str:
    """
    Extract the main article content from a LuatVietnam page.

    Args:
        html: Raw HTML content

    Returns:
        Extracted text content
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')

    # Remove unwanted elements
    unwanted_selectors = [
        'script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript',
        '.sidebar', '.menu', '.navigation', '.ads', '.advertisement', '.social',
        '.share', '.comment', '.related', '.breadcrumb', '.pagination', '.login',
        '.tin-cung-muc', '.tin-lien-quan', '.news-relate'
    ]

    for selector in unwanted_selectors:
        for element in soup.select(selector):
            element.decompose()

    # LuatVietnam content selectors (verified Dec 2025)
    content_selectors = [
        'div.the-article-body',
        'div.the-article',
        'div.article-body',
        'div.entry',
        'div.noi-dung',
        'div.nd-bai-viet',
        'div.content-body',
        'article',
    ]

    content_div = None
    for selector in content_selectors:
        content_div = soup.select_one(selector)
        if content_div:
            text = content_div.get_text(strip=True)
            # Verify it's actual content, not navigation
            if len(text) > 300 and 'Tìm kiếm nâng cao' not in text[:500]:
                break
            content_div = None

    # Look for contract content indicators
    if not content_div:
        contract_keywords = [
            'HỢP ĐỒNG', 'BIÊN BẢN', 'GIẤY ỦY QUYỀN', 'ĐƠN XIN',
            'MẪU SỐ', 'Điều 1', 'BÊN A:', 'BÊN B:', 'CỘNG HÒA'
        ]
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            has_contract = any(kw in text for kw in contract_keywords)
            not_nav = 'Tìm kiếm nâng cao' not in text[:500]

            if has_contract and not_nav and len(text) > 500:
                content_div = div
                break

    if content_div:
        text = content_div.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Filter navigation items
        skip_patterns = [
            'Tin pháp luật', 'Biểu mẫu', 'Thủ tục hành chính',
            'Tìm kiếm nâng cao', 'Đăng nhập', 'Đăng ký',
            'Tin cùng chuyên mục', 'Xem tiếp', 'Facebook', 'Zalo'
        ]

        filtered = [l for l in lines if not any(p in l for p in skip_patterns)]
        return '\n'.join(filtered)

    return ""


def download_template(bypass: CloudflareBypass, url: str, slug: str, output_dir: Path) -> bool:
    """
    Download a single template page.

    Args:
        bypass: CloudflareBypass instance
        url: Template page URL
        slug: Filename slug
        output_dir: Output directory

    Returns:
        True if successful, False otherwise
    """
    output_path = output_dir / f"{slug}.txt"

    logger.info(f"Downloading template: {slug}")
    html = bypass.fetch(url, wait_time=8)

    if not html:
        logger.error(f"Failed to fetch: {slug}")
        return False

    content = extract_article_content(html)

    # Validate content quality
    if not content or len(content) < 200:
        logger.warning(f"Template {slug} has insufficient content ({len(content)} chars)")
        return False

    # Check for Cloudflare challenge page
    if 'Just a moment' in content or 'Checking your browser' in content:
        logger.warning(f"Template {slug} still showing Cloudflare challenge")
        return False

    # Check for valid contract content
    contract_indicators = ['HỢP ĐỒNG', 'BIÊN BẢN', 'Điều', 'BÊN A', 'BÊN B', 'Căn cứ']
    if not any(ind in content for ind in contract_indicators):
        logger.warning(f"Template {slug} doesn't appear to have contract content")
        return False

    # Save to file
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info(f"Saved: {slug}.txt ({len(content)} chars)")
    return True


def create_sample_templates(output_dir: Path) -> int:
    """
    Create sample contract templates as backup.
    Returns number of templates created.
    """
    templates = {
        "hop-dong-vay-tien-mau": """HỢP ĐỒNG VAY TIỀN

Căn cứ Bộ luật Dân sự năm 2015;
Căn cứ vào nhu cầu và khả năng thực tế của các bên;

Hôm nay, ngày ... tháng ... năm 20..., tại ...

Chúng tôi gồm:

BÊN CHO VAY (BÊN A):
Ông/Bà: .................................................
Sinh ngày: ..............................................
CMND/CCCD số: ..................... cấp ngày: ............ tại: ..............
Hộ khẩu thường trú: .....................................
Chỗ ở hiện tại: .........................................
Điện thoại: .............................................

BÊN VAY (BÊN B):
Ông/Bà: .................................................
Sinh ngày: ..............................................
CMND/CCCD số: ..................... cấp ngày: ............ tại: ..............
Hộ khẩu thường trú: .....................................
Chỗ ở hiện tại: .........................................
Điện thoại: .............................................

Hai bên cùng thỏa thuận ký kết hợp đồng vay tiền với các điều khoản sau:

ĐIỀU 1. SỐ TIỀN VAY
1.1. Số tiền vay: ......................... đồng
(Bằng chữ: ...............................................)
1.2. Bên A đã giao đủ số tiền nêu trên cho Bên B vào ngày ký hợp đồng này.
1.3. Bên B xác nhận đã nhận đủ số tiền từ Bên A.

ĐIỀU 2. MỤC ĐÍCH VAY
Bên B vay tiền để sử dụng vào mục đích: ................................

ĐIỀU 3. THỜI HẠN VAY
3.1. Thời hạn vay: ........ tháng
3.2. Kể từ ngày: ....../....../20..... đến ngày: ....../....../20.....
3.3. Bên B có thể trả nợ trước hạn với điều kiện thông báo cho Bên A trước ít nhất 05 ngày.

ĐIỀU 4. LÃI SUẤT
4.1. Lãi suất vay: .......%/tháng (hoặc .......%/năm)
4.2. Lãi suất được tính trên số tiền vay thực tế và thời gian vay thực tế.
4.3. Phương thức tính lãi: Lãi = Số tiền vay x Lãi suất x Số tháng vay
4.4. Lưu ý: Theo Điều 468 Bộ luật Dân sự 2015, lãi suất không được vượt quá 20%/năm.

ĐIỀU 5. PHƯƠNG THỨC TRẢ NỢ
5.1. Bên B có thể trả nợ theo một trong các phương thức sau:
a) Trả một lần cả gốc và lãi khi đến hạn;
b) Trả lãi hàng tháng, trả gốc khi đến hạn;
c) Trả góp hàng tháng (gốc + lãi).
5.2. Phương thức được chọn: ................................
5.3. Hình thức thanh toán: Tiền mặt / Chuyển khoản
Số tài khoản: ....................... Ngân hàng: .....................

ĐIỀU 6. QUYỀN VÀ NGHĨA VỤ CỦA BÊN A
6.1. Quyền của Bên A:
- Yêu cầu Bên B trả đủ tiền gốc và lãi đúng hạn;
- Yêu cầu Bên B sử dụng tiền vay đúng mục đích;
- Được quyền không cho vay tiếp nếu Bên B vi phạm hợp đồng.
6.2. Nghĩa vụ của Bên A:
- Giao đủ tiền cho Bên B theo thỏa thuận;
- Không được yêu cầu Bên B trả lại tiền vay trước thời hạn, trừ trường hợp quy định tại Điều 470 Bộ luật Dân sự.

ĐIỀU 7. QUYỀN VÀ NGHĨA VỤ CỦA BÊN B
7.1. Quyền của Bên B:
- Được sử dụng tiền vay theo mục đích đã thỏa thuận;
- Được trả nợ trước hạn theo quy định tại Điều 3.3.
7.2. Nghĩa vụ của Bên B:
- Sử dụng tiền vay đúng mục đích;
- Trả đủ tiền gốc và lãi đúng hạn;
- Chịu trách nhiệm trước pháp luật nếu không trả nợ đúng hạn.

ĐIỀU 8. XỬ LÝ VI PHẠM
8.1. Nếu Bên B không trả nợ đúng hạn, Bên B phải chịu lãi suất quá hạn bằng 150% lãi suất vay trong hạn đối với số tiền chậm trả.
8.2. Trường hợp Bên B không trả được nợ, Bên A có quyền yêu cầu cơ quan có thẩm quyền giải quyết theo quy định của pháp luật.

ĐIỀU 9. ĐIỀU KHOẢN CHUNG
9.1. Hợp đồng này có hiệu lực kể từ ngày ký.
9.2. Mọi tranh chấp phát sinh từ hợp đồng này được giải quyết bằng thương lượng, hòa giải. Nếu không thành, các bên có quyền khởi kiện tại Tòa án nhân dân có thẩm quyền.
9.3. Hợp đồng được lập thành 02 bản có giá trị pháp lý như nhau, mỗi bên giữ 01 bản.

BÊN CHO VAY (BÊN A)                    BÊN VAY (BÊN B)
(Ký, ghi rõ họ tên)                    (Ký, ghi rõ họ tên)

NGƯỜI LÀM CHỨNG (nếu có):
(Ký, ghi rõ họ tên)""",

        "hop-dong-mua-ban-tai-san-mau": """HỢP ĐỒNG MUA BÁN TÀI SẢN

Căn cứ Bộ luật Dân sự năm 2015;
Căn cứ vào nhu cầu và thỏa thuận của các bên;

Hôm nay, ngày ... tháng ... năm 20..., tại ...

BÊN BÁN (BÊN A):
Ông/Bà: .................................................
Sinh ngày: ..............................................
CMND/CCCD số: ..................... cấp ngày: ............ tại: ..............
Địa chỉ: ................................................
Điện thoại: .............................................

BÊN MUA (BÊN B):
Ông/Bà: .................................................
Sinh ngày: ..............................................
CMND/CCCD số: ..................... cấp ngày: ............ tại: ..............
Địa chỉ: ................................................
Điện thoại: .............................................

Hai bên thỏa thuận ký kết hợp đồng mua bán tài sản với các điều khoản sau:

ĐIỀU 1. ĐỐI TƯỢNG MUA BÁN
1.1. Loại tài sản: ........................................
1.2. Đặc điểm, tính chất: .................................
1.3. Số lượng: ............................................
1.4. Chất lượng/Tình trạng: ...............................
1.5. Nguồn gốc: ...........................................

ĐIỀU 2. GIÁ BÁN VÀ PHƯƠNG THỨC THANH TOÁN
2.1. Giá bán: ......................... đồng
(Bằng chữ: ...............................................)
2.2. Giá trên đã bao gồm/chưa bao gồm: thuế, phí ...
2.3. Phương thức thanh toán:
- Đặt cọc: ................. đồng vào ngày ký hợp đồng
- Thanh toán đợt 2: ........ đồng vào ngày ...............
- Thanh toán còn lại: ...... đồng khi giao nhận tài sản
2.4. Hình thức thanh toán: Tiền mặt / Chuyển khoản

ĐIỀU 3. GIAO NHẬN TÀI SẢN
3.1. Thời điểm giao tài sản: ..............................
3.2. Địa điểm giao tài sản: ...............................
3.3. Chi phí vận chuyển do Bên: ........... chịu
3.4. Bên A có trách nhiệm giao tài sản đúng chủng loại, số lượng, chất lượng như đã thỏa thuận.

ĐIỀU 4. CHUYỂN QUYỀN SỞ HỮU
Theo Điều 161 và Điều 440 Bộ luật Dân sự 2015, quyền sở hữu tài sản được chuyển cho Bên B kể từ thời điểm Bên B nhận tài sản, trừ trường hợp các bên có thỏa thuận khác hoặc pháp luật có quy định khác.

ĐIỀU 5. BẢO HÀNH (nếu có)
5.1. Thời hạn bảo hành: ...................................
5.2. Điều kiện bảo hành: ..................................
5.3. Địa điểm bảo hành: ...................................

ĐIỀU 6. QUYỀN VÀ NGHĨA VỤ CỦA BÊN A
6.1. Giao tài sản đúng chủng loại, số lượng, chất lượng, thời gian, địa điểm.
6.2. Cung cấp thông tin cần thiết về tài sản và hướng dẫn sử dụng (nếu có).
6.3. Bảo đảm quyền sở hữu hợp pháp đối với tài sản bán.
6.4. Chịu trách nhiệm về chất lượng tài sản trong thời gian bảo hành.

ĐIỀU 7. QUYỀN VÀ NGHĨA VỤ CỦA BÊN B
7.1. Thanh toán đầy đủ, đúng hạn theo thỏa thuận.
7.2. Nhận tài sản theo đúng thời gian, địa điểm đã thỏa thuận.
7.3. Kiểm tra tài sản trước khi nhận.
7.4. Chịu rủi ro đối với tài sản kể từ thời điểm nhận tài sản.

ĐIỀU 8. PHẠT VI PHẠM VÀ BỒI THƯỜNG THIỆT HẠI
8.1. Bên vi phạm nghĩa vụ phải chịu phạt vi phạm bằng .....% giá trị hợp đồng.
8.2. Ngoài phạt vi phạm, bên vi phạm còn phải bồi thường thiệt hại thực tế phát sinh (nếu có).

ĐIỀU 9. ĐIỀU KHOẢN CHUNG
9.1. Hợp đồng có hiệu lực từ ngày ký.
9.2. Tranh chấp được giải quyết bằng thương lượng, hòa giải, hoặc Tòa án có thẩm quyền.
9.3. Hợp đồng được lập thành 02 bản, mỗi bên giữ 01 bản có giá trị pháp lý như nhau.

BÊN BÁN (BÊN A)                        BÊN MUA (BÊN B)
(Ký, ghi rõ họ tên)                    (Ký, ghi rõ họ tên)""",

        "hop-dong-thue-nha-mau": """HỢP ĐỒNG THUÊ NHÀ Ở

Căn cứ Bộ luật Dân sự năm 2015;
Căn cứ Luật Nhà ở năm 2014;
Căn cứ vào nhu cầu và thỏa thuận của các bên;

Hôm nay, ngày ... tháng ... năm 20..., tại ...

BÊN CHO THUÊ (BÊN A):
Ông/Bà: .................................................
CMND/CCCD số: ..................... cấp ngày: ............ tại: ..............
Địa chỉ thường trú: .....................................
Điện thoại: .............................................

BÊN THUÊ (BÊN B):
Ông/Bà: .................................................
CMND/CCCD số: ..................... cấp ngày: ............ tại: ..............
Địa chỉ thường trú: .....................................
Điện thoại: .............................................

Hai bên thỏa thuận ký kết hợp đồng thuê nhà với các điều khoản sau:

ĐIỀU 1. ĐỐI TƯỢNG THUÊ
1.1. Bên A đồng ý cho Bên B thuê và Bên B đồng ý thuê ngôi nhà/căn hộ tại địa chỉ: .......................
1.2. Diện tích: ........... m²
1.3. Kết cấu/Số phòng: ...................................
1.4. Tình trạng nhà khi giao: .............................
1.5. Mục đích sử dụng: Để ở / Làm văn phòng / ............

ĐIỀU 2. THỜI HẠN THUÊ
2.1. Thời hạn thuê: ........... tháng/năm
2.2. Từ ngày: ....../....../20..... đến ngày: ....../....../20.....
2.3. Khi hết hạn hợp đồng, nếu Bên B có nhu cầu tiếp tục thuê và Bên A đồng ý thì hai bên sẽ ký hợp đồng mới.

ĐIỀU 3. GIÁ THUÊ VÀ PHƯƠNG THỨC THANH TOÁN
3.1. Giá thuê: ......................... đồng/tháng
(Bằng chữ: ...............................................)
3.2. Giá thuê trên chưa bao gồm: tiền điện, nước, internet, phí quản lý (nếu có).
3.3. Phương thức thanh toán: Thanh toán vào ngày ...... hàng tháng
3.4. Hình thức: Tiền mặt / Chuyển khoản
Số tài khoản: ....................... Ngân hàng: .....................

ĐIỀU 4. TIỀN ĐẶT CỌC
4.1. Tiền đặt cọc: ......................... đồng (tương đương ...... tháng tiền thuê)
4.2. Bên B đã giao số tiền đặt cọc trên cho Bên A vào ngày ký hợp đồng.
4.3. Tiền đặt cọc được hoàn trả khi kết thúc hợp đồng nếu Bên B không vi phạm các điều khoản và bàn giao nhà nguyên trạng.

ĐIỀU 5. CÁC CHI PHÍ KHÁC
5.1. Tiền điện: Bên B thanh toán theo đồng hồ, giá: ......... đồng/kWh hoặc theo giá điện lực
5.2. Tiền nước: Bên B thanh toán theo đồng hồ, giá: ......... đồng/m³
5.3. Internet/Truyền hình: Bên B tự đăng ký và thanh toán
5.4. Phí quản lý/dịch vụ (nếu có): ......... đồng/tháng

ĐIỀU 6. QUYỀN VÀ NGHĨA VỤ CỦA BÊN A
6.1. Quyền của Bên A:
- Nhận tiền thuê nhà đúng hạn;
- Kiểm tra định kỳ tình trạng nhà (có thông báo trước);
- Yêu cầu Bên B bồi thường thiệt hại nếu làm hư hỏng tài sản.
6.2. Nghĩa vụ của Bên A:
- Giao nhà đúng hiện trạng và thời hạn thỏa thuận;
- Bảo đảm quyền sử dụng nhà ổn định cho Bên B;
- Sửa chữa những hư hỏng không do lỗi của Bên B.

ĐIỀU 7. QUYỀN VÀ NGHĨA VỤ CỦA BÊN B
7.1. Quyền của Bên B:
- Sử dụng nhà đúng mục đích;
- Yêu cầu Bên A sửa chữa những hư hỏng không do lỗi của mình.
7.2. Nghĩa vụ của Bên B:
- Trả tiền thuê đầy đủ, đúng hạn;
- Sử dụng nhà đúng mục đích, giữ gìn vệ sinh, an ninh trật tự;
- Không được cho thuê lại, chuyển nhượng nếu không có sự đồng ý của Bên A;
- Không được tự ý sửa chữa, cải tạo nhà khi chưa có sự đồng ý của Bên A;
- Bàn giao nhà nguyên trạng khi kết thúc hợp đồng.

ĐIỀU 8. CHẤM DỨT HỢP ĐỒNG
8.1. Bên nào muốn chấm dứt hợp đồng trước hạn phải thông báo cho bên kia ít nhất 30 ngày.
8.2. Trường hợp Bên B chấm dứt trước hạn không thông báo, Bên B mất tiền đặt cọc.
8.3. Trường hợp Bên A chấm dứt trước hạn không thông báo, Bên A hoàn trả tiền đặt cọc và bồi thường thiệt hại cho Bên B.

ĐIỀU 9. ĐIỀU KHOẢN CHUNG
9.1. Hợp đồng có hiệu lực từ ngày ký.
9.2. Tranh chấp được giải quyết bằng thương lượng, hòa giải, hoặc Tòa án có thẩm quyền.
9.3. Hợp đồng được lập thành 02 bản, mỗi bên giữ 01 bản có giá trị pháp lý như nhau.

BÊN CHO THUÊ (BÊN A)                   BÊN THUÊ (BÊN B)
(Ký, ghi rõ họ tên)                    (Ký, ghi rõ họ tên)""",

        "hop-dong-lao-dong-mau": """HỢP ĐỒNG LAO ĐỘNG
(Loại hợp đồng: Xác định thời hạn / Không xác định thời hạn)

Căn cứ Bộ luật Lao động năm 2019;
Căn cứ vào nhu cầu sử dụng lao động và khả năng làm việc của người lao động;

Hôm nay, ngày ... tháng ... năm 20..., tại ...

Chúng tôi gồm:

BÊN SỬ DỤNG LAO ĐỘNG (BÊN A):
Tên đơn vị: ..............................................
Địa chỉ: ................................................
Mã số thuế: .............................................
Điện thoại: .............................................
Đại diện bởi Ông/Bà: ....................................
Chức vụ: ................................................

NGƯỜI LAO ĐỘNG (BÊN B):
Ông/Bà: .................................................
Sinh ngày: ..............................................
CMND/CCCD số: ..................... cấp ngày: ............ tại: ..............
Địa chỉ thường trú: .....................................
Trình độ: ...............................................
Điện thoại: .............................................

Hai bên thỏa thuận ký kết hợp đồng lao động với các điều khoản sau:

ĐIỀU 1. CÔNG VIỆC VÀ ĐỊA ĐIỂM LÀM VIỆC
1.1. Chức danh/Vị trí: ...................................
1.2. Công việc chính: ....................................
1.3. Địa điểm làm việc: ..................................
1.4. Bên B cam kết thực hiện đúng công việc được giao theo nội quy và quy định của Bên A.

ĐIỀU 2. THỜI HẠN HỢP ĐỒNG
2.1. Loại hợp đồng: Xác định thời hạn ...... tháng / Không xác định thời hạn
2.2. Từ ngày: ....../....../20..... đến ngày: ....../....../20.....
2.3. Thời gian thử việc: ........ ngày/tháng (nếu có)

ĐIỀU 3. THỜI GIỜ LÀM VIỆC VÀ NGHỈ NGƠI
3.1. Thời giờ làm việc: ........ giờ/ngày, ........ ngày/tuần
3.2. Ngày nghỉ hàng tuần: Thứ ........
3.3. Nghỉ phép năm: 12 ngày/năm (theo Điều 113 Bộ luật Lao động 2019)
3.4. Nghỉ lễ, tết theo quy định của pháp luật

ĐIỀU 4. TIỀN LƯƠNG VÀ PHỤ CẤP
4.1. Lương cơ bản: ......................... đồng/tháng
4.2. Lương thử việc: ......................... đồng/tháng (bằng 85% lương cơ bản)
4.3. Phụ cấp (nếu có):
- Phụ cấp ăn trưa: ............. đồng/tháng
- Phụ cấp đi lại: ............. đồng/tháng
- Phụ cấp khác: ............... đồng/tháng
4.4. Ngày trả lương: Ngày ...... hàng tháng
4.5. Hình thức trả lương: Tiền mặt / Chuyển khoản

ĐIỀU 5. CHẾ ĐỘ NÂNG LƯƠNG, THƯỞNG
5.1. Chế độ nâng lương: Theo quy chế của Bên A
5.2. Thưởng: Theo kết quả kinh doanh và đóng góp của Bên B

ĐIỀU 6. BẢO HIỂM XÃ HỘI, BẢO HIỂM Y TẾ, BẢO HIỂM THẤT NGHIỆP
6.1. Bên A có trách nhiệm đóng bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp cho Bên B theo quy định của pháp luật.
6.2. Tỷ lệ đóng theo quy định hiện hành:
- BHXH: Bên A đóng .....%, Bên B đóng .....%
- BHYT: Bên A đóng .....%, Bên B đóng .....%
- BHTN: Bên A đóng .....%, Bên B đóng .....%

ĐIỀU 7. QUYỀN VÀ NGHĨA VỤ CỦA BÊN A
7.1. Quyền của Bên A:
- Điều hành, phân công công việc cho Bên B;
- Khen thưởng, xử lý kỷ luật theo nội quy lao động.
7.2. Nghĩa vụ của Bên A:
- Bảo đảm việc làm, điều kiện làm việc cho Bên B;
- Trả lương đầy đủ, đúng hạn;
- Đóng bảo hiểm cho Bên B theo quy định;
- Thực hiện các quyền lợi khác theo quy định pháp luật.

ĐIỀU 8. QUYỀN VÀ NGHĨA VỤ CỦA BÊN B
8.1. Quyền của Bên B:
- Được hưởng lương, phụ cấp và các chế độ theo hợp đồng;
- Được trang bị phương tiện, điều kiện làm việc;
- Được nghỉ phép, nghỉ lễ theo quy định.
8.2. Nghĩa vụ của Bên B:
- Hoàn thành công việc được giao;
- Chấp hành nội quy, quy định của Bên A;
- Bảo vệ bí mật kinh doanh của Bên A.

ĐIỀU 9. CHẤM DỨT HỢP ĐỒNG
9.1. Hợp đồng chấm dứt theo Điều 34 Bộ luật Lao động 2019.
9.2. Bên B muốn đơn phương chấm dứt hợp đồng phải báo trước:
- 45 ngày đối với hợp đồng không xác định thời hạn
- 30 ngày đối với hợp đồng xác định thời hạn từ 12-36 tháng
- 03 ngày đối với hợp đồng dưới 12 tháng

ĐIỀU 10. ĐIỀU KHOẢN CHUNG
10.1. Hợp đồng có hiệu lực từ ngày ký.
10.2. Những nội dung không quy định trong hợp đồng này được áp dụng theo Bộ luật Lao động và nội quy lao động của Bên A.
10.3. Hợp đồng được lập thành 02 bản, mỗi bên giữ 01 bản có giá trị pháp lý như nhau.

BÊN SỬ DỤNG LAO ĐỘNG (BÊN A)           NGƯỜI LAO ĐỘNG (BÊN B)
(Ký, đóng dấu)                          (Ký, ghi rõ họ tên)""",

        "giay-uy-quyen-mau": """GIẤY ỦY QUYỀN

Căn cứ Bộ luật Dân sự năm 2015;

Hôm nay, ngày ... tháng ... năm 20..., tại ...

BÊN ỦY QUYỀN (BÊN A):
Ông/Bà: .................................................
Sinh ngày: ..............................................
CMND/CCCD số: ..................... cấp ngày: ............ tại: ..............
Hộ khẩu thường trú: .....................................
Chỗ ở hiện tại: .........................................
Điện thoại: .............................................

BÊN ĐƯỢC ỦY QUYỀN (BÊN B):
Ông/Bà: .................................................
Sinh ngày: ..............................................
CMND/CCCD số: ..................... cấp ngày: ............ tại: ..............
Hộ khẩu thường trú: .....................................
Chỗ ở hiện tại: .........................................
Điện thoại: .............................................
Quan hệ với Bên A: ......................................

NỘI DUNG ỦY QUYỀN

ĐIỀU 1. PHẠM VI ỦY QUYỀN
Bên A ủy quyền cho Bên B thay mặt và nhân danh Bên A thực hiện các công việc sau:
.........................................................
.........................................................
.........................................................

ĐIỀU 2. THỜI HẠN ỦY QUYỀN
2.1. Giấy ủy quyền này có hiệu lực từ ngày ký đến ngày: ....../....../20.....
2.2. Hoặc: Cho đến khi hoàn thành công việc được ủy quyền.

ĐIỀU 3. QUYỀN VÀ NGHĨA VỤ CỦA BÊN A
3.1. Chịu trách nhiệm về các hành vi do Bên B thực hiện trong phạm vi ủy quyền.
3.2. Cung cấp các giấy tờ, tài liệu cần thiết cho Bên B thực hiện công việc ủy quyền.
3.3. Có quyền chấm dứt ủy quyền trước thời hạn và phải thông báo cho Bên B biết.

ĐIỀU 4. QUYỀN VÀ NGHĨA VỤ CỦA BÊN B
4.1. Thực hiện công việc trong phạm vi được ủy quyền.
4.2. Không được ủy quyền lại cho người khác nếu không có sự đồng ý bằng văn bản của Bên A.
4.3. Báo cho Bên A về kết quả thực hiện công việc ủy quyền.
4.4. Bàn giao lại các giấy tờ, tài liệu đã nhận sau khi hoàn thành công việc.

ĐIỀU 5. THÙ LAO ỦY QUYỀN (nếu có)
5.1. Bên A trả cho Bên B số tiền: ......................... đồng
5.2. Thời điểm thanh toán: ................................

ĐIỀU 6. CAM KẾT
6.1. Bên A cam kết các thông tin cung cấp là chính xác và chịu trách nhiệm trước pháp luật về tính hợp pháp của việc ủy quyền.
6.2. Bên B cam kết thực hiện đúng nội dung và phạm vi ủy quyền.
6.3. Hai bên cam kết thực hiện đúng các điều khoản của Giấy ủy quyền này.

ĐIỀU 7. ĐIỀU KHOẢN CHUNG
7.1. Giấy ủy quyền này có hiệu lực từ ngày ký.
7.2. Giấy ủy quyền được lập thành 02 bản có giá trị pháp lý như nhau, mỗi bên giữ 01 bản.

BÊN ỦY QUYỀN (BÊN A)                   BÊN ĐƯỢC ỦY QUYỀN (BÊN B)
(Ký, ghi rõ họ tên)                    (Ký, ghi rõ họ tên)

XÁC NHẬN CỦA CƠ QUAN CÓ THẨM QUYỀN (nếu cần):
(Ký, đóng dấu)"""
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for filename, content in templates.items():
        filepath = output_dir / f"{filename}.txt"
        # Only create if doesn't exist or is invalid
        if not filepath.exists() or filepath.stat().st_size < 500:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            logger.info(f"Created sample template: {filename}.txt")
            count += 1

    return count


def main():
    """Main entry point for LuatVietnam crawler."""
    logger.info("Starting LuatVietnam crawler with Cloudflare bypass")
    logger.info(f"Target: {BIEU_MAU_URL}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize Cloudflare bypass
    bypass = CloudflareBypass()

    success_count = 0
    fail_count = 0

    try:
        # Download predefined target templates
        logger.info(f"Downloading {len(TARGET_TEMPLATES)} templates...")

        for url, slug in TARGET_TEMPLATES:
            if download_template(bypass, url, slug, OUTPUT_DIR):
                success_count += 1
            else:
                fail_count += 1

            # Polite delay between requests
            time.sleep(3)

    finally:
        bypass.close()

    # Create sample templates as backup for failed downloads
    sample_count = create_sample_templates(OUTPUT_DIR)
    success_count += sample_count

    logger.info("=" * 50)
    logger.info(f"Crawling complete!")
    logger.info(f"Successfully downloaded: {success_count - sample_count}")
    logger.info(f"Failed: {fail_count}")
    logger.info(f"Sample templates created: {sample_count}")
    logger.info(f"Templates saved to: {OUTPUT_DIR}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
