import sqlite3

import common

def validate_column_id(cursor, value):
    cursor.execute("SELECT EXISTS(SELECT 1 FROM columns WHERE id = ? ANd project_id = ?)", [value, common.current_project])
    exists = cursor.fetchone()[0]
    return exists
    
def validate_task_id(cursor, value):
    cursor.execute("SELECT EXISTS(SELECT 1 FROM tasks WHERE id = ? AND project_id = ?)", [value, common.current_project])
    exists = cursor.fetchone()[0]
    return exists
    
def validate_project_id(cursor, value):
    cursor.execute("SELECT EXISTS(SELECT 1 FROM projects WHERE id = ?)", [value])
    exists = cursor.fetchone()[0]
    return exists

def do_help(conn, cursor, tok):
    print("""
    help: show this help
    exit: exit from program
    c: list the columns
    c s [column_id]: show the column with the number
    p: list the projects
    p a [name]: add a project with the name
    p d [id]: delete project with id
    p r [id]: rename the project with id
    p sw [id]: switch to the project with id
    t a [column_id] [name]: add a task with the name to the colum
    t d [task_id]: delete a task
    t m [task_id] [column_id]: move a task to a column
    """)

def do_column_show(conn, cursor, tok):
    colnum = tok.require_int()
    print(colnum)
    if colnum == None: return
    cursor.execute("SELECT name FROM columns WHERE project_id=? AND id=?", [common.current_project,colnum])
    colname = cursor.fetchone()
    column_name = " ("+colname["name"]+")" if colname!=None else ""
    cursor.execute(
        "SELECT t.id, t.name, COALESCE(c.name,'') AS column_name"
        " FROM tasks AS t"
        " LEFT JOIN columns AS c ON t.column_id = c.id AND c.project_id = ?"
        " WHERE t.column_id = ?",
        (common.current_project, colnum)
    )
    tasks = cursor.fetchall()
    print(f"Column {colnum}{column_name}: {len(tasks)}")
    for t in tasks:
        r = t["id"]
        n = t["name"]
          # Access the column name
        print(f"{r}\t{n}")

def do_task_add(conn, cursor, tok):
    column_id = tok.require_int()
    if column_id == None: return    
    s = tok.get_string()
    if s == "":
        print("String must not be empty")
        return
      
    if not validate_column_id(cursor, column_id):
        print("Error: wrong column")
        return
      
    cursor.execute("SELECT id FROM tasks WHERE project_id=? ORDER BY id ASC", [common.current_project])
    ids = cursor.fetchall()
    next_id = 1  # Start with 1 as the default
    if ids:
        for index, (current_id,) in enumerate(ids):
            if current_id != next_id:  # Gap found
                break
            next_id += 1
        if index == len(ids) - 1:  # No gaps found, use the next number after the last ID
            next_id = ids[-1][0] + 1
    
    cursor.execute("INSERT INTO tasks(id, project_id, name, column_id) VALUES (?, ?, ?, ?)", [next_id, common.current_project, s, column_id])
    conn.commit()
    newid = cursor.lastrowid
    print(f"Added task with id {newid} to column {column_id}")
    

def do_task_move(conn, cursor, tok):
    taskid = tok.require_int()
    if taskid == None: return
    column_id = tok.require_int()
    if column_id == None: return
    
    if not validate_task_id(cursor, taskid):
        print("Error: no such task")
        return
        
    if not validate_column_id(cursor, column_id):
        print("Error: wrong column")
        return
    
    # Check if the new column ID is different from the current one
    cursor.execute("SELECT column_id FROM tasks WHERE id = ?", (taskid,))
    current_column_id = cursor.fetchone()["column_id"]

    if column_id != current_column_id:
        cursor.execute("""
            UPDATE tasks SET column_id=?
            WHERE project_id=? AND id=?
            """, [column_id, common.current_project, taskid])
        conn.commit()
        print("Task moved successfully.")
    else:
        print("Task already in the same column.")
        
        
def do_columns(conn, cursor, tok):
    cursor.execute("""
        SELECT c.id AS id, c.name AS column_name,
        (SELECT COUNT(*) FROM tasks WHERE tasks.column_id = c.id AND tasks.project_id = c.project_id) AS task_count
        FROM columns c
        WHERE c.project_id = ?;
        """,
        (common.current_project,)
    )

    results = cursor.fetchall()
    # Print the column names and task counts
    for row in results:
        ci = row["id"]
        cn = row["column_name"]
        tc = row["task_count"]
        print(f"{ci}\t{cn}: {tc}")
    
def do_projects(conn, cursor, tok):
    cursor.execute("SELECT id, name FROM projects")
    results = cursor.fetchall()
    for row in results:
        i = row["id"]
        n = row["name"]
        print(f"{i}\t{n}")
    
def do_task_delete(conn, cursor, tok):
    taskid = tok.require_int()
    if taskid == None: return
    
    if not validate_task_id(cursor, taskid):
        print("Error: no such task")
        return
    
    cursor.execute("DELETE FROM tasks WHERE id = ? AND project_id = ?", [taskid, common.current_project])
    conn.commit()
    print("Task deleted.")
    
    
def do_project_add(conn, cursor, tok):  
    s = tok.get_string()
    if s == "":
        print("String must not be empty")
        return
      
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
    
    newid = common.add_project(conn, cursor, s)
    print(f"Added project with id {newid}")
    
def do_project_delete(conn, cursor, tok):
    projid = tok.require_int()
    if projid == None: return
    
    if not validate_project_id(cursor, projid):
        print("Error: no such project")
        return
    
    if projid == common.current_project:
        print("Error: can't delete active project")
        return
    
    cursor.execute("DELETE FROM projects WHERE id = ?", [projid])
    conn.commit()
    print("Project deleted.")
    
def do_project_rename(conn, cursor, tok):
    projid = tok.require_int()
    if projid == None: return
    
    if not validate_project_id(cursor, projid):
        print("Error: no such project")
        return
        
    s = tok.get_string()
    if s == "":
        print("String must not be empty")
        return
    
    cursor.execute("UPDATE projects SET name = ? WHERE id = ?", [s, projid])
    conn.commit()
    print("Project renamed.")
    
def do_project_switch(conn, cursor, tok):
    projid = tok.require_int()
    if projid == None: return
    
    if not validate_project_id(cursor, projid):
        print("Error: no such project")
        return
        
    if projid == common.current_project:
        print("Error: can't switch to active project")
        return
        
    common.set_current_project(projid, cursor)
    print(f"Project switched to {common.current_project}")