"""
tests/conftest.py
-----------------
Shared pytest fixtures: sample resume text and on-disk PDF / DOCX fixtures.

PDF generation uses *reportlab* (lightweight, no system dependencies).
DOCX generation uses *python-docx* (already a project dependency).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Canonical sample resume text
# ---------------------------------------------------------------------------

SAMPLE_RESUME_TEXT = textwrap.dedent("""\
    Jane Doe
    jane.doe@example.com  |  +1 (416) 555-0199  |  Toronto, ON

    SUMMARY
    Experienced Machine Learning Engineer with 5 years building production ML
    systems, specialising in NLP, RAG pipelines, and LLM-based applications.

    SKILLS
    Python, PyTorch, TensorFlow, scikit-learn, FastAPI, Docker, Kubernetes,
    PostgreSQL, Redis, AWS, Azure, Git, Machine Learning, Deep Learning,
    Natural Language Processing, LangChain, RAG

    EXPERIENCE
    Senior ML Engineer — Acme Corp (2021–present)
    - Designed and deployed RAG-based document intelligence pipelines.
    - Built FastAPI microservices for real-time model inference.
    - Reduced latency by 40 % via Redis caching and async batching.

    EDUCATION
    B.Sc. Computer Science — University of Toronto (2019)
""")


@pytest.fixture()
def sample_text() -> str:
    """Return the canonical sample resume as a plain string."""
    return SAMPLE_RESUME_TEXT


# ---------------------------------------------------------------------------
# On-disk PDF fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_pdf(tmp_path: Path) -> Path:
    """Write SAMPLE_RESUME_TEXT to a temporary PDF and return its Path."""
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
    except ImportError:
        pytest.skip("reportlab not installed — skipping PDF fixture generation")

    pdf_path = tmp_path / "resume.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=LETTER)
    width, height = LETTER
    y = height - 50

    for line in SAMPLE_RESUME_TEXT.splitlines():
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(50, y, line)
        y -= 14

    c.save()
    return pdf_path


# ---------------------------------------------------------------------------
# On-disk DOCX fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_docx(tmp_path: Path) -> Path:
    """Write SAMPLE_RESUME_TEXT to a temporary DOCX and return its Path."""
    import docx

    docx_path = tmp_path / "resume.docx"
    document = docx.Document()

    for line in SAMPLE_RESUME_TEXT.splitlines():
        document.add_paragraph(line)

    document.save(str(docx_path))
    return docx_path