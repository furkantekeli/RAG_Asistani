import streamlit as st
import config
from models.database import DatabaseManager
from models.document_processor import DocumentProcessor
from models.embedding_service import EmbeddingService
from models.llm_service import LLMService
from controllers.rag_controller import RAGController
from views.components import apply_custom_css, render_sidebar, render_assistant_response


# Configure Streamlit Page
st.set_page_config(
    page_title="Yerel RAG Bilgi Asistanı",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Cached Controller Initialization to prevent reloading models on UI rerenders
@st.cache_resource(show_spinner="Microsoft Foundry Local Yapay Zekâ Modelleri Başlatılıyor...")
def initialize_rag_system():
    db_manager = DatabaseManager()
    doc_processor = DocumentProcessor()
    embedding_service = EmbeddingService()
    llm_service = LLMService()

    controller = RAGController(
        db_manager=db_manager,
        doc_processor=doc_processor,
        embedding_service=embedding_service,
        llm_service=llm_service
    )
    return controller


def main():
    apply_custom_css()

    # Title & Subtitle
    st.markdown('<div class="main-title">🤖 Çevrimdışı RAG Bilgi Asistanı</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Microsoft Foundry Local & SQLite ile Tamamen Yerel, Güvenli Doküman Soru-Cevap Sistemi</div>',
        unsafe_allow_html=True
    )

    # Initialize Controller
    try:
        controller = initialize_rag_system()
    except Exception as e:
        st.error(f"Sistem başlatılırken bir hata oluştu: {str(e)}")
        st.info("Lütfen Foundry Local SDK ve gerekli yapay zeka modellerinin kurulu olduğundan emin olun.")
        st.stop()

    # Render Sidebar and receive user actions
    actions = render_sidebar(controller)

    # Handle File Upload Action
    if actions["upload_button"] and actions["uploaded_file"] is not None:
        file_obj = actions["uploaded_file"]
        file_bytes = file_obj.read()
        filename = file_obj.name

        with st.spinner(f"'{filename}' işleniyor ve vektörleştiriliyor..."):
            result = controller.process_and_index_file(file_bytes, filename)

        if result["success"]:
            st.success(f"✅ {result['message']} (İşlem Süresi: {result['time_taken']:.2f} sn)")
            st.rerun()
        else:
            st.error(f"❌ {result['message']}")

    # Handle Knowledge Base Reset Action
    if actions["clear_button"]:
        controller.clear_knowledge_base()
        st.session_state.messages = []
        st.warning("⚠️ Bilgi tabanı ve sohbet geçmişi başarıyla sıfırlandı.")
        st.rerun()

    # Initialize Session Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                render_assistant_response(message["response_data"])

    # Chat Input Box
    if user_query := st.chat_input("Yüklediğiniz dokümanlar hakkında bir soru sorun..."):
        # Display User Input
        with st.chat_message("user"):
            st.markdown(user_query)
        st.session_state.messages.append({"role": "user", "content": user_query})

        # Process and Display Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Dokümanlar taranıyor ve yerel yanıt üretiliyor..."):
                response_data = controller.answer_question(user_query)
                render_assistant_response(response_data)

            st.session_state.messages.append({
                "role": "assistant",
                "response_data": response_data
            })


if __name__ == "__main__":
    main()