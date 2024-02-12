import sqlite3
import argparse
from tokenizer import Tokenizer
from commands import *

import common

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
          id INTEGER,
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
          id INTEGER,
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
        common.add_project(conn, cursor, "")
    
    common.set_current_project(1, cursor)
    
    print("Enter 'help' for help or 'exit' to exit the program.")
    while True:
        command = input(f"{common.current_project_name} > ")
        print()
        tok = Tokenizer(command)
        first_token = tok.get_token()
        if first_token=="exit":
            break
        elif first_token == "help":
            do_help(conn, cursor, tok)          
        elif first_token == "c":
            match tok.require_word():
                case None:
                    print("Error: wrong command")
                case "":
                    do_columns(conn, cursor, tok)
                case "a":
                    do_column_add(conn, cursor, tok)
                case "s":
                    do_column_show(conn, cursor, tok)
                case _:
                    print("Error: wrong command")    
        elif first_token == "t":
            match tok.require_word():
                case None | "":
                    print("Error: wrong command")
                case "a":
                    do_task_add(conn, cursor, tok)
                case "m":
                    do_task_move(conn, cursor, tok)
                case "d":
                    do_task_delete(conn, cursor, tok)
                case _:
                    print("Error: wrong command")
        elif first_token == "p":
            match tok.require_word():
                case None:
                    print("Error: wrong command")
                case "":
                    do_projects(conn, cursor, tok)
                case "a":
                    do_project_add(conn, cursor, tok)
                case "d":
                    do_project_delete(conn, cursor, tok)
                case "r":
                    do_project_rename(conn, cursor, tok)
                case "sw":
                    do_project_switch(conn, cursor, tok)
                case _:
                    print("Error: wrong command")
        else:
            print("Unknown command. Enter 'help' for help or 'exit' to exit the program.")
        print()
    
    conn.close()
