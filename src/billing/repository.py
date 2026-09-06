import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

from database.connection import get_db_connection
from src.billing.schemas import PriceUpdate


class BillingRepository:
    """
    SQLite Data Access Layer for the `food_prices` table.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def get_current_price_by_food_id(self, food_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves the active price record for a given food ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM food_prices
                WHERE food_id = ? AND active = 1
                ORDER BY id DESC LIMIT 1;
                """,
                (food_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_current_price_by_class_name(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves the active price for a food item by YOLO class_name."""
        sanitized = class_name.strip().lower().replace(" ", "_").replace("-", "_")
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*, f.class_name, f.display_name, f.serving_type AS food_serving_type
                FROM food_prices p
                JOIN foods f ON p.food_id = f.id
                WHERE f.class_name = ? AND f.active = 1 AND p.active = 1
                ORDER BY p.id DESC LIMIT 1;
                """,
                (sanitized,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def set_price(self, food_id: int, price_in: PriceUpdate) -> Dict[str, Any]:
        """
        Updates food price. Deactivates previous active price and inserts new active record
        to maintain an immutable audit trail for research & financial auditing.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # 1. Fetch current serving_type if not provided
            cursor.execute("SELECT serving_type FROM foods WHERE id = ?;", (food_id,))
            food_row = cursor.fetchone()
            default_serving = food_row["serving_type"] if food_row else "piece"
            serving_type = price_in.serving_type or default_serving

            # 2. Deactivate previous active price
            cursor.execute(
                """
                UPDATE food_prices
                SET active = 0, effective_to = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE food_id = ? AND active = 1;
                """,
                (food_id,)
            )

            # 3. Insert new price record
            cursor.execute(
                """
                INSERT INTO food_prices (food_id, serving_type, price, active)
                VALUES (?, ?, ?, 1);
                """,
                (food_id, serving_type, price_in.price)
            )
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM food_prices WHERE id = ?;", (new_id,))
            return dict(cursor.fetchone())
