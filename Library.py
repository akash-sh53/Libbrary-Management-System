 from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)


# Inject current datetime into all templates (so layout.html can use {{ now.year }})
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# ------------------ DB FUNCTIONS ------------------
def init_db():
    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    # Books
    c.execute("""CREATE TABLE IF NOT EXISTS books (
        book_id TEXT PRIMARY KEY,
        title TEXT,
        author TEXT,
        status TEXT DEFAULT 'Available'
    )""")

    # Students
    c.execute("""CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        name TEXT
    )""")

    # Issued books
    c.execute("""CREATE TABLE IF NOT EXISTS issued_books (
        issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id TEXT,
        student_id TEXT,
        issue_date TEXT,
        return_date TEXT,
        FOREIGN KEY(book_id) REFERENCES books(book_id),
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )""")

    conn.commit()
    conn.close()

# ------------------ ROUTES ------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/books")
def books():
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return render_template("books.html", books=books)

@app.route("/add_book", methods=["POST"])
def add_book():
    book_id = request.form["book_id"]
    title = request.form["title"]
    author = request.form["author"]

    conn = sqlite3.connect("library.db")
    try:
        conn.execute("INSERT INTO books (book_id, title, author) VALUES (?, ?, ?)", (book_id, title, author))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return redirect("/books")

@app.route("/students")
def students():
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    conn.close()
    return render_template("students.html", students=students)

@app.route("/add_student", methods=["POST"])
def add_student():
    student_id = request.form["student_id"]
    name = request.form["name"]

    conn = sqlite3.connect("library.db")
    try:
        conn.execute("INSERT INTO students (student_id, name) VALUES (?, ?)", (student_id, name))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return redirect("/students")

@app.route("/issue", methods=["POST"])
def issue_book():
    book_id = request.form["book_id"]
    student_id = request.form["student_id"]

    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    # Check availability
    c.execute("SELECT status FROM books WHERE book_id=?", (book_id,))
    result = c.fetchone()

    if result and result[0] == "Available":
        issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("UPDATE books SET status='Issued' WHERE book_id=?", (book_id,))
        conn.execute("INSERT INTO issued_books (book_id, student_id, issue_date) VALUES (?, ?, ?)",
                     (book_id, student_id, issue_date))
        conn.commit()

    conn.close()
    return redirect("/issued")

@app.route("/return/<book_id>")
def return_book(book_id):
    conn = sqlite3.connect("library.db")
    return_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE books SET status='Available' WHERE book_id=?", (book_id,))
    conn.execute("UPDATE issued_books SET return_date=? WHERE book_id=? AND return_date IS NULL",
                 (return_date, book_id))
    conn.commit()
    conn.close()
    return redirect("/issued")

@app.route("/issued")
def issued_books():
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("""SELECT i.issue_id, b.title, s.name, i.issue_date, i.return_date
                 FROM issued_books i
                 JOIN books b ON i.book_id = b.book_id
                 JOIN students s ON i.student_id = s.student_id""")
    records = c.fetchall()
    conn.close()
    return render_template("issued.html", records=records)

# ------------------ RUN ------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
