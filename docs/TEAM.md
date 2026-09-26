# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `Moi`
- **Mã Nhóm / Lớp:** `K4-L3B-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-DAY10-Moi-DataPipelineDataObservability`
- **Đường Dẫn Repository:** `https://github.com/Tamle25/K4-L3B-DAY10-Moi-DataPipelineDataObservability`

---

## 1. Danh sách thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân | Đóng góp |
|---:|---|---|---|---|---|:---:|
| 1 | Lê Công Tâm | 2A202602406 | tam.lc2602406@st.vinuni.edu.vn | Trưởng nhóm / Data Ingestion & Fault Injection (`crossref.py`, `cleaning.py`, `corruption.py`) | [`report/2A202602406_LeCongTam.md`](../report/2A202602406_LeCongTam.md) | 33.3% |
| 2 | Đoàn Phương Linh | 2A202602382 | linh.dp2602382@st.vinuni.edu.vn | Data Observability & Quality Assurance (`quality.py` GX 1.x, `testset.py`, Freshness SLA) | [`report/2A202602382_DoanPhuongLinh.md`](../report/2A202602382_DoanPhuongLinh.md) | 33.3% |
| 3 | Nguyễn Mạnh Tiến | 2A202602506 | tien.nm2602506@st.vinuni.edu.vn | Pipeline Integration & Resilience (`phase1.py`, `corruption_flow.py`, ChromaDB, MLOps) | [`report/2A202602506_NguyenManhTien.md`](../report/2A202602506_NguyenManhTien.md) | 33.3% |

---

## 2. Chi tiết phân công công việc từng thành viên

### 2.1. Lê Công Tâm - 2A202602406 (Lead)
- **Vai trò:** Data Ingestion & Fault Injection (Lead).
- **Phần việc phụ trách:**
  - **Bước 0:** Khởi tạo repository nhóm, đổi tên repo đúng quy ước `K4-L3B-DAY10-Moi-DataPipelineDataObservability`, mời các thành viên làm Collaborator, chuẩn hóa Git config.
  - **Bước 2:** Xây dựng module thu thập Crossref API với cơ chế Retry & Fallback offline trong `src/ingestion/crossref.py`, bảo toàn 2 bản thô nguyên bản (`crossref_response.json`, `crossref_records.json`).
  - **Bước 3:** Chuẩn hóa schema dữ liệu, khử trùng lặp theo `paper_id`, tính toán trường `age_days` và ghép chuỗi ngữ cảnh `text_for_embedding` trong `src/ingestion/cleaning.py`.
  - **Bước 7:** Thiết kế bộ tiêm lỗi thực nghiệm (Synthetic Data Corruption Suite) trong `src/ingestion/corruption.py` gồm 6 kịch bản lỗi, tự động rebuild lại trường embedding và ghi nhật ký chi tiết ra `data/results/corruption_log.json`.
- **Đóng góp chính / Bài học kỹ thuật:**
  - Kỹ thuật bảo toàn dữ liệu gốc (Raw Preservation) làm mỏ neo phục hồi (Lineage Anchor), ngăn ngừa rủi ro giới hạn truy cập API và bảo đảm tính tái hiện dữ liệu.

### 2.2. Đoàn Phương Linh - 2A202602382
- **Vai trò:** Data Observability & Quality Assurance.
- **Phần việc phụ trách:**
  - **Bước 4:** Thiết lập chốt kiểm soát chất lượng tự động sử dụng **Great Expectations 1.x Ephemeral Context** trong `src/observability/quality.py` với 4 Expectations bắt buộc (`ExpectTableRowCountToBeBetween`, `ExpectColumnValuesToNotBeNull`, `ExpectColumnValuesToBeUnique`, `ExpectColumnValueLengthsToBeBetween`).
  - **Giám sát Freshness SLA:** Xây dựng hàm `evaluate_freshness_sla()` theo dõi độ tươi mới dữ liệu, kích hoạt cảnh báo vi phạm khi tỷ lệ bài báo cũ (> 180 ngày) vượt quá 25%.
  - **Bước 5:** Xây dựng bộ đề đánh giá chuẩn hóa (Benchmark Test Set) gồm 10 câu hỏi Ground Truth phân bổ đều qua 4 dạng bài toán (`summary`, `authors`, `date`, `categories`) trong `src/evaluation/testset.py`.
- **Đóng góp chính / Bài học kỹ thuật:**
  - Nắm vững kiến trúc Ephemeral Context hiện đại của Great Expectations 1.x, hiểu sâu sắc cách thiết lập chốt chặn chất lượng tự động ngăn ngừa dữ liệu lỗi lọt vào Vector DB.

### 2.3. Nguyễn Mạnh Tiến - 2A202602506
- **Vai trò:** Pipeline Integration & Resilience (MLOps).
- **Phần việc phụ trách:**
  - **Bước 1:** Khởi tạo môi trường ảo `.venv`, cài đặt gói dự án ở chế độ phát triển, kiểm tra kết nối các thư viện cốt lõi (`chromadb`, `great_expectations`, `sentence_transformers`), hỗ trợ đồng bộ hóa môi trường nhóm.
  - **Bước 6:** Hoàn thiện pipeline toàn tuyến Phase 1 trong `src/pipelines/phase1.py` và script `script/run_phase1.py`: kết nối luồng Ingest ➔ Clean ➔ ChromaDB Index (`papers-baseline`) ➔ Testset ➔ Đánh giá Hit Rate & Token F1 ➔ Quality Gate và xuất báo cáo `phase1_report.md`.
  - **Bước 8:** Hoàn thiện luồng đối chiếu và tự phục hồi trong `src/pipelines/corruption_flow.py` và script `script/run_corruption_flow.py`: đo lường sự suy thoái khi tiêm lỗi (Silent Failure), kích hoạt cơ chế Idempotent Repair (`repair_from_raw_snapshot`), đánh giá lại hệ thống và xuất bảng đối chiếu 3 trạng thái tại `corruption_report.md`.
  - **Bước 9:** Quản trị hồ sơ nhóm `docs/TEAM.md`, kiểm tra Git hygiene, bảo đảm không lọt secret hay file rác lên repository.
- **Đóng góp chính / Bài học kỹ thuật:**
  - Tư duy thiết kế Idempotent Pipeline trong MLOps, hiểu rõ cơ chế cô lập không gian vector (Vector Isolation) để chứng minh hiện tượng phục hồi chất lượng một cách khoa học.
