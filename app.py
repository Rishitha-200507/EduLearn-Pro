import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Configuration for Image Uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database Connection Helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                         (name, email, hashed_password, role))
            conn.commit()
            conn.close()
            flash('Account created! Please sign in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered!', 'danger')
            return redirect(url_for('signup'))
        except Exception as e:
            return f"Error: {e}"

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # If instructor, fetch their courses to show on dashboard
    courses = []
    if session['role'] == 'instructor':
        conn = get_db_connection()
        courses = conn.execute('SELECT * FROM courses WHERE instructor_id = ?', (session['user_id'],)).fetchall()
        conn.close()

    return render_template('dashboard.html', courses=courses)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- NEW ROUTE: Create Course ---
# --- NEW ROUTE: Create Course (FIXED) ---
@app.route('/create_course', methods=['GET', 'POST'])
def create_course():
    # Security Check: Only instructors can create courses
    if 'user_id' not in session or session['role'] != 'instructor':
        flash('Access denied. Instructors only.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['thumbnail'] # Get the image file

        # Handle Image Upload
        filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Save to Database (NOW INCLUDES THUMBNAIL)
        conn = get_db_connection()
        conn.execute('INSERT INTO courses (title, description, instructor_id, thumbnail) VALUES (?, ?, ?, ?)',
                     (title, description, session['user_id'], filename))
        conn.commit()
        conn.close()

        flash('Course created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_course.html')

@app.route('/courses')
def courses():
    conn = get_db_connection()
    # Fetch ALL courses to show in the catalog
    all_courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('courses.html', courses=all_courses)

# --- NEW ROUTE: Add Lesson ---
@app.route('/course/<int:course_id>/add_lesson', methods=['GET', 'POST'])
def add_lesson(course_id):
    # Security: Ensure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 1. Check if the course actually belongs to this instructor
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    if not course or course['instructor_id'] != session['user_id']:
        conn.close()
        flash('You do not have permission to modify this course.', 'danger')
        return redirect(url_for('dashboard'))

    # 2. Handle Form Submission
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        video_url = request.form['video_url']

        # Save to lessons table
        conn.execute('INSERT INTO lessons (course_id, title, content, video_url) VALUES (?, ?, ?, ?)',
                     (course_id, title, content, video_url))
        conn.commit()
        conn.close()
        
        flash('Lesson added successfully!', 'success')
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('add_lesson.html')

# --- NEW ROUTE: View Course Details ---
@app.route('/course/<int:course_id>')
def course_details(course_id):
    conn = get_db_connection()
    
    # 1. Get the Course Info
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    # 2. Get the Lessons for this course
    lessons = conn.execute('SELECT * FROM lessons WHERE course_id = ?', (course_id,)).fetchall()
    
    conn.close()
    
    if course is None:
        return "Course not found", 404
        
    return render_template('course_details.html', course=course, lessons=lessons)

# --- NEW ROUTE: Edit Course ---
@app.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
def edit_course(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()

    # Security: Ensure only the creator can edit
    if not course or course['instructor_id'] != session['user_id']:
        conn.close()
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['thumbnail']

        # If a new image is uploaded, update it. Otherwise keep the old one.
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn.execute('UPDATE courses SET title = ?, description = ?, thumbnail = ? WHERE id = ?',
                         (title, description, filename, course_id))
        else:
            conn.execute('UPDATE courses SET title = ?, description = ? WHERE id = ?',
                         (title, description, course_id))
        
        conn.commit()
        conn.close()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('edit_course.html', course=course)
# --- NEW ROUTE: Delete Course ---
@app.route('/course/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()

    # Security: Ensure only the creator can delete
    if not course or course['instructor_id'] != session['user_id']:
        conn.close()
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard'))

    # Delete the course (and its lessons)
    conn.execute('DELETE FROM lessons WHERE course_id = ?', (course_id,)) # Delete lessons first
    conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    conn.commit()
    conn.close()
    
    flash('Course deleted successfully.', 'info')
    return redirect(url_for('dashboard'))

# --- NEW ROUTE: Delete Lesson ---
@app.route('/lesson/<int:lesson_id>/delete', methods=['POST'])
def delete_lesson(lesson_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    # Find the lesson and join with course to check instructor permission
    lesson = conn.execute('SELECT lessons.id, courses.instructor_id, lessons.course_id FROM lessons JOIN courses ON lessons.course_id = courses.id WHERE lessons.id = ?', (lesson_id,)).fetchone()

    if not lesson or lesson['instructor_id'] != session['user_id']:
        conn.close()
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard'))

    course_id = lesson['course_id'] # Save this to redirect back correctly
    conn.execute('DELETE FROM lessons WHERE id = ?', (lesson_id,))
    conn.commit()
    conn.close()

    flash('Lesson deleted.', 'info')
    return redirect(url_for('course_details', course_id=course_id))

if __name__ == '__main__':
    app.run(debug=True)