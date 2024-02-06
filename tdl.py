import sqlite3
import argparse

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

class Tokenizer:
    def __init__(self, s):
        self.string = s
        self.pos = 0
        self.l = len(self.string)
    def current(self):
        return self.string[self.pos]
    def get_token(self):
        s = ""
        while self.pos < self.l and self.current().isspace():
            self.pos += 1
        while self.pos < self.l and not self.current().isspace():
            s += self.current()
            self.pos += 1
        return s
    def get_string(self):
        s = ""
        while self.pos < self.l and self.current().isspace():
            self.pos += 1
        while self.pos < self.l:
            s += self.current()
            self.pos += 1
        s = s.strip()
        return s
    def require_int(self):
        s = self.get_token()
        if s.isnumeric():
            return s
        else:
            print("Error: integer required, but got", s)
            return None
    def require_word(self):
        s = self.get_token()
        if not s.isnumeric():
            return s
        else:
            print("Error: word required, but got", s)
            return None
    def require_specific_word(self, t):
        s = self.require_word()
        if s != None:
            if s.lower() == t.lower():
                return s
            else:
                print(f"Error: required {t}, but got {s}")
                return None

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
    s = tok.get_string()
    if s == "":
        print("String must not be empty")
        return
    cursor.execute("INSERT INTO tasks(project_id, name, column_id) VALUES (?, ?, ?)", [current_project, s, 1])
    conn.commit()
    newid = cursor.lastrowid
    print(f"Added task with id {newid} to column 1")

def do_move(conn, cursor, tok):
    taskid = tok.require_int()
    if taskid == None: return
    if tok.require_specific_word("to") == None: return
    column_id = tok.require_int()
    if column_id == None: return
    cursor.execute("""
        UPDATE tasks SET column_id=?
        WHERE project_id=? AND id=?
        """, [column_id, current_project, taskid])
    conn.commit()
    print("Moved the task to the new column.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()   
    
    conn = sqlite3.connect(args.filename)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.executescript('''
        -- Create the projects table
        CREATE TABLE IF NOT EXISTS projects (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE
        );

        -- Create the columns table
        CREATE TABLE IF NOT EXISTS columns (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE
        );

        -- Create the tasks table
        CREATE TABLE IF NOT EXISTS tasks (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          description TEXT, -- Optional field for longer descriptions
          project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          column_id INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE
        );
    ''')
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM projects")
    project_count = cursor.fetchone()["COUNT(*)"]

    if project_count == 0:
        # No projects exist, add a default project
        cursor.execute("INSERT INTO projects(name) VALUES (?)", ("Default",))
        conn.commit()
    
    current_project = 1
    current_project_name = ""

    cursor.execute("SELECT name FROM projects WHERE id = ? ", [current_project])
    current_project_name = cursor.fetchone()["name"]
    
    cursor.execute("SELECT COUNT(*) FROM columns WHERE project_id = ?", [current_project])
    column_count = cursor.fetchone()["COUNT(*)"]

    if column_count == 0:
        default_columns = [
            ("To Do",current_project), 
            ("In Progress",current_project), 
            ("Done",current_project)
        ]
        cursor.executemany("INSERT INTO columns(name, project_id) VALUES (?, ?)", default_columns)
        conn.commit()
    
    print("Enter 'help' for help or 'exit' to exit the program.")
    while True:
        command = input(f"{current_project_name} > ")
        print()
        tok = Tokenizer(command)
        first_token = tok.get_token()
        if first_token=="exit":
            break
        elif first_token == "help":
            print("""
help: show this help
exit: exit from program
show [column_id]: show the task list
add [name]: add a task with the specified name
delete [task_id]: delete a task
move [task_id] to [column_id]: move a task to a column
columns: list the columns
projects: list the projects
""")
        elif first_token == "show":
            do_show(conn, cursor, tok)
        elif first_token == "add":
            do_add(conn, cursor, tok)
        elif first_token == "columns":
            cursor.execute(
                "SELECT c.id as id, c.name AS column_name, COUNT(t.id) AS task_count"
                " FROM columns AS c"
                " LEFT JOIN tasks AS t ON c.id = t.column_id"
                " WHERE c.project_id = ?"
                " GROUP BY c.id",
                (current_project,)
            )

            results = cursor.fetchall()
            # Print the column names and task counts
            for row in results:
                ci = row["id"]
                cn = row["column_name"]
                tc = row["task_count"]
                print(f"{ci}\t{cn}: {tc}")
        elif first_token == "projects":
            cursor.execute("SELECT id, name FROM projects")
            results = cursor.fetchall()
            for row in results:
                i = row["id"]
                n = row["name"]
                print(f"{i}\t{n}")
        elif first_token == "delete":
            taskid = tok.require_int()
            if taskid != None:
                cursor.execute("DELETE FROM tasks WHERE id = ? AND project_id = ? RETURNING id", [taskid, current_project])
                delid = cursor.fetchone()
                if delid:
                    print("Deleted the task.")
                else:
                    print("No task with this id.")
                conn.commit()
        elif first_token == "move":
            do_move(conn, cursor, tok)
        else:
            print("Unknown command. Enter 'help' for help or 'exit' to exit the program.")
        print()
    
    conn.close()
