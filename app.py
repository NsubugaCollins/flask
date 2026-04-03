from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)

# Railway environment variables
db = mysql.connector.connect(
    host=os.getenv("MYSQLHOST"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
    database=os.getenv("MYSQLDATABASE")
)

cursor = db.cursor()

# Home (Read)
@app.route('/')
def index():
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    return render_template('index.html', tasks=tasks)

# Add Task (Create)
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        cursor.execute("INSERT INTO tasks (title) VALUES (%s)", (title,))
        db.commit()
        return redirect('/')
    return render_template('add.html')

# Delete Task
@app.route('/delete/<int:id>')
def delete(id):
    cursor.execute("DELETE FROM tasks WHERE id=%s", (id,))
    db.commit()
    return redirect('/')

# Edit Task
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        title = request.form['title']
        cursor.execute("UPDATE tasks SET title=%s WHERE id=%s", (title, id))
        db.commit()
        return redirect('/')
    
    cursor.execute("SELECT * FROM tasks WHERE id=%s", (id,))
    task = cursor.fetchone()
    return render_template('edit.html', task=task)

if __name__ == '__main__':
    app.run()