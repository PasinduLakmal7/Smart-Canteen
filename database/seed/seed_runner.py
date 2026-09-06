import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.utils.paths import FOODS_SEED_PATH, EMPLOYEES_SEED_PATH, FACE_SEED_PATH, DATABASE_PATH
from src.utils.logging import app_logger
from database.connection import get_db_connection, init_database



def seed_foods_if_empty(seed_file: Optional[Path] = None, db_path: Optional[Path] = None) -> int:
    """
    Seeds the database with initial foods, nutrition, and price records if the foods table is empty.
    Returns the count of seeded items.
    """
    init_database(db_path)
    seed_p = seed_file or FOODS_SEED_PATH

    if not seed_p.exists():
        app_logger.warning(f"Food seed file not found at: {seed_p}")
        return 0

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM foods;")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            app_logger.info(f"Database already contains {existing_count} food records. Skipping food seed.")
            return existing_count

        with open(seed_p, "r", encoding="utf-8") as f:
            food_items: List[Dict[str, Any]] = json.load(f)

        seeded_count = 0
        for item in food_items:
            class_name = item["class_name"]
            display_name = item["display_name"]
            serving_type = item.get("serving_type", "piece")
            standard_serving_g = float(item.get("standard_serving_g", 100.0))
            price = float(item.get("price", 0.0))
            nutr = item.get("nutrition", {})

            # 1. Insert food
            cursor.execute(
                """
                INSERT INTO foods (class_name, display_name, serving_type, standard_serving_g, active)
                VALUES (?, ?, ?, ?, 1);
                """,
                (class_name, display_name, serving_type, standard_serving_g)
            )
            food_id = cursor.lastrowid

            # 2. Insert nutrition
            cursor.execute(
                """
                INSERT INTO nutrition (
                    food_id, basis_type, basis_amount, calories_kcal,
                    protein_g, carbs_g, fat_g, sugar_g, fiber_g, sodium_mg,
                    source_name, source_reference, verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    food_id,
                    nutr.get("basis_type", "per_unit"),
                    float(nutr.get("basis_amount", 1.0)),
                    float(nutr.get("calories_kcal", 0.0)),
                    float(nutr.get("protein_g", 0.0)),
                    float(nutr.get("carbs_g", 0.0)),
                    float(nutr.get("fat_g", 0.0)),
                    float(nutr.get("sugar_g", 0.0)),
                    float(nutr.get("fiber_g", 0.0)),
                    float(nutr.get("sodium_mg", 0.0)),
                    nutr.get("source_name", "MRI Sri Lanka"),
                    nutr.get("source_reference", "Standard Sri Lankan Food Tables"),
                    int(nutr.get("verified", 1))
                )
            )

            # 3. Insert food price
            cursor.execute(
                """
                INSERT INTO food_prices (food_id, serving_type, price, active)
                VALUES (?, ?, ?, 1);
                """,
                (food_id, serving_type, price)
            )
            seeded_count += 1

        app_logger.info(f"Successfully seeded {seeded_count} foods into SQLite database.")
        return seeded_count


def seed_employees_if_empty(seed_file: Optional[Path] = None, db_path: Optional[Path] = None) -> int:
    """
    Seeds the database with sample employee profiles and food preferences if the employees table is empty.
    Returns the count of seeded employees.
    """
    init_database(db_path)
    seed_p = seed_file or EMPLOYEES_SEED_PATH

    if not seed_p.exists():
        app_logger.warning(f"Employees seed file not found at: {seed_p}")
        return 0

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees;")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            app_logger.info(f"Database already contains {existing_count} employees. Skipping employee seed.")
            return existing_count

        with open(seed_p, "r", encoding="utf-8") as f:
            employees_data: List[Dict[str, Any]] = json.load(f)

        seeded_count = 0
        for emp in employees_data:
            code = emp["employee_code"]
            fname = emp["first_name"]
            lname = emp["last_name"]
            dept = emp["department"]
            email = emp["email"]
            prof = emp.get("profile", {})
            prefs = emp.get("preferences", {})

            # 1. Insert Employee
            cursor.execute(
                """
                INSERT INTO employees (employee_code, first_name, last_name, department, email, active)
                VALUES (?, ?, ?, ?, ?, 1);
                """,
                (code, fname, lname, dept, email)
            )
            emp_id = cursor.lastrowid

            # 2. Insert User Profile
            if prof:
                cursor.execute(
                    """
                    INSERT INTO user_profiles (
                        employee_id, age, height_cm, weight_kg, daily_calorie_target,
                        diet_type, health_goal, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        emp_id,
                        int(prof.get("age", 30)),
                        float(prof.get("height_cm", 170.0)),
                        float(prof.get("weight_kg", 70.0)),
                        float(prof.get("daily_calorie_target", 2000.0)),
                        prof.get("diet_type", "normal"),
                        prof.get("health_goal", "maintain"),
                        prof.get("notes", "")
                    )
                )

            # 3. Insert Food Preferences
            if prefs:
                for food in prefs.get("likes", []):
                    cursor.execute(
                        "INSERT OR IGNORE INTO food_preferences (employee_id, food_name, preference_type) VALUES (?, ?, 'like');",
                        (emp_id, food)
                    )
                for food in prefs.get("dislikes", []):
                    cursor.execute(
                        "INSERT OR IGNORE INTO food_preferences (employee_id, food_name, preference_type) VALUES (?, ?, 'dislike');",
                        (emp_id, food)
                    )
                for food in prefs.get("avoid", []):
                    cursor.execute(
                        "INSERT OR IGNORE INTO food_preferences (employee_id, food_name, preference_type) VALUES (?, ?, 'avoid');",
                        (emp_id, food)
                    )

            seeded_count += 1

        app_logger.info(f"Successfully seeded {seeded_count} employee profiles into SQLite database.")
        return seeded_count


