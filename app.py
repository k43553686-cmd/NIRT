from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import random
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB_NAME = "student_ai_portal.db"
otp_storage = {}
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ID_CARD_FOLDER = os.path.join(UPLOAD_FOLDER, 'id_cards')
LIBRARY_CARD_FOLDER = os.path.join(UPLOAD_FOLDER, 'library_cards')
BUS_CARD_FOLDER = os.path.join(UPLOAD_FOLDER, 'bus_cards')
BACKGROUND_FOLDER = os.path.join('static', 'images')
os.makedirs(ID_CARD_FOLDER, exist_ok=True)
os.makedirs(LIBRARY_CARD_FOLDER, exist_ok=True)
os.makedirs(BUS_CARD_FOLDER, exist_ok=True)
os.makedirs(BACKGROUND_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_ID_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_ID_EXTENSIONS


def upload_student_card_file(student, file, card_type):
    folder_map = {
        "id": (ID_CARD_FOLDER, "id_card_file", "uploads/id_cards", "ID card"),
        "library": (LIBRARY_CARD_FOLDER, "library_card_file", "uploads/library_cards", "Library card"),
        "bus": (BUS_CARD_FOLDER, "bus_card_file", "uploads/bus_cards", "Bus card"),
    }
    folder, column, static_folder, label = folder_map[card_type]
    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    filename = secure_filename(f"{student['enrollment']}_{card_type}_card.{ext}")
    save_path = os.path.join(folder, filename)
    file.save(save_path)
    return column, f"{static_folder}/{filename}", label


SEMESTERS = ["1st Semester", "2nd Semester", "3rd Semester", "4th Semester", "5th Semester", "6th Semester", "7th Semester", "8th Semester"]
GRADE_POINTS = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "F": 0}


def get_db():
    db = sqlite3.connect(DB_NAME)
    db.row_factory = sqlite3.Row
    return db


def add_column_if_missing(cursor, table, column, col_type):
    cols = [r[1] for r in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def init_db():
    db = get_db()
    c = db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        enrollment TEXT UNIQUE,
        password TEXT,
        role TEXT,
        phone TEXT,
        semester TEXT,
        address TEXT,
        father_name TEXT,
        mother_name TEXT,
        dob TEXT,
        gender TEXT,
        city TEXT,
        state TEXT,
        pincode TEXT,
        course TEXT,
        admission_year TEXT,
        photo TEXT,
        id_card_file TEXT,
        library_card_file TEXT,
        bus_card_file TEXT
    )
    """)

    for col, typ in [
        ("father_name", "TEXT"), ("mother_name", "TEXT"), ("dob", "TEXT"),
        ("gender", "TEXT"), ("city", "TEXT"), ("state", "TEXT"),
        ("pincode", "TEXT"), ("course", "TEXT"), ("admission_year", "TEXT"),
        ("photo", "TEXT"), ("id_card_file", "TEXT"), ("library_card_file", "TEXT"), ("bus_card_file", "TEXT")
    ]:
        add_column_if_missing(c, "users", col, typ)

    c.execute("""
    CREATE TABLE IF NOT EXISTS marks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment TEXT,
        semester TEXT,
        subject TEXT,
        total_credit INTEGER,
        earned_credit INTEGER,
        grade TEXT,
        sgpa REAL,
        exam TEXT,
        marks_obtained REAL,
        max_marks REAL
    )
    """)
    for col, typ in [("semester", "TEXT"), ("marks_obtained", "REAL"), ("max_marks", "REAL")]:
        add_column_if_missing(c, "marks", col, typ)

    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment TEXT,
        subject TEXT,
        date TEXT,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS assignments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment TEXT,
        semester TEXT,
        subject TEXT,
        title TEXT,
        marks_obtained REAL,
        max_marks REAL,
        submit_date TEXT,
        remarks TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment TEXT,
        student_name TEXT,
        question TEXT,
        answer TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TEXT DEFAULT CURRENT_DATE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS notices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        message TEXT
    )
    """)


    c.execute("""
    CREATE TABLE IF NOT EXISTS grievances(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment TEXT,
        emoji TEXT,
        category TEXT,
        message TEXT,
        severity TEXT,
        status TEXT DEFAULT 'New',
        created_at TEXT DEFAULT CURRENT_DATE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS reverse_attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment TEXT,
        subject TEXT,
        date TEXT,
        status TEXT,
        location_note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS notes_marketplace(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment TEXT,
        title TEXT,
        subject TEXT,
        semester TEXT,
        price REAL,
        description TEXT,
        created_at TEXT DEFAULT CURRENT_DATE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS carbon_wallet(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment TEXT,
        travel_mode TEXT,
        points INTEGER,
        date TEXT,
        note TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS time_bank(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        giver_enrollment TEXT,
        receiver_enrollment TEXT,
        skill TEXT,
        hours REAL,
        status TEXT DEFAULT 'Pending',
        date TEXT DEFAULT CURRENT_DATE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS memory_capsule(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment TEXT,
        title TEXT,
        event_date TEXT,
        memory_type TEXT,
        description TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS library_books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        subject TEXT,
        status TEXT DEFAULT 'Available',
        issued_to TEXT,
        issue_date TEXT
    )
    """)

    if not c.execute("SELECT * FROM library_books").fetchone():
        c.execute("INSERT INTO library_books(title,author,subject) VALUES(?,?,?)",
                  ("Introduction to Cyber Security", "Prof. Ram Devide", "Cyber Security"))
        c.execute("INSERT INTO library_books(title,author,subject) VALUES(?,?,?)",
                  ("Software Testing Methods", "Prof. Chandani Sharma", "Software Testing"))
        c.execute("INSERT INTO library_books(title,author,subject) VALUES(?,?,?)",
                  ("Mobile Computing Basics", "Prof. Deepesh Kumar", "Mobile Computing"))

    if not c.execute("SELECT * FROM users WHERE email='admin@gmail.com'").fetchone():
        c.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                  ("Admin", "admin@gmail.com", generate_password_hash("admin123"), "admin"))

    if not c.execute("SELECT * FROM users WHERE email='faculty@gmail.com'").fetchone():
        c.execute("INSERT INTO users(name,email,password,role,phone) VALUES(?,?,?,?,?)",
                  ("Faculty", "faculty@gmail.com", generate_password_hash("faculty123"), "faculty", "9999999999"))

    if not c.execute("SELECT * FROM users WHERE email='student@gmail.com'").fetchone():
        c.execute("""
        INSERT INTO users(name,email,enrollment,password,role,phone,semester,address,course,admission_year)
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """, ("Student Demo", "student@gmail.com", "ENR001", generate_password_hash("student123"),
              "student", "9876543210", "5th Semester", "Bhopal", "B.Tech CSE", "2022"))

    db.commit()
    db.close()


