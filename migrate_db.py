import sqlite3
import os

DB_FILE = "data/truecheck.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print("Database file not found (it might be created on app startup).")
        return

    print(f"Connecting to database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if classroom_id column exists in user table
    cursor.execute("PRAGMA table_info(user)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "classroom_id" not in columns:
        print("Adding classroom_id column to user table...")
        try:
            # SQLite supports ADD COLUMN
            cursor.execute("ALTER TABLE user ADD COLUMN classroom_id INTEGER REFERENCES classroom(id)")
            conn.commit()
            print("Migration successful: Added classroom_id to user table.")
        except Exception as e:
            print(f"Migration failed: {e}")
    else:
        print("classroom_id column already exists in user table.")

    conn.close()

if __name__ == "__main__":
    migrate()
