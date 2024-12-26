from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
import pandas as pd
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection function
def connect_db():
    return sqlite3.connect('students.db')

# Create tables and insert default data if they don't exist
def create_db():
    conn = connect_db()
    cursor = conn.cursor()

    # Create teacher and student tables with dynamic subject names
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
                        marks_subject1 INTEGER,
                        marks_subject2 INTEGER,
                        marks_subject3 INTEGER,
                        total_marks INTEGER,
                        average REAL,
                        rank INTEGER,
                        subject1 TEXT,
                        subject2 TEXT,
                        subject3 TEXT
                    )''')

    # Add default teacher
    cursor.execute("INSERT INTO teacher (username, password) VALUES ('admin', 'admin')")
    conn.commit()
    conn.close()

# Call create_db to initialize the database when the app starts
create_db()

# Teacher login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teacher WHERE username = ? AND password = ?", (username, password))
        teacher = cursor.fetchone()
        conn.close()

        if teacher:
            session['teacher_id'] = teacher[0]
            return redirect(url_for('enter_marks'))
        else:
            flash('Invalid credentials. Please try again.')
            return redirect(url_for('login'))

    return render_template('login.html')

# Teacher logout
@app.route('/logout')
def logout():
    session.pop('teacher_id', None)
    return redirect(url_for('login'))

# Enter student marks with dynamic subjects
@app.route('/enter_marks', methods=['GET', 'POST'])
def enter_marks():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        class_name = request.form['class_name']
        section = request.form['section']

        # Subject names and marks from the form
        subject1 = request.form['subject1']
        subject2 = request.form['subject2']
        subject3 = request.form['subject3']

        marks_subject1 = int(request.form['marks_subject1'])
        marks_subject2 = int(request.form['marks_subject2'])
        marks_subject3 = int(request.form['marks_subject3'])

        total_marks = marks_subject1 + marks_subject2 + marks_subject3
        average = total_marks / 3

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO student (name, class_name, section, marks_subject1, marks_subject2, marks_subject3, total_marks, average, subject1, subject2, subject3)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                          (name, class_name, section, marks_subject1, marks_subject2, marks_subject3, total_marks, average, subject1, subject2, subject3))
        conn.commit()
        conn.close()

        flash('Marks added successfully!')
        return redirect(url_for('enter_marks'))

    return render_template('enter_marks.html')

# Display student marks with rank
@app.route('/results')
def results():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()

    # Fetch all students ordered by total_marks in descending order
    cursor.execute('''SELECT id, name, class_name, section, total_marks, average FROM student ORDER BY total_marks DESC''')
    students = cursor.fetchall()

    # Assign rank based on total_marks
    rank = 1
    for student in students:
        cursor.execute('UPDATE student SET rank = ? WHERE id = ?', (rank, student[0]))
        rank += 1

    conn.commit()
    conn.close()

    return render_template('result.html', students=students)

# Home page to display student results and filters for class and section
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()

    # Get distinct classes and sections
    cursor.execute('SELECT DISTINCT class_name FROM student')
    classes = cursor.fetchall()

    cursor.execute('SELECT DISTINCT section FROM student')
    sections = cursor.fetchall()

    students = []
    average_marks = None

    if request.method == 'POST':
        class_name = request.form['class_name']
        section = request.form['section']
        
        # Fetch student data based on selected class and section
        cursor.execute('''SELECT name, total_marks, average FROM student WHERE class_name = ? AND section = ?''', 
                       (class_name, section))
        students = cursor.fetchall()

        # Calculate average marks for the selected class and section
        cursor.execute('''SELECT AVG(average) FROM student WHERE class_name = ? AND section = ?''', 
                       (class_name, section))
        average_marks = cursor.fetchone()[0]

    conn.close()

    return render_template('index.html', classes=classes, sections=sections, students=students, average_marks=average_marks)

# Export to Excel
@app.route('/export_excel')
def export_excel():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT name, class_name, section, total_marks, average FROM student')
    students = cursor.fetchall()

    df = pd.DataFrame(students, columns=['Name', 'Class', 'Section', 'Total Marks', 'Average'])
    df.to_excel('students_results.xlsx', index=False)

    conn.close()
    return send_file('students_results.xlsx', as_attachment=True)

# Export to PDF
@app.route('/export_pdf')
def export_pdf():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT name, class_name, section, total_marks, average FROM student')
    students = cursor.fetchall()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Student Results", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(40, 10, txt="Name", border=1)
    pdf.cell(40, 10, txt="Class", border=1)
    pdf.cell(40, 10, txt="Section", border=1)
    pdf.cell(40, 10, txt="Total Marks", border=1)
    pdf.cell(40, 10, txt="Average", border=1)
    pdf.ln()

    for student in students:
        pdf.cell(40, 10, txt=student[0], border=1)
        pdf.cell(40, 10, txt=student[1], border=1)
        pdf.cell(40, 10, txt=student[2], border=1)
        pdf.cell(40, 10, txt=str(student[3]), border=1)
        pdf.cell(40, 10, txt=str(student[4]), border=1)
        pdf.ln()

    pdf.output('students_results.pdf')
    conn.close()

    return send_file('students_results.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
