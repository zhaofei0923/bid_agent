"""Tencent Cloud Document Parser — OCR-based PDF extraction for scanned documents.

Uses Tencent Cloud's intelligent document recognition API to extract text
from scanned/image-based PDF pages that local parsers (pymupdf4llm) cannot handle.

This is a supplementary parser, NOT a replacement for local parsing.
Usage pattern (hybrid):
    1. Local pymupdf4llm parses all pages
    2. Pages with < SCAN_THRESHOLD chars are flagged as scanned
    3. Only those scanned pages are sent to Tencent Cloud for OCR
    4. OCR results are merged back into the full document
"""

import asyncio
import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TencentDocParserError(Exception):
    """Raised when Tencent Cloud document parsing fails."""


class TencentDocParser:
    """Client for Tencent Cloud's intelligent document recognition API.

    Supports:
    - Full-page OCR for scanned PDF pages
    - Table structure recognition
    - Mixed Chinese/English text
    """

    def __init__(self, secret_id: str, secret_key: str, region: str = "ap-guangzhou") -> None:
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        self._client = None

    def _get_client(self):
        """Lazy-init Tencent Cloud OCR client."""
        if self._client is None:
            try:
                from tencentcloud.common import credential
                from tencentcloud.common.profile.client_profile import ClientProfile
                from tencentcloud.common.profile.http_profile import HttpProfile
                from tencentcloud.ocr.v20181119 import ocr_client
            except ImportError as exc:
                raise TencentDocParserError(
                    "tencentcloud-sdk-python-ocr not installed. "
                    "Install with: pip install tencentcloud-sdk-python-ocr"
                ) from exc
            cred = credential.Credential(self.secret_id, self.secret_key)
            http_profile = HttpProfile()
            http_profile.endpoint = "ocr.tencentcloudapi.com"
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            self._client = ocr_client.OcrClient(cred, self.region, client_profile)
        return self._client

    async def ocr_pdf_pages(
        self,
        file_path: str | Path,
        page_numbers: list[int],
        *,
        concurrency: int = 3,
    ) -> dict[int, str]:
        """OCR specific pages of a PDF file.

        Args:
            file_path: Path to the PDF file.
            page_numbers: 1-indexed page numbers to OCR.
            concurrency: Max concurrent API calls.

        Returns:
            Dict mapping page_number → extracted text.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        # Extract individual page images using PyMuPDF
        page_images = await asyncio.to_thread(
            self._extract_page_images, file_path, page_numbers
        )

        # OCR each page with concurrency control
        sem = asyncio.Semaphore(concurrency)
        results: dict[int, str] = {}

        async def _ocr_one(page_num: int, image_bytes: bytes) -> None:
            async with sem:
                try:
                    text = await self._call_ocr_api(image_bytes)
                    results[page_num] = text
                    logger.info(
                        "Tencent OCR page %d: extracted %d chars",
                        page_num, len(text),
                    )
                except Exception:
                    logger.warning(
                        "Tencent OCR failed for page %d", page_num, exc_info=True
                    )
                    results[page_num] = ""

        tasks = [
            _ocr_one(page_num, img_bytes)
            for page_num, img_bytes in page_images.items()
        ]
        await asyncio.gather(*tasks)
        return results

    def _extract_page_images(
        self, file_path: Path, page_numbers: list[int]
    ) -> dict[int, bytes]:
        """Render specific PDF pages to PNG images (sync, runs in thread pool).

        Uses 2x scaling (144 DPI) for better OCR accuracy.
        """
        import fitz  # PyMuPDF

        doc = fitz.open(str(file_path))
        images: dict[int, bytes] = {}

        for page_num in page_numbers:
            if page_num < 1 or page_num > doc.page_count:
                logger.warning("Page %d out of range (1-%d)", page_num, doc.page_count)
                continue
            page = doc.load_page(page_num - 1)  # 0-indexed
            # 2x zoom for better OCR quality
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            images[page_num] = pix.tobytes("png")

        doc.close()
        return images

    async def _call_ocr_api(self, image_bytes: bytes) -> str:
        """Call Tencent Cloud GeneralAccurateOCR API for a single page image.

        Uses the high-accuracy general OCR endpoint which handles:
        - Printed text (Chinese + English mixed)
        - Tables
        - Handwriting (partial)
        """
        from tencentcloud.ocr.v20181119 import models as ocr_models

        client = self._get_client()
        req = ocr_models.GeneralAccurateOCRRequest()
        req.ImageBase64 = base64.b64encode(image_bytes).decode("ascii")
        req.IsWords = False

        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, client.GeneralAccurateOCR, req)

        if not resp.TextDetections:
            return ""

        # Reconstruct text preserving line order
        lines: list[str] = []
        for detection in resp.TextDetections:
            text = detection.DetectedText or ""
            if text.strip():
                lines.append(text.strip())

        return "\n".join(lines)

    async def ocr_table_page(self, image_bytes: bytes) -> str:
        """Call Tencent Cloud TableOCR for a page that contains tables.

        Returns Markdown-formatted table text for better downstream processing.
        """
        from tencentcloud.ocr.v20181119 import models as ocr_models

        client = self._get_client()
        req = ocr_models.RecognizeTableAccurateOCRRequest()
        req.ImageBase64 = base64.b64encode(image_bytes).decode("ascii")

        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(
                None, client.RecognizeTableAccurateOCR, req
            )
        except Exception:
            logger.warning("Table OCR failed, falling back to general OCR", exc_info=True)
            return await self._call_ocr_api(image_bytes)

        if not resp.TableDetections:
            return await self._call_ocr_api(image_bytes)

        # Collect all table cells and non-table text
        parts: list[str] = []
        for table in resp.TableDetections:
            if hasattr(table, "TableHtml") and table.TableHtml:
                # Convert HTML table to simple Markdown
                parts.append(self._html_table_to_markdown(table.TableHtml))
            elif hasattr(table, "Cells") and table.Cells:
                parts.append(self._cells_to_markdown(table.Cells))

        return "\n\n".join(parts) if parts else await self._call_ocr_api(image_bytes)

    @staticmethod
    def _html_table_to_markdown(html: str) -> str:
        """Convert simple HTML table to Markdown table format."""
        import re

        # Extract rows
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE)
        if not rows:
            # Strip all tags as fallback
            return re.sub(r"<[^>]+>", " ", html).strip()

        md_rows: list[str] = []
        for i, row in enumerate(rows):
            cells = re.findall(
                r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE
            )
            cell_texts = [
                re.sub(r"<[^>]+>", "", c).strip().replace("|", "\\|")
                for c in cells
            ]
            md_rows.append("| " + " | ".join(cell_texts) + " |")
            if i == 0:
                md_rows.append("| " + " | ".join("---" for _ in cell_texts) + " |")

        return "\n".join(md_rows)

    @staticmethod
    def _cells_to_markdown(cells: list) -> str:
        """Convert table cells array to Markdown table."""
        if not cells:
            return ""
        # Group cells by row
        row_map: dict[int, dict[int, str]] = {}
        for cell in cells:
            r = getattr(cell, "RowTl", 0)
            c = getattr(cell, "ColTl", 0)
            text = getattr(cell, "Text", "").strip().replace("|", "\\|")
            if r not in row_map:
                row_map[r] = {}
            row_map[r][c] = text

        if not row_map:
            return ""

        max_col = max(c for cols in row_map.values() for c in cols) + 1
        md_rows: list[str] = []
        for i, r in enumerate(sorted(row_map)):
            cols = row_map[r]
            row_cells = [cols.get(c, "") for c in range(max_col)]
            md_rows.append("| " + " | ".join(row_cells) + " |")
            if i == 0:
                md_rows.append("| " + " | ".join("---" for _ in row_cells) + " |")

        return "\n".join(md_rows)


def get_tencent_doc_parser() -> TencentDocParser | None:
    """Factory: return a TencentDocParser if enabled and credentials are configured, else None."""
    from app.config import get_settings

    s = get_settings()
    if not s.TENCENT_OCR_ENABLED:
        return None
    if not s.TENCENT_OCR_SECRET_ID or not s.TENCENT_OCR_SECRET_KEY:
        logger.info("Tencent OCR enabled but credentials missing — scanned pages will be skipped")
        return None
    return TencentDocParser(
        secret_id=s.TENCENT_OCR_SECRET_ID,
        secret_key=s.TENCENT_OCR_SECRET_KEY,
        region=s.TENCENT_OCR_REGION,
    )
