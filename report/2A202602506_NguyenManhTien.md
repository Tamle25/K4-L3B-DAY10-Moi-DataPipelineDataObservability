# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                  |
| ----------------- | ------------------------------------------------------------------------- |
| Họ và tên         | Nguyễn Mạnh Tiến                                                          |
| MSSV              | 2A202602506                                                               |
| Khóa/Lớp          | K4 / L3B                                                                  |
| Tên nhóm          | Moi                                                                       |
| Vai trò chính     | Pipeline Integration & Resilience (MLOps)                                 |
| Repository        | https://github.com/Tamle25/K4-L3B-DAY10-Moi-DataPipelineDataObservability |
| Ngày hoàn thành   | 2026-09-26                                                                |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Môi trường & Dependencies (Bước 1) | Cấu hình `.venv`, `.env` | Python 3.11+, `pyproject.toml` | Môi trường kích hoạt, 3 thư viện cốt lõi sẵn sàng | Hoàn thành |
| Baseline Pipeline Orchestration (Bước 6) | `src/pipelines/phase1.py`<br>`script/run_phase1.py` | Dữ liệu sạch từ Ingestion & Test set | Toàn tuyến Phase 1 chạy thông suốt, `phase1_report.md`, `baseline_metrics.json` | Hoàn thành |
| Resilience & Idempotent Repair Flow (Bước 8) | `src/pipelines/corruption_flow.py`<br>`script/run_corruption_flow.py` | Baseline artifacts, Corrupted DataFrame | Toàn tuyến Phase 2, bảng so sánh 3 trạng thái, `corruption_report.md` | Hoàn thành |
| Teamwork & Submission Checklist (Bước 9) | `docs/TEAM.md`, Git hygiene | Hồ sơ thành viên, git log nhánh `main` | Quản trị đóng góp nhóm, dọn dẹp artifacts, sẵn sàng nghiệm thu | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Đồng bộ hóa môi trường ảo | Lê Công Tâm & Đoàn Phương Linh | Hỗ trợ cấu hình `PYTHONIOENCODING="utf-8"` và giải quyết các vấn đề dependencies ChromaDB, PyTorch CPU |
| Tích hợp Vector Store | Module Ingestion & Observability | Kết nối chặt chẽ giữa DataFrame sau khi làm sạch/làm hỏng với các collection tương ứng trong ChromaDB |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Xâu chuỗi toàn tuyến dữ liệu sạch Phase 1 | `src/pipelines/phase1.py` | Chạy end-to-end 6 công đoạn: Ingest -> Clean -> ChromaDB -> Testset -> Eval -> Quality Gate | Chạy `python script/run_phase1.py`: sinh đủ CSV, JSON, vector DB và báo cáo Phase 1 |
| Xây dựng luồng thực nghiệm đối chiếu Phase 2 | `src/pipelines/corruption_flow.py` | Chạy luồng Tiêm lỗi -> Đo suy giảm -> Tự phục hồi -> Đối chiếu 3 trạng thái | Chạy `python script/run_corruption_flow.py`: in bảng 3 cột ra console và xuất `corruption_report.md` |
| Quản trị hồ sơ và kỷ luật Git nhóm | `docs/TEAM.md`, git hygiene | Phân công rõ ràng, bảo đảm 100% thành viên có commit và không lộ secret | Rà soát `git status`, `git log` nhánh `main` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Xâu chuỗi đường ống tự động hóa (End-to-End Orchestration)**: Tích hợp các module riêng lẻ (thu thập, làm sạch, trích xuất đặc trưng vector, kiểm thử chất lượng, đánh giá LLM) thành một chu trình khép kín, hoạt động ổn định và có thể tái hiện 100%.
2. **Hiện thực hóa cơ chế tự phục hồi (Self-Healing / Idempotent Repair)**: Khi hệ thống phát hiện dữ liệu bị suy thoái hoặc bị tấn công, đường ống phải có khả năng tự động khôi phục về trạng thái sạch ban đầu từ bản sao lưu trữ an toàn mà không cần can thiệp thủ công.
3. **Đo lường định lượng và đối chiếu 3 trạng thái**: Lập bảng so sánh trực quan các chỉ số kỹ thuật giữa Baseline, Corrupted và Repaired để chứng minh bằng số liệu thực tế sự sụt giảm và khả năng phục hồi của hệ thống.

