"""Kiem thu module Ingestion (Crossref raw API & Fallback Snapshot)."""
from pathlib import Path
from core.config import Settings
from ingestion.crossref import fetch_source_records, load_raw_records, parse_crossref_payload


def test_load_raw_records_from_snapshot(settings: Settings):
    assert settings.paths.raw_records_json.exists(), "Tệp raw_records.json phải tồn tại"
    records = load_raw_records(settings.paths.raw_records_json)
    assert isinstance(records, list)
    assert len(records) > 0, "Snapshot thô phải chứa ít nhất 1 bản ghi"

    sample = records[0]
    assert hasattr(sample, "paper_id")
    assert hasattr(sample, "title")
    assert hasattr(sample, "published")


def test_parse_crossref_payload(sample_raw_record):
    payload = {"message": {"items": [sample_raw_record]}}
    records = parse_crossref_payload(payload)
    assert len(records) == 1
    assert records[0].paper_id == "10.1145/3637528.test001"
    assert records[0].title == "Test Data Observability for LLM RAG"


def test_fetch_source_records_fallback(settings: Settings):
    # Test fetch_source_records với snapshot có sẵn
    records = fetch_source_records(settings)
    assert isinstance(records, list)
    assert len(records) >= 20, "Phải nạp được tối thiểu 20 bản ghi scholarly"
