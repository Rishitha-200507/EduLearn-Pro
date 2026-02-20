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
    
    conn = get_db_connection()
    courses = []

    # If Instructor: Show courses they created
    if session['role'] == 'instructor':
        courses = conn.execute('SELECT * FROM courses WHERE instructor_id = ?', (session['user_id'],)).fetchall()
    
    # If Student: Show courses they are enrolled in
    elif session['role'] == 'student':
        # This SQL joins the courses table with the enrollments table
        courses = conn.execute('''
            SELECT courses.* FROM courses 
            JOIN enrollments ON courses.id = enrollments.course_id 
            WHERE enrollments.user_id = ?
        ''', (session['user_id'],)).fetchall()

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
    
    # 1. Grab the search term from the URL (if there is one)
    search_query = request.args.get('search', '')
    
    # 2. If the user searched for something, filter the database
    if search_query:
        # We use % around the search term as wildcards (e.g., %Python% matches "Advanced Python")
        sql_query = 'SELECT * FROM courses WHERE title LIKE ? OR description LIKE ?'
        wildcard_search = f"%{search_query}%"
        all_courses = conn.execute(sql_query, (wildcard_search, wildcard_search)).fetchall()
    
    # 3. If there is no search, just show everything
    else:
        all_courses = conn.execute('SELECT * FROM courses').fetchall()
        
    conn.close()
    
    # We pass the search_query back to the template so the search bar doesn't clear itself
    return render_template('courses.html', courses=all_courses, search_query=search_query)

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
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    lessons = conn.execute('SELECT * FROM lessons WHERE course_id = ?', (course_id,)).fetchall()
    
    completed_lesson_ids = []
    if 'user_id' in session and session.get('role') == 'student':
        completed = conn.execute('''
            SELECT completed_lessons.lesson_id 
            FROM completed_lessons 
            JOIN lessons ON completed_lessons.lesson_id = lessons.id
            WHERE completed_lessons.user_id = ? AND lessons.course_id = ?
        ''', (session['user_id'], course_id)).fetchall()
        
        # THE FIX: We wrap the list in set() to instantly destroy any duplicate clicks!
        completed_lesson_ids = list(set([row['lesson_id'] for row in completed]))

    conn.close()

    if course is None:
        flash('Course not found!', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('course_details.html', course=course, lessons=lessons, completed_lesson_ids=completed_lesson_ids)

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

# --- NEW ROUTE: Enroll in a Course ---
@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll(course_id):
    # 1. Make sure the user is logged in
    if 'user_id' not in session:
        flash('Please log in to enroll in courses.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    
    # 2. Check if they are already enrolled (no duplicates!)
    existing = conn.execute('SELECT * FROM enrollments WHERE user_id = ? AND course_id = ?', 
                            (user_id, course_id)).fetchone()
    
    if existing:
        flash('You are already enrolled in this course!', 'info')
    else:
        # 3. Save the enrollment to the database
        conn.execute('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', 
                     (user_id, course_id))
        conn.commit()
        flash('Successfully enrolled! The course has been added to your dashboard.', 'success')
        
    conn.close()
    return redirect(url_for('dashboard'))

# --- NEW ROUTE: Add a Quiz to a Lesson ---
@app.route('/add_quiz/<int:lesson_id>', methods=['GET', 'POST'])
def add_quiz(lesson_id):
    # Only allow instructors to access this page
    if 'user_id' not in session or session.get('role') != 'instructor':
        flash('Only instructors can add quizzes.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    
    # Verify the lesson exists and get the course_id so we know where to redirect later
    lesson = conn.execute('SELECT * FROM lessons WHERE id = ?', (lesson_id,)).fetchone()
    
    if not lesson:
        flash('Lesson not found!', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))

    # If the instructor submits the form
    if request.method == 'POST':
        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option']

        # Save the new quiz to the database
        conn.execute('''
            INSERT INTO quizzes (lesson_id, question, option_a, option_b, option_c, option_d, correct_option)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (lesson_id, question, option_a, option_b, option_c, option_d, correct_option))
        
        conn.commit()
        conn.close()
        
        flash('Quiz added successfully!', 'success')
        return redirect(url_for('course_details', course_id=lesson['course_id']))

    conn.close()
    return render_template('add_quiz.html', lesson=lesson)

# --- NEW ROUTE: User Profile ---
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Make sure the user is logged in
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    user_id = session['user_id']
    
    # If the user submits the update form
    if request.method == 'POST':
        name = request.form['name']
        file = request.files['profile_pic']
        
        # If they uploaded a new image
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Update database with new name AND new picture
            conn.execute('UPDATE users SET name = ?, profile_pic = ? WHERE id = ?', 
                         (name, filename, user_id))
        else:
            # Update database with ONLY the new name (keep old picture)
            conn.execute('UPDATE users SET name = ? WHERE id = ?', (name, user_id))
            
        conn.commit()
        session['user_name'] = name  # Update the session so the welcome message changes
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
        
    # Fetch current user data to display on the page
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    return render_template('profile.html', user=user)

# --- NEW ROUTE: Mark Lesson as Complete ---
@app.route('/complete_lesson/<int:lesson_id>', methods=['POST'])
def complete_lesson(lesson_id):
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    
    # Find out which course this lesson belongs to so we can redirect the user back
    lesson = conn.execute('SELECT course_id FROM lessons WHERE id = ?', (lesson_id,)).fetchone()
    
    if lesson:
        try:
            # Try to save the completed lesson
            conn.execute('INSERT INTO completed_lessons (user_id, lesson_id) VALUES (?, ?)', 
                         (user_id, lesson_id))
            conn.commit()
            flash('Lesson marked as complete! Great job!', 'success')
        except sqlite3.IntegrityError:
            # If we get an IntegrityError, it means the UNIQUE constraint caught a duplicate
            # meaning they already completed it. We just ignore it!
            pass
            
    conn.close()
    return redirect(url_for('course_details', course_id=lesson['course_id']))

# --- NEW ROUTE: Student Takes a Quiz ---
@app.route('/take_quiz/<int:lesson_id>', methods=['GET', 'POST'])
def take_quiz(lesson_id):
    # Only allow logged-in students
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Only students can take quizzes.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    lesson = conn.execute('SELECT * FROM lessons WHERE id = ?', (lesson_id,)).fetchone()
    
    # Fetch the quiz for this specific lesson
    quiz = conn.execute('SELECT * FROM quizzes WHERE lesson_id = ?', (lesson_id,)).fetchone()

    # If the instructor hasn't added a quiz yet, send the student back
    if not quiz:
        flash('No quiz available for this lesson yet!', 'info')
        conn.close()
        return redirect(url_for('course_details', course_id=lesson['course_id']))

    # When the student clicks "Submit Answer"
    if request.method == 'POST':
        selected_option = request.form.get('answer')
        
        if selected_option == quiz['correct_option']:
            flash('🎉 Correct! Great job!', 'success')
        else:
            flash(f'❌ Incorrect. The correct answer was Option {quiz["correct_option"]}. Keep learning!', 'danger')
        
        conn.close()
        return redirect(url_for('course_details', course_id=lesson['course_id']))

    conn.close()
    return render_template('take_quiz.html', lesson=lesson, quiz=quiz)

# --- NEW ROUTE: Generate Certificate ---
@app.route('/certificate/<int:course_id>')
def certificate(course_id):
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please log in as a student to view certificates.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    # Calculate progress to verify they are actually at 100%
    lessons = conn.execute('SELECT id FROM lessons WHERE course_id = ?', (course_id,)).fetchall()
    total_lessons = len(lessons)
    
    completed = conn.execute('''
        SELECT completed_lessons.lesson_id 
        FROM completed_lessons 
        JOIN lessons ON completed_lessons.lesson_id = lessons.id
        WHERE completed_lessons.user_id = ? AND lessons.course_id = ?
    ''', (session['user_id'], course_id)).fetchall()
    
    completed_count = len(set([row['lesson_id'] for row in completed]))
    conn.close()

    # Only show certificate if progress is 100%
    if total_lessons > 0 and completed_count == total_lessons:
        from datetime import date
        today = date.today().strftime("%B %d, %Y")
        return render_template('certificate.html', user=user, course=course, date=today)
    else:
        flash('You must complete all lessons to earn your certificate!', 'warning')
        return redirect(url_for('course_details', course_id=course_id))
    

if __name__ == '__main__':
    app.run(debug=True)