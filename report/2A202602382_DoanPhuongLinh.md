# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                  |
| ----------------- | ------------------------------------------------------------------------- |
| Họ và tên         | Đoàn Phương Linh                                                          |
| MSSV              | 2A202602382                                                               |
| Khóa/Lớp          | K4 / L3B                                                                  |
| Tên nhóm          | Moi                                                                       |
| Vai trò chính     | Data Observability & Quality Assurance                                    |
| Repository        | https://github.com/Tamle25/K4-L3B-DAY10-Moi-DataPipelineDataObservability |
| Ngày hoàn thành   | 2026-09-26                                                                |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Data Quality Gate (Bước 4) | `src/observability/quality.py`<br>- `run_data_quality_checks()`<br>- `evaluate_freshness_sla()`<br>- `build_freshness_report()` | DataFrame sạch hoặc DataFrame bị lỗi | `data/quality/*_quality_report.json`<br>`data/quality/freshness_report.json` | Hoàn thành |
| Benchmark Testset Generator (Bước 5) | `src/evaluation/testset.py`<br>- `build_test_set()`<br>- Các builder câu hỏi theo nhóm | DataFrame sạch (`papers_clean.json`) | `data/eval/test_set.json` (10 câu hỏi chuẩn hóa) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Kiểm định dữ liệu đầu vào Ingestion | Lê Công Tâm (`cleaning.py`) | Đưa ra yêu cầu schema cần có các cột `paper_id`, `title`, `summary`, `age_days`, `text_for_embedding` để Quality Gate có thể kiểm định |
| Đánh giá chất lượng mô hình | Nguyễn Mạnh Tiến (`phase1.py` & `corruption_flow.py`) | Cung cấp bộ test set chuẩn 10 câu để pipeline đo lường các chỉ số Hit Rate và Token F1 trên cả 3 trạng thái |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Thiết lập chốt kiểm soát GX 1.x & Freshness SLA | `src/observability/quality.py` | Cài đặt 4 Expectations và logic Freshness SLA cảnh báo khi bài cũ > 25% | Chạy lệnh test Bước 4: in ra `Tín hiệu hoàn thành: Quality check status = True` |
| Sinh bộ đề kiểm thử chuẩn 10 câu hỏi | `src/evaluation/testset.py` | Sinh đủ 10 câu Ground Truth phân bổ đều qua 4 loại: summary, authors, date, categories | Chạy lệnh test Bước 5: in ra `Tín hiệu hoàn thành: Sinh được 10 câu hỏi test` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Thiết lập chốt kiểm soát tự động trước khi nạp Vector DB**: Dữ liệu bẩn nếu lọt vào Vector Database sẽ gây ra hiện tượng suy thoái chất lượng âm thầm (Silent Failure). Cần một chốt chặn tự động kiểm tra tính đúng đắn về số lượng dòng, tính duy nhất, trường bắt buộc và độ dài tối thiểu.
2. **Giám sát độ tươi mới của dữ liệu (Freshness SLA)**: Tri thức AI cần được cập nhật thường xuyên. Nếu tài liệu quá cũ (trên 180 ngày) chiếm tỷ lệ cao trong cơ sở tri thức, AI sẽ đưa ra câu trả lời lỗi thời.
3. **Chuẩn hóa bộ đề đánh giá Ground Truth**: Cần một tập câu hỏi kiểm thử khách quan, đại diện và có đáp án chuẩn để lượng hóa chính xác năng lực truy xuất thông tin của RAG Agent.

### Cách triển khai
- **Cấu hình Great Expectations 1.x Ephemeral Context**: Sử dụng kiến trúc hiện đại của GX 1.x không phụ thuộc file config tĩnh:
  ```python
  context = gx.get_context(mode="ephemeral")
  data_source = context.data_sources.add_pandas(name="papers_source")
  data_asset = data_source.add_dataframe_asset(name="papers_asset")
  batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
  ```
