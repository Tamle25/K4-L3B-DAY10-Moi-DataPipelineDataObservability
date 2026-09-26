"""Kiem thu module Observability (Great Expectations 1.x & Freshness SLA)."""
from pathlib import Path
import pandas as pd
from core.config import Settings
from observability.quality import build_freshness_report, run_data_quality_checks


def test_great_expectations_baseline_passed(baseline_clean_df, settings: Settings):
    report = run_data_quality_checks(baseline_clean_df, settings, report_name="test_baseline")
    assert report.get("success") is True, f"Baseline DataFrame phải pass toàn bộ 4 expectations: {report}"
    assert report.get("row_count") == len(baseline_clean_df)


def test_great_expectations_catches_null_and_duplicate(baseline_clean_df, settings: Settings):
    # Tạo bản ghi bẩn: summary rỗng và duplicate paper_id
    corrupted_df = baseline_clean_df.copy()
    corrupted_df.loc[0, "summary"] = ""
    # Thêm 1 dòng trùng
    corrupted_df = pd.concat([corrupted_df, corrupted_df.iloc[[0]]], ignore_index=True)

    report = run_data_quality_checks(corrupted_df, settings, report_name="test_corrupted")
    assert report.get("success") is False, "GX phải bắt được vi phạm rỗng và trùng lặp"


def test_freshness_sla_monitoring(baseline_clean_df, settings: Settings, tmp_path: Path):
    out_file = tmp_path / "test_freshness.json"
    report = build_freshness_report(baseline_clean_df, settings, out_file)

    assert "is_fresh" in report
    assert "stale_pct" in report
    assert "run_at" in report
    assert out_file.exists()


def test_freshness_sla_violation_alert(baseline_clean_df, settings: Settings, tmp_path: Path):
    stale_df = baseline_clean_df.copy()
    # Gán 50% số bài có age_days > 180 (vượt ngưỡng 25%)
    stale_df.loc[:len(stale_df)//2, "age_days"] = 300

    out_file = tmp_path / "test_stale_freshness.json"
    report = build_freshness_report(stale_df, settings, out_file)
    assert report["is_fresh"] is False, "Phải báo động đỏ vi phạm SLA khi có quá 25% bài cũ"
