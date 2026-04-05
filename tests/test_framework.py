"""
tests/test_framework.py
------------------------
Integration tests for ResumeExtractor (coordinator) and ResumeParserFramework.
"""
from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock, patch, patch as mock_patch
import pytest
from resume_parser.base import FieldExtractor, FileParser
from resume_parser.coordinator import ResumeExtractor
from resume_parser.extractors.email_extractor import RegexEmailExtractor
from resume_parser.extractors.name_extractor import LLMNameExtractor, RegexNameExtractor
from resume_parser.extractors.skills_extractor import KeywordSkillsExtractor
from resume_parser.framework import ResumeParserFramework
from resume_parser.models import ResumeData


def _stub_extractors(name="Jane Doe", email="jane@example.com", skills=None):
    skills = skills or ["Python", "AWS"]
    name_ext = MagicMock(spec=FieldExtractor)
    name_ext.extract.return_value = name
    email_ext = MagicMock(spec=FieldExtractor)
    email_ext.extract.return_value = email
    skills_ext = MagicMock(spec=FieldExtractor)
    skills_ext.extract.return_value = skills
    return {"name": name_ext, "email": email_ext, "skills": skills_ext}


def _stub_parser(text: str) -> FileParser:
    parser = MagicMock(spec=FileParser)
    parser.extract_text.return_value = text
    return parser


class TestResumeExtractor:

    def test_returns_resume_data_instance(self):
        result = ResumeExtractor(_stub_extractors()).extract("text")
        assert isinstance(result, ResumeData)

    def test_calls_all_extractors_with_same_text(self):
        stubs = _stub_extractors()
        ResumeExtractor(stubs).extract("resume text")
        for stub in stubs.values():
            stub.extract.assert_called_once_with("resume text")

    def test_assembles_fields_correctly(self):
        stubs = _stub_extractors(name="Alice", email="alice@co.com", skills=["Go"])
        result = ResumeExtractor(stubs).extract("text")
        assert result.name == "Alice"
        assert result.email == "alice@co.com"
        assert result.skills == ["Go"]

    def test_raises_value_error_on_missing_extractor(self):
        with pytest.raises(ValueError, match="Missing extractors"):
            ResumeExtractor({"name": MagicMock(spec=FieldExtractor)})

    def test_raises_type_error_when_not_field_extractor(self):
        stubs = _stub_extractors()
        stubs["name"] = "not_an_extractor"
        with pytest.raises(TypeError, match="must be a FieldExtractor instance"):
            ResumeExtractor(stubs)

    def test_raises_type_error_when_not_dict(self):
        with pytest.raises(TypeError, match="must be a dict"):
            ResumeExtractor([])  # type: ignore[arg-type]

    def test_result_is_immutable(self):
        """ResumeData is frozen=True; attribute assignment must raise."""
        result = ResumeExtractor(_stub_extractors()).extract("text")
        with pytest.raises((AttributeError, TypeError)):
            result.name = "hacked"  # type: ignore[misc]


class TestResumeParserFramework:

    def test_selects_pdf_parser_for_dot_pdf(self, tmp_path):
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"fake")
        explicit = _stub_parser("Jane Doe\njane@example.com")
        # Pass explicit parser so we don't need a real PDF
        framework = ResumeParserFramework(_stub_extractors(), parser=explicit)
        framework.parse_resume(str(pdf))
        explicit.extract_text.assert_called_once_with(str(pdf))

    def test_auto_selects_pdf_parser_class(self, tmp_path, sample_pdf):
        """Auto-selection should instantiate PDFParser for .pdf suffix."""
        stub = _stub_parser("Jane Doe\njane@example.com")
        with patch.dict("resume_parser.framework._PARSER_REGISTRY", {".pdf": lambda: stub}):
            framework = ResumeParserFramework(_stub_extractors())
            result = framework.parse_resume(str(sample_pdf))
        assert isinstance(result, ResumeData)
        stub.extract_text.assert_called_once_with(str(sample_pdf))

    def test_auto_selects_word_parser_class(self, tmp_path, sample_docx):
        stub = _stub_parser("Jane Doe\njane@example.com")
        with patch.dict("resume_parser.framework._PARSER_REGISTRY", {".docx": lambda: stub}):
            framework = ResumeParserFramework(_stub_extractors())
            result = framework.parse_resume(str(sample_docx))
        assert isinstance(result, ResumeData)
        stub.extract_text.assert_called_once_with(str(sample_docx))

    def test_raises_value_error_for_unsupported_extension(self, tmp_path):
        txt = tmp_path / "resume.txt"
        txt.write_text("Jane Doe")
        with pytest.raises(ValueError, match="Unsupported file type"):
            ResumeParserFramework(_stub_extractors()).parse_resume(str(txt))

    def test_explicit_parser_overrides_auto_selection(self, tmp_path):
        fake = tmp_path / "resume.xyz"
        fake.write_text("Jane Doe\njane@example.com")
        explicit = _stub_parser("Jane Doe\njane@example.com")
        result = ResumeParserFramework(_stub_extractors(), parser=explicit).parse_resume(str(fake))
        explicit.extract_text.assert_called_once()
        assert isinstance(result, ResumeData)

    def test_parse_pdf_end_to_end(self, sample_pdf, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        framework = ResumeParserFramework(extractors={
            "name": LLMNameExtractor(),
            "email": RegexEmailExtractor(),
            "skills": KeywordSkillsExtractor(),
        })
        result = framework.parse_resume(str(sample_pdf))
        assert isinstance(result, ResumeData)
        assert result.email == "jane.doe@example.com"
        assert len(result.skills) > 0

    def test_parse_docx_end_to_end(self, sample_docx, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        framework = ResumeParserFramework(extractors={
            "name": LLMNameExtractor(),
            "email": RegexEmailExtractor(),
            "skills": KeywordSkillsExtractor(),
        })
        result = framework.parse_resume(str(sample_docx))
        assert result.name == "Jane Doe"
        assert result.email == "jane.doe@example.com"
        assert "Python" in result.skills
        assert "Machine Learning" in result.skills

    def test_to_dict_output_shape(self, sample_docx, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        framework = ResumeParserFramework(extractors={
            "name": RegexNameExtractor(),
            "email": RegexEmailExtractor(),
            "skills": KeywordSkillsExtractor(),
        })
        d = framework.parse_resume(str(sample_docx)).to_dict()
        assert set(d.keys()) == {"name", "email", "skills"}
        assert isinstance(d["name"], str)
        assert isinstance(d["email"], str)
        assert isinstance(d["skills"], list)