import sqlite3

def setup_enrollments():
    conn = sqlite3.connect('database.db')
    try:
        # This creates a table to track which user is in which course
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
        print("✅ SUCCESS: 'enrollments' table is ready!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_enrollments()