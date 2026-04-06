#!/usr/bin/env python3
"""
MOJ Crawler - Fetches official templates, contracts, and forms from Ministry of Justice websites.

Sources:
- htpldn.moj.gov.vn: Enterprise legal support portal
- dichvucong.moj.gov.vn: Public services portal
"""

import os
import re
import time
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
HTPLDN_BASE_URL = "https://htpldn.moj.gov.vn"
DICHVUCONG_BASE_URL = "https://dichvucong.moj.gov.vn"

# Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Known form/template pages from htpldn.moj.gov.vn
# These are sample contract templates and legal forms
HTPLDN_TEMPLATE_PAGES = [
    # Sample contract pages - these are typical paths for legal templates
    "/Pages/ho-tro-phap-ly/bieu-mau.aspx",
    "/Pages/bieu-mau-hop-dong.aspx",
    "/tin-tuc/bieu-mau-van-ban",
]

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "raw" / "moj"


def create_session() -> requests.Session:
    """Create a requests session with appropriate headers."""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def fetch_page(session: requests.Session, url: str, max_retries: int = 3) -> Optional[str]:
    """
    Fetch a page with retry logic.

    Args:
        session: Requests session object
        url: URL to fetch
        max_retries: Maximum number of retry attempts

    Returns:
        HTML content as string, or None if fetch failed
    """
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=30, verify=True)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text from a PDF file.

    TODO: Implement PDF text extraction using PyMuPDF or pdfplumber.
    For MVP, this is a stub that returns a placeholder.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text (placeholder for now)
    """
    # TODO: Install and use PyMuPDF (fitz) or pdfplumber for PDF extraction
    # Example implementation:
    # import fitz  # PyMuPDF
    # doc = fitz.open(pdf_path)
    # text = ""
    # for page in doc:
    #     text += page.get_text()
    # return text
    logger.warning(f"PDF extraction not implemented. File: {pdf_path}")
    return f"[PDF content from {pdf_path.name} - extraction not implemented]"


def extract_text_from_docx(docx_path: Path) -> str:
    """
    Extract text from a DOCX file.

    TODO: Implement DOCX text extraction using python-docx.
    For MVP, this is a stub that returns a placeholder.

    Args:
        docx_path: Path to DOCX file

    Returns:
        Extracted text (placeholder for now)
    """
    # TODO: Install and use python-docx for DOCX extraction
    # Example implementation:
    # from docx import Document
    # doc = Document(docx_path)
    # text = "\n".join([para.text for para in doc.paragraphs])
    # return text
    logger.warning(f"DOCX extraction not implemented. File: {docx_path}")
    return f"[DOCX content from {docx_path.name} - extraction not implemented]"


def download_file(session: requests.Session, url: str, output_path: Path) -> bool:
    """
    Download a file (PDF/DOC/DOCX) to disk.

    Args:
        session: Requests session
        url: URL of the file
        output_path: Path to save the file

    Returns:
        True if successful, False otherwise
    """
    try:
        response = session.get(url, timeout=60, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded file to {output_path}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def extract_content_from_html(html: str) -> str:
    """
    Extract main content from MOJ HTML page.

    Args:
        html: Raw HTML content

    Returns:
        Extracted text content
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Remove unwanted elements
    for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        element.decompose()

    # Try multiple content selectors
    content_selectors = [
        {'class': 'content-detail'},
        {'class': 'article-content'},
        {'class': 'post-content'},
        {'class': 'main-content'},
        {'id': 'content'},
        {'class': 'news-detail'},
        {'class': 'detail-content'},
    ]

    content_div = None
    for selector in content_selectors:
        content_div = soup.find('div', selector)
        if content_div:
            break

    # Try article tag
    if not content_div:
        content_div = soup.find('article')

    # Fallback to main or body
    if not content_div:
        content_div = soup.find('main') or soup.find('body')

    if content_div:
        text = content_div.get_text(separator='\n', strip=True)
        return text

    return ""