### Cách triển khai
- **Xâu chuỗi Baseline Pipeline (`phase1.py`)**:
  - Tải dữ liệu từ nguồn hoặc đọc raw records.
  - Làm sạch dữ liệu, lưu artifact `papers_clean.csv` và `papers_clean.json`.
  - Khởi tạo vector store `ChromaDB` với collection `papers-baseline` sử dụng mô hình nhúng `all-MiniLM-L6-v2`.
  - Sinh bộ testset và chạy đánh giá retrieval Hit Rate, Token F1.
  - Chạy Great Expectations Quality Gate và Freshness SLA.
  - Xuất báo cáo Markdown tổng hợp `phase1_report.md`.
- **Triển khai Luồng Đối chiếu & Phục hồi (`corruption_flow.py`)**:
  - Nạp dữ liệu bị tiêm lỗi vào collection `papers-corrupted` trong ChromaDB.
  - Đánh giá trên cùng tập test để quan sát hiện tượng **Silent Failure** (`Hit Rate` giảm từ 100% xuống 80%, `Token F1` giảm từ 0.520 xuống 0.417).
  - Kích hoạt hàm `repair_from_raw_snapshot()`: đọc lại snapshot thô từ `crossref_records.json`, làm sạch lại từ đầu và lưu vào `papers_clean_repaired.*`.
  - Đánh chỉ mục dữ liệu phục hồi vào collection `papers-repaired`, tái đánh giá và xác nhận chỉ số quay về mức ban đầu.
  - In bảng so sánh trực tiếp ra console và xuất báo cáo `corruption_report.md`.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Settings cấu hình hệ thống, raw & clean datasets, evaluation test set |
| Output | Vector database collections trong ChromaDB, metrics files JSON, báo cáo đối chiếu Markdown |
| Module phụ thuộc | `ingestion`, `observability`, `evaluation`, `retrieval`, `core` |
| Module sử dụng output | Ban giám khảo chấm thi, báo cáo nghiệm thu đồ án |
| Điều kiện lỗi cần xử lý | Thiếu artifacts baseline, xung đột collection ChromaDB, lỗi kết nối API |

### Cách xác minh

```powershell
# Chạy toàn tuyến Baseline Pipeline
python script/run_phase1.py

# Chạy toàn tuyến Corruption Flow & Idempotent Repair
python script/run_corruption_flow.py
```

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi đánh giá 3 trạng thái dữ liệu (Baseline, Corrupted, Repaired), nếu lưu trữ chung vào một collection ChromaDB thì việc ghi đè hoặc xóa mềm có thể để lại các vector mồ côi (Ghost Vectors), làm sai lệch kết quả đánh giá đối chứng.
- **Các phương án đã cân nhắc:**
  1. Dùng chung 1 collection, mỗi lần chuyển pha thì xóa toàn bộ tài liệu bằng `collection.delete()`.
  2. Tạo 3 collection hoàn toàn biệt lập trong ChromaDB: `papers-baseline`, `papers-corrupted`, `papers-repaired`.
