"""
examples/run_example.py
------------------------
Demonstrates the two primary use cases of the Resume Parser Framework:

1. Parsing a Word (.docx) resume.
2. Parsing a PDF resume.

Both examples use the same extractor configuration.  The LLMNameExtractor
will call the OpenAI API if OPENAI_API_KEY is set; otherwise it
automatically falls back to the regex-based extractor.

Usage
-----
    # From the project root:
    python examples/run_example.py

    # With an OpenAI key for LLM-based name extraction:
    OPENAI_API_KEY=sk-... python examples/run_example.py
"""

from __future__ import annotations

import json
import logging
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path when running as a script
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from resume_parser.extractors.email_extractor import RegexEmailExtractor
from resume_parser.extractors.name_extractor import LLMNameExtractor
from resume_parser.extractors.skills_extractor import KeywordSkillsExtractor
from resume_parser.framework import ResumeParserFramework

logging.basicConfig(level=logging.WARNING)  # suppress info logs for demo clarity

# ---------------------------------------------------------------------------
# Generate sample fixtures in a temp directory
# ---------------------------------------------------------------------------

SAMPLE_RESUME_TEXT = textwrap.dedent("""\
    Jane Doe
    jane.doe@gmail.com  |  +1 (416) 555-0199  |  Toronto, ON

    SUMMARY
    Machine Learning Engineer with 5 years building production ML systems.
    Specialisation in NLP, RAG pipelines, and LLM-based applications.

    SKILLS
    Python, PyTorch, TensorFlow, scikit-learn, FastAPI, Docker, Kubernetes,
    PostgreSQL, Redis, AWS, Azure, Git, Machine Learning, Deep Learning,
    Natural Language Processing, LangChain, RAG, Generative AI

    EXPERIENCE
    Senior ML Engineer — Acme Corp  (2021–present)
    - Designed and deployed RAG-based document intelligence pipelines.
    - Built FastAPI microservices for real-time model inference.
    - Reduced latency 40 % via Redis caching and async batching.

    EDUCATION
    B.Sc. Computer Science — University of Toronto (2019)
""")


def _make_docx(dest: Path) -> Path:
    import docx
    doc = docx.Document()
    for line in SAMPLE_RESUME_TEXT.splitlines():
        doc.add_paragraph(line)
    path = dest / "sample_resume.docx"
    doc.save(str(path))
    return path


def _make_pdf(dest: Path) -> Path:
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
    except ImportError:
        print("⚠  reportlab not installed — skipping PDF fixture generation.")
        print("   Install with:  pip install reportlab")
        return None

    path = dest / "sample_resume.pdf"
    c = canvas.Canvas(str(path), pagesize=LETTER)
    _, height = LETTER
    y = height - 50
    for line in SAMPLE_RESUME_TEXT.splitlines():
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(50, y, line)
        y -= 14
    c.save()
    return path


# ---------------------------------------------------------------------------
# Build the shared framework (same extractors for both formats)
# ---------------------------------------------------------------------------

def build_framework() -> ResumeParserFramework:
    """
    Assemble the framework with:
    - LLMNameExtractor  (OpenAI gpt-4o-mini, auto-falls-back to regex)
    - RegexEmailExtractor
    - KeywordSkillsExtractor
    """
    return ResumeParserFramework(
        extractors={
            "name": LLMNameExtractor(),
            "email": RegexEmailExtractor(),
            "skills": KeywordSkillsExtractor(),
        }
    )


def _print_result(label: str, result) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(json.dumps(result.to_dict(), indent=2))


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

def main() -> None:
    import tempfile

    framework = build_framework()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # ── Example 1: Word Document ─────────────────────────────────────
        docx_path = _make_docx(tmp_path)
        print(f"\n[1] Parsing Word document: {docx_path.name}")
        word_result = framework.parse_resume(str(docx_path))
        _print_result("Word (.docx) parse result", word_result)

        # ── Example 2: PDF ───────────────────────────────────────────────
        pdf_path = _make_pdf(tmp_path)
        if pdf_path is not None:
            print(f"\n[2] Parsing PDF: {pdf_path.name}")
            pdf_result = framework.parse_resume(str(pdf_path))
            _print_result("PDF parse result", pdf_result)
        else:
            print("\n[2] PDF example skipped (reportlab not installed).")


if __name__ == "__main__":
    main()