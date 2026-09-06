"""
SQLite Database Repository for Phase 4 Face Biometric Embeddings.
Manages persistent storage, active filtering, and sample retrieval for face embeddings.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from database.connection import get_db_connection, init_database
from src.face_recognition.schemas import EnrolledEmployeeSummary
from src.utils.logging import app_logger


class FaceRepository:
    """Handles CRUD operations for employee face embeddings in SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        init_database(self.db_path)

    def save_embedding(
        self,
        employee_id: int,
        embedding: List[float],
        model_name: str = "yunet_sface_128d",
        sample_tag: str = "frontal",
        quality_score: float = 1.0
    ) -> int:
        """
        Inserts a new face embedding record for an employee.
        Returns the created record ID.
        """
        embedding_json = json.dumps([round(float(x), 6) for x in embedding])
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO face_embeddings (
                    employee_id, embedding, model_name, sample_tag, quality_score, active
                ) VALUES (?, ?, ?, ?, ?, 1);
                """,
                (employee_id, embedding_json, model_name, sample_tag, quality_score)
            )
            emb_id = cursor.lastrowid
            app_logger.info(f"Saved face embedding {emb_id} for employee ID {employee_id} (tag: {sample_tag}).")
            return emb_id

    def get_all_active_embeddings(self) -> List[Dict[str, Any]]:
        """
        Retrieves all active face embeddings joined with employee metadata.
        Returns a list of dicts with parsed float embeddings.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    fe.id,
                    fe.employee_id,
                    fe.sample_tag,
                    fe.quality_score,
                    fe.model_name,
                    fe.embedding,
                    e.employee_code,
                    e.first_name,
                    e.last_name,
                    e.department
                FROM face_embeddings fe
                JOIN employees e ON fe.employee_id = e.id
                WHERE fe.active = 1 AND e.active = 1;
                """
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                try:
                    vec = json.loads(r["embedding"])
                    results.append({
                        "id": r["id"],
                        "employee_id": r["employee_id"],
                        "employee_code": r["employee_code"],
                        "name": f"{r['first_name']} {r['last_name']}",
                        "department": r["department"],
                        "sample_tag": r["sample_tag"],
                        "quality_score": r["quality_score"],
                        "model_name": r["model_name"],
                        "embedding": vec
                    })
                except Exception as e:
                    app_logger.warning(f"Skipping corrupted embedding ID {r['id']}: {e}")
            return results

    def get_embeddings_by_employee(self, employee_id: int) -> List[Dict[str, Any]]:
        """Retrieves all active embeddings for a specific employee."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, employee_id, sample_tag, quality_score, model_name, embedding, created_at
                FROM face_embeddings
                WHERE employee_id = ? AND active = 1;
                """,
                (employee_id,)
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "employee_id": r["employee_id"],
                    "sample_tag": r["sample_tag"],
                    "quality_score": r["quality_score"],
                    "model_name": r["model_name"],
                    "embedding": json.loads(r["embedding"]),
                    "created_at": r["created_at"]
                })
            return results

    def list_enrolled_employees(self) -> List[EnrolledEmployeeSummary]:
        """Lists summaries of all employees who have enrolled face samples."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    e.id AS employee_id,
                    e.employee_code,
                    e.first_name,
                    e.last_name,
                    e.department,
                    COUNT(fe.id) AS sample_count,
                    GROUP_CONCAT(fe.sample_tag) AS sample_tags,
                    MAX(fe.created_at) AS last_updated,
                    e.active
                FROM employees e
                JOIN face_embeddings fe ON e.id = fe.employee_id
                WHERE fe.active = 1 AND e.active = 1
                GROUP BY e.id;
                """
            )
            rows = cursor.fetchall()
            summaries = []
            for r in rows:
                raw_tags = r["sample_tags"] or ""
                tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                summaries.append(EnrolledEmployeeSummary(
                    employee_id=r["employee_id"],
                    employee_code=r["employee_code"],
                    name=f"{r['first_name']} {r['last_name']}",
                    department=r["department"],
                    sample_count=r["sample_count"],
                    sample_tags=tags,
                    active=bool(r["active"])
                ))
            return summaries

    def deactivate_by_employee(self, employee_id: int) -> int:
        """Deactivates all biometric face embeddings for an employee."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE face_embeddings SET active = 0 WHERE employee_id = ?;",
                (employee_id,)
            )
            count = cursor.rowcount
            app_logger.info(f"Deactivated {count} face embeddings for employee ID {employee_id}.")
            return count

    def delete_by_employee(self, employee_id: int) -> int:
        """Hard-deletes all face embeddings for an employee."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM face_embeddings WHERE employee_id = ?;", (employee_id,))
            return cursor.rowcount
