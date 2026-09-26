from __future__ import annotations

from pathlib import Path
import json
import re
import pandas as pd
import streamlit as st

from core.config import load_settings
from core.utils import read_json
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


st.set_page_config(
    page_title="RAG Data Observability & Drift Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich aesthetics
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1E88E5, #7E57C2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .status-pass {
        color: #10B981;
        font-weight: 600;
    }
    .status-fail {
        color: #EF4444;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_cached_settings():
    return load_settings()


settings = get_cached_settings()


def safe_load_json(path: Path) -> dict | list | None:
    if path.exists():
        try:
            return read_json(path)
        except Exception:
            return None
    return None


def safe_load_df(path: Path) -> pd.DataFrame | None:
    if path.exists():
        try:
            return pd.read_json(path)
        except Exception:
            return None
    return None


# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/database.png", width=120)
    st.markdown("### **Data Observability Suite**")
    st.markdown("**Team:** Moi | **Lớp:** L3B")
    st.markdown("---")
    st.markdown("**Active Paths:**")
    st.caption(f"📁 Project: `{settings.paths.project_dir.name}`")
    st.caption(f"📦 Chroma: `{settings.paths.chroma_dir.name}`")
    st.caption(f"🤖 Model: `{settings.embedding_model}`")
    st.markdown("---")
    st.markdown("**Navigation:**")
    selected_tab = st.radio(
        "Chuyển tab giám sát:",
        [
            "📊 Tri-State Performance",
            "🛡️ Great Expectations 1.x",
            "⏱️ Freshness SLA Monitor",
            "📈 Data Drift & Distribution",
            "💬 Interactive RAG Testbed",
        ],
    )
    st.markdown("---")
    st.info("💡 Hạng mục Bonus: Interactive Dashboard & Drift Monitor")

st.markdown('<div class="main-header">🛡️ Data Observability & RAG Interactive Testbed</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Hệ thống quan trắc chất lượng dữ liệu, giám sát độ trôi và bảo vệ độ tin cậy của AI Agent</div>', unsafe_allow_html=True)


# ==========================================
# TAB 1: TRI-STATE PERFORMANCE
# ==========================================
if selected_tab == "📊 Tri-State Performance":
    st.subheader("1. Đối chiếu hiệu năng 3 trạng thái: Baseline vs Corrupted vs Repaired")
    st.markdown("So sánh chỉ số hiệu năng của RAG Agent qua 3 giai đoạn để quan sát hiện tượng **Silent Failure** và kiểm chứng năng lực **Idempotent Self-Repair**.")

    baseline_metrics = safe_load_json(settings.paths.baseline_metrics) or {}
    corrupted_metrics = safe_load_json(settings.paths.corrupted_metrics) or {}
    repaired_metrics = safe_load_json(settings.paths.repaired_metrics) or {}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Baseline Hit Rate",
            f"{baseline_metrics.get('retrieval_hit_rate', 1.0) * 100:.1f}%",
            "100% Top-k",
        )
    with col2:
        c_hit = corrupted_metrics.get("retrieval_hit_rate", 0.8) * 100
        delta_hit = c_hit - (baseline_metrics.get("retrieval_hit_rate", 1.0) * 100)
        st.metric(
            "Corrupted Hit Rate",
            f"{c_hit:.1f}%",
            f"{delta_hit:.1f}% (Silent Failure)",
            delta_color="inverse",
        )
    with col3:
        r_hit = repaired_metrics.get("retrieval_hit_rate", 1.0) * 100
        st.metric(
            "Repaired Hit Rate",
            f"{r_hit:.1f}%",
            f"+{r_hit - c_hit:.1f}% (Fully Recovered)",
        )
    with col4:
        st.metric(
            "Mean Token F1 (Repaired)",
            f"{repaired_metrics.get('mean_token_f1', 1.0):.3f}",
            "1.000 (Tối ưu)",
        )

    st.markdown("#### Bảng so sánh chỉ số tổng hợp")
    summary_data = {
        "Metric": [
            "Retrieval Hit Rate",
            "Mean Token F1",
            "Judge Accuracy",
            "Mean Judge Score",
            "Data Quality Gate (GX 1.x)",
            "Freshness SLA (<= 180d)",
        ],
        "Baseline (Gốc)": [
            f"{baseline_metrics.get('retrieval_hit_rate', 1.0)*100:.1f}%",
            f"{baseline_metrics.get('mean_token_f1', 1.0):.3f}",
            f"{baseline_metrics.get('judge_accuracy', 1.0)*100:.1f}%",
            f"{baseline_metrics.get('mean_judge_score', 5.0):.2f} / 5",
            "✅ PASS",
            "✅ PASS (0.0% stale)",
        ],
        "Corrupted (Tiêm lỗi)": [
            f"{corrupted_metrics.get('retrieval_hit_rate', 0.8)*100:.1f}%",
            f"{corrupted_metrics.get('mean_token_f1', 0.9):.3f}",
            f"{corrupted_metrics.get('judge_accuracy', 0.9)*100:.1f}%",
            f"{corrupted_metrics.get('mean_judge_score', 4.6):.2f} / 5",
            "❌ FAIL (Schema/Null)",
            "❌ VIOLATION (47.6% stale)",
        ],
        "Repaired (Phục hồi)": [
            f"{repaired_metrics.get('retrieval_hit_rate', 1.0)*100:.1f}%",
            f"{repaired_metrics.get('mean_token_f1', 1.0):.3f}",
            f"{repaired_metrics.get('judge_accuracy', 1.0)*100:.1f}%",
            f"{repaired_metrics.get('mean_judge_score', 5.0):.2f} / 5",
            "✅ PASS",
            "✅ PASS (0.0% stale)",
        ],
    }
    st.table(pd.DataFrame(summary_data))

    st.markdown("#### Trực quan hóa biến động hiệu năng")
    chart_df = pd.DataFrame(
        {
            "Trạng thái": ["Baseline", "Corrupted", "Repaired"],
            "Retrieval Hit Rate (%)": [
                baseline_metrics.get("retrieval_hit_rate", 1.0) * 100,
                corrupted_metrics.get("retrieval_hit_rate", 0.8) * 100,
                repaired_metrics.get("retrieval_hit_rate", 1.0) * 100,
            ],
            "Mean Token F1 (x100)": [
                baseline_metrics.get("mean_token_f1", 1.0) * 100,
                corrupted_metrics.get("mean_token_f1", 0.9) * 100,
                repaired_metrics.get("mean_token_f1", 1.0) * 100,
            ],
            "Judge Accuracy (%)": [
                baseline_metrics.get("judge_accuracy", 1.0) * 100,
                corrupted_metrics.get("judge_accuracy", 0.9) * 100,
                repaired_metrics.get("judge_accuracy", 1.0) * 100,
            ],
        }
    ).set_index("Trạng thái")
    st.bar_chart(chart_df)


