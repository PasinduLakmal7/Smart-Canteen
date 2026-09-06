"""
Smart Canteen Database Layer (Phase 2).
Provides SQLite connection management, table schemas, and seeding utilities.
"""
from database.connection import get_db_connection, init_database
from database.seed.seed_runner import seed_database_if_empty

__all__ = ["get_db_connection", "init_database", "seed_database_if_empty"]
