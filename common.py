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
        
def add_project(conn, cursor, name):
    if name.strip() == "":
        name = "Project"
    
    cursor.execute("SELECT id FROM projects ORDER BY id ASC")
    ids = cursor.fetchall()
    next_id = 1  # Start with 1 as the default
    if ids:
        for index, (current_id,) in enumerate(ids):
            if current_id != next_id:  # Gap found
                break
            next_id += 1
        if index == len(ids) - 1:  # No gaps found, use the next number after the last ID
            next_id = ids[-1][0] + 1
    
    cursor.execute("INSERT INTO projects(name, id) VALUES (?,?)", (name,next_id))
    conn.commit()
    i = cursor.lastrowid
    add_default_columns(conn, cursor, i)
    return i
    
def add_default_columns(conn, cursor, proj_id):
    default_columns = [
        ("To Do",proj_id, 1), 
        ("In Progress",proj_id, 2), 
        ("Done",proj_id, 3)
    ]
    cursor.executemany("INSERT INTO columns(name, project_id, id) VALUES (?, ?, ?)", default_columns)
    conn.commit()