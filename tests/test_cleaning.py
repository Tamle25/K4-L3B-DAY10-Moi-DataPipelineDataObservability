"""Kiem thu module Cleaning & Pre-embed Modeling."""
from datetime import UTC, datetime
from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord, _clean_text
from ingestion.cleaning import (
    _clean_str,
    _parse_date,
    build_clean_dataframe,
    format_text_for_embedding,
)


def test_clean_text_removes_jats_tags():
    raw_text = "<jats:p>Data observability catches <jats:italic>silent</jats:italic> failures &amp; bugs.</jats:p>"
    cleaned = _clean_text(raw_text)
    assert "<jats" not in cleaned
    assert "</jats" not in cleaned
    assert "silent failures & bugs." in cleaned


def test_normalize_whitespace():
    text = "  Multiple    spaces   \n  and newlines  \t "
    assert normalize_whitespace(text) == "Multiple spaces and newlines"


def test_parse_date_formats():
    assert _parse_date("2026-06-01") == datetime(2026, 6, 1)
    assert _parse_date("2026-06") == datetime(2026, 6, 1)
    assert _parse_date("2026") == datetime(2026, 1, 1)
    assert _parse_date(None) is None


def test_format_text_for_embedding():
    composed = format_text_for_embedding(
        title="Scaling Data Pipelines",
        authors_joined="Nguyen Van A, Tran B",
        published="2026-05-15",
        categories_joined="Distributed Systems",
        summary="This study analyzes distributed data observability.",
    )
    assert "Title: Scaling Data Pipelines" in composed
    assert "Authors: Nguyen Van A, Tran B" in composed
    assert "Published: 2026-05-15" in composed
    assert "Categories: Distributed Systems" in composed
    assert "Summary: This study analyzes distributed data observability." in composed


def test_build_clean_dataframe_pipeline():
    now = datetime(2026, 9, 26, 12, 0, 0, tzinfo=UTC)
    sample_p = PaperRecord(
        paper_id="10.1145/test.001",
        title="Test Data Observability",
        summary="Empirical analysis of LLM data pipelines.",
        authors=["Jane Doe"],
        categories=["AI"],
        primary_category="AI",
        published="2026-06-01",
        updated="2026-06-01",
        abs_url="https://doi.org/10.1145/test.001",
        pdf_url="https://doi.org/10.1145/test.001.pdf",
        comment="Test record",
    )
    # Gửi 2 bản ghi trùng DOI
    df = build_clean_dataframe([sample_p, sample_p], now)

    # Kiểm tra khử trùng lặp (Deduplication)
    assert len(df) == 1, "Phải khử trùng lặp theo DOI duy nhất"
    assert "paper_id" in df.columns
    assert "text_for_embedding" in df.columns
    assert "age_days" in df.columns
    assert df["age_days"].iloc[0] > 0