- **4 Hàng rào kiểm định bắt buộc**:
  1. `ExpectTableRowCountToBeBetween(min_value=5, max_value=5000)`: Đảm bảo tập dữ liệu không bị rỗng hoặc quá tải.
  2. `ExpectColumnValuesToNotBeNull`: Áp dụng cho `paper_id`, `title`, `text_for_embedding`.
  3. `ExpectColumnValuesToBeUnique`: Áp dụng cho `paper_id` nhằm chống trùng lặp vector.
  4. `ExpectColumnValueLengthsToBeBetween(min_value=30)`: Đảm bảo trường `summary` có đầy đủ thông tin ngữ nghĩa.
- **Freshness SLA Monitoring**: Hàm `evaluate_freshness_sla()` tính toán tỷ lệ dòng có `age_days > 180`. Nếu tỷ lệ vượt quá ngưỡng `0.25` (25%), trả về `is_fresh = False` và kích hoạt warning.
- **Benchmark Testset Builder**: Thuật toán phân bổ 10 câu hỏi qua 4 nhóm nghiệp vụ:
  - `summary` (3 câu): Trích xuất câu đầu tiên của abstract làm Ground Truth.
  - `authors` (3 câu): Danh sách tác giả chính xác.
  - `date` (2 câu): Ngày xuất bản chuẩn YYYY-MM-DD.
  - `categories` (2 câu): Lĩnh vực nghiên cứu.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | pandas DataFrame từ bước Clean hoặc Corrupted |
| Output | Báo cáo kiểm định `baseline_quality_report.json`, `corrupted_quality_report.json`, `test_set.json` |
| Module phụ thuộc | Thư viện `great_expectations 1.x`, `pandas`, `core.config.Settings` |
| Module sử dụng output | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `evaluation.metrics` |
| Điều kiện lỗi cần xử lý | DataFrame rỗng, thiếu cột kiểm tra, dữ liệu trùng lặp hoặc summary rỗng |

### Cách xác minh

```powershell
# Xác minh Bước 4: Quality Checks
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print('Tín hiệu hoàn thành: Quality check status =', res['success'])"

# Xác minh Bước 5: Benchmark Test Set
python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print(f'Tín hiệu hoàn thành: Sinh được {len(ts)} câu hỏi test')"
```

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Great Expectations phiên bản 1.x có sự thay đổi mang tính đột phá về API so với phiên bản cũ 0.18.x (chuyển từ DataContext dạng file tĩnh `great_expectations.yml` sang Fluent Data Source và Ephemeral Context trực tiếp trong mã nguồn).
- **Các phương án đã cân nhắc:**
  1. Khởi tạo thư mục `gx/` trên đĩa và quản lý qua CLI `great_expectations init`.
  2. Sử dụng Ephemeral Context hoàn toàn trong bộ nhớ (`gx.get_context(mode="ephemeral")`).