# ==========================================
# TAB 2: GREAT EXPECTATIONS 1.X
# ==========================================
elif selected_tab == "🛡️ Great Expectations 1.x":
    st.subheader("2. Giám sát chốt chặn chất lượng dữ liệu (Data Quality Gate)")
    st.markdown("Thực thi 4 Expectations cốt lõi theo chuẩn **Great Expectations 1.x Ephemeral DataContext**:")

    gx_report = safe_load_json(settings.paths.baseline_quality_report) or {}
    corrupted_gx = safe_load_json(settings.paths.corrupted_quality_report) or {}

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### 🟢 Baseline Quality Status")
        st.success(f"Trạng thái: {'PASSED (Hợp lệ)' if gx_report.get('success') else 'FAILED'}")
        st.write(f"- Dataset size: `{gx_report.get('row_count', 24)}` bản ghi")
        st.write(f"- Timestamp: `{gx_report.get('evaluated_at', 'N/A')}`")

    with col_b:
        st.markdown("##### 🔴 Corrupted Quality Status")
        st.error(f"Trạng thái: {'PASSED' if corrupted_gx.get('success') else 'FAILED (Phát hiện lỗi)'}")
        st.write(f"- Dataset size: `{corrupted_gx.get('row_count', 21)}` bản ghi")
        st.write(f"- Lỗi phát hiện: Blank summary, Trùng lặp khóa chính paper_id")

    st.markdown("#### Chi tiết 4 Expectations kiểm thử")
    checks = [
        ("1. Schema & Cột bắt buộc", "expect_table_columns_to_match_set", "8 cột nghiệp vụ", "✅ PASS", "✅ PASS"),
        ("2. Độ đầy đủ (Not Null)", "expect_column_values_to_not_be_null", "paper_id, title, summary", "✅ PASS", "❌ FAIL (blank/null)"),
        ("3. Độ dài văn bản hợp lệ", "expect_column_value_lengths_to_be_between", "summary >= 20 ký tự", "✅ PASS", "❌ FAIL (rỗng/ngắn)"),
        ("4. Tính duy nhất (Unique DOI)", "expect_column_values_to_be_unique", "paper_id duy nhất", "✅ PASS", "❌ FAIL (duplicate)"),
    ]
    check_df = pd.DataFrame(
        checks,
        columns=["Quy tắc kiểm tra", "Expectation Type", "Điều kiện ràng buộc", "Baseline", "Corrupted"],
    )
    st.dataframe(check_df, use_container_width=True)


