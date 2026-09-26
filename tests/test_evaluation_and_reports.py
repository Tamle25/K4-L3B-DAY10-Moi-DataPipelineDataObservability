"""Kiem thu module Evaluation, Reporting va Pipelines Integration."""
from pathlib import Path
from core.config import Settings
from evaluation.metrics import _token_f1
from evaluation.testset import build_test_set
from observability.reporting import generate_corruption_report, generate_phase1_report
from pipelines.corruption_flow import _print_comparison_table


def test_token_f1_calculation():
    # Exactly matching
    assert _token_f1("Anh Tran, Quoc Pham", "Anh Tran, Quoc Pham") == 1.0
    # Empty
    assert _token_f1("", "Something") == 0.0
    assert _token_f1("Reference", "") == 0.0
    # Overlap
    f1 = _token_f1("Data Observability Pipeline", "Data Observability System")
    assert 0.5 <= f1 < 1.0


def test_build_test_set_structure(baseline_clean_df, tmp_path: Path):
    out_path = tmp_path / "test_set_gen.json"
    test_set = build_test_set(baseline_clean_df, out_path)

    assert len(test_set) == 10
    types = {item["question_type"] for item in test_set}
    assert "summary" in types
    assert "authors" in types
    assert "date" in types
    assert "categories" in types
    assert out_path.exists()


def test_reporting_generators(settings: Settings, tmp_path: Path):
    p1_report = tmp_path / "test_phase1.md"
    generate_phase1_report(
        p1_report,
        source_summary={"raw_records": 24, "clean_records": 24},
        metrics={"samples": 10, "retrieval_hit_rate": 1.0, "mean_token_f1": 1.0, "judge_accuracy": 1.0, "mean_judge_score": 5.0},
        quality={"success": True, "expectations": ["table_columns", "not_null"]},
        freshness={"is_fresh": True, "stale_pct": 0.0},
    )
    assert p1_report.exists()
    content_p1 = p1_report.read_text(encoding="utf-8")
    assert "Baseline" in content_p1

    c_report = tmp_path / "test_corruption.md"
    generate_corruption_report(
        c_report,
        baseline_metrics={"retrieval_hit_rate": 1.0, "mean_token_f1": 1.0, "judge_accuracy": 1.0, "mean_judge_score": 5.0},
        corrupted_metrics={"retrieval_hit_rate": 0.8, "mean_token_f1": 0.9, "judge_accuracy": 0.9, "mean_judge_score": 4.6},
        repaired_metrics={"retrieval_hit_rate": 1.0, "mean_token_f1": 1.0, "judge_accuracy": 1.0, "mean_judge_score": 5.0},
        corrupted_quality={"success": False},
        repaired_quality={"success": True},
        corrupted_freshness={"is_fresh": False, "stale_pct": 0.476},
        repaired_freshness={"is_fresh": True, "stale_pct": 0.0},
    )
    assert c_report.exists()
    content_c = c_report.read_text(encoding="utf-8")
    assert "Comparison" in content_c or "Baseline" in content_c


def test_print_comparison_table_coverage():
    # Test hàm in bảng đối chiếu
    _print_comparison_table(
        baseline_metrics={"retrieval_hit_rate": 1.0, "mean_token_f1": 1.0, "judge_accuracy": 1.0},
        corrupted_metrics={"retrieval_hit_rate": 0.8, "mean_token_f1": 0.9, "judge_accuracy": 0.9},
        repaired_metrics={"retrieval_hit_rate": 1.0, "mean_token_f1": 1.0, "judge_accuracy": 1.0},
        corrupted_quality={"success": False},
        repaired_quality={"success": True},
        corrupted_freshness={"is_fresh": False},
        repaired_freshness={"is_fresh": True},
    )
