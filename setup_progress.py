import sqlite3
import os

print(f"Running in: {os.getcwd()}")
db_path = 'database.db'

if os.path.exists(db_path):
    print("Found database.db!")
    conn = sqlite3.connect(db_path)
    try:
        # Create a table to track which user finished which lesson
        conn.execute('''
            CREATE TABLE IF NOT EXISTS completed_lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (lesson_id) REFERENCES lessons (id),
                UNIQUE(user_id, lesson_id)
            )
        ''')
        # The UNIQUE constraint stops a student from getting double credit for the same lesson!
        
        conn.commit()
        print("✅ SUCCESS: 'completed_lessons' table is ready!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()
else:
    print("❌ ERROR: Could not find database.db. Are you in the right folder?")