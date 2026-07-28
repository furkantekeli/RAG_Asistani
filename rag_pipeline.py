"""
Command Line Interface (CLI) for Local RAG Assistant.
Uses the unified RAGController from the MVC architecture.
"""

from models.database import DatabaseManager
from models.document_processor import DocumentProcessor
from models.embedding_service import EmbeddingService
from models.llm_service import LLMService
from controllers.rag_controller import RAGController


def main():
    print("Foundry Local ve Modeller Başlatılıyor...")

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

    print("\n--- YEREL RAG ASİSTANI (Senior MVC CLI Sürümü) ---")
    print("Çıkmak için 'cikis' yazabilirsiniz.\n")

    stats = controller.get_knowledge_base_stats()
    print(f"Mevcut Durum: {stats['unique_files_count']} dosya, {stats['total_chunks']} metin parçası yüklü.")

    while True:
        soru = input("\nSorunuz: ").strip()
        if soru.lower() in ['cikis', 'exit', 'q']:
            break
        if not soru:
            continue

        print("Dokümanlar taranıyor ve cevap üretiliyor...")
        result = controller.answer_question(soru)

        print("\n[Asistanın Yanıtı]:")
        print(result["answer"])
        print(f"*(Güven Skoru: {result['confidence_score']:.4f} | Süre: {result['time_taken']:.2f}s | Durum: {result['status']})*")

    print("\nModeller kapatıldı. İyi çalışmalar!")


if __name__ == "__main__":
    main()