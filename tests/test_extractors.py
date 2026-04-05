"""
tests/test_extractors.py
-------------------------
Unit tests for all three FieldExtractor implementations.

LLMNameExtractor is tested with the OpenAI client mocked so no live API
calls are made.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from resume_parser.extractors.email_extractor import RegexEmailExtractor
from resume_parser.extractors.name_extractor import LLMNameExtractor, RegexNameExtractor
from resume_parser.extractors.skills_extractor import KeywordSkillsExtractor


# ===========================================================================
# RegexNameExtractor
# ===========================================================================

class TestRegexNameExtractor:
    def setup_method(self):
        self.extractor = RegexNameExtractor()

    def test_extracts_name_from_first_line(self):
        assert self.extractor.extract("Jane Doe\njane@example.com") == "Jane Doe"

    def test_extracts_three_part_name(self):
        assert self.extractor.extract("Mary Anne Johnson\nme@company.org") == "Mary Anne Johnson"

    def test_skips_email_lines(self):
        assert self.extractor.extract("jane@example.com\nJane Doe") == "Jane Doe"

    def test_skips_url_lines(self):
        assert self.extractor.extract("https://linkedin.com/in/jane\nJane Doe") == "Jane Doe"

    def test_skips_phone_number_lines(self):
        assert self.extractor.extract("+1 416 555 0199\nJane Doe") == "Jane Doe"

    def test_returns_empty_string_when_no_name_found(self):
        assert self.extractor.extract("jane@example.com\nhttps://github.com/jane") == ""

    def test_handles_hyphenated_name(self):
        assert self.extractor.extract("Anne-Marie Dupont\ncontact@example.com") == "Anne-Marie Dupont"

    def test_returns_string_type(self):
        assert isinstance(self.extractor.extract("John Smith\ntest@test.com"), str)


# ===========================================================================
# LLMNameExtractor
# ===========================================================================

class TestLLMNameExtractor:

    def test_falls_back_to_regex_when_no_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        extractor = LLMNameExtractor()
        assert extractor.extract("Jane Doe\njane@example.com") == "Jane Doe"

    def test_calls_openai_api_when_key_present(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        mock_choice = MagicMock()
        mock_choice.message.content = "Jane Doe"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("resume_parser.extractors.name_extractor.OpenAI", return_value=mock_client):
            result = LLMNameExtractor().extract("Jane Doe\njane@example.com")

        assert result == "Jane Doe"
        mock_client.chat.completions.create.assert_called_once()

    def test_falls_back_on_api_exception(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("quota exceeded")

        with patch("resume_parser.extractors.name_extractor.OpenAI", return_value=mock_client):
            result = LLMNameExtractor().extract("Jane Doe\njane@example.com")

        assert result == "Jane Doe"

    def test_custom_fallback_extractor_is_used(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        custom_fallback = MagicMock()
        custom_fallback.extract.return_value = "Custom Name"
        result = LLMNameExtractor(fallback_extractor=custom_fallback).extract("text")
        custom_fallback.extract.assert_called_once_with("text")
        assert result == "Custom Name"

    def test_strips_whitespace_from_llm_response(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        mock_choice = MagicMock()
        mock_choice.message.content = "  Jane Doe  \n"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("resume_parser.extractors.name_extractor.OpenAI", return_value=mock_client):
            result = LLMNameExtractor().extract("Jane Doe\njane@example.com")

        assert result == "Jane Doe"

    def test_truncates_long_text_to_2000_chars(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        mock_choice = MagicMock()
        mock_choice.message.content = "Jane Doe"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("resume_parser.extractors.name_extractor.OpenAI", return_value=mock_client):
            LLMNameExtractor().extract("Jane Doe\n" + "x" * 5000)

        call_kwargs = mock_client.chat.completions.create.call_args
        user_content = call_kwargs.kwargs["messages"][1]["content"]
        assert len(user_content) <= 2000


# ===========================================================================
# RegexEmailExtractor
# ===========================================================================

class TestRegexEmailExtractor:
    def setup_method(self):
        self.extractor = RegexEmailExtractor()

    def test_extracts_simple_email(self):
        assert self.extractor.extract("Contact: jane@example.com") == "jane@example.com"

    def test_extracts_plus_addressed_email(self):
        assert self.extractor.extract("jane+work@company.org") == "jane+work@company.org"

    def test_extracts_subdomain_email(self):
        assert self.extractor.extract("user@mail.company.co.uk") == "user@mail.company.co.uk"

    def test_returns_first_email_when_multiple(self):
        assert self.extractor.extract("primary@example.com and backup@other.org") == "primary@example.com"

    def test_returns_empty_string_when_none(self):
        assert self.extractor.extract("no contact info here") == ""

    def test_lowercases_result(self):
        assert self.extractor.extract("JANE@EXAMPLE.COM") == "jane@example.com"

    def test_extracts_from_multiline_text(self, sample_text):
        assert self.extractor.extract(sample_text) == "jane.doe@example.com"

    def test_returns_string_type(self):
        assert isinstance(self.extractor.extract("test@test.com"), str)


# ===========================================================================
# KeywordSkillsExtractor
# ===========================================================================

class TestKeywordSkillsExtractor:
    def setup_method(self):
        self.extractor = KeywordSkillsExtractor()

    def test_extracts_known_skills(self):
        skills = self.extractor.extract("Proficient in Python, Docker, and AWS.")
        assert "Python" in skills
        assert "Docker" in skills
        assert "AWS" in skills

    def test_case_insensitive_matching(self):
        skills = self.extractor.extract("experience with PYTHON and pytorch")
        assert "Python" in skills
        assert "PyTorch" in skills

    def test_preserves_canonical_casing(self):
        skills = self.extractor.extract("uses fastapi and postgresql")
        assert "FastAPI" in skills
        assert "PostgreSQL" in skills

    def test_no_partial_matches_for_go(self):
        skills = self.extractor.extract("Works at Google with good results")
        assert "Go" not in skills

    def test_deduplication_enabled(self):
        skills = self.extractor.extract("Python python PYTHON")
        assert skills.count("Python") == 1

    def test_custom_vocabulary(self):
        extractor = KeywordSkillsExtractor(vocabulary=["Zig", "Odin"])
        skills = extractor.extract("I know Zig and some Odin.")
        assert "Zig" in skills
        assert "Odin" in skills
        assert "Python" not in skills

    def test_returns_empty_list_when_no_skills(self):
        assert self.extractor.extract("No relevant skills here.") == []

    def test_multi_word_skill_matching(self):
        skills = self.extractor.extract("Experience with Machine Learning and Natural Language Processing.")
        assert "Machine Learning" in skills
        assert "Natural Language Processing" in skills

    def test_returns_list_type(self):
        assert isinstance(self.extractor.extract("Python developer"), list)

    def test_extracts_from_full_sample(self, sample_text):
        skills = self.extractor.extract(sample_text)
        for expected in ["Python", "FastAPI", "Redis", "AWS", "Docker", "Machine Learning"]:
            assert expected in skills