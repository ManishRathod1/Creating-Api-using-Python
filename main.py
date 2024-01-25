import os

from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
import mysql.connector
import secrets

app = Flask(__name__, template_folder='template')
app.secret_key = secrets.token_hex(16)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'port': '3306',
    'database': 'assignment3'
}


@app.route('/')
def log():
    return render_template('login.html')


@app.route('/get_data')
def get_data():
    return render_template('display_data.html')


def get_user_projects(user_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    select_user_projects = """  SELECT p.project_id, p.project_name
                                 FROM project p
                                 JOIN user_project up ON p.project_id = up.project_id
                                 WHERE up.user_id = %s;
                            """
    cursor.execute(select_user_projects, (user_id,))

    projects = cursor.fetchall()

    cursor.close()
    conn.close()

    return projects


@app.route('/task_page')
def task_page():
    if 'user_id' not in session:
        return redirect(url_for('log'))

    user_id = session['user_id']

    user_projects = get_user_projects(user_id)

    return render_template('create_task.html', user_projects=user_projects)


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/registration')
def registration_page():
    return render_template('registration.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    username = request.form['username']
    password = request.form['password']

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    insert_query = "insert into user(user_name, password) values(%s, %s)"
    values = (username, password)
    cursor.execute(insert_query, values)
    conn.commit()
    cursor.close()
    conn.close()
    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        get_user = "SELECT user_id, user_name FROM user WHERE user_name = %s AND password = %s"
        values = (username, password)
        cursor.execute(get_user, values)

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')


@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if 'user_id' not in session:
        return redirect(url_for('log'))

    if request.method == 'POST':
        project_name = request.form['projectName']
        user_id = session['user_id']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        insert_project = "INSERT INTO project (project_name) VALUES (%s)"
        project_values = (project_name,)
        cursor.execute(insert_project, project_values)

        project_id = cursor.lastrowid

        insert_user_project = "INSERT INTO user_project (user_id, project_id) VALUES (%s, %s)"
        user_project_values = (user_id, project_id)
        cursor.execute(insert_user_project, user_project_values)

        conn.commit()
        cursor.close()
        conn.close()

        return render_template('index.html', success_message='Project created!')

    return redirect(url_for('index'))


@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('log'))

    if request.method == 'POST':
        project_id = request.form['user_project_id']
        task_name = request.form['task_name']
        user_id = session['user_id']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        insert_project = "INSERT INTO task (task_name) VALUES (%s)"
        task_values = (task_name,)
        cursor.execute(insert_project, task_values)
        task_id = cursor.lastrowid
        get_user_project_id = "select user_project_id from user_project where user_id = %s and project_id = %s"

        user_project_values = (user_id, project_id)
        cursor.execute(get_user_project_id, user_project_values)
        user_project_id = cursor.fetchone()

        us_p_id = user_project_id[0]

        insert_task_project = "INSERT INTO task_project (user_project_id, task_id) VALUES (%s, %s)"

        user_task_values = (us_p_id, task_id)
        cursor.execute(insert_task_project, user_task_values)

        conn.commit()
        cursor.close()
        conn.close()

        return render_template('create_task.html', success_message='Task created successfully!')

    return redirect(url_for('task_page'))


@app.route('/get_task_project_data')
def get_task_project_data_route():
    if 'user_id' not in session:
        return redirect(url_for('log'))

    user_id = session['user_id']
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    select_task_project_data = """
            SELECT u.user_id, u.user_name, p.project_id, p.project_name, tp.task_id, t.task_name
            FROM user u
            JOIN user_project up ON u.user_id = up.user_id
            JOIN project p ON up.project_id = p.project_id
            JOIN task_project tp ON up.user_project_id = tp.user_project_id
            JOIN task t ON tp.task_id = t.task_id
            WHERE u.user_id = %s;
        """

    cursor.execute(select_task_project_data, (user_id,))
    task_project_data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({'task_project_data': task_project_data})


if __name__ == '__main__':
    app.run(debug=True)
