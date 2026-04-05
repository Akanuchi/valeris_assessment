"""
resume_parser/coordinator.py
------------------------------
ResumeExtractor — orchestrates all FieldExtractors and assembles ResumeData.
"""
from __future__ import annotations
import logging
from typing import Any
from resume_parser.base import FieldExtractor
from resume_parser.models import ResumeData

logger = logging.getLogger(__name__)
_REQUIRED_FIELDS = ("name", "email", "skills")


class ResumeExtractor:
    """
    Run each FieldExtractor against the resume text and assemble ResumeData.

    Parameters
    ----------
    extractors:
        Dict mapping field name → FieldExtractor. Required keys: "name", "email", "skills".

    Raises
    ------
    TypeError  – if extractors is not a dict, or values aren't FieldExtractors.
    ValueError – if any required field key is missing.
    """

    def __init__(self, extractors: dict[str, FieldExtractor[Any]]) -> None:
        self._validate_extractors(extractors)
        self._extractors = extractors

    def extract(self, text: str) -> ResumeData:
        """Run all extractors and return a populated ResumeData."""
        logger.info("ResumeExtractor: starting extraction (%d chars).", len(text))
        name: str = self._run("name", text, default="")
        email: str = self._run("email", text, default="")
        skills: list[str] = self._run("skills", text, default=[])
        result = ResumeData(name=name, email=email, skills=skills)
        logger.info("ResumeExtractor: extraction complete → %r", result)
        return result

    def _run(self, field: str, text: str, *, default: Any) -> Any:
        try:
            return self._extractors[field].extract(text)
        except Exception as exc:
            logger.error("Extractor for '%s' raised: %s", field, exc)
            return default

    @staticmethod
    def _validate_extractors(extractors: dict[str, FieldExtractor[Any]]) -> None:
        if not isinstance(extractors, dict):
            raise TypeError(f"'extractors' must be a dict, got {type(extractors).__name__!r}")
        missing = [f for f in _REQUIRED_FIELDS if f not in extractors]
        if missing:
            raise ValueError(f"Missing extractors for required field(s): {missing}.")
        for key, ext in extractors.items():
            if not isinstance(ext, FieldExtractor):
                raise TypeError(
                    f"extractors['{key}'] must be a FieldExtractor instance, "
                    f"got {type(ext).__name__!r}"
                )