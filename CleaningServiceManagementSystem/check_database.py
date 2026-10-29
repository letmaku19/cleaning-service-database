import sqlite3

DB_NAME = "cleaning_service.db"

try:
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        print("DATABASE TABLES:", cursor.fetchall())
        for table in ("customers", "schedules", "users"):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"TOTAL {table.upper()}:", cursor.fetchone()[0])
except sqlite3.Error as error:
    print("DATABASE ERROR:", error)
