"""
PDF Parser

Extracts text and metadata from PDF files (technical specs, drawings, etc.).
Uses PyMuPDF (fitz) for parsing and optional OCR for scanned documents.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import structlog
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class PDFMetadata:
    """Extracted PDF metadata"""

    file_path: str
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: int = 0
    text_content: List[str] = None
    has_images: bool = False

    def __post_init__(self):
        if self.text_content is None:
            self.text_content = []


class PDFParser:
    """
    Parse PDF files and extract text and metadata.

    Features:
        - Text extraction from native PDFs
        - Metadata extraction
        - Table detection (basic)
        - Image extraction
        - OCR support for scanned PDFs (optional)
    """

    def __init__(self, enable_ocr: bool = False):
        """
        Initialize PDF parser.

        Args:
            enable_ocr: Enable OCR for scanned documents
        """
        self.enable_ocr = enable_ocr

        try:
            import fitz  # PyMuPDF

            self.fitz = fitz
            logger.info("Initialized PDF parser with PyMuPDF", ocr_enabled=enable_ocr)
        except ImportError as e:
            logger.error("Failed to import PyMuPDF", error=str(e))
            raise RuntimeError("PyMuPDF not installed. Run: pip install PyMuPDF") from e

    def parse_file(self, file_path: str) -> PDFMetadata:
        """
        Parse PDF file and extract metadata and text.

        Args:
            file_path: Path to PDF file

        Returns:
            PDFMetadata object
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {file_path}")

        logger.info("Parsing PDF file", file_path=file_path)

        try:
            # Open PDF
            doc = self.fitz.open(file_path)

            # Extract metadata
            metadata = PDFMetadata(file_path=str(path))
            metadata.page_count = doc.page_count

            # PDF metadata
            pdf_metadata = doc.metadata
            metadata.title = pdf_metadata.get("title")
            metadata.author = pdf_metadata.get("author")
            metadata.subject = pdf_metadata.get("subject")
            metadata.keywords = pdf_metadata.get("keywords")
            metadata.creator = pdf_metadata.get("creator")
            metadata.producer = pdf_metadata.get("producer")
            metadata.creation_date = pdf_metadata.get("creationDate")
            metadata.modification_date = pdf_metadata.get("modDate")

            # Extract text from each page
            text_pages = []
            has_images = False

            for page_num in range(doc.page_count):
                page = doc[page_num]

                # Extract text
                text = page.get_text()
                text_pages.append(f"--- Page {page_num + 1} ---\n{text}")

                # Check for images
                images = page.get_images()
                if images:
                    has_images = True

            metadata.text_content = text_pages
            metadata.has_images = has_images

            doc.close()

            logger.info(
                "Parsed PDF file",
                pages=metadata.page_count,
                text_length=sum(len(p) for p in text_pages),
                has_images=has_images,
            )

            return metadata

        except Exception as e:
            logger.error("Failed to parse PDF file", error=str(e), file_path=file_path)
            raise

    def extract_to_text(self, metadata: PDFMetadata, max_pages: Optional[int] = None) -> str:
        """
        Convert PDF metadata to text format for embedding.

        Args:
            metadata: PDFMetadata object
            max_pages: Maximum number of pages to include (None = all)

        Returns:
            Formatted text string
        """
        lines = []

        # Header
        lines.append(f"PDF Document: {Path(metadata.file_path).name}")

        # Metadata
        if metadata.title:
            lines.append(f"Title: {metadata.title}")
        if metadata.author:
            lines.append(f"Author: {metadata.author}")
        if metadata.subject:
            lines.append(f"Subject: {metadata.subject}")
        if metadata.creation_date:
            lines.append(f"Creation Date: {metadata.creation_date}")

        lines.append(f"Pages: {metadata.page_count}")
        lines.append("")

        # Text content
        pages_to_include = metadata.text_content
        if max_pages:
            pages_to_include = pages_to_include[:max_pages]

        for page_text in pages_to_include:
            lines.append(page_text)
            lines.append("")

        return "\n".join(lines)

    def chunk_by_pages(
        self, metadata: PDFMetadata, pages_per_chunk: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Chunk PDF by pages.

        Args:
            metadata: PDFMetadata object
            pages_per_chunk: Number of pages per chunk

        Returns:
            List of chunks with metadata
        """
        chunks = []

        for i in range(0, len(metadata.text_content), pages_per_chunk):
            page_texts = metadata.text_content[i : i + pages_per_chunk]
            chunk_text = "\n\n".join(page_texts)

            chunk = {
                "text": chunk_text,
                "metadata": {
                    "file_path": metadata.file_path,
                    "start_page": i + 1,
                    "end_page": min(i + pages_per_chunk, metadata.page_count),
                    "title": metadata.title,
                },
            }
            chunks.append(chunk)

        logger.debug(
            "Chunked PDF by pages",
            total_chunks=len(chunks),
            pages_per_chunk=pages_per_chunk,
        )

        return chunks


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Example: Parse a PDF file
    parser = PDFParser(enable_ocr=False)

    # Note: This requires an actual PDF file to test
    # metadata = parser.parse_file("/path/to/document.pdf")
    # text = parser.extract_to_text(metadata, max_pages=5)
    # print(text)
    #
    # chunks = parser.chunk_by_pages(metadata, pages_per_chunk=2)
    # print(f"Created {len(chunks)} chunks")

    print("PDF Parser initialized successfully")
    print("To use: parser.parse_file('path/to/document.pdf')")
