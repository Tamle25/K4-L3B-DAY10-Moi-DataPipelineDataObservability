"""Pytest conftest: fixtures dung chung cho toan bo test suite."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest
import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json


@pytest.fixture(scope="session")
def settings() -> Settings:
    return load_settings()


@pytest.fixture(scope="session")
def sample_raw_record() -> dict:
    return {
        "DOI": "10.1145/3637528.test001",
        "title": ["Test Data Observability for LLM RAG"],
        "abstract": "<jats:p>This is a test abstract with   redundant  spaces and <jats:italic>markup</jats:italic>.</jats:p>",
        "author": [{"given": "Jane", "family": "Doe"}, {"name": "AI Lab"}],
        "created": {"date-time": "2026-06-01T10:00:00Z"},
        "published": {"date-parts": [[2026, 6, 1]]},
        "subject": ["Artificial Intelligence", "Databases"],
    }


@pytest.fixture(scope="session")
def baseline_clean_df(settings: Settings) -> pd.DataFrame:
    if settings.paths.clean_json.exists():
        return pd.read_json(settings.paths.clean_json)
    # Fallback minimal df if file not present
    return pd.DataFrame([
        {
            "paper_id": "10.1145/test",
            "title": "Test Title",
            "abstract": "Test Summary text.",
            "authors_joined": "Jane Doe",
            "published": "2026-06-01",
            "categories_joined": "AI",
            "summary": "Test Summary text.",
            "age_days": 10,
            "text_for_embedding": "Title: Test Title\nAuthors: Jane Doe\nPublished: 2026-06-01\nCategories: AI\nSummary: Test Summary text.",
        }
    ])