def seed_faces_if_empty(seed_file: Optional[Path] = None, db_path: Optional[Path] = None) -> int:
    """
    Seeds the database with initial employee face embeddings if the face_embeddings table is empty.
    Returns the count of seeded embeddings.
    """
    init_database(db_path)
    seed_p = seed_file or FACE_SEED_PATH

    if not seed_p.exists():
        app_logger.warning(f"Face seed file not found at: {seed_p}")
        return 0

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM face_embeddings;")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            app_logger.info(f"Database already contains {existing_count} face embeddings. Skipping face seed.")
            return existing_count

        with open(seed_p, "r", encoding="utf-8") as f:
            face_records: List[Dict[str, Any]] = json.load(f)

        seeded_count = 0
        for item in face_records:
            emp_code = item["employee_code"]
            cursor.execute("SELECT id FROM employees WHERE employee_code = ?;", (emp_code,))
            row = cursor.fetchone()
            if not row:
                app_logger.warning(f"Cannot seed face embedding: Employee '{emp_code}' not found in DB.")
                continue

            emp_id = row["id"]
            emb_json = json.dumps([round(float(x), 6) for x in item["embedding"]])
            model_name = item.get("model_name", "sface_128d")
            sample_tag = item.get("sample_tag", "frontal")
            quality_score = float(item.get("quality_score", 1.0))

            cursor.execute(
                """
                INSERT INTO face_embeddings (
                    employee_id, embedding, model_name, sample_tag, quality_score, active
                ) VALUES (?, ?, ?, ?, ?, 1);
                """,
                (emp_id, emb_json, model_name, sample_tag, quality_score)
            )
            seeded_count += 1

        app_logger.info(f"Successfully seeded {seeded_count} face embeddings into SQLite database.")
        return seeded_count


def seed_database_if_empty(db_path: Optional[Path] = None) -> int:
    """Convenience function that seeds foods, employees, and face embeddings if empty."""
    f_count = seed_foods_if_empty(db_path=db_path)
    seed_employees_if_empty(db_path=db_path)
    seed_faces_if_empty(db_path=db_path)
    return f_count

