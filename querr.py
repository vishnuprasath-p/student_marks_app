def create_db():
    conn = connect_db()
    cursor = conn.cursor()

    # Create teacher and student tables (with section column)
    cursor.execute('''CREATE TABLE IF NOT EXISTS teacher (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS student (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        class_name TEXT NOT NULL,
                        section TEXT NOT NULL,
                        marks_1 INTEGER,
                        marks_2 INTEGER,
                        marks_3 INTEGER,
                        total_marks INTEGER,
                        average REAL,
                        rank INTEGER
                    )''')

    # Add default teacher (for simplicity)
    cursor.execute("INSERT INTO teacher (username, password) VALUES ('admin', 'admin')")
    conn.commit()
    conn.close()

# Call create_db to initialize the database when the app starts
create_db()
