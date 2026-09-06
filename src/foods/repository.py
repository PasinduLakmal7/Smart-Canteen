import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from database.connection import get_db_connection
from src.foods.schemas import FoodItem, FoodCreate, FoodUpdate, ServingType


class FoodRepository:
    """
    SQLite Data Access Layer for the `foods` catalog table.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def get_all(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """Retrieves all food records from the database."""
        query = "SELECT * FROM foods"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY id ASC;"

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_by_id(self, food_id: int) -> Optional[Dict[str, Any]]:
        """Finds a food record by integer ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM foods WHERE id = ?;", (food_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_class_name(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Finds a food record by exact YOLO class_name."""
        sanitized = class_name.strip().lower().replace(" ", "_").replace("-", "_")
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM foods WHERE class_name = ?;", (sanitized,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create(self, food: FoodCreate) -> Dict[str, Any]:
        """Inserts a new food item into the catalog."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO foods (class_name, display_name, serving_type, standard_serving_g, active)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    food.class_name,
                    food.display_name,
                    food.serving_type.value,
                    food.standard_serving_g,
                    1 if food.active else 0
                )
            )
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM foods WHERE id = ?;", (new_id,))
            return dict(cursor.fetchone())

    def update(self, food_id: int, update_data: FoodUpdate) -> Optional[Dict[str, Any]]:
        """Updates specific fields of an existing food item."""
        updates = []
        params = []

        if update_data.display_name is not None:
            updates.append("display_name = ?")
            params.append(update_data.display_name)
        if update_data.serving_type is not None:
            updates.append("serving_type = ?")
            params.append(update_data.serving_type.value)
        if update_data.standard_serving_g is not None:
            updates.append("standard_serving_g = ?")
            params.append(update_data.standard_serving_g)
        if update_data.active is not None:
            updates.append("active = ?")
            params.append(1 if update_data.active else 0)

        if not updates:
            return self.get_by_id(food_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(food_id)

        sql = f"UPDATE foods SET {', '.join(updates)} WHERE id = ?;"

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            if cursor.rowcount == 0:
                return None
            cursor.execute("SELECT * FROM foods WHERE id = ?;", (food_id,))
            return dict(cursor.fetchone())

    def delete(self, food_id: int) -> bool:
        """Deactivates (soft deletes) or removes a food item."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE foods SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (food_id,))
            return cursor.rowcount > 0
