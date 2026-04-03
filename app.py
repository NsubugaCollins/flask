from flask import Flask, render_template, request, redirect, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
    user_row = cursor.fetchone()
    cursor.close()
    db.close()
    if user_row:
        return User(user_row[0], user_row[1])
    return None

# --- DATABASE CONNECTION (RAILWAY SAFE) ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT", 3306))
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')
        
        db = get_db_connection()
        cursor = db.cursor()
        try:
            hash_pw = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hash_pw))
            db.commit()
            return redirect('/login')
        except mysql.connector.IntegrityError:
            return render_template('register.html', error='Username already exists')
        finally:
            cursor.close()
            db.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
        user_row = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user_row and check_password_hash(user_row[2], password):
            user = User(user_row[0], user_row[1])
            login_user(user)
            return redirect('/')
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')

# --- HOME (READ) ---
@app.route('/')
@login_required
def index():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (current_user.id,))
    tasks = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('index.html', tasks=tasks)

# --- ADD TASK ---
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form['title']

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("INSERT INTO tasks (title, user_id) VALUES (%s, %s)", (title, current_user.id))
        db.commit()

        cursor.close()
        db.close()

        return redirect('/')

    return render_template('add.html')

# --- DELETE TASK ---
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("DELETE FROM tasks WHERE id=%s AND user_id=%s", (id, current_user.id))
    db.commit()

    cursor.close()
    db.close()

    return redirect('/')

# --- EDIT TASK ---
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db_connection()
    cursor = db.cursor()

    if request.method == 'POST':
        title = request.form['title']

        cursor.execute("UPDATE tasks SET title=%s WHERE id=%s AND user_id=%s", (title, id, current_user.id))
        db.commit()

        cursor.close()
        db.close()

        return redirect('/')

    cursor.execute("SELECT * FROM tasks WHERE id=%s AND user_id=%s", (id, current_user.id))
    task = cursor.fetchone()
    if not task:
        return redirect('/')

    cursor.close()
    db.close()

    return render_template('edit.html', task=task)

# --- IMPORTANT: NO app.run() FOR GUNICORN ---