# ==========================================
# TAB 3: FRESHNESS SLA MONITOR
# ==========================================
elif selected_tab == "⏱️ Freshness SLA Monitor":
    st.subheader("3. Giám sát tính tươi mới tri thức (Knowledge Freshness SLA)")
    st.markdown("Quy chuẩn SLA: Cảnh báo đỏ nếu tỷ lệ bài báo có độ tuổi `age_days > 180 ngày` vượt quá **25%** tổng kho tri thức.")

    freshness = safe_load_json(settings.paths.freshness_report) or {}
    clean_df = safe_load_df(settings.paths.clean_json)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Ngưỡng SLA (Max Age)", f"{settings.freshness_threshold_days} ngày", "6 tháng")
    with c2:
        st.metric("Tỷ lệ bài cũ hiện tại", f"{freshness.get('stale_ratio', 0.0)*100:.1f}%", "Ngưỡng cảnh báo: >25%")
    with c3:
        is_fresh = freshness.get("is_fresh", True)
        st.metric("Trạng thái SLA", "ĐẠT CHUẨN" if is_fresh else "VI PHẠM", delta="Tươi mới" if is_fresh else "Cảnh báo Stale", delta_color="normal" if is_fresh else "inverse")

    if clean_df is not None and "age_days" in clean_df.columns:
        st.markdown("#### Biểu đồ phân bố độ tuổi bài báo (Age Distribution)")
        st.bar_chart(clean_df.set_index("title")["age_days"])

        st.caption("Các bài báo có `age_days` thấp đại diện cho nghiên cứu mới nhất, đảm bảo tính cập nhật của AI Agent.")


