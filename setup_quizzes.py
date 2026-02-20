import sqlite3
import os

print(f"Running in: {os.getcwd()}")
db_path = 'database.db'

if os.path.exists(db_path):
    print("Found database.db!")
    conn = sqlite3.connect(db_path)
    try:
        # Create a table for quizzes linked to specific lessons
        conn.execute('''
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_option TEXT NOT NULL, 
                FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        print("✅ SUCCESS: 'quizzes' table has been added to your database!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()
else:
    print("❌ ERROR: Could not find database.db. Are you in the right folder?")