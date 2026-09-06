from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import sqlite3

from database.connection import get_db_connection
from src.utils.logging import app_logger


class TransactionRepository:
    """
    SQLite WAL Data Access Repository for Meal Transactions & Itemized Records.
    Guarantees atomic multi-table inserts and immutable snapshot retrieval.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def create_transaction(self, tx_data: Dict[str, Any], items: List[Dict[str, Any]]) -> int:
        """
        Atomically records a new meal transaction along with all itemized snapshot rows.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            insert_tx_sql = """
            INSERT INTO meal_transactions (
                transaction_code, employee_id, total_calories, total_protein,
                total_carbs, total_fat, total_sugar, total_fiber, total_sodium_mg,
                total_amount, payment_status, payment_method, transaction_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP));
            """
            cursor.execute(insert_tx_sql, (
                tx_data["transaction_code"],
                tx_data["employee_id"],
                float(tx_data.get("total_calories", 0.0)),
                float(tx_data.get("total_protein", 0.0)),
                float(tx_data.get("total_carbs", 0.0)),
                float(tx_data.get("total_fat", 0.0)),
                float(tx_data.get("total_sugar", 0.0)),
                float(tx_data.get("total_fiber", 0.0)),
                float(tx_data.get("total_sodium_mg", 0.0)),
                float(tx_data.get("total_amount", 0.0)),
                tx_data.get("payment_status", "completed"),
                tx_data.get("payment_method", "payroll"),
                tx_data.get("transaction_date")
            ))
            tx_id = cursor.lastrowid

            insert_item_sql = """
            INSERT INTO meal_transaction_items (
                transaction_id, food_id, food_name, display_name, quantity,
                serving_size_g, calories, protein, carbs, fat, sugar, fiber,
                sodium_mg, unit_price, subtotal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            for item in items:
                cursor.execute(insert_item_sql, (
                    tx_id,
                    item.get("food_id"),
                    item["food_name"],
                    item["display_name"],
                    int(item.get("quantity", 1)),
                    float(item.get("serving_size_g", 100.0)),
                    float(item.get("calories", 0.0)),
                    float(item.get("protein", 0.0)),
                    float(item.get("carbs", 0.0)),
                    float(item.get("fat", 0.0)),
                    float(item.get("sugar", 0.0)),
                    float(item.get("fiber", 0.0)),
                    float(item.get("sodium_mg", 0.0)),
                    float(item.get("unit_price", 0.0)),
                    float(item.get("subtotal", 0.0))
                ))

            return tx_id

    def get_transaction_by_id(self, tx_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single transaction with employee info and itemized lines."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = """
            SELECT t.*, e.employee_code, e.first_name, e.last_name, e.department, e.email
            FROM meal_transactions t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.id = ?;
            """
            cursor.execute(sql, (tx_id,))
            row = cursor.fetchone()
            if not row:
                return None

            tx_dict = dict(row)
            items_cursor = conn.cursor()
            items_cursor.execute("SELECT * FROM meal_transaction_items WHERE transaction_id = ? ORDER BY id ASC;", (tx_id,))
            tx_dict["items"] = [dict(i) for i in items_cursor.fetchall()]
            return tx_dict

    def get_transaction_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Retrieves a transaction by human-readable transaction code (e.g. TX-20260905-0001)."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = """
            SELECT t.*, e.employee_code, e.first_name, e.last_name, e.department, e.email
            FROM meal_transactions t
            JOIN employees e ON t.employee_id = e.id
            WHERE t.transaction_code = ?;
            """
            cursor.execute(sql, (code.strip().upper(),))
            row = cursor.fetchone()
            if not row:
                return None

            tx_dict = dict(row)
            items_cursor = conn.cursor()
            items_cursor.execute("SELECT * FROM meal_transaction_items WHERE transaction_id = ? ORDER BY id ASC;", (tx_dict["id"],))
            tx_dict["items"] = [dict(i) for i in items_cursor.fetchall()]
            return tx_dict

    def list_employee_transactions(
        self,
        employee_id: int,
        date_filter: Optional[str] = None,
        month_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lists transactions for a specific employee with date / month filters."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            conditions = ["t.employee_id = ?"]
            params: List[Any] = [employee_id]

            if date_filter:
                conditions.append("DATE(t.transaction_date) = DATE(?)")
                params.append(date_filter)
            elif month_filter:
                conditions.append("strftime('%Y-%m', t.transaction_date) = ?")
                params.append(month_filter)

            where_clause = " AND ".join(conditions)
            sql = f"""
            SELECT t.*, e.employee_code, e.first_name, e.last_name, e.department
            FROM meal_transactions t
            JOIN employees e ON t.employee_id = e.id
            WHERE {where_clause}
            ORDER BY t.transaction_date DESC, t.id DESC
            LIMIT ? OFFSET ?;
            """
            params.extend([limit, offset])
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            results = []
            for r in rows:
                tx_dict = dict(r)
                items_cursor = conn.cursor()
                items_cursor.execute("SELECT * FROM meal_transaction_items WHERE transaction_id = ?;", (tx_dict["id"],))
                tx_dict["items"] = [dict(i) for i in items_cursor.fetchall()]
                results.append(tx_dict)

            return results

    def get_employee_monthly_stats(self, employee_id: int, month: str) -> Dict[str, Any]:
        """Calculates aggregated meal and calorie stats for an employee in a given month (YYYY-MM)."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            sql = """
            SELECT 
                COUNT(id) as total_meals,
                COALESCE(SUM(total_calories), 0.0) as total_calories,
                COALESCE(SUM(total_amount), 0.0) as total_spent,
                COALESCE(SUM(total_protein), 0.0) as total_protein,
                COALESCE(SUM(total_carbs), 0.0) as total_carbs,
                COALESCE(SUM(total_fat), 0.0) as total_fat,
                COUNT(DISTINCT DATE(transaction_date)) as active_days
            FROM meal_transactions
            WHERE employee_id = ? AND strftime('%Y-%m', transaction_date) = ?;
            """
            cursor.execute(sql, (employee_id, month))
            row = cursor.fetchone()
            return dict(row) if row else {
                "total_meals": 0, "total_calories": 0.0, "total_spent": 0.0,
                "total_protein": 0.0, "total_carbs": 0.0, "total_fat": 0.0, "active_days": 0
            }

    def list_all_transactions(
        self,
        employee_id: Optional[int] = None,
        date_str: Optional[str] = None,
        department: Optional[str] = None,
        payment_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lists transactions across the canteen with flexible filters for the Admin Portal."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            conditions = ["1=1"]
            params: List[Any] = []

            if employee_id is not None:
                conditions.append("t.employee_id = ?")
                params.append(employee_id)
            if date_str:
                conditions.append("DATE(t.transaction_date) = DATE(?)")
                params.append(date_str)
            if department:
                conditions.append("e.department = ?")
                params.append(department)
            if payment_status:
                conditions.append("t.payment_status = ?")
                params.append(payment_status)

            where_clause = " AND ".join(conditions)
            sql = f"""
            SELECT t.*, e.employee_code, e.first_name, e.last_name, e.department, e.email
            FROM meal_transactions t
            JOIN employees e ON t.employee_id = e.id
            WHERE {where_clause}
            ORDER BY t.transaction_date DESC, t.id DESC
            LIMIT ? OFFSET ?;
            """
            params.extend([limit, offset])
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            results = []
            for r in rows:
                tx_dict = dict(r)
                items_cursor = conn.cursor()
                items_cursor.execute("SELECT * FROM meal_transaction_items WHERE transaction_id = ?;", (tx_dict["id"],))
                tx_dict["items"] = [dict(i) for i in items_cursor.fetchall()]
                results.append(tx_dict)

            return results

    def get_canteen_analytics(self) -> Dict[str, Any]:
        """Calculates global canteen KPIs: total transactions, revenue, today's sales, and top dishes."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Global totals
            cursor.execute("""
            SELECT 
                COUNT(id) as total_tx,
                COALESCE(SUM(total_amount), 0.0) as total_rev,
                COALESCE(SUM(total_calories), 0.0) as total_cals
            FROM meal_transactions;
            """)
            overall = cursor.fetchone()

            # Today's totals
            cursor.execute("""
            SELECT 
                COUNT(id) as today_tx,
                COALESCE(SUM(total_amount), 0.0) as today_rev
            FROM meal_transactions
            WHERE DATE(transaction_date) = DATE('now', 'localtime');
            """)
            today = cursor.fetchone()

            # Top 5 most consumed dishes
            cursor.execute("""
            SELECT 
                food_name,
                display_name,
                SUM(quantity) as total_ordered,
                SUM(subtotal) as total_dish_revenue
            FROM meal_transaction_items
            GROUP BY food_name, display_name
            ORDER BY total_ordered DESC
            LIMIT 5;
            """)
            top_dishes = [dict(r) for r in cursor.fetchall()]

            return {
                "total_transactions": overall["total_tx"] if overall else 0,
                "total_revenue_lkr": float(overall["total_rev"]) if overall else 0.0,
                "total_calories_served": float(overall["total_cals"]) if overall else 0.0,
                "today_transactions": today["today_tx"] if today else 0,
                "today_revenue_lkr": float(today["today_rev"]) if today else 0.0,
                "top_dishes": top_dishes
            }

    def count_transactions(self) -> int:
        """Returns the total number of transactions recorded in the database."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM meal_transactions;")
            return cursor.fetchone()[0]
