import streamlit as st
from typing import Dict, Any, List


def apply_custom_css():
    """Applies custom CSS for a polished, modern, Senior-level UI appearance."""
    st.markdown("""
        <style>
        /* Modern Header & Card Styling */
        .main-title {
            font-size: 2.2rem;
            font-weight: 800;
            background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }
        .sub-title {
            font-size: 1.0rem;
            color: #888;
            margin-bottom: 1.5rem;
        }
        .metric-card {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            margin-bottom: 10px;
        }
        .badge-success {
            background-color: #28a745;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .badge-warning {
            background-color: #ffc107;
            color: #212529;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .badge-info {
            background-color: #17a2b8;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .source-box {
            background-color: rgba(0, 0, 0, 0.2);
            border-left: 3px solid #00C9FF;
            padding: 10px;
            border-radius: 4px;
            margin-top: 8px;
            font-size: 0.88rem;
        }
        </style>
    """, unsafe_allow_html=True)


def render_sidebar(controller) -> Dict[str, Any]:
    """
    Renders the sidebar containing file upload, stats, and control buttons.
    Returns any user actions triggered (e.g., uploaded file or reset command).
    """
    with st.sidebar:
        st.header("📂 Doküman Yükleme & Yönetim")
        st.caption("Desteklenen Formatlar: `.txt`, `.md`, `.pdf`")

        # File Upload Widget
        uploaded_file = st.file_uploader(
            "Bilgi Tabanına Eklemek İçin Dosya Seçin",
            type=["txt", "md", "pdf"],
            accept_multiple_files=False
        )

        upload_button = False
        if uploaded_file is not None:
            upload_button = st.button("📥 Dokümanı İşle ve İndeksle", type="primary", use_container_width=True)

        st.divider()

        # Knowledge Base Statistics
        st.subheader("📊 Bilgi Tabanı Durumu")
        stats = controller.get_knowledge_base_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Dosya Sayısı", stats["unique_files_count"])
        with col2:
            st.metric("Metin Parçası", stats["total_chunks"])

        if stats["file_names"]:
            with st.expander("📄 İndekslenen Dosya Listesi"):
                for fn in stats["file_names"]:
                    st.text(f"• {fn}")

        st.divider()

        # Management Controls
        st.subheader("⚙️ Sistem Kontrolleri")
        clear_button = st.button("🗑️ Bilgi Tabanını Sıfırla", type="secondary", use_container_width=True)

        st.divider()
        st.markdown("**Çalışma Zamanı (AI Runtime)**")
        st.markdown("🟢 **Foundry Local SDK** (Çevrimdışı / Offline)")
        st.caption("• Embedding: `qwen3-embedding-0.6b`\n• LLM: `phi-3.5-mini`")

    return {
        "uploaded_file": uploaded_file,
        "upload_button": upload_button,
        "clear_button": clear_button
    }


def render_assistant_response(response_data: Dict[str, Any]):
    """
    Renders the assistant's response message with source attribution expanders and badges.
    """
    st.markdown(response_data["answer"])

    # Badges & Latency
    score = response_data.get("confidence_score", 0.0)
    status = response_data.get("status", "UNKNOWN")
    time_taken = response_data.get("time_taken", 0.0)

    if status == "SUCCESS":
        badge_html = f'<span class="badge-success">🎯 Güven Skoru: {score:.4f}</span>'
    elif status == "BELOW_THRESHOLD":
        badge_html = f'<span class="badge-warning">⚠️ Güven Skoru: {score:.4f} (Eşik Altı)</span>'
    else:
        badge_html = '<span class="badge-info">ℹ️ Bilgi Yok</span>'

    st.markdown(
        f"{badge_html} &nbsp;&nbsp; ⏱️ *Yanıt Süresi: {time_taken:.2f} saniye*",
        unsafe_allow_html=True
    )

    # Sources Attribution Expander
    sources = response_data.get("sources", [])
    if sources and status == "SUCCESS":
        with st.expander("🔍 Kullanılan Bağlam ve Kaynak Metin Parçaları"):
            for idx, src in enumerate(sources, 1):
                st.markdown(
                    f"<div class='source-box'>"
                    f"<b>Kaynak {idx}:</b> {src['dosya_adi']} (Parça #{src['chunk_index']})<br/>"
                    f"<b>Benzerlik Skoru:</b> {src['score']:.4f}<br/>"
                    f"<i>\"{src['icerik']}\"</i>"
                    f"</div>",
                    unsafe_allow_html=True
                )
