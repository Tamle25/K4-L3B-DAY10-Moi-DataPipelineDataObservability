"""Kiem thu Synthetic Corruption, Idempotent Repair va Self-Healing."""
from pathlib import Path
import pandas as pd
from core.config import Settings
from ingestion.corruption import corrupt_clean_dataframe
from pipelines.corruption_flow import repair_from_raw_snapshot
from pipelines.self_healing import AutomatedSelfHealingOrchestrator


def test_synthetic_corruption_scenarios(baseline_clean_df, tmp_path: Path):
    log_file = tmp_path / "test_corruption_log.json"
    corrupted_df = corrupt_clean_dataframe(baseline_clean_df.copy(), log_file)

    assert log_file.exists()
    assert len(corrupted_df) < len(baseline_clean_df), "Phải có kịch bản drop bài mới"
    assert (corrupted_df["summary"] == "").any(), "Phải có kịch bản blank summary"
    assert corrupted_df["paper_id"].duplicated().any(), "Phải có kịch bản duplicate rows"


def test_idempotent_repair_consistency(settings: Settings):
    # Gọi repair 2 lần liên tiếp, kết quả phải đồng nhất 100% (Idempotent)
    repaired_1 = repair_from_raw_snapshot(settings)
    repaired_2 = repair_from_raw_snapshot(settings)

    assert len(repaired_1) == len(repaired_2)
    assert (repaired_1["paper_id"].values == repaired_2["paper_id"].values).all()


def test_automated_self_healing_orchestrator(settings: Settings, baseline_clean_df, tmp_path: Path):
    orchestrator = AutomatedSelfHealingOrchestrator(settings)
    log_file = tmp_path / "test_corrupt_log.json"
    corrupted_df = corrupt_clean_dataframe(baseline_clean_df.copy(), log_file)

    is_valid, quality, freshness = orchestrator.evaluate_batch(corrupted_df, "test_batch")
    assert is_valid is False, "Dữ liệu bẩn phải bị đánh giá là INVALID"

    healed_df, incident = orchestrator.trigger_self_healing(corrupted_df, quality, freshness)
    assert incident.healing_status == "RESOLVED_AUTOMATICALLY"
    assert incident.revalidated_quality_pass is True
    assert incident.revalidated_freshness_pass is True
    assert len(healed_df) >= len(corrupted_df)
