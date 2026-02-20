import sqlite3
import os

print(f"Running in: {os.getcwd()}")
db_path = 'database.db'

if os.path.exists(db_path):
    print("Found the correct database.db!")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (course_id) REFERENCES courses (id)
            )
        ''')
        conn.commit()
        print("✅ SUCCESS: 'enrollments' table is firmly in your database!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()
else:
    print("❌ ERROR: Could not find database.db. Are you in the right folder?")