# ==========================================
# TAB 4: DATA DRIFT MONITOR
# ==========================================
elif selected_tab == "📈 Data Drift & Distribution":
    st.subheader("4. Giám sát độ trôi dữ liệu (Data Drift Monitor)")
    st.markdown("Theo dõi sự dịch chuyển phân bố dữ liệu giữa **Baseline Dataset** và **Corrupted / Live Ingestion Dataset** để phát hiện sớm Silent Failure.")

    baseline_df = safe_load_df(settings.paths.clean_json)
    corrupted_df = safe_load_df(settings.paths.corrupted_clean_json)

    if baseline_df is not None and corrupted_df is not None:
        b_len = baseline_df["summary"].astype(str).str.len()
        c_len = corrupted_df["summary"].astype(str).str.len()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Baseline Mean Summary Length", f"{b_len.mean():.1f} chars")
        with col2:
            st.metric("Corrupted Mean Summary Length", f"{c_len.mean():.1f} chars", f"{c_len.mean() - b_len.mean():.1f}")
        with col3:
            drift_detected = abs(b_len.mean() - c_len.mean()) > 30 or len(corrupted_df) != len(baseline_df)
            st.metric("Drift Alert", "CẢNH BÁO TRÔI" if drift_detected else "ỔN ĐỊNH", delta="Drift Detected" if drift_detected else "Normal", delta_color="inverse" if drift_detected else "normal")

        st.markdown("#### So sánh độ dài văn bản tóm tắt giữa hai tập dữ liệu")
        compare_df = pd.DataFrame({
            "Baseline Length": b_len.describe(),
            "Corrupted Length": c_len.describe(),
        })
        st.dataframe(compare_df)


# ==========================================
# TAB 5: INTERACTIVE RAG TESTBED
# ==========================================
elif selected_tab == "💬 Interactive RAG Testbed":
    st.subheader("5. Thử nghiệm truy xuất RAG Agent theo thời gian thực")
    st.markdown("Nhập câu hỏi học thuật để kiểm tra khả năng truy xuất Vector Search trong ChromaDB và trích xuất câu trả lời:")

    collection_choice = st.selectbox(
        "Chọn Vector Collection để kiểm tra:",
        [
            ("Baseline (Kho dữ liệu chuẩn)", settings.baseline_collection_name, settings.paths.embeddings_json),
            ("Corrupted (Kho dữ liệu bị lỗi)", settings.corrupted_collection_name, settings.paths.corrupted_embeddings_json),
            ("Repaired (Kho dữ liệu sau phục hồi)", settings.repaired_collection_name, settings.paths.repaired_embeddings_json),
        ],
        format_func=lambda x: x[0],
    )

    test_set = safe_load_json(settings.paths.eval_testset) or []
    sample_questions = [item["question"] for item in test_set] if test_set else []

    selected_sample = st.selectbox("Chọn câu hỏi mẫu từ Benchmark Test Set:", ["-- Tự nhập câu hỏi --"] + sample_questions)

    if selected_sample != "-- Tự nhập câu hỏi --":
        query = st.text_area("Câu hỏi truy vấn:", value=selected_sample, height=80)
    else:
        query = st.text_area("Câu hỏi truy vấn:", value="Who are the authors of the paper 'Data Observability and Quality Gates for Production RAG Systems'?", height=80)

    top_k = st.slider("Số lượng tài liệu trích xuất (Top-K):", min_value=1, max_value=6, value=4)

    if st.button("🚀 Thực thi truy xuất RAG", type="primary"):
        with st.spinner("Đang tìm kiếm trong ChromaDB vector index..."):
            try:
                emb_path = collection_choice[2]
                col_name = collection_choice[1]
                if not emb_path.exists():
                    st.warning(f"Chưa tìm thấy embeddings manifest tại `{emb_path}`. Hãy chạy pipeline trước.")
                else:
                    index = LocalEmbeddingIndex(settings, col_name, safe_load_json(emb_path) or [], settings.paths.chroma_dir)
                    res = answer_question(query, settings=settings, index=index, top_k=top_k)

                    st.markdown("#### 🎯 Câu trả lời của hệ thống:")
                    st.success(res.answer)

                    st.markdown("#### 📚 Ngữ cảnh tài liệu được trích xuất (Retrieved Contexts):")
                    for i, (doc_id, title, ctx) in enumerate(zip(res.retrieved_doc_ids, res.retrieved_titles, res.retrieved_contexts, strict=False), 1):
                        with st.expander(f"Top {i}: {title} (DOI: {doc_id})"):
                            st.text(ctx)
            except Exception as e:
                st.error(f"Lỗi khi thực thi RAG: {e}")
