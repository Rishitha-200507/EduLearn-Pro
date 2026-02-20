import sqlite3
import os

print(f"Running in: {os.getcwd()}")
db_path = 'database.db'

if os.path.exists(db_path):
    print("Found database.db!")
    conn = sqlite3.connect(db_path)
    try:
        # Add the profile_pic column to the users table
        conn.execute('ALTER TABLE users ADD COLUMN profile_pic TEXT')
        conn.commit()
        print("✅ SUCCESS: 'profile_pic' column added to users table!")
    except sqlite3.OperationalError as e:
        print(f"ℹ️ Info: {e} (The column might already exist!)")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()
else:
    print("❌ ERROR: Could not find database.db. Are you in the right folder?")