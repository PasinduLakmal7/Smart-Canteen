import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from database.connection import get_db_connection
from src.profiles.schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    UserProfileCreate,
    UserProfileUpdate,
    FoodPreferenceSet
)


class ProfileRepository:
    """
    SQLite Data Access Layer for Employees, User Profiles, and Food Preferences.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    # ==========================================
    # 1. EMPLOYEE CRUD
    # ==========================================
    def get_all_employees(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Lists all employees."""
        query = "SELECT * FROM employees"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY id ASC;"

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_employee_by_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Finds an employee by integer ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE id = ?;", (employee_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_employee_by_code(self, employee_code: str) -> Optional[Dict[str, Any]]:
        """Finds an employee by unique employee code (e.g. EMP001)."""
        clean_code = employee_code.strip().upper()
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE employee_code = ?;", (clean_code,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_employee_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Finds an employee by email."""
        clean_email = email.strip().lower()
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE email = ?;", (clean_email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_employee(self, emp: EmployeeCreate) -> Dict[str, Any]:
        """Creates a new employee record."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO employees (employee_code, first_name, last_name, department, email, active)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    emp.employee_code,
                    emp.first_name,
                    emp.last_name,
                    emp.department,
                    emp.email,
                    1 if emp.active else 0
                )
            )
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM employees WHERE id = ?;", (new_id,))
            return dict(cursor.fetchone())

    def update_employee(self, employee_id: int, update_data: EmployeeUpdate) -> Optional[Dict[str, Any]]:
        """Updates employee basic info."""
        updates = []
        params = []

        if update_data.first_name is not None:
            updates.append("first_name = ?")
            params.append(update_data.first_name)
        if update_data.last_name is not None:
            updates.append("last_name = ?")
            params.append(update_data.last_name)
        if update_data.department is not None:
            updates.append("department = ?")
            params.append(update_data.department)
        if update_data.email is not None:
            updates.append("email = ?")
            params.append(update_data.email)
        if update_data.active is not None:
            updates.append("active = ?")
            params.append(1 if update_data.active else 0)

        if not updates:
            return self.get_employee_by_id(employee_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(employee_id)

        sql = f"UPDATE employees SET {', '.join(updates)} WHERE id = ?;"

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            if cursor.rowcount == 0:
                return None
            cursor.execute("SELECT * FROM employees WHERE id = ?;", (employee_id,))
            return dict(cursor.fetchone())

    def deactivate_employee(self, employee_id: int) -> bool:
        """Deactivates an employee."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE employees SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (employee_id,))
            return cursor.rowcount > 0

    # ==========================================
    # 2. USER PROFILE CRUD
    # ==========================================
    def get_profile_by_employee_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves nutrition & biometric profile for an employee."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE employee_id = ?;", (employee_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_profile(self, employee_id: int, profile_in: UserProfileCreate) -> Dict[str, Any]:
        """Creates a nutrition profile for an employee."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_profiles (
                    employee_id, age, height_cm, weight_kg, daily_calorie_target,
                    diet_type, health_goal, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    employee_id,
                    profile_in.age,
                    profile_in.height_cm,
                    profile_in.weight_kg,
                    profile_in.daily_calorie_target,
                    profile_in.diet_type.value,
                    profile_in.health_goal.value,
                    profile_in.notes or ""
                )
            )
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM user_profiles WHERE id = ?;", (new_id,))
            return dict(cursor.fetchone())

    def update_profile(self, employee_id: int, update_data: UserProfileUpdate) -> Optional[Dict[str, Any]]:
        """Updates biometric and dietary goals for an employee."""
        updates = []
        params = []

        if update_data.age is not None:
            updates.append("age = ?")
            params.append(update_data.age)
        if update_data.height_cm is not None:
            updates.append("height_cm = ?")
            params.append(update_data.height_cm)
        if update_data.weight_kg is not None:
            updates.append("weight_kg = ?")
            params.append(update_data.weight_kg)
        if update_data.daily_calorie_target is not None:
            updates.append("daily_calorie_target = ?")
            params.append(update_data.daily_calorie_target)
        if update_data.diet_type is not None:
            updates.append("diet_type = ?")
            params.append(update_data.diet_type.value)
        if update_data.health_goal is not None:
            updates.append("health_goal = ?")
            params.append(update_data.health_goal.value)
        if update_data.notes is not None:
            updates.append("notes = ?")
            params.append(update_data.notes)

        if not updates:
            return self.get_profile_by_employee_id(employee_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(employee_id)

        sql = f"UPDATE user_profiles SET {', '.join(updates)} WHERE employee_id = ?;"

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            return self.get_profile_by_employee_id(employee_id)

    # ==========================================
    # 3. FOOD PREFERENCES CRUD
    # ==========================================
    def get_preferences(self, employee_id: int) -> Dict[str, List[str]]:
        """Retrieves food preferences partitioned by likes, dislikes, and avoid."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT food_name, preference_type FROM food_preferences WHERE employee_id = ?;", (employee_id,))
            rows = cursor.fetchall()

            res = {"likes": [], "dislikes": [], "avoid": []}
            for row in rows:
                ptype = row["preference_type"]
                fname = row["food_name"]
                if ptype == "like":
                    res["likes"].append(fname)
                elif ptype == "dislike":
                    res["dislikes"].append(fname)
                elif ptype == "avoid":
                    res["avoid"].append(fname)
            return res

    def set_preferences(self, employee_id: int, prefs: FoodPreferenceSet) -> Dict[str, List[str]]:
        """Replaces all food preferences for an employee."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            # Clear existing preferences
            cursor.execute("DELETE FROM food_preferences WHERE employee_id = ?;", (employee_id,))

            for food in prefs.likes:
                cursor.execute(
                    "INSERT INTO food_preferences (employee_id, food_name, preference_type) VALUES (?, ?, 'like');",
                    (employee_id, food.strip().lower())
                )
            for food in prefs.dislikes:
                cursor.execute(
                    "INSERT INTO food_preferences (employee_id, food_name, preference_type) VALUES (?, ?, 'dislike');",
                    (employee_id, food.strip().lower())
                )
            for food in prefs.avoid:
                cursor.execute(
                    "INSERT INTO food_preferences (employee_id, food_name, preference_type) VALUES (?, ?, 'avoid');",
                    (employee_id, food.strip().lower())
                )

            cursor.execute("SELECT food_name, preference_type FROM food_preferences WHERE employee_id = ?;", (employee_id,))
            rows = cursor.fetchall()
            res = {"likes": [], "dislikes": [], "avoid": []}
            for row in rows:
                ptype = row["preference_type"]
                fname = row["food_name"]
                if ptype == "like":
                    res["likes"].append(fname)
                elif ptype == "dislike":
                    res["dislikes"].append(fname)
                elif ptype == "avoid":
                    res["avoid"].append(fname)
            return res
