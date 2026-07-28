import time
from typing import Dict, Any, List
import config
from models.database import DatabaseManager
from models.document_processor import DocumentProcessor
from models.embedding_service import EmbeddingService
from models.llm_service import LLMService


class RAGController:
    """
    Main controller orchestrating the RAG pipeline end-to-end:
    - Document Ingestion & Chunking
    - Vector Embedding Generation & Storage
    - Query Embedding & Similarity Retrieval
    - Grounded LLM Response Generation & Metrics Tracking
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        doc_processor: DocumentProcessor,
        embedding_service: EmbeddingService,
        llm_service: LLMService
    ):
        self.db = db_manager
        self.doc_processor = doc_processor
        self.embedding_service = embedding_service
        self.llm_service = llm_service

    def process_and_index_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parses a file, splits into chunks, generates vector embeddings, and stores in DB.
        Returns a summary dict with chunk counts and processing time.
        """
        start_time = time.time()

        # 1. Extract text
        raw_text = self.doc_processor.extract_text_from_file(file_content, filename)
        if not raw_text.strip():
            return {
                "success": False,
                "message": "Dosya boş veya okunabilir metin içerik bulunamadı.",
                "chunks_count": 0,
                "time_taken": 0.0
            }

        # 2. Chunk text
        chunks = self.doc_processor.split_text_into_chunks(raw_text, filename)
        if not chunks:
            return {
                "success": False,
                "message": "Dosya anlamlı metin parçalarına bölünemedi.",
                "chunks_count": 0,
                "time_taken": 0.0
            }

        # 3. Generate embeddings
        for chunk in chunks:
            vector = self.embedding_service.generate_embedding(chunk["icerik"])
            chunk["vektor"] = vector

        # 4. Save to Database
        inserted_count = self.db.insert_chunks(chunks)
        elapsed = time.time() - start_time

        return {
            "success": True,
            "message": f"'{filename}' başarıyla işlendi ve {inserted_count} metin parçasına bölünüp veritabanına indekslendi.",
            "chunks_count": inserted_count,
            "time_taken": elapsed
        }

    def answer_question(self, user_query: str) -> Dict[str, Any]:
        """
        Processes a user question through the retrieval and generation pipeline.
        Enforces confidence thresholding and measures latency.
        """
        start_time = time.time()

        # Check DB state
        stats = self.db.get_stats()
        if stats["total_chunks"] == 0:
            return {
                "answer": "Henüz herhangi bir doküman yüklenmedi. Lütfen sol panelden bir dosya yükleyin.",
                "confidence_score": 0.0,
                "status": "NO_DOCUMENTS",
                "sources": [],
                "time_taken": 0.0
            }

        # 1. Vectorize User Query
        query_vector = self.embedding_service.generate_embedding(user_query)

        # 2. Retrieve All DB Chunks & Calculate Similarities
        all_chunks = self.db.get_all_chunks()
        top_matches = self.embedding_service.find_top_relevant_chunks(
            query_vector, all_chunks, top_k=config.TOP_K_RESULTS
        )

        top_score = top_matches[0]["score"] if top_matches else 0.0

        # 3. Confidence Threshold Guardrail Check
        if top_score < config.SIMILARITY_THRESHOLD:
            elapsed = time.time() - start_time
            return {
                "answer": "Bu sorunun cevabı yüklenen dokümanlarda bulunmamaktadır.",
                "confidence_score": top_score,
                "status": "BELOW_THRESHOLD",
                "sources": top_matches,
                "time_taken": elapsed
            }

        # 4. Generate LLM Grounded Answer
        answer = self.llm_service.generate_answer(user_query, top_matches)
        elapsed = time.time() - start_time

        return {
            "answer": answer,
            "confidence_score": top_score,
            "status": "SUCCESS",
            "sources": top_matches,
            "time_taken": elapsed
        }

    def clear_knowledge_base(self) -> Dict[str, Any]:
        """Resets and clears all indexed documents from the database."""
        self.db.clear_database()
        return {
            "success": True,
            "message": "Bilgi tabanı ve tüm vektör indeksleri sıfırlandı."
        }

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Returns database statistics."""
        return self.db.get_stats()
