import sqlite3
import os

# Print where we are running from to be sure
print(f"Running in: {os.getcwd()}")

db_path = 'database.db'

if os.path.exists(db_path):
    print("Found database.db!")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('ALTER TABLE courses ADD COLUMN thumbnail TEXT')
        conn.commit()
        print("✅ SUCCESS: 'thumbnail' column added!")
    except sqlite3.OperationalError as e:
        print(f"ℹ️ Info: {e} (Column might already exist, which is good)")
    conn.close()
else:
    print("❌ ERROR: Could not find database.db. Are you in the right folder?")