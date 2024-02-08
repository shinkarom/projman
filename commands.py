import sqlite3

current_project = 1

def validate_column_id(cursor, value):
    valid_ids = [row[0] for row in cursor.execute("SELECT id FROM columns WHERE project_id = ?", [current_project])]
    return value in valid_ids

def do_help(conn, cursor, tok):
    print("""
    help: show this help
    exit: exit from program
    show [column_id]: show the task list
    add [column_id] [name]: add a task with the name to the colum
    delete [task_id]: delete a task
    move [task_id] [column_id]: move a task to a column
    columns: list the columns
    projects: list the projects
    """)

def do_show(conn, cursor, tok):
    colnum = tok.require_int()
    if colnum == None: return
    cursor.execute("SELECT name FROM columns WHERE project_id=? AND id=?", [current_project,colnum])
    colname = cursor.fetchone()
    column_name = " ("+colname["name"]+")" if colname!=None else ""
    cursor.execute(
        "SELECT t.id, t.name, COALESCE(c.name,'') AS column_name"
        " FROM tasks AS t"
        " LEFT JOIN columns AS c ON t.column_id = c.id AND c.project_id = ?"
        " WHERE t.column_id = ?",
        (current_project, colnum)
    )
    tasks = cursor.fetchall()
    print(f"Column {colnum}{column_name}: {len(tasks)}")
    for t in tasks:
        r = t["id"]
        n = t["name"]
          # Access the column name
        print(f"{r}\t{n}")

def do_add(conn, cursor, tok):
    column_id = tok.require_int()
    if column_id == None: return    
    s = tok.get_string()
    if s == "":
        print("String must not be empty")
        return
      
    if not validate_column_id(cursor, column_id):
        print("Error: wrong column")
        return
      
    cursor.execute("SELECT id FROM tasks WHERE project_id=? ORDER BY id ASC", [current_project])
    ids = cursor.fetchall()
    next_id = 1  # Start with 1 as the default
    if ids:
        for index, (current_id,) in enumerate(ids):
            if current_id != next_id:  # Gap found
                break
            next_id += 1
        if index == len(ids) - 1:  # No gaps found, use the next number after the last ID
            next_id = ids[-1][0] + 1
    
    cursor.execute("INSERT INTO tasks(id, project_id, name, column_id) VALUES (?, ?, ?, ?)", [next_id, current_project, s, column_id])
    conn.commit()
    newid = cursor.lastrowid
    print(f"Added task with id {newid} to column {column_id}")
    

def do_move(conn, cursor, tok):
    taskid = tok.require_int()
    if taskid == None: return
    column_id = tok.require_int()
    if column_id == None: return
    cursor.execute("SELECT 1 FROM tasks WHERE id = ? AND project_id = ?", (taskid, current_project))
    task_exists = cursor.fetchone()!=None  # True if task exists, False otherwise
    if not task_exists:
        print("No such task.")
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
            """, [column_id, current_project, taskid])
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
        (current_project,)
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
    
def do_delete(conn, cursor, tok):
    taskid = tok.require_int()
    if taskid == None: return
    cursor.execute("DELETE FROM tasks WHERE id = ? AND project_id = ? RETURNING id", [taskid, current_project])
    delid = cursor.fetchone()
    if delid:
        print("Deleted the task.")
    else:
        print("No task with this id.")
    conn.commit()