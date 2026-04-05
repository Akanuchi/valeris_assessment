"""
resume_parser/base.py
---------------------
Abstract interfaces that every concrete parser and extractor must implement.

Keeping the interfaces in a single module makes the contract explicit and
avoids circular imports between the parsers/ and extractors/ sub-packages.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

logger = logging.getLogger(__name__)

# Generic type variable used by FieldExtractor so the return type of
# ``extract`` can be specialised per field (str, List[str], etc.).
T = TypeVar("T")


class FileParser(ABC):
    """
    Contract for all file-format-specific parsers.

    A ``FileParser`` is responsible for one thing only: converting a file
    on disk into a single plain-text string.  All higher-level concerns
    (field extraction, coordination) are handled elsewhere.
    """

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        Read *file_path* and return its textual content.

        Parameters
        ----------
        file_path:
            Absolute or relative path to the resume file.

        Returns
        -------
        str
            The full textual content of the document, with pages/sections
            joined by newlines.

        Raises
        ------
        FileNotFoundError
            If *file_path* does not exist.
        ValueError
            If the file cannot be parsed (corrupt, wrong format, etc.).
        """


class FieldExtractor(ABC, Generic[T]):
    """
    Contract for all field-specific extraction strategies.

    Each extractor focuses on a *single* output field and is completely
    independent of the file format.  This separation lets strategies be
    mixed and matched freely (e.g. swap ``LLMNameExtractor`` for
    ``RegexNameExtractor`` without touching anything else).

    Type parameter *T* allows subclasses to declare their precise return
    type (``str`` for name/email, ``List[str]`` for skills).
    """

    @abstractmethod
    def extract(self, text: str) -> T:
        """
        Extract a single field value from *text*.

        Parameters
        ----------
        text:
            The full plain-text content of the resume.

        Returns
        -------
        T
            The extracted value; returns a sensible empty sentinel
            (``""`` or ``[]``) rather than raising when the field is
            not found, so the framework can always produce a complete
            ``ResumeData`` object.
        """