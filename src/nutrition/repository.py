import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

from database.connection import get_db_connection
from src.nutrition.schemas import NutritionUpdate


class NutritionRepository:
    """
    SQLite Data Access Layer for the `nutrition` table.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def get_by_food_id(self, food_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves nutrition facts for a given food ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM nutrition WHERE food_id = ?;", (food_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_class_name(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves nutrition facts directly by joining on foods.class_name."""
        sanitized = class_name.strip().lower().replace(" ", "_").replace("-", "_")
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT n.*, f.class_name, f.display_name, f.serving_type, f.standard_serving_g
                FROM nutrition n
                JOIN foods f ON n.food_id = f.id
                WHERE f.class_name = ? AND f.active = 1;
                """,
                (sanitized,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_nutrition(self, food_id: int, update_data: NutritionUpdate) -> Optional[Dict[str, Any]]:
        """Updates nutrition facts for a food item."""
        updates = []
        params = []

        fields = [
            ("basis_type", update_data.basis_type.value if update_data.basis_type else None),
            ("basis_amount", update_data.basis_amount),
            ("calories_kcal", update_data.calories_kcal),
            ("protein_g", update_data.protein_g),
            ("carbs_g", update_data.carbs_g),
            ("fat_g", update_data.fat_g),
            ("sugar_g", update_data.sugar_g),
            ("fiber_g", update_data.fiber_g),
            ("sodium_mg", update_data.sodium_mg),
            ("source_name", update_data.source_name),
            ("source_reference", update_data.source_reference)
        ]

        for col, val in fields:
            if val is not None:
                updates.append(f"{col} = ?")
                params.append(val)

        if not updates:
            return self.get_by_food_id(food_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(food_id)

        sql = f"UPDATE nutrition SET {', '.join(updates)} WHERE food_id = ?;"

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            return self.get_by_food_id(food_id)
