from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)

# --- DATABASE CONNECTION (RAILWAY SAFE) ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT", 3306))
    )

# --- HOME (READ) ---
@app.route('/')
def index():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('index.html', tasks=tasks)

# --- ADD TASK ---
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("INSERT INTO tasks (title) VALUES (%s)", (title,))
        db.commit()

        cursor.close()
        db.close()

        return redirect('/')

    return render_template('add.html')

# --- DELETE TASK ---
@app.route('/delete/<int:id>')
def delete(id):
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("DELETE FROM tasks WHERE id=%s", (id,))
    db.commit()

    cursor.close()
    db.close()

    return redirect('/')

# --- EDIT TASK ---
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    db = get_db_connection()
    cursor = db.cursor()

    if request.method == 'POST':
        title = request.form['title']

        cursor.execute("UPDATE tasks SET title=%s WHERE id=%s", (title, id))
        db.commit()

        cursor.close()
        db.close()

        return redirect('/')

    cursor.execute("SELECT * FROM tasks WHERE id=%s", (id,))
    task = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template('edit.html', task=task)

# --- IMPORTANT: NO app.run() FOR GUNICORN ---