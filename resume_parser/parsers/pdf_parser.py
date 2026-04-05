"""
resume_parser/parsers/pdf_parser.py
------------------------------------
Concrete FileParser for PDF documents using pdfplumber.
"""
from __future__ import annotations
import logging
from pathlib import Path
import pdfplumber
from resume_parser.base import FileParser

logger = logging.getLogger(__name__)


class PDFParser(FileParser):
    """
    Extract plain text from a PDF resume using pdfplumber.

    Each page is extracted individually and joined with newlines so that
    section boundaries are preserved in the output string.

    Parameters
    ----------
    strip_whitespace:
        When True (default), leading/trailing whitespace is stripped per page.
    """

    def __init__(self, *, strip_whitespace: bool = True) -> None:
        self._strip_whitespace = strip_whitespace

    def extract_text(self, file_path: str) -> str:
        """
        Read file_path (must be a PDF) and return its full text content.

        Raises
        ------
        FileNotFoundError  – if file_path does not exist.
        ValueError         – if the file is not a .pdf or cannot be parsed.
        """
        path = Path(file_path)
        self._validate_path(path)
        logger.info("PDFParser: opening '%s'", path)
        pages: list[str] = []
        try:
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    raw = page.extract_text() or ""
                    text = raw.strip() if self._strip_whitespace else raw
                    if text:
                        pages.append(text)
                    else:
                        logger.debug("PDFParser: page %d yielded no text.", i)
        except Exception as exc:
            raise ValueError(f"PDFParser could not parse '{path}': {exc}") from exc
        full_text = "\n".join(pages)
        logger.info("PDFParser: extracted %d chars from %d page(s).", len(full_text), len(pages))
        return full_text

    @staticmethod
    def _validate_path(path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"File not found: '{path}'")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"PDFParser expects a '.pdf' file, got '{path.suffix}'")