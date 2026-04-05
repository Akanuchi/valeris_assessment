"""
resume_parser/extractors/skills_extractor.py
----------------------------------------------
Rule-based keyword skills extractor.
"""
from __future__ import annotations
import logging
import re
from typing import List
from resume_parser.base import FieldExtractor

logger = logging.getLogger(__name__)

DEFAULT_SKILLS: list[str] = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "C", "C++", "C#", "Go",
    "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB",
    "Bash", "Shell", "PowerShell", "SQL", "PL/SQL",
    # Web / Frontend
    "HTML", "CSS", "React", "Vue", "Angular", "Next.js", "Svelte",
    "Tailwind CSS", "Bootstrap", "jQuery",
    # Backend / Frameworks
    "Node.js", "Django", "Flask", "FastAPI", "Spring Boot", "Express",
    "Rails", "Laravel", "ASP.NET",
    # Data / ML / AI
    "Machine Learning", "Deep Learning", "Reinforcement Learning",
    "Natural Language Processing", "NLP", "Computer Vision",
    "Large Language Models", "LLM", "Generative AI", "GenAI",
    "RAG", "Retrieval-Augmented Generation",
    "TensorFlow", "PyTorch", "Keras", "scikit-learn", "XGBoost", "LightGBM",
    "Hugging Face", "LangChain", "LangGraph", "OpenAI", "Gemini",
    "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly",
    "NLTK", "spaCy", "Transformers",
    # MLOps / Data Engineering
    "MLflow", "Kubeflow", "Airflow", "Apache Spark", "Kafka",
    "dbt", "Databricks", "Azure Databricks", "Snowflake", "Redshift",
    "BigQuery", "Hive",
    # Databases
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch",
    "Cassandra", "DynamoDB", "Firebase", "Pinecone", "Weaviate", "Chroma",
    # Cloud & DevOps
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Helm",
    "Terraform", "Ansible", "Jenkins", "GitHub Actions", "CircleCI",
    "ArgoCD", "Prometheus", "Grafana", "Datadog",
    # APIs & Protocols
    "REST", "GraphQL", "gRPC", "WebSockets", "OAuth", "JWT",
    # VCS & Tooling
    "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence",
    # Methodologies
    "Agile", "Scrum", "Kanban", "TDD", "BDD", "CI/CD", "DevOps", "MLOps",
]


class KeywordSkillsExtractor(FieldExtractor[List[str]]):
    """
    Extract skills via whole-word, case-insensitive keyword matching.

    Parameters
    ----------
    vocabulary:
        List of skill strings to match. Defaults to DEFAULT_SKILLS.
    deduplicate:
        Remove duplicate matches (default True), preserving first-occurrence order.
    """

    def __init__(
        self,
        vocabulary: list[str] | None = None,
        *,
        deduplicate: bool = True,
    ) -> None:
        self._vocabulary = vocabulary or DEFAULT_SKILLS
        self._deduplicate = deduplicate
        # Pre-compile patterns for performance
        self._patterns: list[tuple[str, re.Pattern[str]]] = [
            (skill, self._compile(skill)) for skill in self._vocabulary
        ]

    def extract(self, text: str) -> List[str]:
        found: list[str] = []
        seen: set[str] = set()
        for canonical, pattern in self._patterns:
            if pattern.search(text):
                key = canonical.lower()
                if self._deduplicate and key in seen:
                    continue
                seen.add(key)
                found.append(canonical)
        logger.info("KeywordSkillsExtractor: found %d skill(s).", len(found))
        return found

    @staticmethod
    def _compile(skill: str) -> re.Pattern[str]:
        # Allow flexible whitespace between words (useful after PDF extraction)
        escaped = r"\s+".join(re.escape(w) for w in skill.split())
        return re.compile(rf"\b{escaped}\b", re.IGNORECASE)