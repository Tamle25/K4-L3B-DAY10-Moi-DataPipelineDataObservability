from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ingestion.cleaning import format_text_for_embedding


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Giả lập 6 dạng sự cố dữ liệu thực tế (Synthetic Data Corruption Suite):
    1. Drop latest records: Bỏ rơi 20% các bài báo mới nhất.
    2. Blank summary: Xóa trắng phần tóm tắt ở một số dòng.
    3. Inject noise: Chèn các chuỗi ký tự rác vào tóm tắt.
    4. Truncate title: Cắt ngắn tiêu đề xuống dưới 8 ký tự.
    5. Stale date: Lùi ngày xuất bản về 365 ngày trước.
    6. Duplicate rows: Nhân đôi các dòng để tạo trùng lặp.

    Ghi nhật ký chi tiết vào output_log_path và rebuild lại text_for_embedding.
    """
    corrupted_df = df.copy()
    log_details: list[dict[str, Any]] = []
    corruption_counts: dict[str, int] = {
        "drop_latest_records": 0,
        "blank_summary": 0,
        "inject_noise": 0,
        "truncate_title": 0,
        "stale_date": 0,
        "duplicate_rows": 0,
    }

    n_rows = len(corrupted_df)
    if n_rows == 0:
        return corrupted_df

    # 1. Drop latest records (20% bản ghi mới nhất)
    # df đã được sort theo published giảm dần ở bước clean
    n_drop = max(1, int(round(n_rows * 0.20)))
    dropped_rows = corrupted_df.iloc[:n_drop]
    for _, row in dropped_rows.iterrows():
        log_details.append(
            {
                "type": "drop_latest_records",
                "paper_id": str(row["paper_id"]),
                "description": f"Dropped latest record '{row['title']}' (published: {row['published']})",
            }
        )
    corruption_counts["drop_latest_records"] = n_drop
    corrupted_df = corrupted_df.iloc[n_drop:].reset_index(drop=True)

    # 2. Blank summary (xóa rỗng tóm tắt ở 2 dòng đầu)
    # Gây lỗi ExpectColumnValueLengthsToBeBetween (summary < 30 ký tự)
    blank_indices = [0, 1] if len(corrupted_df) >= 2 else [0]
    for idx in blank_indices:
        pid = str(corrupted_df.at[idx, "paper_id"])
        old_summary = corrupted_df.at[idx, "summary"]
        corrupted_df.at[idx, "summary"] = ""
        corrupted_df.at[idx, "summary_chars"] = 0
        log_details.append(
            {
                "type": "blank_summary",
                "paper_id": pid,
                "description": f"Blanked summary of paper '{pid}' (was {len(str(old_summary))} chars)",
            }
        )
        corruption_counts["blank_summary"] += 1

    # 3. Inject noise (chèn chuỗi rác vào tóm tắt ở 2 dòng tiếp theo)
    noise_indices = [2, 3] if len(corrupted_df) >= 4 else []
    noise_text = " [CORRUPTED_NOISE: ERROR_CORRUPT_NULL_BYTE_404_DATA_CORRUPTION_LEAK] "
    for idx in noise_indices:
        pid = str(corrupted_df.at[idx, "paper_id"])
        old_summary = str(corrupted_df.at[idx, "summary"])
        corrupted_summary = noise_text * 3 + old_summary[:50] + noise_text
        corrupted_df.at[idx, "summary"] = corrupted_summary
        corrupted_df.at[idx, "summary_chars"] = len(corrupted_summary)
        log_details.append(
            {
                "type": "inject_noise",
                "paper_id": pid,
                "description": f"Injected synthetic noise into summary of paper '{pid}'",
            }
        )
        corruption_counts["inject_noise"] += 1

    # 4. Truncate title (< 8 ký tự ở 2 dòng tiếp theo)
    truncate_indices = [4, 5] if len(corrupted_df) >= 6 else []
    for idx in truncate_indices:
        pid = str(corrupted_df.at[idx, "paper_id"])
        old_title = str(corrupted_df.at[idx, "title"])
        corrupted_title = old_title[:5] if len(old_title) > 5 else "Err"
        corrupted_df.at[idx, "title"] = corrupted_title
        log_details.append(
            {
                "type": "truncate_title",
                "paper_id": pid,
                "description": f"Truncated title of paper '{pid}' from '{old_title}' to '{corrupted_title}'",
            }
        )
        corruption_counts["truncate_title"] += 1

    # 5. Stale date (lùi ngày xuất bản về 365 ngày trước cho nhiều dòng để kích hoạt Freshness SLA warning)
    stale_count = max(6, int(len(corrupted_df) * 0.4))
    stale_indices = list(range(min(stale_count, len(corrupted_df))))
    for idx in stale_indices:
        pid = str(corrupted_df.at[idx, "paper_id"])
        old_pub = str(corrupted_df.at[idx, "published"])
        try:
            old_dt = datetime.strptime(old_pub[:10], "%Y-%m-%d")
            new_dt = old_dt - timedelta(days=365)
            new_pub = new_dt.strftime("%Y-%m-%d")
        except Exception:
            new_pub = "2024-01-01"
        corrupted_df.at[idx, "published"] = new_pub
        if "age_days" in corrupted_df.columns:
            corrupted_df.at[idx, "age_days"] = int(corrupted_df.at[idx, "age_days"]) + 365
        log_details.append(
            {
                "type": "stale_date",
                "paper_id": pid,
                "description": f"Shifted published date for '{pid}' from {old_pub} to {new_pub} (-365 days)",
            }
        )
        corruption_counts["stale_date"] += 1

    # 6. Duplicate rows (nhân đôi 2 dòng để vi phạm tính duy nhất của paper_id)
    dup_indices = [0, 1] if len(corrupted_df) >= 2 else [0]
    dup_rows = corrupted_df.iloc[dup_indices].copy()
    for _, row in dup_rows.iterrows():
        log_details.append(
            {
                "type": "duplicate_rows",
                "paper_id": str(row["paper_id"]),
                "description": f"Duplicated row with paper_id '{row['paper_id']}'",
            }
        )
        corruption_counts["duplicate_rows"] += 1
    corrupted_df = pd.concat([corrupted_df, dup_rows], ignore_index=True)

    # 7. Rebuild text_for_embedding
    new_text_for_embedding = []
    for _, row in corrupted_df.iterrows():
        t = format_text_for_embedding(
            title=str(row["title"]),
            authors_joined=str(row.get("authors_joined", "")),
            published=str(row.get("published", "")),
            categories_joined=str(row.get("categories_joined", "")),
            summary=str(row.get("summary", "")),
        )
        new_text_for_embedding.append(t)
    corrupted_df["text_for_embedding"] = new_text_for_embedding

    # 8. Ghi log ra output_log_path
    log_payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "original_rows": n_rows,
        "corrupted_rows": len(corrupted_df),
        "corruption_counts": corruption_counts,
        "details": log_details,
    }
    output_log_path = Path(output_log_path)
    output_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_log_path, "w", encoding="utf-8") as f:
        json.dump(log_payload, f, ensure_ascii=False, indent=2)

    return corrupted_df

