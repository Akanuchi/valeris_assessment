"""
resume_parser/framework.py
----------------------------
ResumeParserFramework — single public entry point.

Combines a FileParser with a ResumeExtractor and exposes:
    parse_resume(file_path: str) -> ResumeData
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any
from resume_parser.base import FieldExtractor, FileParser
from resume_parser.coordinator import ResumeExtractor
from resume_parser.models import ResumeData
from resume_parser.parsers.pdf_parser import PDFParser
from resume_parser.parsers.word_parser import WordParser

logger = logging.getLogger(__name__)

_PARSER_REGISTRY: dict[str, type[FileParser]] = {
    ".pdf": PDFParser,
    ".docx": WordParser,
}


class ResumeParserFramework:
    """
    Top-level coordinator: routes a file to the right parser, then runs
    field extractors and returns a ResumeData.

    Parameters
    ----------
    extractors:
        Dict mapping field name → FieldExtractor instance.
        Required keys: "name", "email", "skills".
    parser:
        Explicit FileParser; when None the framework auto-selects by suffix.
    """

    def __init__(
        self,
        extractors: dict[str, FieldExtractor[Any]],
        parser: FileParser | None = None,
    ) -> None:
        self._extractor = ResumeExtractor(extractors)
        self._explicit_parser = parser

    def parse_resume(self, file_path: str) -> ResumeData:
        """
        Parse a resume and return structured data.

        Raises
        ------
        FileNotFoundError
            If file_path does not exist.
        ValueError
            If the suffix is unsupported and no explicit parser was given.
        """
        path = Path(file_path)
        parser = self._resolve_parser(path)
        logger.info("ResumeParserFramework: parsing '%s' with %s", path.name, type(parser).__name__)
        text = parser.extract_text(file_path)
        return self._extractor.extract(text)

    def _resolve_parser(self, path: Path) -> FileParser:
        if self._explicit_parser is not None:
            return self._explicit_parser
        suffix = path.suffix.lower()
        parser_class = _PARSER_REGISTRY.get(suffix)
        if parser_class is None:
            supported = ", ".join(_PARSER_REGISTRY)
            raise ValueError(
                f"Unsupported file type '{suffix}'. "
                f"Supported: {supported}. "
                "Pass an explicit 'parser' to handle custom formats."
            )
        return parser_class()