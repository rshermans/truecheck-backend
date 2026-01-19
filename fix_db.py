import sqlite3
import os

# Use the correct database file
DB_FILE = "data/truecheck.db"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

print(f"✅ Using database: {DB_FILE}")

def fix_database():
    print(f"🔧 Fixing database {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Fix AnalysisResult table (add missing columns)
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(analysisresult)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"   Current columns in analysisresult: {columns}")
        
        if "sources_data" not in columns:
            print("   ➕ Adding sources_data column to analysisresult...")
            cursor.execute("ALTER TABLE analysisresult ADD COLUMN sources_data TEXT DEFAULT '[]'")
            
        if "full_json_data" not in columns:
            print("   ➕ Adding full_json_data column to analysisresult...")
            cursor.execute("ALTER TABLE analysisresult ADD COLUMN full_json_data TEXT DEFAULT '{}'")
            
        if "user_id" not in columns:
            print("   ➕ Adding user_id column to analysisresult...")
            cursor.execute("ALTER TABLE analysisresult ADD COLUMN user_id INTEGER REFERENCES user(id)")
            
        if "student_name" not in columns:
            print("   ➕ Adding student_name column to analysisresult...")
            cursor.execute("ALTER TABLE analysisresult ADD COLUMN student_name TEXT DEFAULT 'Anônimo'")
            
        if "verdict" not in columns:
             print("   ➕ Adding verdict column to analysisresult...")
             cursor.execute("ALTER TABLE analysisresult ADD COLUMN verdict TEXT")

        if "discrepancy_level" not in columns:
             print("   ➕ Adding discrepancy_level column to analysisresult...")
             cursor.execute("ALTER TABLE analysisresult ADD COLUMN discrepancy_level TEXT")

    except Exception as e:
        print(f"   ⚠️  Error fixing AnalysisResult: {e}")

    # 2. Create News table if it doesn't exist
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news'")
        if not cursor.fetchone():
            print("   ➕ Creating news table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    url TEXT NOT NULL,
                    image_url TEXT,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    language TEXT DEFAULT 'pt',
                    category TEXT DEFAULT 'Geral',
                    tags TEXT DEFAULT '[]'
                )
            """)
        else:
            print("   ✅ News table already exists")
    except Exception as e:
        print(f"   ⚠️  Error creating News table: {e}")

    conn.commit()
    conn.close()
    print("✅ Database fix completed successfully!")

if __name__ == "__main__":
    fix_database()
