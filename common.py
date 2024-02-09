import sqlite3

current_project = 1
current_project_name = ""

def set_current_project(value, cursor):
    global current_project, current_project_name
    current_project = value
    cursor.execute("SELECT name FROM projects WHERE id = ? ", [current_project])
    current_project_name = cursor.fetchone()["name"]
    if current_project_name == "":
        current_project_name = f"Project {current_project}"