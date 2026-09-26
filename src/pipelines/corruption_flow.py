from __future__ import annotations

from typing import Any
import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def repair_from_raw_snapshot(settings: Settings) -> pd.DataFrame:
    """Idempotent repair: rebuild lại dataframe sạch trực tiếp từ raw snapshot đáng tin cậy.

    Vì hàm này luôn đọc lại từ `data/raw/crossref_records.json` (không dựa trên
    bản corrupted), gọi lại nhiều lần cho kết quả giống hệt nhau -> idempotent.
    """
    records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(records, now_utc())
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    repaired_df.to_json(
        settings.paths.repaired_clean_json, orient="records", indent=2, force_ascii=False
    )
    return repaired_df


def _print_comparison_table(
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """In bảng so sánh hiệu năng 3 cột rõ ràng ra console."""
    def _pct(v: Any) -> str:
        try:
            return f"{float(v) * 100:.1f}%"
        except (TypeError, ValueError):
            return "N/A"

    def _num(v: Any) -> str:
        try:
            return f"{float(v):.3f}"
        except (TypeError, ValueError):
            return "N/A"

    b_hit = _pct(baseline_metrics.get("retrieval_hit_rate"))
    c_hit = _pct(corrupted_metrics.get("retrieval_hit_rate"))
    r_hit = _pct(repaired_metrics.get("retrieval_hit_rate"))

    b_f1 = _num(baseline_metrics.get("mean_token_f1"))
    c_f1 = _num(corrupted_metrics.get("mean_token_f1"))
    r_f1 = _num(repaired_metrics.get("mean_token_f1"))

    b_judge = _pct(baseline_metrics.get("judge_accuracy"))
    c_judge = _pct(corrupted_metrics.get("judge_accuracy"))
    r_judge = _pct(repaired_metrics.get("judge_accuracy"))

    c_q = str(corrupted_quality.get("success", False))
    r_q = str(repaired_quality.get("success", True))

    c_fresh = str(corrupted_freshness.get("is_fresh", False))
    r_fresh = str(repaired_freshness.get("is_fresh", True))

    table = f"""
========================================================================================
           BẢNG ĐỐI CHIẾU HIỆU NĂNG 3 TRẠNG THÁI: BASELINE vs CORRUPTED vs REPAIRED
========================================================================================
| Metric                     | Baseline (Gốc)  | Corrupted (Bị lỗi) | Repaired (Phục hồi) |
+----------------------------+-----------------+--------------------+---------------------+
| Retrieval Hit Rate         | {b_hit:<15} | {c_hit:<18} | {r_hit:<19} |
| Mean Token F1              | {b_f1:<15} | {c_f1:<18} | {r_f1:<19} |
| Judge Accuracy             | {b_judge:<15} | {c_judge:<18} | {r_judge:<19} |
| Data Quality Gate (GX 1.x) | True            | {c_q:<18} | {r_q:<19} |
| Freshness SLA (<= 180d)    | True            | {c_fresh:<18} | {r_fresh:<19} |
========================================================================================
"""
    print(table)


def run_corruption_flow_pipeline(settings: Settings | None = None) -> None:
    """Xâu chuỗi toàn tuyến Phase 2:
    1. Load baseline & tiêm lỗi dữ liệu thực nghiệm (Synthetic Data Corruption).
    2. Nạp dữ liệu bẩn vào ChromaDB và đo lường sự suy giảm hiệu năng (Silent Failure).
    3. Kiểm tra chốt chất lượng Data Observability (GX 1.x & Freshness SLA).
    4. Kích hoạt cơ chế phục hồi an toàn repair_from_raw_snapshot().
    5. Đánh giá hệ thống sau phục hồi và kết xuất bảng so sánh 3 trạng thái.
    """
    if settings is None:
        settings = load_settings()

    # 1. Load baseline metrics và clean dataset.
    if not settings.paths.baseline_metrics.exists() or not settings.paths.clean_json.exists():
        raise RuntimeError(
            "Không tìm thấy baseline artifacts. Hãy chạy `python script/run_phase1.py` trước."
        )
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_df = pd.read_json(settings.paths.clean_json)
    print(f"[CorruptionFlow] Đã load baseline: {len(baseline_df)} dòng.")

    # 2. Tạo corrupted dataframe và lưu artifacts.
    corrupted_df = corrupt_clean_dataframe(baseline_df.copy(), settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    corrupted_df.to_json(
        settings.paths.corrupted_clean_json, orient="records", indent=2, force_ascii=False
    )
    print(f"[CorruptionFlow] Đã lưu corrupted dataset: {len(corrupted_df)} dòng.")

    # 3. Rebuild index và evaluate trên dữ liệu bị lỗi (quan sát Silent Failure).
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, embeddings_output_path=settings.paths.corrupted_embeddings_json
    )
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(
        "[CorruptionFlow] Corrupted metrics -> "
        f"hit_rate={corrupted_bundle.summary['retrieval_hit_rate']:.2f}, "
        f"token_f1={corrupted_bundle.summary['mean_token_f1']:.2f}"
    )

    # 4. Quality checks / freshness trên corrupted data.
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, report_name="corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, settings.paths.freshness_report
    )
    print(f"[CorruptionFlow] Corrupted quality status = {corrupted_quality.get('success')}")

    # 5. Repair lại từ raw records (idempotent).
    repaired_df = repair_from_raw_snapshot(settings)
    print(f"[CorruptionFlow] Đã phục hồi dataset: {len(repaired_df)} dòng.")

    # 6. Evaluate repaired dataset.
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, embeddings_output_path=settings.paths.repaired_embeddings_json
    )
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, report_name="repaired")
    repaired_freshness = build_freshness_report(
        repaired_df, settings, settings.paths.freshness_report
    )
    print(
        "[CorruptionFlow] Repaired metrics -> "
        f"hit_rate={repaired_bundle.summary['retrieval_hit_rate']:.2f}, "
        f"token_f1={repaired_bundle.summary['mean_token_f1']:.2f}"
    )

    # 7. Tạo comparison report (Baseline vs Corrupted vs Repaired).
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"[CorruptionFlow] Đã ghi comparison report tại {settings.paths.comparison_report}")

    # 8. In bảng so sánh trực quan ra console
    _print_comparison_table(
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )


def main() -> None:
    settings = load_settings()
    run_corruption_flow_pipeline(settings)


if __name__ == "__main__":
    main()

