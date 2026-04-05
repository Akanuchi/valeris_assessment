"""
resume_parser/extractors/name_extractor.py
-------------------------------------------
Name extractors: LLM-based (primary) with regex fallback.
"""
from __future__ import annotations
import logging
import os
import re
from resume_parser.base import FieldExtractor

# Module-level import so tests can patch 'resume_parser.extractors.name_extractor.OpenAI'
try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a precise resume-parsing assistant. "
    "Extract ONLY the candidate's full name from the resume text. "
    "Return the name and nothing else — no labels, no punctuation, no explanation. "
    "If you cannot determine the name with confidence, return an empty string."
)

# Word component: starts uppercase, rest lowercase, allows internal hyphens
_WORD = r"[A-ZÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÃÑ][a-záéíóúàèìòùäëïöüâêîôûãñ'\-]*"


class LLMNameExtractor(FieldExtractor[str]):
    """
    Extract the candidate's name using OpenAI (gpt-4o-mini by default).

    Falls back to RegexNameExtractor when OPENAI_API_KEY is absent or any
    exception is raised during the API call.

    Parameters
    ----------
    model:
        OpenAI model identifier. Default: "gpt-4o-mini".
    fallback_extractor:
        FieldExtractor used when API unavailable. Defaults to RegexNameExtractor().
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        fallback_extractor: FieldExtractor[str] | None = None,
    ) -> None:
        self._model = model
        self._fallback = fallback_extractor or RegexNameExtractor()

    def extract(self, text: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("LLMNameExtractor: OPENAI_API_KEY not set — using fallback.")
            return self._fallback.extract(text)
        try:
            return self._call_openai(api_key, text)
        except Exception as exc:
            logger.error("LLMNameExtractor: API error (%s) — using fallback.", exc)
            return self._fallback.extract(text)

    def _call_openai(self, api_key: str, text: str) -> str:
        client = OpenAI(api_key=api_key)
        snippet = text[:2000]  # names appear near the top; cap token usage
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": snippet},
            ],
            temperature=0,
            max_tokens=30,
        )
        name = (response.choices[0].message.content or "").strip()
        logger.info("LLMNameExtractor: extracted name='%s'", name)
        return name


class RegexNameExtractor(FieldExtractor[str]):
    """
    Heuristic name extractor: scans the first lines for a title-case name.

    Handles hyphenated words (Anne-Marie), 2–5 word names, and accented chars.
    Skips lines that look like emails, URLs, or phone numbers.
    Returns "" if no match found in first _SCAN_LINES lines.
    """

    _SCAN_LINES = 10
    # A name word: optional hyphenated second part (Anne-Marie, O'Brien)
    _NAME_WORD = rf"{_WORD}(?:-{_WORD})?"
    _NAME_RE = re.compile(
        rf"^{_NAME_WORD}(?:\s+{_NAME_WORD}){{1,4}}$"
    )
    _SKIP_RE = re.compile(
        r"(https?://|www\.|@|\d{{3}}[\s\-]\d{{3}}|\+\d|[A-Z]{{2,}}\s*:)",
        re.IGNORECASE,
    )

    def extract(self, text: str) -> str:
        for line in text.splitlines()[:self._SCAN_LINES]:
            candidate = line.strip()
            if not candidate or self._SKIP_RE.search(candidate):
                continue
            if self._NAME_RE.match(candidate):
                logger.info("RegexNameExtractor: found name='%s'", candidate)
                return candidate
        logger.warning("RegexNameExtractor: no name found in first %d lines.", self._SCAN_LINES)
        return ""