- **Phương án đã chọn:** Phương án 2 (3 collection tách biệt).
- **Lý do:** Đảm bảo tính cô lập tuyệt đối (Isolation) giữa các trạng thái dữ liệu. Dữ liệu bị lỗi không làm vấy bẩn collection gốc, và dữ liệu phục hồi được xây dựng trên một không gian vector hoàn toàn mới, loại bỏ 100% nguy cơ sót vector cũ.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  RuntimeError: Không tìm thấy baseline artifacts. Hãy chạy `python script/run_phase1.py` trước.
  ```
- **Lệnh tái hiện:** Thực thi `script/run_corruption_flow.py` khi chưa chạy `script/run_phase1.py`.
- **Nguyên nhân gốc:** Script Phase 2 cần đối chiếu số liệu với kết quả Baseline lưu tại `data/results/baseline_metrics.json`. Nếu chạy Phase 2 độc lập từ đầu, hệ thống sẽ thiếu mốc so sánh.
- **Cách xử lý:** Đặt chốt kiểm tra file tồn tại ngay tại đầu hàm `run_corruption_flow_pipeline()`, in ra hướng dẫn rõ ràng yêu cầu chạy Phase 1 trước nếu phát hiện thiếu artifact.
- **Cách xác minh sau khi sửa:** Khi chạy theo đúng trình tự Phase 1 -> Phase 2, toàn bộ luồng hoạt động mượt mà, tải đầy đủ số liệu và xuất ra bảng đối chiếu hoàn chỉnh.
- **Điều học được:** Trong thiết kế pipeline MLOps nhiều giai đoạn, các chốt kiểm soát tiên quyết (Prerequisite Gates) và thông báo lỗi tường minh giúp tiết kiệm rất nhiều thời gian gỡ rối.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index:**  
   Crossref API -> Raw JSON -> Bóc tách PaperRecord -> Clean DataFrame (loại bỏ null, deduplicate, tính age_days, format text) -> SentenceTransformer sinh embedding vector -> Đánh chỉ mục Persistent ChromaDB.
2. **Evaluation set và ground-truth document IDs:**  
   Đóng vai trò là bài thi chuẩn hóa cố định. Mỗi câu hỏi gắn liền với DOI gốc. Khi truy vấn, hệ thống đo lường xem mô hình có đưa đúng tài liệu chứa đáp án vào top-k hay không.
3. **Quality checks khác freshness monitoring:**  
   Quality checks đo độ đúng đắn của cấu trúc dữ liệu tại thời điểm xử lý (schema contract). Freshness monitoring đo lường độ trôi dạt về mặt thời gian (temporal relevance), đảm bảo dữ liệu không bị lỗi thời.
4. **Tại sao phải dùng chung test set:**  
   Để bảo đảm tính khách quan trong phương pháp nghiên cứu thực nghiệm. Khi giữ nguyên test set, mọi sự suy giảm hay phục hồi của chỉ số đều xuất phát từ chất lượng của dữ liệu được lập chỉ mục.
5. **Dấu hiệu chứng minh phục hồi thành công:**  
   Các chỉ số hiệu năng (Hit Rate 100%, Token F1 0.520) và trạng thái kiểm định (Quality Gate = True, Freshness = True) tại trạng thái Repaired khớp hoàn toàn với trạng thái Baseline ban đầu.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 100.0% | 80.0% | 100.0% | Giảm 20% ở corrupted do mất bài, phục hồi 100% sau repair |
| `mean_token_f1` | 0.520 | 0.417 | 0.520 | Sụt giảm mạnh do nhiễu văn bản và tóm tắt rỗng |
| `judge_accuracy` | 50.0% | 40.0% | 50.0% | Độ chính xác câu trả lời suy giảm tương ứng |
| `mean_judge_score` | 3.000 | 2.600 | 3.000 | Phản ánh mức độ tin cậy của phản hồi AI |
| Quality checks (GX 1.x) | `True` | `False` | `True` | Chốt chặn Great Expectations phát hiện vi phạm |
| Freshness status | `True` | `False` | `True` | Kích hoạt cảnh báo vi phạm SLA khi 47.6% bài bị cũ |

### Kết luận nhân quả
- Dữ liệu bị tiêm lỗi đã gây ra hiện tượng **Silent Failure**: chương trình vẫn chạy không crash, nhưng chất lượng kết quả trả về bị suy giảm nghiêm trọng (Hit Rate giảm 20%).
- Chốt chặn **Great Expectations 1.x** và **Freshness SLA** đã hoạt động như một hệ thống radar cảnh báo sớm, phát hiện ngay lập tức dữ liệu độc hại trước khi gây hậu quả thực tế.
- Cơ chế **Idempotent Repair** từ raw snapshot đã khôi phục hoàn toàn 100% năng lực hoạt động của hệ thống.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Hiểm họa của Silent Failure trong hệ thống AI**: Trong phần mềm truyền thống, lỗi dữ liệu thường gây crash app; trong hệ thống RAG, lỗi dữ liệu chỉ âm thầm làm AI trả lời sai (hallucination), cực kỳ nguy hiểm nếu không có Data Observability.
2. **Tính Idempotent trong MLOps**: Một pipeline phục hồi dữ liệu phải có tính chất Idempotent - đảm bảo hệ thống có thể tự chữa lành (Self-Healing) một cách nhất quán và tin cậy.
3. **Tách biệt không gian lưu trữ thực nghiệm**: Việc quản lý các collection riêng biệt trong Vector DB là bài học thực tế quý báu để tránh tình trạng Ghost Vectors và ô nhiễm dữ liệu chéo.

### Hướng cải thiện
- Xây dựng dashboard giám sát thời gian thực với Grafana hoặc Streamlit để trực quan hóa các chỉ số Data Quality và RAG Performance theo thời gian thực.
