import sqlite3

def update_database():
    print("Connecting to database...")
    conn = sqlite3.connect('database.db')
    
    try:
        # This SQL command adds the missing column
        conn.execute('ALTER TABLE courses ADD COLUMN thumbnail TEXT')
        conn.commit()
        print("✅ Success! The 'thumbnail' column has been added to your database.")
    except sqlite3.OperationalError as e:
        # If the column already exists, it will throw an error, which is fine.
        print(f"ℹ️ Note: {e} (This probably means the column is already there!)")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_database()