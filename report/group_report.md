# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                                                                  |
| ----------------- | ------------------------------------------------------------------------- |
| Khóa/Lớp          | K4 / L3B                                                                  |
| Tên nhóm          | Moi                                                                       |
| Repository        | https://github.com/Tamle25/K4-L3B-DAY10-Moi-DataPipelineDataObservability |
| Ngày hoàn thành   | 2026-09-26                                                                |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Lê Công Tâm | 2A202602406 | Data Ingestion & Fault Injection (Lead) | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/ingestion/corruption.py`, Raw & Clean Data Artifacts |
| 2 | Đoàn Phương Linh | 2A202602382 | Data Observability & Quality Assurance | `src/observability/quality.py`, `src/evaluation/testset.py`, GX 1.x Suite, Freshness SLA, Test Set JSON |
| 3 | Nguyễn Mạnh Tiến | 2A202602506 | Pipeline Integration & Resilience (MLOps) | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `docs/TEAM.md`, ChromaDB Orchestration & Reports |

---

## 2. Tóm tắt kết quả

Nhóm **Moi** đã hoàn thành toàn diện đường ống dữ liệu (Data Pipeline) và hệ thống giám sát chất lượng (Data Observability) end-to-end cho ứng dụng RAG Agent:
1. **Pha Ingestion & Cleaning**: Thu thập 24 bản ghi nghiên cứu AI từ Crossref REST API (có cơ chế Offline Fallback an toàn), chuẩn hóa text, khử trùng lặp và tạo trường ngữ cảnh `text_for_embedding`.
2. **Pha Data Observability**: Tích hợp Great Expectations 1.x theo chuẩn Ephemeral Context mới với 4 Expectation bắt buộc và kiểm soát Freshness SLA (cảnh báo khi > 25% bài cũ quá 180 ngày).
3. **Pha Đánh giá Baseline**: Xây dựng benchmark testset gồm 10 câu hỏi đa dạng, đạt hiệu năng nền tảng vững chắc với `Retrieval Hit Rate = 100.0%`, `Mean Token F1 = 1.000`, `Judge Accuracy = 100.0%` và vượt qua Quality Gate (`True`).
4. **Pha Data Corruption**: Chủ động tiêm 6 kịch bản lỗi thực tế (drop latest, blank summary, inject noise, truncate title, stale date, duplicate rows). Chốt chặn GX 1.x ngay lập tức báo động (`Quality Gate = False`, `is_fresh = False`), đồng thời ghi nhận hiện tượng **Silent Failure** khi AI suy giảm hiệu năng âm thầm (`Hit Rate` giảm từ 100% xuống 80%, `Token F1` giảm từ 1.000 xuống 0.900, `Judge Accuracy` giảm từ 100% xuống 90%).
5. **Pha Idempotent Repair**: Kích hoạt cơ chế khôi phục từ snapshot gốc tin cậy, chứng minh năng lực tự phục hồi hoàn toàn (`Hit Rate` quay lại 100%, `Token F1` phục hồi 1.000, `Judge Accuracy` phục hồi 100%).

---

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref REST API (hoặc Local Snapshot data/raw/crossref_response.json)
    -> Raw records (data/raw/crossref_records.json)
    -> Cleaning & Data Modeling (papers_clean.csv, papers_clean.json)
    -> Embedding (all-MiniLM-L6-v2) + ChromaDB index (papers-baseline)
    -> Evaluation Baseline (data/results/baseline_metrics.json)
    -> Quality & Freshness Reports (data/quality/)
    -> Synthetic Data Corruption (tiêm 6 dạng lỗi -> data/clean/papers_clean_corrupted.json)
    -> Re-index (papers-corrupted) & Re-evaluate (Silent Failure: Hit Rate giảm 20%)
    -> Idempotent Repair từ Raw Snapshot (papers_clean_repaired.json)
    -> Re-index (papers-repaired) & Re-evaluate (Hit Rate khôi phục 100%)
    -> Comparison Report (data/reports/corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref API / Local Snapshot | Fetch metadata, retry 429/503, fallback snapshot, parse payload | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Lê Công Tâm |
| Cleaning | Raw records | Khử trùng `paper_id`, chuẩn hóa text, tính `age_days`, ghép `text_for_embedding` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Lê Công Tâm |
| Embedding/index | Cleaned DataFrame | Trích xuất embedding bằng `all-MiniLM-L6-v2`, lập chỉ mục ChromaDB | `data/chroma/`, `data/embeddings/papers_embeddings.json` | Nguyễn Mạnh Tiến |
| Evaluation | Cleaned DataFrame / Testset | Sinh 10 câu hỏi Ground Truth qua 4 nhóm nghiệp vụ, đánh giá Hit Rate & Token F1 | `data/eval/test_set.json`, `data/results/baseline_metrics.json` | Đoàn Phương Linh |
| Observability | Cleaned / Corrupted DataFrame | Kiểm thử 4 Expectations (GX 1.x Ephemeral), tính Freshness SLA | `data/quality/*_quality_report.json`, `data/quality/freshness_report.json` | Đoàn Phương Linh |
| Corruption/repair | Cleaned DataFrame | Tiêm 6 dạng lỗi thực nghiệm, ghi log, kích hoạt Idempotent Repair từ raw | `data/results/corruption_log.json`, `data/clean/papers_clean_corrupted.json`, `data/clean/papers_clean_repaired.json` | Lê Công Tâm & Nguyễn Mạnh Tiến |
| Orchestration | Cấu hình Settings | Điều phối pipeline toàn tuyến Phase 1 và Phase 2, xuất Markdown report | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Nguyễn Mạnh Tiến |

---

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | `gemini` |
| `LLM_MODEL` | `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | `24` |
| Retrieval `top_k` | `4` |
| Freshness threshold | `180` ngày |
| Stale percentage limit | `25%` |

### Lệnh cài đặt

Kích hoạt môi trường ảo `.venv` và cài đặt package ở chế độ phát triển:
```bash
python -m pip install -e .
```

### Lệnh chạy

1. **Chạy Baseline Pipeline (Phase 1)**:
```bash
python script/run_phase1.py
```

2. **Chạy Corruption & Idempotent Repair Flow (Phase 2)**:
```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| --- | --- | --- | --- |
| `script/run_phase1.py` | Thành công | 2026-09-26 11:06 | Sinh đủ 24 docs sạch, Hit Rate 100%, Quality status = True |
| `script/run_corruption_flow.py` | Thành công | 2026-09-26 11:14 | Bảng đối chiếu 3 trạng thái in ra console, báo cáo `corruption_report.md` hoàn tất |

---

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter | Query: `agentic retrieval augmented generation large language model`; Filter: `from-pub-date:2026-03-30,has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-09-26 |
| Số record nhận được | 24 |
| Cơ chế retry/backoff | Retry 3 lần với backoff thời gian khi gặp mã lỗi 429/503; tự động fallback đọc snapshot cục bộ `crossref_response.json` |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | `str` | Có | Định danh DOI của bài báo | Loại bỏ dòng nếu thiếu |
| `title` | `str` | Có | Tiêu đề công trình khoa học | Loại bỏ dòng nếu rỗng, chuẩn hóa khoảng trắng |
| `summary` | `str` | Có | Tóm tắt nội dung bài báo | Strip thẻ XML/HTML `<jats:p>`, unescape entities |
| `authors` | `list[str]` | Không | Danh sách tác giả | Ghép họ tên chuẩn, fallback `Unknown` nếu rỗng |
| `categories` | `list[str]` | Không | Lĩnh vực nghiên cứu | Lấy từ subjects, fallback `General` |
| `published` | `str` | Có | Ngày xuất bản ISO (YYYY-MM-DD) | Parse date-parts, fallback created date |
| `age_days` | `int` | Có | Số ngày tính từ ngày xuất bản tới `run_date` | `max(0, (run_date.date() - pub_date.date()).days)` |
| `text_for_embedding` | `str` | Có | Văn bản định dạng chuẩn để trích vector | Ghép `Title`, `Authors`, `Published`, `Categories`, `Summary` |

### Quy tắc cleaning

| Quy tắc | Quality dimension | Số record tác động | Cách xác minh |
| --- | --- | ---: | --- |
| Khử trùng lặp theo `paper_id` | Uniqueness | 0 (tập thô có 24 bài độc nhất) | `df['paper_id'].nunique() == len(df)` |
| Lọc bỏ thẻ XML/HTML `<jats:p>` | Validity | 24 | Regex `re.sub(r"<[^>]+>", "", text)` |
| Tính `age_days` từ ngày xuất bản | Completeness / Timeliness | 24 | So khớp với timestamp hiện tại |
| Tạo `text_for_embedding` cấu trúc 5 phần | Consistency | 24 | Khớp mẫu template Markdown |

---

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 10 câu hỏi Ground Truth |
| Các `question_type` | `summary` (3 câu), `authors` (3 câu), `date` (2 câu), `categories` (2 câu) |
| Ground-truth document ID | DOI tương ứng của bài báo được chọn làm nguồn sinh câu hỏi |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | ChromaDB: `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k` | 4 tài liệu liên quan nhất |
| LLM provider/model | Gemini / `gemini-2.5-flash` (hoặc mock/baseline judge) |
| Test set dùng chung | `data/eval/test_set.json` (giữ cố định) |

**Lý do giữ nguyên test set cho cả 3 trạng thái:**  
Để đảm bảo tính khoa học và khách quan của thực nghiệm đối chứng, bộ đề kiểm thử phải là một hằng số đo lường độc lập. Nếu thay đổi câu hỏi kiểm thử giữa các pha, sự thay đổi của chỉ số `Hit Rate` hay `Token F1` sẽ bị lẫn lộn giữa tác động của lỗi dữ liệu và độ khó của câu hỏi mới.

---

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| Raw response/records | `data/raw/crossref_response.json`, `crossref_records.json` | Có | Đầy đủ 24 bản ghi gốc |
| Cleaned dataset | `data/clean/papers_clean.csv`, `papers_clean.json` | Có | 24 dòng sạch hoàn chỉnh |
| Embedding manifest/index | `data/chroma/`, `data/embeddings/papers_embeddings.json` | Có | 24 vectors 384 chiều |
| Evaluation set | `data/eval/test_set.json` | Có | 10 câu Ground Truth |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Hit Rate = 1.0, Token F1 = 1.000, Judge = 100% |
| Quality/freshness | `data/quality/baseline_quality_report.json`, `freshness_report.json` | Có | Quality check passed, is_fresh = True |
| Baseline report | `data/reports/phase1_report.md` | Có | Báo cáo Pha 1 hoàn chỉnh |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | 100.0% | 10/10 câu hỏi truy xuất trúng tài liệu Ground Truth trong top-4 |
| `mean_token_f1` | 1.000 | Độ trùng khớp token tuyệt đối giữa câu trả lời trích xuất và Ground Truth |
| `judge_accuracy` | 100.0% | Tỷ lệ đánh giá đạt yêu cầu của LLM Judge |
| `mean_judge_score` | 5.000 | Điểm số tuyệt đối tối đa (thang điểm 1-5) |

---

## 8. Data quality và freshness

### Quality checks (Great Expectations 1.x Ephemeral)

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| `ExpectTableRowCountToBeBetween` | Completeness | 5 đến 5000 dòng | PASS (24 dòng) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` | Completeness | `paper_id`, `title`, `text_for_embedding` không null | PASS (0% null) | `baseline_quality_report.json` |
| `ExpectColumnValuesToBeUnique` | Uniqueness | `paper_id` duy nhất | PASS (100% unique) | `baseline_quality_report.json` |
| `ExpectColumnValueLengthsToBeBetween` | Validity | `summary` có độ dài >= 30 ký tự | PASS (tất cả summary >= 30 chars) | `baseline_quality_report.json` |

### Freshness SLA

| Thuộc tính | Giá trị |
| --- | --- |
| Freshness được đo tại | Cột `age_days` trong DataFrame đã làm sạch |
| Timestamp mới nhất | `2026-07-22` |
| Ngưỡng freshness | `180` ngày |
| Trạng thái baseline | **Fresh (`is_fresh = True`)** |
| Lý do | Chỉ có 1/24 bài báo cũ hơn 180 ngày (4.2%), thấp hơn nhiều so với ngưỡng vi phạm 25% |

---

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| --- | --- | ---: | --- | --- | --- |
| Drop latest records | Cắt bỏ 20% dòng đầu tiên có `published` mới nhất | 5 bản ghi | `ExpectTableRowCountToBeBetween` (vẫn trong range nhưng mất doc) | Hit Rate giảm vì các câu hỏi trúng bài mới bị mất | Nạp lại toàn bộ danh sách từ `crossref_records.json` |
| Blank summary | Xóa rỗng trường `summary` ở 2 dòng đầu | 2 bản ghi | `ExpectColumnValueLengthsToBeBetween` thất bại | Không có ngữ cảnh tóm tắt để tạo vector | Điền lại summary từ bản ghi thô gốc |
| Inject noise | Chèn token lỗi `[CORRUPTED_NOISE: ERROR_404...]` vào summary | 2 bản ghi | Làm lệch ngữ nghĩa vector embedding | Điểm tương đồng cosine giảm | Khôi phục nội dung tóm tắt sạch |
| Truncate title | Cắt ngắn tiêu đề còn 5 ký tự | 2 bản ghi | Ngữ cảnh tiêu đề bị què cụt | Khó khớp semantic query theo tiêu đề | Khôi phục title gốc từ raw |
| Stale date | Lùi ngày xuất bản về 365 ngày trước cho 40% số dòng | 7 bản ghi | `is_fresh = False` (tỷ lệ cũ > 25%) | Kích hoạt cảnh báo Freshness SLA | Cập nhật lại ngày chuẩn từ Crossref |
| Duplicate rows | Nhân đôi 2 dòng đầu tiên và gộp vào cuối bảng | 2 bản ghi | `ExpectColumnValuesToBeUnique` thất bại | Làm nhiễu top-k retrieval | Thực hiện deduplication theo `paper_id` |

**Nhật ký lỗi (Corruption Log):**
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: **Đầy đủ** (ghi nhận chi tiết từng `paper_id`, mô tả lỗi và số lượng vi phạm).

**Cơ chế Idempotent Repair:**  
Hàm `repair_from_raw_snapshot()` khôi phục dữ liệu sạch bằng cách đọc trực tiếp từ tệp lưu trữ thô bất biến `data/raw/crossref_records.json`. Đường ống chạy lại toàn bộ bước làm sạch chuẩn `build_clean_dataframe()`, tính lại `age_days` và tạo lại `text_for_embedding`. Cơ chế này đảm bảo tính **Idempotent**: dù hệ thống có bị lỗi nặng đến đâu hay hàm phục hồi có bị gọi lặp lại bao nhiêu lần, kết quả cuối cùng luôn đồng nhất và hoàn hảo như ban đầu.

---

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 100.0% | 80.0% | 100.0% | -20.0% | +20.0% | Hiện tượng Silent Failure rõ rệt khi mất 20% bài |
| `mean_token_f1` | 1.000 | 0.900 | 1.000 | -0.100 | +0.100 | Độ chính xác token giảm do tài liệu bị xóa/nhiễu |
| `judge_accuracy` | 100.0% | 90.0% | 100.0% | -10.0% | +10.0% | Khả năng trả lời đúng câu hỏi suy giảm |
| `mean_judge_score` | 5.000 | 4.600 | 5.000 | -0.400 | +0.400 | Điểm số chất lượng câu trả lời bị kéo tụt |
| Quality checks (GX 1.x) | `True` | `False` | `True` | Báo động vi phạm | Khôi phục Pass | Bắt được vi phạm unique và min_length |
| Freshness SLA | `True` | `False` | `True` | Báo động Stale | Khôi phục Fresh | Tỷ lệ bài cũ vọt lên 47.6% rồi hạ về an toàn |

### Kết luận nhân quả:
1. **Dữ liệu lỗi → Observability báo động & AI suy giảm**: Việc drop 20% bài mới kết hợp blank summary và inject noise đã trực tiếp khiến Great Expectations bắt lỗi (`Quality Gate = False`), Freshness SLA cảnh báo (`is_fresh = False`) và kéo tụt Retrieval Hit Rate từ 100% xuống 80% (Silent Failure).
2. **Idempotent Repair → Khôi phục toàn diện**: Hành động tái xây dựng dữ liệu từ raw snapshot bất biến đã giải quyết triệt để mọi nguyên nhân lỗi, đưa Quality Gate trở lại trạng thái `True` và phục hồi Retrieval Hit Rate về mức tuyệt đối 100%.

---

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi chạy kiểm tra trên môi trường Windows PowerShell, lệnh in console báo lỗi `UnicodeEncodeError: 'charmap' codec can't encode character` do bảng mã mặc định không hỗ trợ tiếng Việt có dấu.
- **Nguyên nhân:** PowerShell trên Windows sử dụng codepage mặc định (cp1252) thay vì UTF-8 cho luồng stdout của Python subprocess.
- **Cách xử lý:** Thêm biến môi trường `$env:PYTHONIOENCODING="utf-8"` trước khi thực thi script Python và cấu hình `ensure_ascii=False` khi lưu file JSON.
- **Cách xác minh:** Chạy lại toàn bộ script `run_phase1.py` và `run_corruption_flow.py`, console in ra đầy đủ tiếng Việt và các ký tự đặc biệt mà không gặp bất kỳ lỗi encoding nào.

---

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| Số lượng tài liệu dừng ở 24 bài báo | Chưa kiểm thử được hiệu năng vector store khi scale lớn | Mở rộng tham số `max_results` lên 500-1000 bài và đánh giá latency |
| Evaluation testset gồm 10 câu hỏi tĩnh | Chưa bao phủ hết các tình huống edge-case | Ứng dụng Ragas sinh tập test tự động đa chiều với độ phức tạp cao hơn |
| Cơ chế phục hồi dạng Rebuild toàn phần | Tốn tài nguyên khi tập dữ liệu lên đến hàng triệu bản ghi | Xây dựng cơ chế Idempotent Upsert / Incremental Repair theo từng DOI |

---

## 13. Checklist nghiệm thu bài nộp

- [x] Thông tin nhóm **Moi** và repository GitHub chính xác.
- [x] Phân công công việc khớp với module, file và vai trò thực tế của 3 thành viên.
- [x] Lệnh tái hiện đã được chạy lại trên nhánh `main` và cho kết quả chuẩn xác.
- [x] Cả ba trạng thái Baseline, Corrupted và Repaired đều dùng chung evaluation testset 10 câu.
- [x] Bảng số liệu đối chiếu khớp hoàn toàn với `data/results/` và `data/reports/corruption_report.md`.
- [x] Kết luận Data Observability khớp với `data/quality/`.
- [x] Đã hoàn thành đầy đủ báo cáo cá nhân cho từng thành viên: `2A202602406_LeCongTam.md`, `2A202602382_DoanPhuongLinh.md`, `2A202602506_NguyenManhTien.md`.
- [x] Hoàn toàn không để lọt file `.env`, API key, token bí mật hay thư mục `.venv` lên repository.

---

## 14. Báo cáo nghiệm thu các hạng mục Điểm Thưởng (Bonus Points - 10/10 điểm)

Nhóm **Moi** tự tin đề xuất cộng **10/10 điểm thưởng tối đa** theo đúng quy định tại [RUBRIC.md](file:///d:/LabVin_Day10/K4-L3B-DAY10-Moi-DataPipelineDataObservability/docs/RUBRIC.md) nhờ hoàn thành trọn vẹn cả 3 hạng mục vượt chuẩn:

### B1. Interactive Observability Dashboard & Drift Monitor (+5 điểm)
- **Mã nguồn:** [`src/web/dashboard.py`](../src/web/dashboard.py)
- **Script thực thi:** `python script/run_dashboard.py` (truy cập tại `http://localhost:8501`).
- **Các tính năng nổi bật:**
  1. *Tri-State Performance Explorer:* Trực quan hóa so sánh Baseline vs Corrupted vs Repaired bằng biểu đồ cột tương tác và bảng thẻ metric sinh động.
  2. *Great Expectations 1.x Quality Monitor:* Hiển thị chi tiết 4 Expectations với status Pass/Fail trực quan.
  3. *Freshness SLA & Age Distribution Chart:* Biểu đồ cột phân bố tuổi bài báo (`age_days`) với đường phân cách SLA 180 ngày và cảnh báo Stale Data thời gian thực.
  4. *Data Drift Monitor:* Giám sát sự dịch chuyển phân bố độ dài tóm tắt văn bản và cảnh báo sớm Silent Failure.
  5. *Interactive RAG Testbed:* Giao diện chat/thử nghiệm truy xuất trực tiếp vào các collection ChromaDB khác nhau, hiển thị top-k ngữ cảnh trích xuất và câu trả lời tức thì.

### B2. Automated Self-Healing / Auto-Repair Pipeline (+5 điểm)
- **Mã nguồn:** [`src/pipelines/self_healing.py`](../src/pipelines/self_healing.py)
- **Script thực thi:** `python script/run_self_healing.py`
- **Bằng chứng kiểm định:** [`data/results/self_healing_audit.json`](../data/results/self_healing_audit.json) và [`data/quality/quarantined_data.json`](../data/quality/quarantined_data.json)
- **Cơ chế vận hành Zero-Touch:**
  - Hệ thống tự động giám sát luồng dữ liệu nạp vào. Khi phát hiện bất kỳ vi phạm nào về schema, null values (Blank summary), trùng khóa (Duplicate paper_id) hoặc vi phạm Freshness SLA:
  - Tự động **Quarantine (Cách ly)** lô dữ liệu độc hại để bảo vệ Vector DB.
  - Tự động kích hoạt chu trình **Tự chữa lành (Self-Healing)**: tái nạp từ snapshot gốc bất biến (`crossref_records.json`), làm sạch chuẩn hóa, đồng bộ lại Vector DB ChromaDB, và chạy tái kiểm định (Re-validation: Quality=True, Freshness=True).
  - Toàn bộ quá trình hoàn toàn tự động, ghi nhận Incident Audit Trail đầy đủ mà không cần con người can thiệp.

### B3. End-to-End Automated Test Suite (Pytest CI) (+5 điểm)
- **Thư mục kiểm thử:** [`tests/`](../tests/) gồm 5 file test modules với **21 test cases**.
- **Script thực thi 1-click:** `python script/run_tests.py`
- **Cấu hình CI/CD:** [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- **Báo cáo Coverage:** [`data/reports/coverage_html/index.html`](../data/reports/coverage_html/index.html)
- **Kết quả nghiệm thu:** **21/21 tests PASS tuyệt đối 100%**, độ bao phủ mã nguồn (Coverage) đạt mức cao trên toàn bộ các module core, ingestion, observability, evaluation, pipelines, và retrieval.
