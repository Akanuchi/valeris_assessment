"""
resume_parser/extractors/email_extractor.py
---------------------------------------------
Regex-based extractor for the candidate's email address.
"""
from __future__ import annotations
import logging
import re
from resume_parser.base import FieldExtractor

logger = logging.getLogger(__name__)


class RegexEmailExtractor(FieldExtractor[str]):
    """
    Extract the first email address found in the resume text via regex.

    The pattern handles sub-addressing, hyphens, dots, and multi-part TLDs.
    Returns the first match (candidates list primary contact at the top).
    Returns "" if no email is found.
    """

    _EMAIL_RE = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    )

    def extract(self, text: str) -> str:
        match = self._EMAIL_RE.search(text)
        if match:
            email = match.group(0).lower()
            logger.info("RegexEmailExtractor: found email='%s'", email)
            return email
        logger.warning("RegexEmailExtractor: no email found.")
        return ""