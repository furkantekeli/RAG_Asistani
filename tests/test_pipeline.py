import os
import sys
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.document_processor import DocumentProcessor
from models.database import DatabaseManager
import config


class TestRAGComponents(unittest.TestCase):

    def setUp(self):
        self.doc_processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        self.test_db_path = os.path.join(os.path.dirname(__file__), "test_rag.db")
        self.db_manager = DatabaseManager(db_path=self.test_db_path)

    def tearDown(self):
        self.db_manager.clear_database()
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

    def test_document_processor_chunking(self):
        sample_text = (
            "Bu proje yerel yapay zeka asistanı olarak tasarlanmıştır. "
            "Kullanıcılar kendi dokümanlarını yükleyebilirler. "
            "Sistem tamamen internetsiz ve güvenli bir şekilde çalışır. "
            "Foundry Local altyapısı kullanılmaktadır."
        )
        chunks = self.doc_processor.split_text_into_chunks(sample_text, "test.txt")
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0]["dosya_adi"], "test.txt")
        self.assertEqual(chunks[0]["chunk_index"], 0)

    def test_database_operations(self):
        sample_chunks = [
            {
                "dosya_adi": "rehber.txt",
                "chunk_index": 0,
                "icerik": "Yerel RAG asistanı rehberi.",
                "vektor": [0.1, 0.2, 0.3, 0.4]
            },
            {
                "dosya_adi": "rehber.txt",
                "chunk_index": 1,
                "icerik": "Foundry Local kurulum adımları.",
                "vektor": [0.5, 0.6, 0.7, 0.8]
            }
        ]

        inserted = self.db_manager.insert_chunks(sample_chunks)
        self.assertEqual(inserted, 2)

        stats = self.db_manager.get_stats()
        self.assertEqual(stats["total_chunks"], 2)
        self.assertEqual(stats["unique_files_count"], 1)
        self.assertIn("rehber.txt", stats["file_names"])

        all_chunks = self.db_manager.get_all_chunks()
        self.assertEqual(len(all_chunks), 2)
        self.assertEqual(all_chunks[0][3], "Yerel RAG asistanı rehberi.")
        self.assertEqual(all_chunks[0][4], [0.1, 0.2, 0.3, 0.4])


if __name__ == "__main__":
    unittest.main()
