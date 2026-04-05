"""
Data models for the Resume Parser Framework.
"""

from dataclasses import dataclass, field, asdict
from typing import List
import json


@dataclass(frozen=True)
class ResumeData:
    """
    Encapsulates structured data extracted from a resume.

    Attributes:
        name:   Full name of the candidate.
        email:  Email address of the candidate.
        skills: List of technical/professional skills.
    """

    name: str = ""
    email: str = ""
    skills: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return a plain dictionary representation."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Return a JSON-formatted string of the resume data."""
        return json.dumps(self.to_dict(), indent=indent)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ResumeData(name={self.name!r}, email={self.email!r}, skills={self.skills!r})"