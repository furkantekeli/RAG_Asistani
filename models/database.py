import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Tuple, Any
import config


class DatabaseManager:
    """
    Manages SQLite database connections, schema creation, document indexing,
    and vector queries for the RAG pipeline.
    """

    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a new SQLite database connection."""
        return sqlite3.connect(self.db_path)

    def _initialize_schema(self) -> None:
        """Creates the required tables if they do not exist, or resets legacy schemas."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if legacy table exists and lacks new columns
            cursor.execute("PRAGMA table_info(dokumanlar)")
            columns = [col[1] for col in cursor.fetchall()]

            if columns and "dosya_adi" not in columns:
                cursor.execute("DROP TABLE dokumanlar")
                conn.commit()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS dokumanlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dosya_adi TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    icerik TEXT NOT NULL,
                    vektor TEXT NOT NULL,
                    eklenme_tarihi TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def insert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Inserts a list of document chunks into the database.
        Each chunk is a dict with: 'dosya_adi', 'chunk_index', 'icerik', 'vektor' (list of floats).
        Returns the number of inserted chunks.
        """
        now = datetime.now().isoformat()
        records = [
            (
                chunk["dosya_adi"],
                chunk["chunk_index"],
                chunk["icerik"],
                json.dumps(chunk["vektor"]),
                now
            )
            for chunk in chunks
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO dokumanlar (dosya_adi, chunk_index, icerik, vektor, eklenme_tarihi)
                VALUES (?, ?, ?, ?, ?)
                """,
                records
            )
            conn.commit()

        return len(records)

    def get_all_chunks(self) -> List[Tuple[int, str, int, str, List[float]]]:
        """
        Retrieves all document chunks from the database.
        Returns a list of tuples: (id, dosya_adi, chunk_index, icerik, vector_list)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, dosya_adi, chunk_index, icerik, vektor FROM dokumanlar"
            )
            rows = cursor.fetchall()

        parsed_rows = []
        for r_id, dosya_adi, chunk_idx, icerik, vektor_json in rows:
            parsed_rows.append((r_id, dosya_adi, chunk_idx, icerik, json.loads(vektor_json)))

        return parsed_rows

    def clear_database(self) -> None:
        """Clears all records from the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dokumanlar")
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistical overview of the database (total chunks, unique files)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), COUNT(DISTINCT dosya_adi) FROM dokumanlar")
            total_chunks, unique_files = cursor.fetchone()

            cursor.execute("SELECT DISTINCT dosya_adi FROM dokumanlar")
            file_list = [row[0] for row in cursor.fetchall()]

        return {
            "total_chunks": total_chunks or 0,
            "unique_files_count": unique_files or 0,
            "file_names": file_list
        }
