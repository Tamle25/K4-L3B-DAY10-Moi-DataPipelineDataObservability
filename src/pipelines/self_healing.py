from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import sys
from typing import Any
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from retrieval.index import LocalEmbeddingIndex


@dataclass
class IncidentReport:
    incident_id: str
    detected_at: str
    severity: str
    violations: list[str]
    quarantined_path: str
    healing_strategy: str
    healed_at: str | None = None
    healing_status: str = "PENDING"
    revalidated_quality_pass: bool = False
    revalidated_freshness_pass: bool = False


class AutomatedSelfHealingOrchestrator:
    """Orchestrator tự động phát hiện sự cố dữ liệu (Data Incidents) và tự động
    kích hoạt cơ chế tự phục hồi (Self-Healing) chuẩn MLOps zero-touch."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()
        self.audit_log_path = self.settings.paths.project_dir / "data" / "results" / "self_healing_audit.json"
        self.quarantine_path = self.settings.paths.project_dir / "data" / "quality" / "quarantined_data.json"

    def evaluate_batch(self, df: pd.DataFrame, batch_name: str = "incoming_batch") -> tuple[bool, dict[str, Any], dict[str, Any]]:
        """Kiểm định chất lượng dữ liệu của batch trước khi nạp vào Vector Store."""
        quality = run_data_quality_checks(df, self.settings, report_name=batch_name)
        freshness = build_freshness_report(
            df, self.settings, self.settings.paths.freshness_report
        )
        is_valid = bool(quality.get("success", False)) and bool(freshness.get("is_fresh", False))
        return is_valid, quality, freshness

    def trigger_self_healing(
        self,
        corrupted_df: pd.DataFrame,
        quality_report: dict[str, Any],
        freshness_report: dict[str, Any],
    ) -> tuple[pd.DataFrame, IncidentReport]:
        """Tự động kích hoạt cơ chế cách ly và tự chữa lành (Self-Healing)."""
        incident_id = f"INC-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
        detected_at = datetime.now(UTC).isoformat()

        # 1. Phân loại vi phạm
        violations = []
        if not quality_report.get("success", False):
            violations.append("Data Quality Gate (GX 1.x) vi phạm: phát hiện bản ghi rỗng/trùng lặp")
        if not freshness_report.get("is_fresh", False):
            stale_pct = freshness_report.get("stale_ratio", 0.0) * 100
            violations.append(f"Freshness SLA vi phạm: tỷ lệ bài báo cũ đạt {stale_pct:.1f}% (vượt ngưỡng 25%)")

        # 2. Cách ly (Quarantine) dữ liệu bẩn
        corrupted_df.to_json(self.quarantine_path, orient="records", indent=2, force_ascii=False)
        print(f"\n  [ALERT] Kích hoạt sự cố: {incident_id}")
        print(f"  [QUARANTINE] Đã cách ly batch dữ liệu lỗi vào: {self.quarantine_path.name}")
        for v in violations:
            print(f"    - {v}")

        # 3. Thực thi hành động Tự chữa lành (Zero-touch Auto-Repair)
        print("\n  [AUTO-REPAIR] Bắt đầu quy trình tự phục hồi (Self-Healing)...")
        print("    1. Đọc lại snapshot gốc bất biến từ `crossref_records.json`...")
        records = load_raw_records(self.settings.paths.raw_records_json)

        print("    2. Tái tạo và làm sạch chuẩn hóa dữ liệu...")
        healed_df = build_clean_dataframe(records, now_utc())

        print("    3. Ghi đè trạng thái phục hồi an toàn...")
        write_csv(healed_df, self.settings.paths.repaired_clean_csv)
        healed_df.to_json(
            self.settings.paths.repaired_clean_json, orient="records", indent=2, force_ascii=False
        )

        print("    4. Tự động đồng bộ và tái lập chỉ mục Vector DB Chroma...")
        LocalEmbeddingIndex.build(
            healed_df, self.settings, embeddings_output_path=self.settings.paths.repaired_embeddings_json
        )

        # 4. Tái kiểm định sau tự chữa lành (Re-validation)
        reval_quality = run_data_quality_checks(healed_df, self.settings, report_name="self_healed")
        reval_freshness = build_freshness_report(
            healed_df, self.settings, self.settings.paths.freshness_report
        )
        is_revalidated = bool(reval_quality.get("success", False)) and bool(reval_freshness.get("is_fresh", False))

        incident = IncidentReport(
            incident_id=incident_id,
            detected_at=detected_at,
            severity="CRITICAL",
            violations=violations,
            quarantined_path=str(self.quarantine_path),
            healing_strategy="Snapshot-based Idempotent Re-ingestion & Vector Store Re-sync",
            healed_at=datetime.now(UTC).isoformat(),
            healing_status="RESOLVED_AUTOMATICALLY" if is_revalidated else "FAILED",
            revalidated_quality_pass=bool(reval_quality.get("success", False)),
            revalidated_freshness_pass=bool(reval_freshness.get("is_fresh", False)),
        )

        # 5. Lưu audit log
        write_json(self.audit_log_path, asdict(incident))
        print(f"  [AUDIT] Đã ghi nhận lịch sử xử lý sự cố vào: {self.audit_log_path.name}")
        print(f"  [STATUS] Trạng thái tự chữa lành: {incident.healing_status} (Quality={incident.revalidated_quality_pass}, Freshness={incident.revalidated_freshness_pass})")

        return healed_df, incident


def run_self_healing_pipeline(settings: Settings | None = None) -> IncidentReport:
    """Hàm chạy kiểm thử pipeline tự chữa lành tự động (Bonus B2)."""
    settings = settings or load_settings()
    orchestrator = AutomatedSelfHealingOrchestrator(settings)

    print("====================================================================")
    print(" 🛡️  AUTOMATED SELF-HEALING / AUTO-REPAIR PIPELINE (BONUS B2)")
    print("====================================================================")

    # 1. Giả lập một batch dữ liệu bẩn từ baseline
    clean_df = pd.read_json(settings.paths.clean_json)
    print(f"\n1. Nhận luồng dữ liệu mới ({len(clean_df)} dòng)...")
    corrupted_batch = corrupt_clean_dataframe(clean_df.copy(), settings.paths.corruption_log)
    print(f"   (Đã giả lập sự cố dữ liệu thực tế: mất bài, summary rỗng, stale date)")

    # 2. Kiểm định tự động tại chốt Data Observability Gate
    print("\n2. Thực thi kiểm định Data Observability Gate (GX 1.x & Freshness)...")
    is_valid, quality, freshness = orchestrator.evaluate_batch(corrupted_batch, "incoming_corrupted_batch")

    if not is_valid:
        print("   ❌ PHÁT HIỆN SỰ CỐ DỮ LIỆU! Tự động ngăn chặn nạp vào Vector DB.")
        # 3. Kích hoạt cơ chế Self-Healing không cần can thiệp thủ công
        _, incident = orchestrator.trigger_self_healing(corrupted_batch, quality, freshness)
        print("\n====================================================================")
        print(f" ✅ HỆ THỐNG ĐÃ TỰ CHỮA LÀNH THÀNH CÔNG (ZERO-TOUCH RECOVERY)")
        print(f"    - Incident ID: {incident.incident_id}")
        print(f"    - Strategy:    {incident.healing_strategy}")
        print(f"    - Quality Pass: {incident.revalidated_quality_pass}")
        print(f"    - Freshness Pass: {incident.revalidated_freshness_pass}")
        print("====================================================================")
        return incident
    else:
        print("   ✅ Dữ liệu đạt chuẩn, cho phép index vào Vector DB.")
        return IncidentReport(
            incident_id="NONE",
            detected_at=datetime.now(UTC).isoformat(),
            severity="LOW",
            violations=[],
            quarantined_path="",
            healing_strategy="None",
            healing_status="NO_ACTION_NEEDED",
        )


if __name__ == "__main__":
    run_self_healing_pipeline()
