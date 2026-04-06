# Resume Parser Framework

A pluggable, production-grade resume parsing framework built in Python. Supports multiple file formats and configurable field-specific extraction strategies, designed with extensibility and clean OOD principles at its core.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Extraction Strategies](#extraction-strategies)
- [Setup](#setup)
- [Usage](#usage)
- [Running Tests](#running-tests)
- [Extending the Framework](#extending-the-framework)

---

## Overview

Given a resume file (PDF or Word), the framework extracts and returns a structured JSON object:

```json
{
  "name": "Jane Doe",
  "email": "jane.doe@gmail.com",
  "skills": ["Python", "Machine Learning", "FastAPI", "Docker"]
}
```

---

## Architecture

The framework is built around four layers of abstraction, each with a single responsibility:

```
ResumeParserFramework          ← single entry point: parse_resume(file_path)
        │
        ├── FileParser          ← extracts raw text from a file
        │     ├── PDFParser         (pdfplumber)
        │     └── WordParser        (python-docx)
        │
        └── ResumeExtractor     ← orchestrates field-level extraction
              ├── NameExtractor     (LLM-based → regex fallback)
              ├── EmailExtractor    (regex)
              └── SkillsExtractor   (keyword matching)
```

Each layer is defined by an abstract base class (`FileParser`, `FieldExtractor[T]`), making every component independently replaceable without touching the rest of the system.

---

## Project Structure

```
ValerisAssessment/
├── resume_parser/
│   ├── __init__.py
│   ├── base.py                  # Abstract interfaces
│   ├── models.py                # ResumeData dataclass
│   ├── coordinator.py           # ResumeExtractor
│   ├── framework.py             # ResumeParserFramework
│   ├── parsers/
│   │   ├── pdf_parser.py
│   │   └── word_parser.py
│   └── extractors/
│       ├── name_extractor.py
│       ├── email_extractor.py
│       └── skills_extractor.py
├── tests/
│   ├── conftest.py
│   ├── test_parsers.py
│   ├── test_extractors.py
│   └── test_framework.py
├── examples/
│   └── run_example.py
├── conftest.py
├── requirements.txt
└── README.md
```

---

## Extraction Strategies

| Field | Strategy | Rationale |
|---|---|---|
| `name` | **LLM-based** (OpenAI `gpt-4o-mini`) with **regex fallback** | Names are highly contextual — LLMs handle international names, titles, and noisy formatting. Falls back to regex automatically if no API key is set. |
| `email` | **Regex** | Emails have a well-defined format. Regex is deterministic, instant, and needs no model. |
| `skills` | **Rule-based keyword matching** | Scans against a curated vocabulary of 100+ tech skills. Zero latency, easily extended. |

> **No API key required.** The framework works fully out of the box. The LLM only improves name extraction accuracy — if `OPENAI_API_KEY` is not set, it falls back to the regex extractor automatically.

---

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/Akanuchi/valeris_assessment.git
cd valeris_assessment
```

**2. Create and activate a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate       # Mac/Linux
.venv\Scripts\activate          # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. (Optional) Set your OpenAI API key for LLM-based name extraction**
```bash
export OPENAI_API_KEY="sk-..."  # Mac/Linux
set OPENAI_API_KEY=sk-...       # Windows
```

---

## Usage

### Run the built-in example (PDF + DOCX)

```bash
python examples/run_example.py
```

### Parse your own resume

```python
from resume_parser.framework import ResumeParserFramework
from resume_parser.extractors.name_extractor import RegexNameExtractor
from resume_parser.extractors.email_extractor import RegexEmailExtractor
from resume_parser.extractors.skills_extractor import KeywordSkillsExtractor
import json

framework = ResumeParserFramework(
    extractors={
        "name":   RegexNameExtractor(),
        "email":  RegexEmailExtractor(),
        "skills": KeywordSkillsExtractor(),
    }
)

# Works with both .pdf and .docx — auto-detected from file suffix
result = framework.parse_resume("my_resume.pdf")
print(json.dumps(result.to_dict(), indent=2))
```

### Parse a Word document

```python
result = framework.parse_resume("my_resume.docx")
print(result.name)
print(result.email)
print(result.skills)
```

### Use the LLM extractor for better name accuracy

```python
from resume_parser.extractors.name_extractor import LLMNameExtractor

framework = ResumeParserFramework(
    extractors={
        "name":   LLMNameExtractor(),   # requires OPENAI_API_KEY
        "email":  RegexEmailExtractor(),
        "skills": KeywordSkillsExtractor(),
    }
)
```

### Use a custom skills vocabulary

```python
framework = ResumeParserFramework(
    extractors={
        "name":   RegexNameExtractor(),
        "email":  RegexEmailExtractor(),
        "skills": KeywordSkillsExtractor(vocabulary=["Zig", "Odin", "Carbon"]),
    }
)
```

---

## Running Tests

```bash
pytest tests/ -v
```

The test suite covers 60 cases across all components:
- Happy paths for both PDF and DOCX parsing
- Edge cases: corrupt files, wrong extensions, missing files
- All extractor strategies including mocked OpenAI API calls
- End-to-end integration tests with real generated fixtures

---

## Extending the Framework

### Add a new file format

```python
from resume_parser.base import FileParser

class MarkdownParser(FileParser):
    def extract_text(self, file_path: str) -> str:
        with open(file_path) as f:
            return f.read()

framework = ResumeParserFramework(
    extractors={...},
    parser=MarkdownParser()
)
```

### Add a new extraction strategy

```python
from resume_parser.base import FieldExtractor

class NERNameExtractor(FieldExtractor[str]):
    def extract(self, text: str) -> str:
        # use spaCy, HuggingFace, etc.
        ...

framework = ResumeParserFramework(
    extractors={
        "name":   NERNameExtractor(),
        "email":  RegexEmailExtractor(),
        "skills": KeywordSkillsExtractor(),
    }
)
```