- **Phương án đã chọn:** Phương án 2 (Ephemeral Context).
- **Lý do:** Giúp mã nguồn tinh gọn, không phát sinh các file cấu hình YAML cồng kềnh trong repo Git, dễ dàng tích hợp vào CI/CD hoặc container hóa sau này mà không lo ngại vấn đề sai lệch đường dẫn thư mục làm việc.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  KeyError: 'expectation_type' khi đọc kết quả từ ExpectationSuiteValidationResult trong GX 1.x
  ```
- **Lệnh tái hiện:** Truy cập trực tiếp thuộc tính `er["expectation_type"]` trên đối tượng `ExpectationValidationResult` của GX 1.x.
- **Nguyên nhân gốc:** Trong API GX 1.x, cấu trúc trả về là đối tượng Pydantic, trường loại expectation được chuyển vào `er.expectation_config.type` thay vì dict key trực tiếp.
- **Cách xử lý:** Cập nhật lại cách trích xuất kết quả chi tiết:
  ```python
  "expectation_type": er.expectation_config.type,
  "success": bool(er.success),
  "kwargs": {k: v for k, v in er.expectation_config.kwargs.items() if k != "batch_id"}
  ```
- **Cách xác minh sau khi sửa:** Kết quả kiểm định được serialize chuẩn xác ra tệp JSON trong `data/quality/` mà không phát sinh lỗi.
- **Điều học được:** Khi làm việc với các thư viện vừa nâng cấp phiên bản lớn (Major Release), cần đọc kỹ migration guide của nhà phát triển để nắm bắt đúng Object Model mới.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index:**  
   Metadata bài báo được cào về từ API công khai -> Lưu bản thô -> Làm sạch và định dạng trường tổng hợp `text_for_embedding` -> Đưa qua chốt kiểm định Data Quality Gate -> Nếu đạt tiêu chuẩn mới được nạp vào ChromaDB để chuyển đổi thành vector không gian đa chiều.
2. **Evaluation set và ground-truth document IDs:**  
   Tập test gồm 10 câu hỏi chuẩn hóa đi kèm định danh bài báo gốc (`ground_truth_doc_ids`). Chỉ số `retrieval_hit_rate` được tính bằng tỷ lệ số câu hỏi mà tài liệu đúng được xếp hạng trong top-4 kết quả vector search.
3. **Sự khác biệt giữa Quality checks và Freshness monitoring:**  
   Quality checks bảo đảm dữ liệu có cấu trúc hợp lệ (không null, không trùng, đúng định dạng). Freshness monitoring bảo đảm dữ liệu mang tính thời sự, bảo vệ AI khỏi tri thức lỗi thời dù dữ liệu đó hoàn toàn hợp lệ về mặt cấu trúc.
4. **Tại sao phải dùng chung test set:**  
   Duy trì tính nhất quán của thước đo. Để chứng minh tác động của sự cố dữ liệu (Corruption) và hiệu quả của cơ chế phục hồi (Repair), tập câu hỏi thử nghiệm bắt buộc phải cố định.
5. **Dấu hiệu chứng minh phục hồi thành công:**  
   Data Quality Gate chuyển từ `False` về `True`, Freshness SLA trở về trạng thái tươi mới (`is_fresh = True`), và Retrieval Hit Rate của RAG Agent khôi phục từ 80% lên 100%.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 100.0% | 80.0% | 100.0% | Bị sụt giảm 20% do tập dữ liệu mất các bài báo mới nhất |
| `mean_token_f1` | 0.520 | 0.417 | 0.520 | Độ chính xác token giảm mạnh do summary bị hỏng và dính nhiễu |
| `judge_accuracy` | 50.0% | 40.0% | 50.0% | AI trả lời sai do ngữ cảnh retrieved bị sai lệch |
| `mean_judge_score` | 3.000 | 2.600 | 3.000 | Điểm số chất lượng câu trả lời bị giảm |
| Quality checks (GX 1.x) | `True` | `False` | `True` | Bắt lỗi chính xác ngay khi có bản ghi rỗng hoặc trùng |
| Freshness status | `True` | `False` | `True` | Đạt SLA ở baseline, cảnh báo đỏ ở corrupted (47.6% bài cũ) |

### Kết luận nhân quả
- Lỗi dữ liệu `Blank summary` và `Duplicate rows` đã ngay lập tức kích hoạt cờ đỏ của Great Expectations (`Quality Gate = False`), giúp đội ngũ kỹ thuật phát hiện sự cố trước khi dữ liệu độc hại được phục vụ người dùng.
- Cơ chế `repair_from_raw_snapshot` đã đưa toàn bộ 4 Expectation và Freshness SLA trở về trạng thái đạt chuẩn (`True`), khôi phục hoàn toàn chất lượng trả lời của mô hình.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Kiến trúc Data Observability chủ động**: Không chờ người dùng phàn nàn AI trả lời sai mới đi tìm lỗi; phải đặt chốt kiểm định tự động chặn dữ liệu bẩn ngay tại đường ống Ingestion.
2. **Sức mạnh của Great Expectations 1.x**: Việc khai báo các ràng buộc chất lượng dưới dạng code (Expectations as Code) mang lại tính minh bạch và khả năng tự động hóa kiểm định cao.
3. **Bộ đề đánh giá là kim chỉ nam**: Một bộ test set chuẩn với ground-truth doc IDs rõ ràng là cơ sở duy nhất để lượng hóa chính xác mức độ suy thoái hay phục hồi của AI.

### Hướng cải thiện
- Mở rộng Expectation Suite sang kiểm tra phân phối embedding (ngăn chặn hiện tượng trôi dạt dữ liệu - Data Drift).