def slugify(text: str) -> str:
    """
    Create a safe filename slug from text.

    Args:
        text: Input text

    Returns:
        URL-safe slug string
    """
    # Remove Vietnamese diacritics for filename safety
    text = text.lower()
    text = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', text)
    text = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', text)
    text = re.sub(r'[ìíịỉĩ]', 'i', text)
    text = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', text)
    text = re.sub(r'[ùúụủũưừứựửữ]', 'u', text)
    text = re.sub(r'[ỳýỵỷỹ]', 'y', text)
    text = re.sub(r'đ', 'd', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text[:80] if text else 'untitled'


def find_template_links(soup: BeautifulSoup, base_url: str) -> List[Tuple[str, str]]:
    """
    Find links to templates/forms in the page.

    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative links

    Returns:
        List of (url, title) tuples
    """
    links = []

    # Look for links containing keywords related to templates/contracts
    keywords = [
        'mẫu', 'biểu mẫu', 'hợp đồng', 'đơn', 'tờ khai',
        'mau', 'bieu-mau', 'hop-dong', 'don', 'to-khai'
    ]

    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.get_text(strip=True)

        # Check if link text or href contains relevant keywords
        text_lower = text.lower()
        href_lower = href.lower()

        is_relevant = any(kw in text_lower or kw in href_lower for kw in keywords)

        if is_relevant and text:
            full_url = urljoin(base_url, href)
            # Skip non-http links and anchors
            if full_url.startswith('http') and '#' not in full_url:
                links.append((full_url, text))

    return links


def crawl_htpldn(session: requests.Session, output_dir: Path) -> int:
    """
    Crawl htpldn.moj.gov.vn for legal templates.

    Args:
        session: Requests session
        output_dir: Output directory

    Returns:
        Number of documents collected
    """
    logger.info("Crawling htpldn.moj.gov.vn")
    count = 0

    # Try to access main page and find template sections
    main_url = HTPLDN_BASE_URL
    html = fetch_page(session, main_url)

    if not html:
        logger.warning("Could not access htpldn.moj.gov.vn main page")
        return count

    soup = BeautifulSoup(html, 'html.parser')
    template_links = find_template_links(soup, main_url)

    logger.info(f"Found {len(template_links)} potential template links")

    # Process each template link
    for url, title in template_links[:15]:  # Limit to 15 for MVP
        logger.info(f"Processing: {title}")

        # Check file type
        url_lower = url.lower()

        if url_lower.endswith('.pdf'):
            # Download PDF
            slug = slugify(title)
            pdf_path = output_dir / f"{slug}.pdf"
            if download_file(session, url, pdf_path):
                # Extract text (stub)
                text = extract_text_from_pdf(pdf_path)
                if text:
                    txt_path = output_dir / f"{slug}.txt"
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    count += 1

        elif url_lower.endswith('.doc') or url_lower.endswith('.docx'):
            # Download DOC/DOCX
            slug = slugify(title)
            ext = '.docx' if url_lower.endswith('.docx') else '.doc'
            doc_path = output_dir / f"{slug}{ext}"
            if download_file(session, url, doc_path):
                # Extract text (stub)
                text = extract_text_from_docx(doc_path)
                if text:
                    txt_path = output_dir / f"{slug}.txt"
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    count += 1

        else:
            # Assume HTML page - fetch and extract content
            page_html = fetch_page(session, url)
            if page_html:
                content = extract_content_from_html(page_html)
                if content and len(content) > 100:
                    slug = slugify(title)
                    txt_path = output_dir / f"{slug}.txt"
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    count += 1
                    logger.info(f"Saved: {slug}.txt ({len(content)} chars)")

        time.sleep(1)

    return count


def crawl_dichvucong(session: requests.Session, output_dir: Path) -> int:
    """
    Crawl dichvucong.moj.gov.vn for public service forms.

    Args:
        session: Requests session
        output_dir: Output directory

    Returns:
        Number of documents collected
    """
    logger.info("Crawling dichvucong.moj.gov.vn")
    count = 0

    # Main public services portal
    main_url = DICHVUCONG_BASE_URL
    html = fetch_page(session, main_url)

    if not html:
        logger.warning("Could not access dichvucong.moj.gov.vn")
        return count

    soup = BeautifulSoup(html, 'html.parser')

    # Look for service categories and form links
    template_links = find_template_links(soup, main_url)

    logger.info(f"Found {len(template_links)} potential form links")

    # Process each link
    for url, title in template_links[:10]:  # Limit for MVP
        logger.info(f"Processing: {title}")

        page_html = fetch_page(session, url)
        if page_html:
            content = extract_content_from_html(page_html)
            if content and len(content) > 100:
                slug = slugify(title)
                txt_path = output_dir / f"dvc-{slug}.txt"
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                count += 1
                logger.info(f"Saved: dvc-{slug}.txt ({len(content)} chars)")

        time.sleep(1)

    return count


def create_sample_contract_templates(output_dir: Path) -> int:
    """
    Create sample contract template files based on common Vietnamese legal formats.
    These serve as baseline examples when actual crawling yields limited results.

    Args:
        output_dir: Output directory

    Returns:
        Number of templates created
    """
    # Sample contract templates in Vietnamese
    templates = {
        "hop-dong-lao-dong-mau": """
HỢP ĐỒNG LAO ĐỘNG
(Mẫu tham khảo)

Căn cứ Bộ luật Lao động năm 2019;
Căn cứ nhu cầu và khả năng của các bên;

Hôm nay, ngày ... tháng ... năm ..., tại ...

Chúng tôi gồm:

BÊN A (NGƯỜI SỬ DỤNG LAO ĐỘNG):
Tên công ty/tổ chức: ...
Địa chỉ: ...
Điện thoại: ...
Mã số thuế: ...
Đại diện bởi: ... Chức vụ: ...

BÊN B (NGƯỜI LAO ĐỘNG):
Họ và tên: ...
Sinh ngày: ...
Số CMND/CCCD: ... Ngày cấp: ... Nơi cấp: ...
Địa chỉ thường trú: ...
Điện thoại: ...

Hai bên thỏa thuận ký kết hợp đồng lao động với các điều khoản sau:

Điều 1. Công việc và địa điểm làm việc
1.1. Loại hợp đồng: Hợp đồng lao động xác định thời hạn/không xác định thời hạn
1.2. Chức danh: ...
1.3. Công việc phải làm: ...
1.4. Địa điểm làm việc: ...

Điều 2. Thời hạn hợp đồng
2.1. Thời hạn hợp đồng: ... tháng
2.2. Từ ngày: ... đến ngày: ...

Điều 3. Tiền lương và phụ cấp
3.1. Mức lương cơ bản: ... đồng/tháng
3.2. Phụ cấp (nếu có): ...
3.3. Hình thức trả lương: Tiền mặt/Chuyển khoản
3.4. Thời điểm trả lương: Ngày ... hàng tháng

Điều 4. Thời giờ làm việc, nghỉ ngơi
4.1. Thời giờ làm việc: ... giờ/ngày, ... ngày/tuần
4.2. Nghỉ hàng tuần: ...
4.3. Nghỉ phép năm: ... ngày/năm

Điều 5. Bảo hiểm xã hội, bảo hiểm y tế
Bên A có trách nhiệm đóng bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp cho Bên B theo quy định của pháp luật.

Điều 6. Quyền và nghĩa vụ của các bên
6.1. Quyền và nghĩa vụ của Bên A: Theo quy định tại Điều 6 Bộ luật Lao động
6.2. Quyền và nghĩa vụ của Bên B: Theo quy định tại Điều 5 Bộ luật Lao động

Điều 7. Điều khoản thi hành
7.1. Hợp đồng có hiệu lực kể từ ngày ký.
7.2. Hợp đồng được lập thành 02 bản có giá trị pháp lý như nhau, mỗi bên giữ 01 bản.

BÊN A                                    BÊN B
(Ký, ghi rõ họ tên, đóng dấu)           (Ký, ghi rõ họ tên)
""",

        "hop-dong-vay-tien-mau": """
HỢP ĐỒNG VAY TIỀN
(Mẫu tham khảo)

Căn cứ Bộ luật Dân sự năm 2015;
Căn cứ thỏa thuận của các bên;

Hôm nay, ngày ... tháng ... năm ..., tại ...

Chúng tôi gồm:

BÊN CHO VAY (BÊN A):
Họ và tên: ...
Sinh ngày: ...
Số CMND/CCCD: ... Ngày cấp: ... Nơi cấp: ...
Địa chỉ: ...
Điện thoại: ...

BÊN VAY (BÊN B):
Họ và tên: ...
Sinh ngày: ...
Số CMND/CCCD: ... Ngày cấp: ... Nơi cấp: ...
Địa chỉ: ...
Điện thoại: ...

Hai bên cùng thỏa thuận ký kết hợp đồng vay tiền với các điều khoản sau:

Điều 1. Số tiền vay
1.1. Số tiền vay: ... đồng (Bằng chữ: ...)
1.2. Bên A đã giao đủ số tiền nêu trên cho Bên B vào ngày ký hợp đồng này.

Điều 2. Mục đích vay
Bên B vay tiền để: ...

Điều 3. Thời hạn vay
3.1. Thời hạn vay: ... tháng
3.2. Từ ngày: ... đến ngày: ...

Điều 4. Lãi suất
4.1. Lãi suất: ...%/năm (hoặc ...%/tháng)
4.2. Phương thức tính lãi: ...

Điều 5. Phương thức trả nợ
5.1. Bên B trả gốc và lãi theo phương thức: ...
5.2. Thời điểm trả: ...

Điều 6. Quyền và nghĩa vụ của các bên
6.1. Quyền và nghĩa vụ của Bên A:
- Yêu cầu Bên B trả đủ gốc và lãi đúng hạn
- Không được đòi lại tiền trước thời hạn trừ trường hợp quy định tại Điều 470 BLDS

6.2. Quyền và nghĩa vụ của Bên B:
- Sử dụng tiền vay đúng mục đích
- Trả đủ gốc và lãi đúng hạn
- Chịu trách nhiệm nếu vi phạm nghĩa vụ trả nợ

Điều 7. Xử lý vi phạm
Nếu Bên B không trả nợ đúng hạn, Bên B phải chịu lãi suất chậm trả theo quy định của pháp luật.

Điều 8. Điều khoản chung
8.1. Hợp đồng có hiệu lực kể từ ngày ký.
8.2. Mọi tranh chấp phát sinh được giải quyết bằng thương lượng, nếu không thành sẽ đưa ra Tòa án có thẩm quyền.
8.3. Hợp đồng được lập thành 02 bản, mỗi bên giữ 01 bản.

BÊN A                                    BÊN B
(Ký, ghi rõ họ tên)                     (Ký, ghi rõ họ tên)
""",

        "hop-dong-thue-nha-mau": """
HỢP ĐỒNG THUÊ NHÀ Ở
(Mẫu tham khảo)

Căn cứ Bộ luật Dân sự năm 2015;
Căn cứ Luật Nhà ở năm 2023;

Hôm nay, ngày ... tháng ... năm ..., tại ...

BÊN CHO THUÊ (BÊN A):
Họ và tên: ...
Số CMND/CCCD: ... Ngày cấp: ... Nơi cấp: ...
Địa chỉ thường trú: ...
Điện thoại: ...

BÊN THUÊ (BÊN B):
Họ và tên: ...
Số CMND/CCCD: ... Ngày cấp: ... Nơi cấp: ...
Địa chỉ thường trú: ...
Điện thoại: ...

Hai bên thỏa thuận ký kết hợp đồng thuê nhà với nội dung sau:

Điều 1. Đối tượng thuê
1.1. Bên A đồng ý cho Bên B thuê nhà tại địa chỉ: ...
1.2. Diện tích: ... m2
1.3. Tình trạng nhà: ...

Điều 2. Thời hạn thuê
2.1. Thời hạn thuê: ... tháng/năm
2.2. Từ ngày: ... đến ngày: ...

Điều 3. Giá thuê và phương thức thanh toán
3.1. Giá thuê: ... đồng/tháng
3.2. Phương thức thanh toán: Tiền mặt/Chuyển khoản
3.3. Thời điểm thanh toán: Ngày ... hàng tháng
3.4. Tiền đặt cọc: ... đồng (tương đương ... tháng tiền thuê)

Điều 4. Các chi phí khác
4.1. Tiền điện: Bên B thanh toán theo số điện thực tế sử dụng
4.2. Tiền nước: Bên B thanh toán theo số nước thực tế sử dụng
4.3. Các chi phí khác: ...

Điều 5. Quyền và nghĩa vụ của Bên A
5.1. Giao nhà đúng thời hạn, đúng hiện trạng đã thỏa thuận
5.2. Bảo đảm quyền sử dụng nhà ổn định cho Bên B
5.3. Sửa chữa những hư hỏng lớn không do lỗi của Bên B
5.4. Hoàn trả tiền đặt cọc khi kết thúc hợp đồng (nếu không có thiệt hại)

Điều 6. Quyền và nghĩa vụ của Bên B
6.1. Sử dụng nhà đúng mục đích đã thỏa thuận
6.2. Trả tiền thuê đầy đủ, đúng hạn
6.3. Bảo quản tài sản, không tự ý sửa chữa, cải tạo
6.4. Trả lại nhà đúng thời hạn và đúng hiện trạng

Điều 7. Chấm dứt hợp đồng
7.1. Hết thời hạn thuê
7.2. Hai bên thỏa thuận chấm dứt trước hạn
7.3. Bên vi phạm nghĩa vụ theo quy định pháp luật

Điều 8. Điều khoản chung
8.1. Hợp đồng có hiệu lực từ ngày ký.
8.2. Mọi sửa đổi, bổ sung phải được lập thành văn bản.
8.3. Hợp đồng được lập thành 02 bản, mỗi bên giữ 01 bản.

BÊN A                                    BÊN B
(Ký, ghi rõ họ tên)                     (Ký, ghi rõ họ tên)
""",

        "hop-dong-mua-ban-tai-san-mau": """
HỢP ĐỒNG MUA BÁN TÀI SẢN
(Mẫu tham khảo)

Căn cứ Bộ luật Dân sự năm 2015;

Hôm nay, ngày ... tháng ... năm ..., tại ...

BÊN BÁN (BÊN A):
Họ và tên: ...
Số CMND/CCCD: ... Ngày cấp: ... Nơi cấp: ...
Địa chỉ: ...
Điện thoại: ...

BÊN MUA (BÊN B):
Họ và tên: ...
Số CMND/CCCD: ... Ngày cấp: ... Nơi cấp: ...
Địa chỉ: ...
Điện thoại: ...

Hai bên thỏa thuận ký kết hợp đồng mua bán tài sản với nội dung sau:

Điều 1. Tài sản mua bán
1.1. Loại tài sản: ...
1.2. Đặc điểm: ...
1.3. Số lượng: ...
1.4. Tình trạng: ...

Điều 2. Giá bán và phương thức thanh toán
2.1. Giá bán: ... đồng (Bằng chữ: ...)
2.2. Phương thức thanh toán: Tiền mặt/Chuyển khoản
2.3. Thời điểm thanh toán:
- Đặt cọc: ... đồng vào ngày ký hợp đồng
- Thanh toán còn lại: ... đồng khi giao tài sản

Điều 3. Giao nhận tài sản
3.1. Thời điểm giao tài sản: ...
3.2. Địa điểm giao tài sản: ...
3.3. Chi phí vận chuyển: Bên ... chịu

Điều 4. Chuyển quyền sở hữu
Quyền sở hữu tài sản được chuyển cho Bên B kể từ thời điểm Bên B nhận tài sản, trừ trường hợp các bên có thỏa thuận khác.

Điều 5. Bảo hành (nếu có)
5.1. Thời hạn bảo hành: ...
5.2. Điều kiện bảo hành: ...

Điều 6. Quyền và nghĩa vụ của Bên A
6.1. Giao tài sản đúng chủng loại, số lượng, chất lượng
6.2. Cung cấp thông tin cần thiết về tài sản
6.3. Bảo đảm quyền sở hữu hợp pháp đối với tài sản

Điều 7. Quyền và nghĩa vụ của Bên B
7.1. Thanh toán đầy đủ, đúng hạn
7.2. Nhận tài sản theo thỏa thuận
7.3. Chịu rủi ro đối với tài sản kể từ thời điểm nhận tài sản

Điều 8. Phạt vi phạm
Bên vi phạm nghĩa vụ phải bồi thường thiệt hại cho bên bị vi phạm theo quy định của pháp luật.

Điều 9. Điều khoản chung
9.1. Hợp đồng có hiệu lực từ ngày ký.
9.2. Tranh chấp được giải quyết bằng thương lượng, hòa giải, hoặc Tòa án.
9.3. Hợp đồng được lập thành 02 bản, mỗi bên giữ 01 bản.

BÊN A                                    BÊN B
(Ký, ghi rõ họ tên)                     (Ký, ghi rõ họ tên)
""",

        "giay-uy-quyen-mau": """
GIẤY ỦY QUYỀN
(Mẫu tham khảo)

Căn cứ Bộ luật Dân sự năm 2015;

Hôm nay, ngày ... tháng ... năm ..., tại ...

BÊN ỦY QUYỀN (BÊN A):
Họ và tên: ...
Sinh ngày: ...
Số CMND/CCCD: ... Ngày cấp: ... Nơi cấp: ...
Địa chỉ thường trú: ...
Điện thoại: ...

BÊN ĐƯỢC ỦY QUYỀN (BÊN B):
Họ và tên: ...
Sinh ngày: ...
Số CMND/CCCD: ... Ngày cấp: ... Nơi cấp: ...
Địa chỉ thường trú: ...
Điện thoại: ...

Bằng văn bản này, Bên A ủy quyền cho Bên B thực hiện các công việc sau:

Điều 1. Nội dung ủy quyền
Bên A ủy quyền cho Bên B thay mặt và nhân danh Bên A thực hiện các công việc sau:
1. ...
2. ...
3. ...

Điều 2. Thời hạn ủy quyền
2.1. Từ ngày: ... đến ngày: ...
2.2. Hoặc cho đến khi hoàn thành công việc được ủy quyền.

Điều 3. Phạm vi ủy quyền
3.1. Bên B chỉ được thực hiện các công việc trong phạm vi được ủy quyền.
3.2. Bên B không được ủy quyền lại cho người thứ ba (trừ khi có sự đồng ý của Bên A).

Điều 4. Quyền và nghĩa vụ của các bên
4.1. Bên A:
- Cung cấp đầy đủ giấy tờ, tài liệu cần thiết
- Chịu trách nhiệm về các công việc do Bên B thực hiện trong phạm vi ủy quyền

4.2. Bên B:
- Thực hiện công việc trong phạm vi ủy quyền
- Báo cáo kết quả thực hiện cho Bên A
- Không được thực hiện các giao dịch vượt quá phạm vi ủy quyền

Điều 5. Chấm dứt ủy quyền
5.1. Hết thời hạn ủy quyền
5.2. Công việc được ủy quyền đã hoàn thành
5.3. Bên A hoặc Bên B hủy bỏ ủy quyền (có thông báo trước)
5.4. Một trong hai bên chết hoặc mất năng lực hành vi dân sự

Điều 6. Điều khoản chung
6.1. Giấy ủy quyền này có hiệu lực kể từ ngày ký.
6.2. Giấy ủy quyền được lập thành 02 bản, mỗi bên giữ 01 bản.

BÊN ỦY QUYỀN (BÊN A)                    BÊN ĐƯỢC ỦY QUYỀN (BÊN B)
(Ký, ghi rõ họ tên)                     (Ký, ghi rõ họ tên)

XÁC NHẬN CỦA CƠ QUAN CÓ THẨM QUYỀN (nếu cần):
"""
    }

    count = 0
    for filename, content in templates.items():
        filepath = output_dir / f"{filename}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        logger.info(f"Created sample template: {filename}.txt")
        count += 1

    return count


def main():
    """Main entry point for MOJ crawler."""
    logger.info("Starting MOJ crawler")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create session
    session = create_session()

    total_count = 0

    # Crawl htpldn.moj.gov.vn
    htpldn_count = crawl_htpldn(session, OUTPUT_DIR)
    total_count += htpldn_count
    logger.info(f"Collected {htpldn_count} documents from htpldn.moj.gov.vn")

    # Crawl dichvucong.moj.gov.vn
    dvc_count = crawl_dichvucong(session, OUTPUT_DIR)
    total_count += dvc_count
    logger.info(f"Collected {dvc_count} documents from dichvucong.moj.gov.vn")

    # Create sample templates as fallback
    # (these serve as reference templates regardless of crawl results)
    sample_count = create_sample_contract_templates(OUTPUT_DIR)
    total_count += sample_count
    logger.info(f"Created {sample_count} sample contract templates")

    logger.info(f"MOJ crawling complete. Total documents: {total_count}")
    logger.info(f"Documents saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
