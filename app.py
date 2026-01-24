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

        # Save to Database
        conn = get_db_connection()
        conn.execute('INSERT INTO courses (title, description, instructor_id) VALUES (?, ?, ?)',
                     (title, description, session['user_id']))
        conn.commit()
        conn.close()

        flash('Course created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_course.html')

if __name__ == '__main__':
    app.run(debug=True)