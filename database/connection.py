import sqlite3
import os
from pathlib import Path
from typing import Generator, Optional
from contextlib import contextmanager

from src.utils.paths import DATABASE_PATH, ensure_dir
from src.utils.logging import app_logger
from database.models import (
    CREATE_FOODS_TABLE,
    CREATE_NUTRITION_TABLE,
    CREATE_FOOD_PRICES_TABLE,
    CREATE_EMPLOYEES_TABLE,
    CREATE_USER_PROFILES_TABLE,
    CREATE_FOOD_PREFERENCES_TABLE,
    CREATE_FACE_EMBEDDINGS_TABLE,
    CREATE_MEAL_TRANSACTIONS_TABLE,
    CREATE_MEAL_TRANSACTION_ITEMS_TABLE,
    CREATE_INDEXES
)


def get_db_path() -> Path:
    """Returns the configured database path, ensuring the parent directory exists."""
    ensure_dir(DATABASE_PATH.parent)
    return DATABASE_PATH


@contextmanager
def get_db_connection(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that yields a thread-safe SQLite connection with row_factory set to sqlite3.Row.
    Automatically commits on success or rolls back on exception.
    """
    path = db_path or get_db_path()
    conn = sqlite3.connect(str(path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")

    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        app_logger.error(f"Database error during transaction: {e}")
        raise
    finally:
        conn.close()


def init_database(db_path: Optional[Path] = None) -> None:
    """
    Initializes the SQLite database tables and indexes if they do not already exist.
    """
    path = db_path or get_db_path()
    app_logger.info(f"Initializing Smart Canteen database at: {path}")

    with get_db_connection(path) as conn:
        cursor = conn.cursor()
        # Phase 2 tables
        cursor.execute(CREATE_FOODS_TABLE)
        cursor.execute(CREATE_NUTRITION_TABLE)
        cursor.execute(CREATE_FOOD_PRICES_TABLE)
        # Phase 3 tables
        cursor.execute(CREATE_EMPLOYEES_TABLE)
        cursor.execute(CREATE_USER_PROFILES_TABLE)
        cursor.execute(CREATE_FOOD_PREFERENCES_TABLE)
        # Phase 4 tables
        cursor.execute(CREATE_FACE_EMBEDDINGS_TABLE)
        # Phase 5 tables
        cursor.execute(CREATE_MEAL_TRANSACTIONS_TABLE)
        cursor.execute(CREATE_MEAL_TRANSACTION_ITEMS_TABLE)

        for idx_sql in CREATE_INDEXES:
            cursor.execute(idx_sql)

    app_logger.info("Database tables and indexes initialized successfully.")

