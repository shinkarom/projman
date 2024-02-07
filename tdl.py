import sqlite3
import argparse
from tokenizer import Tokenizer
from commands import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()   
    
    conn = sqlite3.connect(args.filename)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.executescript('''     
        -- Create the projects table
        CREATE TABLE IF NOT EXISTS projects (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL
        );

        -- Create the columns table
        CREATE TABLE IF NOT EXISTS columns (
          id INTEGER,
          name TEXT NOT NULL,
          project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE
        );

        -- Create the tasks table
        CREATE TABLE IF NOT EXISTS tasks (
          id INTEGER PRIMARY KEY,
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
        cursor.execute("INSERT INTO projects(name) VALUES (?)", ("",))
        conn.commit()
    
    current_project = 1
    current_project_name = ""

    cursor.execute("SELECT name FROM projects WHERE id = ? ", [current_project])
    current_project_name = cursor.fetchone()["name"]
    if current_project_name == "":
        current_project_name = str(current_project)
    
    cursor.execute("SELECT COUNT(*) FROM columns WHERE project_id = ?", [current_project])
    column_count = cursor.fetchone()[0]

    if column_count == 0:
        default_columns = [
            ("To Do",current_project, 1), 
            ("In Progress",current_project, 2), 
            ("Done",current_project, 3)
        ]
        cursor.executemany("INSERT INTO columns(name, project_id, id) VALUES (?, ?, ?)", default_columns)
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
            do_help(conn, cursor, tok)
        elif first_token == "show":
            do_show(conn, cursor, tok)
        elif first_token == "add":
            do_add(conn, cursor, tok)
        elif first_token == "columns":
            do_columns(conn, cursor, tok)
        elif first_token == "projects":
            do_projects(conn, cursor, tok)
        elif first_token == "delete":
            do_delete(conn, cursor, tok)
        elif first_token == "move":
            do_move(conn, cursor, tok)
        else:
            print("Unknown command. Enter 'help' for help or 'exit' to exit the program.")
        print()
    
    conn.close()