init_db()


def login_required(role=None):
    def wrapper(fn):
        from functools import wraps
        @wraps(fn)
        def inner(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Access denied", "danger")
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return inner
    return wrapper


def safe_percent(obtained, max_marks):
    try:
        obtained = float(obtained or 0)
        max_marks = float(max_marks or 0)
        return round((obtained / max_marks) * 100, 2) if max_marks else 0
    except Exception:
        return 0


def build_marksheet(rows):
    grouped = {}
    for r in rows:
        sem = r["semester"] or "Not Set"
        grouped.setdefault(sem, {"rows": [], "total_credit": 0, "earned_credit": 0, "weighted_points": 0, "total_marks": 0, "obtained_marks": 0})
        g = grouped[sem]
        g["rows"].append(r)
        credit = float(r["total_credit"] or 0)
        earned = float(r["earned_credit"] or 0)
        gp = float(r["sgpa"] or 0)
        obtained = float(r["marks_obtained"] or 0)
        maximum = float(r["max_marks"] or 0)
        g["total_credit"] += credit
        g["earned_credit"] += earned
        g["weighted_points"] += credit * gp
        g["obtained_marks"] += obtained
        g["total_marks"] += maximum
    for sem, g in grouped.items():
        g["sgpa"] = round(g["weighted_points"] / g["total_credit"], 2) if g["total_credit"] else 0
        g["percentage"] = round((g["obtained_marks"] / g["total_marks"]) * 100, 2) if g["total_marks"] else 0
        g["result"] = "PASS" if g["rows"] and all((row["grade"] or "").upper() != "F" for row in g["rows"]) else "FAIL"
    return grouped


def build_assignment_sheet(rows):
    grouped = {}
    for r in rows:
        sem = r["semester"] or "Not Set"
        grouped.setdefault(sem, {"rows": [], "total_marks": 0, "obtained_marks": 0})
        g = grouped[sem]
        g["rows"].append(r)
        g["obtained_marks"] += float(r["marks_obtained"] or 0)
        g["total_marks"] += float(r["max_marks"] or 0)
    for sem, g in grouped.items():
        g["percentage"] = round((g["obtained_marks"] / g["total_marks"]) * 100, 2) if g["total_marks"] else 0
    return grouped


def ai_predict(avg_marks, attendance_percent):
    score = (avg_marks * 0.7) + (attendance_percent * 0.3)
    return "Pass / Safe" if score >= 55 else "At Risk"


def academic_dna(avg_marks, attp, assignment_avg):
    if avg_marks >= 75 and attp >= 75:
        return "Consistent Performer"
    if avg_marks >= 70 and attp < 65:
        return "Self Learner - Attendance Improve"
    if assignment_avg >= avg_marks + 10:
        return "Practical / Assignment Strong"
    if attp >= 80 and avg_marks < 55:
        return "Hard Working - Needs Concept Support"
    return "Balanced Learner"


def grievance_severity(emoji):
    if emoji in ["😡", "🚨", "😢"]:
        return "High"
    if emoji in ["😟", "😐"]:
        return "Medium"
    return "Low"


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=? AND role=?", (email, role)).fetchone()
        db.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            session["enrollment"] = user["enrollment"]
            return redirect(url_for(f"{role}_dashboard"))
        flash("Invalid login details", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            db = get_db()
            db.execute("""
                INSERT INTO users(name,email,enrollment,password,role,phone,semester,address)
                VALUES(?,?,?,?,?,?,?,?)
            """, (request.form["name"], request.form["email"], request.form.get("enrollment"),
                  generate_password_hash(request.form["password"]), "student",
                  request.form.get("phone"), request.form.get("semester"), request.form.get("address")))
            db.commit(); db.close()
            flash("Registration successful. Login now.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email or enrollment already exists", "danger")
    return render_template("register.html", semesters=SEMESTERS)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        role = request.form.get("role")
        email = request.form.get("email")
        verification_value = request.form.get("verification_value")
        new_pw = request.form.get("new_password")
        confirm_pw = request.form.get("confirm_password")

        if new_pw != confirm_pw:
            flash("Passwords do not match", "danger")
            return render_template("forgot_password.html")

        db = get_db()
        if role == "student":
            user = db.execute("SELECT * FROM users WHERE email=? AND role=? AND enrollment=?", (email, role, verification_value)).fetchone()
        else:
            user = db.execute("SELECT * FROM users WHERE email=? AND role=? AND phone=?", (email, role, verification_value)).fetchone()

        if user:
            hashed_pw = generate_password_hash(new_pw)
            db.execute("UPDATE users SET password=? WHERE id=?", (hashed_pw, user["id"]))
            db.commit()
            db.close()
            flash("Password reset successfully! Please login.", "success")
            return redirect(url_for("login"))
        else:
            db.close()
            flash("Invalid verification details. Please verify your Email and Enrollment/Phone.", "danger")
    return render_template("forgot_password.html")


@app.route("/student")
@login_required("student")
def student_dashboard():
    enr = session.get("enrollment")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    marks = db.execute("SELECT * FROM marks WHERE enrollment=? ORDER BY semester,id", (enr,)).fetchall()
    assignments = db.execute("SELECT * FROM assignments WHERE enrollment=? ORDER BY id DESC", (enr,)).fetchall()
    attendance = db.execute("SELECT * FROM attendance WHERE enrollment=? ORDER BY date DESC", (enr,)).fetchall()
    notices = db.execute("SELECT * FROM notices ORDER BY id DESC LIMIT 5").fetchall()
    questions = db.execute("SELECT * FROM questions WHERE enrollment=? ORDER BY id DESC", (enr,)).fetchall()
    grievances = db.execute("SELECT * FROM grievances WHERE enrollment=? ORDER BY id DESC LIMIT 5", (enr,)).fetchall()
    notes = db.execute("SELECT * FROM notes_marketplace ORDER BY id DESC LIMIT 8").fetchall()
    carbon_rows = db.execute("SELECT * FROM carbon_wallet WHERE enrollment=? ORDER BY date DESC LIMIT 10", (enr,)).fetchall()
    time_rows = db.execute("SELECT * FROM time_bank WHERE giver_enrollment=? OR receiver_enrollment=? ORDER BY id DESC LIMIT 10", (enr, enr)).fetchall()
    memories = db.execute("SELECT * FROM memory_capsule WHERE enrollment=? ORDER BY event_date DESC LIMIT 8", (enr,)).fetchall()
    library_books = db.execute("SELECT * FROM library_books ORDER BY id DESC").fetchall()

    present = len([a for a in attendance if a["status"] == "Present"])
    absent = len([a for a in attendance if a["status"] == "Absent"])
    leave = len([a for a in attendance if a["status"] == "Leave"])
    attp = round((present / len(attendance)) * 100, 2) if attendance else 0
    mark_percents = [safe_percent(m["marks_obtained"], m["max_marks"]) for m in marks if m["max_marks"]]
    avg = round(sum(mark_percents) / len(mark_percents), 2) if mark_percents else 0
    assignment_percents = [safe_percent(a["marks_obtained"], a["max_marks"]) for a in assignments if a["max_marks"]]
    assignment_avg = round(sum(assignment_percents) / len(assignment_percents), 2) if assignment_percents else 0
    prediction = ai_predict(avg, attp)
    dna = academic_dna(avg, attp, assignment_avg)
    carbon_points = sum([int(c["points"] or 0) for c in carbon_rows])
    marksheet = build_marksheet(marks)
    assignment_sheet = build_assignment_sheet(assignments)
    db.close()
    return render_template("student_dashboard.html", user=user, marks=marks, assignments=assignments, marksheet=marksheet, assignment_sheet=assignment_sheet,
                           attendance=attendance, notices=notices, questions=questions, grievances=grievances, notes=notes,
                           carbon_rows=carbon_rows, carbon_points=carbon_points, time_rows=time_rows, memories=memories, dna=dna, assignment_avg=assignment_avg,
                           attp=attp, avg=avg, prediction=prediction, present=present, absent=absent, leave=leave, library_books=library_books)


@app.route("/student/bio", methods=["GET", "POST"])
@login_required("student")
def student_bio():
    db = get_db()
    if request.method == "POST":
        db.execute("""
        UPDATE users SET phone=?,semester=?,address=?,father_name=?,mother_name=?,dob=?,gender=?,city=?,state=?,pincode=?,course=?,admission_year=?
        WHERE id=? AND role='student'
        """, (request.form.get("phone"), request.form.get("semester"), request.form.get("address"),
              request.form.get("father_name"), request.form.get("mother_name"), request.form.get("dob"),
              request.form.get("gender"), request.form.get("city"), request.form.get("state"),
              request.form.get("pincode"), request.form.get("course"), request.form.get("admission_year"), session["user_id"]))
        db.commit(); db.close()
        flash("Bio data updated successfully", "success")
        return redirect(url_for("student_dashboard"))
    user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    db.close()
    return render_template("student_bio.html", user=user, semesters=SEMESTERS)


@app.route("/ask-question", methods=["POST"])
@login_required("student")
def ask_question():
    db = get_db()
    db.execute("INSERT INTO questions(enrollment,student_name,question,status) VALUES(?,?,?,?)",
               (session.get("enrollment"), session.get("name"), request.form["question"], "Pending"))
    db.commit(); db.close()
    flash("Question sent to faculty", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/faculty")
@login_required("faculty")
def faculty_dashboard():
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        like = f"%{q}%"
        students = db.execute("""SELECT * FROM users WHERE role='student' AND
            (name LIKE ? OR enrollment LIKE ? OR email LIKE ? OR phone LIKE ? OR course LIKE ?) ORDER BY id DESC""",
            (like, like, like, like, like)).fetchall()
    else:
        students = db.execute("SELECT * FROM users WHERE role='student' ORDER BY id DESC").fetchall()
    marks = db.execute("SELECT * FROM marks ORDER BY id DESC LIMIT 30").fetchall()
    attendance = db.execute("SELECT * FROM attendance ORDER BY id DESC LIMIT 30").fetchall()
    assignments = db.execute("SELECT * FROM assignments ORDER BY id DESC LIMIT 30").fetchall()
    questions = db.execute("SELECT * FROM questions ORDER BY id DESC LIMIT 20").fetchall()
    grievances = db.execute("SELECT * FROM grievances ORDER BY id DESC LIMIT 20").fetchall()
    reverse_requests = db.execute("SELECT * FROM reverse_attendance ORDER BY id DESC LIMIT 20").fetchall()
    time_bank_rows = db.execute("SELECT * FROM time_bank ORDER BY id DESC LIMIT 20").fetchall()
    pending_questions = db.execute("SELECT COUNT(*) c FROM questions WHERE status='Pending'").fetchone()["c"]
    pending_grievances = db.execute("SELECT COUNT(*) c FROM grievances WHERE status='New'").fetchone()["c"]
    counts = {
        "students": db.execute("SELECT COUNT(*) c FROM users WHERE role='student'").fetchone()["c"],
        "marks": db.execute("SELECT COUNT(*) c FROM marks").fetchone()["c"],
        "attendance": db.execute("SELECT COUNT(*) c FROM attendance").fetchone()["c"],
        "assignments": db.execute("SELECT COUNT(*) c FROM assignments").fetchone()["c"],
        "grievances": db.execute("SELECT COUNT(*) c FROM grievances").fetchone()["c"],
    }
    present_total = db.execute("SELECT COUNT(*) c FROM attendance WHERE status='Present'").fetchone()["c"]
    absent_total = db.execute("SELECT COUNT(*) c FROM attendance WHERE status='Absent'").fetchone()["c"]
    leave_total = db.execute("SELECT COUNT(*) c FROM attendance WHERE status='Leave'").fetchone()["c"]
    total_att = present_total + absent_total + leave_total
    attendance_percent = round((present_total / total_att) * 100, 2) if total_att else 0
    notices = db.execute("SELECT * FROM notices ORDER BY id DESC LIMIT 20").fetchall()
    db.close()
    return render_template("faculty_dashboard.html", students=students, marks=marks, attendance=attendance,
                           assignments=assignments, questions=questions, grievances=grievances, reverse_requests=reverse_requests, time_bank_rows=time_bank_rows,
                           pending_questions=pending_questions, pending_grievances=pending_grievances,
                           counts=counts, q=q, present_total=present_total, absent_total=absent_total, leave_total=leave_total,
                           attendance_percent=attendance_percent, notices=notices)


@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    db = get_db()
    counts = {
        "students": db.execute("SELECT COUNT(*) c FROM users WHERE role='student'").fetchone()["c"],
        "faculty": db.execute("SELECT COUNT(*) c FROM users WHERE role='faculty'").fetchone()["c"],
        "marks": db.execute("SELECT COUNT(*) c FROM marks").fetchone()["c"],
        "attendance": db.execute("SELECT COUNT(*) c FROM attendance").fetchone()["c"],
        "assignments": db.execute("SELECT COUNT(*) c FROM assignments").fetchone()["c"],
        "questions": db.execute("SELECT COUNT(*) c FROM questions").fetchone()["c"],
        "grievances": db.execute("SELECT COUNT(*) c FROM grievances").fetchone()["c"],
        "notes": db.execute("SELECT COUNT(*) c FROM notes_marketplace").fetchone()["c"],
        "transport entries": db.execute("SELECT COUNT(*) c FROM carbon_wallet").fetchone()["c"],
        "time bank": db.execute("SELECT COUNT(*) c FROM time_bank").fetchone()["c"]
    }
    users = db.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    marks = db.execute("SELECT * FROM marks ORDER BY id DESC LIMIT 50").fetchall()
    attendance = db.execute("SELECT * FROM attendance ORDER BY id DESC LIMIT 50").fetchall()
    assignments = db.execute("SELECT * FROM assignments ORDER BY id DESC LIMIT 50").fetchall()
    questions = db.execute("SELECT * FROM questions ORDER BY id DESC LIMIT 50").fetchall()
    db.close()
    return render_template("admin_dashboard.html", counts=counts, users=users, marks=marks,
                           attendance=attendance, assignments=assignments, questions=questions)


@app.route("/add_student", methods=["GET", "POST"])
@login_required("faculty")
def add_student():
    if request.method == "POST":
        try:
            db = get_db()
            db.execute("""
            INSERT INTO users(name,email,enrollment,password,role,phone,semester,course)
            VALUES(?,?,?,?,?,?,?,?)
            """, (request.form["name"], request.form["email"], request.form["enrollment"],
                  generate_password_hash(request.form.get("password") or "student123"), "student",
                  request.form.get("phone"), request.form.get("semester"), request.form.get("course")))
            db.commit(); db.close()
            flash("Student account added. Student will fill bio data.", "success")
            return redirect(url_for("faculty_dashboard"))
        except sqlite3.IntegrityError:
            flash("Email or enrollment already exists", "danger")
    return render_template("add_student.html", semesters=SEMESTERS)


@app.route("/student_profile/<int:id>")
@login_required("faculty")
def view_student(id):
    db = get_db()
    student = db.execute("SELECT * FROM users WHERE id=? AND role='student'", (id,)).fetchone()
    if not student:
        db.close()
        return "Student not found"

    marks = db.execute("SELECT * FROM marks WHERE enrollment=? ORDER BY semester,id", (student["enrollment"],)).fetchall()
    attendance = db.execute("SELECT * FROM attendance WHERE enrollment=? ORDER BY date DESC", (student["enrollment"],)).fetchall()
    assignments = db.execute("SELECT * FROM assignments WHERE enrollment=? ORDER BY id DESC", (student["enrollment"],)).fetchall()

    present = len([a for a in attendance if a["status"] == "Present"])
    absent = len([a for a in attendance if a["status"] == "Absent"])
    leave = len([a for a in attendance if a["status"] == "Leave"])
    attp = round((present / len(attendance)) * 100, 2) if attendance else 0

    mark_percents = [safe_percent(m["marks_obtained"], m["max_marks"]) for m in marks if m["max_marks"]]
    avg = round(sum(mark_percents) / len(mark_percents), 2) if mark_percents else 0
    assignment_percents = [safe_percent(a["marks_obtained"], a["max_marks"]) for a in assignments if a["max_marks"]]
    assignment_avg = round(sum(assignment_percents) / len(assignment_percents), 2) if assignment_percents else 0
    prediction = ai_predict(avg, attp)
    dna = academic_dna(avg, attp, assignment_avg)
    marksheet = build_marksheet(marks)
    assignment_sheet = build_assignment_sheet(assignments)
    db.close()

    return render_template("student_profile.html", student=student, marks=marks, attendance=attendance, assignments=assignments,
                           present=present, absent=absent, leave=leave, attp=attp, avg=avg, assignment_avg=assignment_avg,
                           prediction=prediction, dna=dna, marksheet=marksheet, assignment_sheet=assignment_sheet)


@app.route("/edit_student/<int:id>", methods=["GET", "POST"])
@login_required("faculty")
def edit_student(id):
    db = get_db()
    if request.method == "POST":
        db.execute("UPDATE users SET name=?,email=?,enrollment=?,phone=?,semester=?,course=? WHERE id=? AND role='student'",
                   (request.form["name"], request.form["email"], request.form["enrollment"],
                    request.form.get("phone"), request.form.get("semester"), request.form.get("course"), id))
        db.commit(); db.close()
        flash("Student account updated", "success")
        return redirect(url_for("faculty_dashboard"))
    student = db.execute("SELECT * FROM users WHERE id=? AND role='student'", (id,)).fetchone()
    db.close()
    return render_template("edit_student.html", student=student, semesters=SEMESTERS)


@app.route("/delete_student/<int:id>")
@login_required("faculty")
def delete_student(id):
    db = get_db()
    student = db.execute("SELECT * FROM users WHERE id=? AND role='student'", (id,)).fetchone()
    if student:
        db.execute("DELETE FROM marks WHERE enrollment=?", (student["enrollment"],))
        db.execute("DELETE FROM attendance WHERE enrollment=?", (student["enrollment"],))
        db.execute("DELETE FROM assignments WHERE enrollment=?", (student["enrollment"],))
        db.execute("DELETE FROM questions WHERE enrollment=?", (student["enrollment"],))
        db.execute("DELETE FROM grievances WHERE enrollment=?", (student["enrollment"],))
        db.execute("DELETE FROM reverse_attendance WHERE enrollment=?", (student["enrollment"],))
        db.execute("DELETE FROM notes_marketplace WHERE enrollment=?", (student["enrollment"],))
        db.execute("DELETE FROM carbon_wallet WHERE enrollment=?", (student["enrollment"],))
        db.execute("DELETE FROM time_bank WHERE giver_enrollment=? OR receiver_enrollment=?", (student["enrollment"], student["enrollment"]))
        db.execute("DELETE FROM memory_capsule WHERE enrollment=?", (student["enrollment"],))
        db.execute("DELETE FROM users WHERE id=? AND role='student'", (id,))
        db.commit()
    db.close()
    flash("Student deleted successfully", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/add-mark", methods=["GET", "POST"])
@login_required("faculty")
def add_mark():
    db = get_db()
    if request.method == "POST":
        enrollment = request.form.get("enrollment")
        semester = request.form.get("semester")
        exam = request.form.get("exam") or "Final Result"
        subjects = request.form.getlist("subject[]")
        marks_obtained = request.form.getlist("marks_obtained[]")
        max_marks = request.form.getlist("max_marks[]")
        total_credits = request.form.getlist("total_credit[]")
        earned_credits = request.form.getlist("earned_credit[]")
        grades = request.form.getlist("grade[]")

        saved = 0
        for i, subject in enumerate(subjects):
            subject = (subject or "").strip()
            if not subject:
                continue
            grade = grades[i] if i < len(grades) else "F"
            total_credit = total_credits[i] if i < len(total_credits) else 0
            earned_credit = earned_credits[i] if i < len(earned_credits) else total_credit
            obtained = marks_obtained[i] if i < len(marks_obtained) else 0
            maximum = max_marks[i] if i < len(max_marks) else 100
            db.execute("""
                INSERT INTO marks(enrollment,semester,subject,total_credit,earned_credit,grade,sgpa,exam,marks_obtained,max_marks)
                VALUES(?,?,?,?,?,?,?,?,?,?)
            """, (enrollment, semester, subject, total_credit, earned_credit, grade,
                  GRADE_POINTS.get(grade, 0), exam, obtained, maximum))
            saved += 1

        db.commit(); db.close()
        flash(f"{saved} subject marks added for {semester}", "success")
        return redirect(url_for("faculty_dashboard"))
    students = db.execute("SELECT * FROM users WHERE role='student' ORDER BY name").fetchall()
    db.close()
    return render_template("add_mark.html", students=students, semesters=SEMESTERS)


@app.route("/edit-mark/<int:id>", methods=["GET", "POST"])
@login_required("faculty")
def edit_mark(id):
    db = get_db()
    if request.method == "POST":
        grade = request.form.get("grade")
        db.execute("""UPDATE marks SET enrollment=?,semester=?,subject=?,total_credit=?,earned_credit=?,grade=?,sgpa=?,exam=?,marks_obtained=?,max_marks=? WHERE id=?""",
                   (request.form.get("enrollment"), request.form.get("semester"), request.form.get("subject"),
                    request.form.get("total_credit"), request.form.get("earned_credit"), grade, GRADE_POINTS.get(grade, 0),
                    request.form.get("exam"), request.form.get("marks_obtained"), request.form.get("max_marks"), id))
        db.commit(); db.close(); flash("Marks updated", "success"); return redirect(url_for("faculty_dashboard"))
    mark = db.execute("SELECT * FROM marks WHERE id=?", (id,)).fetchone()
    students = db.execute("SELECT * FROM users WHERE role='student' ORDER BY name").fetchall()
    db.close()
    return render_template("edit_mark.html", mark=mark, students=students, semesters=SEMESTERS)


@app.route("/delete-mark/<int:id>")
@login_required("faculty")
def delete_mark(id):
    db = get_db(); db.execute("DELETE FROM marks WHERE id=?", (id,)); db.commit(); db.close()
    flash("Mark deleted", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/add-assignment", methods=["GET", "POST"])
@login_required("faculty")
def add_assignment():
    db = get_db()
    if request.method == "POST":
        enrollment = request.form.get("enrollment")
        semester = request.form.get("semester")
        submit_date = request.form.get("submit_date")
        subjects = request.form.getlist("subject[]")
        titles = request.form.getlist("title[]")
        marks_obtained = request.form.getlist("marks_obtained[]")
        max_marks = request.form.getlist("max_marks[]")
        remarks = request.form.getlist("remarks[]")

        saved = 0
        for i, subject in enumerate(subjects):
            subject = (subject or "").strip()
            title = titles[i] if i < len(titles) else "Assignment"
            if not subject and not title:
                continue
            db.execute("""
            INSERT INTO assignments(enrollment,semester,subject,title,marks_obtained,max_marks,submit_date,remarks)
            VALUES(?,?,?,?,?,?,?,?)
            """, (enrollment, semester, subject, title,
                  marks_obtained[i] if i < len(marks_obtained) else 0,
                  max_marks[i] if i < len(max_marks) else 10, submit_date,
                  remarks[i] if i < len(remarks) else ""))
            saved += 1

        db.commit(); db.close(); flash(f"{saved} assignment subject marks added for {semester}", "success"); return redirect(url_for("faculty_dashboard"))
    students = db.execute("SELECT * FROM users WHERE role='student' ORDER BY name").fetchall(); db.close()
    return render_template("add_assignment.html", students=students, semesters=SEMESTERS, today=date.today())


@app.route("/edit-assignment/<int:id>", methods=["GET", "POST"])
@login_required("faculty")
def edit_assignment(id):
    db = get_db()
    if request.method == "POST":
        db.execute("""UPDATE assignments SET enrollment=?,semester=?,subject=?,title=?,marks_obtained=?,max_marks=?,submit_date=?,remarks=? WHERE id=?""",
                   (request.form.get("enrollment"), request.form.get("semester"), request.form.get("subject"),
                    request.form.get("title"), request.form.get("marks_obtained"), request.form.get("max_marks"),
                    request.form.get("submit_date"), request.form.get("remarks"), id))
        db.commit(); db.close(); flash("Assignment updated", "success"); return redirect(url_for("faculty_dashboard"))
    assignment = db.execute("SELECT * FROM assignments WHERE id=?", (id,)).fetchone()
    students = db.execute("SELECT * FROM users WHERE role='student' ORDER BY name").fetchall(); db.close()
    return render_template("edit_assignment.html", assignment=assignment, students=students, semesters=SEMESTERS)


@app.route("/delete-assignment/<int:id>")
@login_required("faculty")
def delete_assignment(id):
    db = get_db(); db.execute("DELETE FROM assignments WHERE id=?", (id,)); db.commit(); db.close()
    flash("Assignment deleted", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/add-attendance", methods=["GET", "POST"])
@login_required("faculty")
def add_attendance():
    db = get_db()
    if request.method == "POST":
        db.execute("INSERT INTO attendance(enrollment,subject,date,status) VALUES(?,?,?,?)",
                   (request.form["enrollment"], request.form["subject"], request.form["date"], request.form["status"]))
        db.commit(); db.close(); flash("Attendance saved", "success"); return redirect(url_for("faculty_dashboard"))
    students = db.execute("SELECT * FROM users WHERE role='student' ORDER BY name").fetchall(); db.close()
    return render_template("add_attendance.html", students=students, today=date.today())


@app.route("/edit-attendance/<int:id>", methods=["GET", "POST"])
@login_required("faculty")
def edit_attendance(id):
    db = get_db()
    if request.method == "POST":
        db.execute("UPDATE attendance SET enrollment=?,subject=?,date=?,status=? WHERE id=?",
                   (request.form["enrollment"], request.form["subject"], request.form["date"], request.form["status"], id))
        db.commit(); db.close(); flash("Attendance updated", "success"); return redirect(url_for("faculty_dashboard"))
    attendance = db.execute("SELECT * FROM attendance WHERE id=?", (id,)).fetchone()
    students = db.execute("SELECT * FROM users WHERE role='student' ORDER BY name").fetchall(); db.close()
    return render_template("edit_attendance.html", attendance=attendance, students=students)


@app.route("/delete-attendance/<int:id>")
@login_required("faculty")
def delete_attendance(id):
    db = get_db(); db.execute("DELETE FROM attendance WHERE id=?", (id,)); db.commit(); db.close()
    flash("Attendance deleted", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/answer-question/<int:id>", methods=["GET", "POST"])
@login_required("faculty")
def answer_question(id):
    db = get_db()
    if request.method == "POST":
        db.execute("UPDATE questions SET answer=?, status='Answered' WHERE id=?", (request.form["answer"], id))
        db.commit(); db.close(); flash("Answer sent to student", "success"); return redirect(url_for("faculty_dashboard"))
    question = db.execute("SELECT * FROM questions WHERE id=?", (id,)).fetchone(); db.close()
    return render_template("answer_question.html", question=question)


@app.route("/silent-grievance", methods=["POST"])
@login_required("student")
def silent_grievance():
    emoji = request.form.get("emoji")
    db = get_db()
    db.execute("INSERT INTO grievances(enrollment,emoji,category,message,severity) VALUES(?,?,?,?,?)",
               (session.get("enrollment"), emoji, request.form.get("category"), request.form.get("message"), grievance_severity(emoji)))
    db.commit(); db.close()
    flash("Anonymous emoji grievance submitted", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/update-grievance/<int:id>/<status>")
@login_required("faculty")
def update_grievance(id, status):
    db = get_db(); db.execute("UPDATE grievances SET status=? WHERE id=?", (status, id)); db.commit(); db.close()
    flash("Grievance status updated", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/reverse-attendance", methods=["POST"])
@login_required("student")
def reverse_attendance():
    db = get_db()
    db.execute("INSERT INTO reverse_attendance(enrollment,subject,date,status,location_note) VALUES(?,?,?,?,?)",
               (session.get("enrollment"), request.form.get("subject"), request.form.get("date"), "Pending", request.form.get("location_note")))
    db.commit(); db.close()
    flash("Reverse attendance request sent to faculty", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/approve-reverse-attendance/<int:id>/<status>")
@login_required("faculty")
def approve_reverse_attendance(id, status):
    db = get_db()
    row = db.execute("SELECT * FROM reverse_attendance WHERE id=?", (id,)).fetchone()
    if row:
        db.execute("UPDATE reverse_attendance SET status=? WHERE id=?", (status, id))
        if status == "Approved":
            db.execute("INSERT INTO attendance(enrollment,subject,date,status) VALUES(?,?,?,?)", (row["enrollment"], row["subject"], row["date"], "Present"))
    db.commit(); db.close()
    flash("Reverse attendance updated", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/add-note", methods=["POST"])
@login_required("student")
def add_note():
    db = get_db()
    db.execute("INSERT INTO notes_marketplace(enrollment,title,subject,semester,price,description) VALUES(?,?,?,?,?,?)",
               (session.get("enrollment"), request.form.get("title"), request.form.get("subject"), request.form.get("semester"), request.form.get("price"), request.form.get("description")))
    db.commit(); db.close()
    flash("Notes added to marketplace", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/carbon-entry", methods=["POST"])
@login_required("student")
def carbon_entry():
    mode = request.form.get("travel_mode")
    points_map = {"Cycle": 2, "Bus": 1, "Walk": 2, "Car": -2, "Bike": -1}
    db = get_db()
    db.execute("INSERT INTO carbon_wallet(enrollment,travel_mode,points,date,note) VALUES(?,?,?,?,?)",
               (session.get("enrollment"), mode, points_map.get(mode, 0), request.form.get("date"), request.form.get("note")))
    db.commit(); db.close()
    flash("Carbon wallet updated", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/time-bank", methods=["POST"])
@login_required("student")
def time_bank():
    db = get_db()
    db.execute("INSERT INTO time_bank(giver_enrollment,receiver_enrollment,skill,hours,status) VALUES(?,?,?,?,?)",
               (session.get("enrollment"), request.form.get("receiver_enrollment"), request.form.get("skill"), request.form.get("hours"), "Pending"))
    db.commit(); db.close()
    flash("Time bank skill exchange request added", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/update-time-bank/<int:id>/<status>")
@login_required("faculty")
def update_time_bank(id, status):
    db = get_db(); db.execute("UPDATE time_bank SET status=? WHERE id=?", (status, id)); db.commit(); db.close()
    flash("Time bank status updated", "success")
    return redirect(url_for("faculty_dashboard"))


@app.route("/memory-capsule", methods=["POST"])
@login_required("student")
def memory_capsule():
    db = get_db()
    db.execute("INSERT INTO memory_capsule(enrollment,title,event_date,memory_type,description) VALUES(?,?,?,?,?)",
               (session.get("enrollment"), request.form.get("title"), request.form.get("event_date"), request.form.get("memory_type"), request.form.get("description")))
    db.commit(); db.close()
    flash("Memory capsule event saved", "success")
    return redirect(url_for("student_dashboard"))



@app.route("/upload-card/<card_type>/<int:id>", methods=["GET", "POST"])
@login_required("faculty")
def upload_card(card_type, id):
    if card_type not in ["id", "library", "bus"]:
        flash("Invalid card type", "danger")
        return redirect(url_for("faculty_dashboard"))

    db = get_db()
    student = db.execute("SELECT * FROM users WHERE id=? AND role='student'", (id,)).fetchone()
    if not student:
        db.close()
        flash("Student not found", "danger")
        return redirect(url_for("faculty_dashboard"))

    labels = {"id": "Identity Card", "library": "Library Card", "bus": "Bus Card"}
    field_names = {"id": "card_file", "library": "card_file", "bus": "card_file"}

    if request.method == "POST":
        file = request.files.get("card_file")
        if not file or file.filename == "":
            db.close()
            flash(f"Please choose {labels[card_type]} image/PDF", "danger")
            return redirect(url_for("upload_card", card_type=card_type, id=id))
        if not allowed_file(file.filename):
            db.close()
            flash("Only PNG, JPG, JPEG, WEBP or PDF files are allowed", "danger")
            return redirect(url_for("upload_card", card_type=card_type, id=id))

        column, static_path, label = upload_student_card_file(student, file, card_type)
        db.execute(f"UPDATE users SET {column}=? WHERE id=? AND role='student'", (static_path, id))
        db.commit()
        db.close()
        flash(f"{labels[card_type]} uploaded successfully", "success")
        return redirect(url_for("view_student", id=id))

    db.close()
    return render_template("upload_card.html", student=student, card_type=card_type, card_label=labels[card_type])


@app.route("/upload-id-card/<int:id>", methods=["GET", "POST"])
@login_required("faculty")
def upload_id_card(id):
    return upload_card("id", id)

@app.route("/notice", methods=["GET", "POST"])
@login_required("admin")
def notice():
    if request.method == "POST":
        db = get_db()
        db.execute("INSERT INTO notices(title,message) VALUES(?,?)", (request.form["title"], request.form["message"]))
        db.commit(); db.close(); flash("Notice published", "success"); return redirect(url_for("admin_dashboard"))
    return render_template("notice.html")


@app.route("/faculty_login", methods=["GET", "POST"])
def faculty_login():
    if request.method == "POST":
        email = request.form["email"]; password = request.form["password"]
        db = get_db(); user = db.execute("SELECT * FROM users WHERE email=? AND role='faculty'", (email,)).fetchone(); db.close()
        if user and check_password_hash(user["password"], password):
            otp = str(random.randint(100000, 999999)); otp_storage[email] = otp
            print("OTP:", otp); session["otp_user"] = email
            return redirect(url_for("verify_otp"))
        flash("Invalid faculty login", "danger")
    return render_template("faculty_login.html")


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if "otp_user" not in session:
        return redirect(url_for("faculty_login"))
    email = session["otp_user"]
    if request.method == "POST":
        if otp_storage.get(email) == request.form["otp"]:
            db = get_db(); user = db.execute("SELECT * FROM users WHERE email=? AND role='faculty'", (email,)).fetchone(); db.close()
            session["user_id"] = user["id"]; session["name"] = user["name"]; session["role"] = user["role"]; session["enrollment"] = user["enrollment"]
            otp_storage.pop(email, None); session.pop("otp_user", None)
            return redirect(url_for("faculty_dashboard"))
        flash("Invalid OTP", "danger")
    return render_template("verify_otp.html")


@app.route("/faculty_register", methods=["GET", "POST"])
def faculty_register():
    if request.method == "POST":
        db = get_db()
        db.execute("INSERT INTO users(name,email,password,role,phone) VALUES(?,?,?,?,?)",
                   (request.form["name"], request.form["email"], generate_password_hash(request.form["password"]), "faculty", request.form.get("phone")))
        db.commit(); db.close(); flash("Faculty Registered", "success"); return redirect(url_for("login"))
    return render_template("faculty_register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/faculty/library", methods=["GET", "POST"])
@login_required("faculty")
def manage_library():
    db = get_db()
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        subject = request.form.get("subject")
        db.execute("INSERT INTO library_books (title, author, subject, status) VALUES (?, ?, ?, 'Available')", (title, author, subject))
        db.commit()
        flash("Book added to library catalog", "success")
    books = db.execute("SELECT * FROM library_books ORDER BY id DESC").fetchall()
    db.close()
    return render_template("manage_library.html", books=books)


@app.route("/faculty/library/delete/<int:book_id>")
@login_required("faculty")
def delete_book(book_id):
    db = get_db()
    db.execute("DELETE FROM library_books WHERE id=?", (book_id,))
    db.commit()
    db.close()
    flash("Book deleted from library", "success")
    return redirect(url_for("manage_library"))


@app.route("/student/library/borrow/<int:book_id>")
@login_required("student")
def borrow_book(book_id):
    db = get_db()
    book = db.execute("SELECT * FROM library_books WHERE id=? AND status='Available'", (book_id,)).fetchone()
    if book:
        enr = session.get("enrollment")
        issue_date = date.today().isoformat()
        db.execute("UPDATE library_books SET status='Issued', issued_to=?, issue_date=? WHERE id=?", (enr, issue_date, book_id))
        db.commit()
        flash(f"You have borrowed '{book['title']}' successfully", "success")
    else:
        flash("Book is not available for borrowing", "danger")
    db.close()
    return redirect(url_for("student_dashboard"))


@app.route("/student/library/return/<int:book_id>")
@login_required("student")
def return_book(book_id):
    db = get_db()
    enr = session.get("enrollment")
    book = db.execute("SELECT * FROM library_books WHERE id=? AND issued_to=?", (book_id, enr)).fetchone()
    if book:
        db.execute("UPDATE library_books SET status='Available', issued_to=NULL, issue_date=NULL WHERE id=?", (book_id,))
        db.commit()
        flash(f"You have returned '{book['title']}' successfully", "success")
    else:
        flash("Book record not found or not borrowed by you", "danger")
    db.close()
    return redirect(url_for("student_dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
