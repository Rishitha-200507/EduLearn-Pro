import sqlite3

# Connect to the database (it will create 'database.db' if it doesn't exist)
connection = sqlite3.connect('database.db')

# Create a cursor object to execute SQL commands
cursor = connection.cursor()

# 1. Create Users Table (Students and Instructors)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'student'
)
''')

# 2. Create Courses Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    instructor_id INTEGER,
    FOREIGN KEY (instructor_id) REFERENCES users (id)
)
''')

# 3. Create Lessons Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT NOT NULL,
    content TEXT,
    video_url TEXT,
    lesson_order INTEGER,
    FOREIGN KEY (course_id) REFERENCES courses (id)
)
''')

# 4. Create Enrollments Table (Links Students to Courses)
cursor.execute('''
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    course_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (course_id) REFERENCES courses (id)
)
''')

# Commit the changes and close
connection.commit()
connection.close()

print("Database initialized and tables created successfully!")