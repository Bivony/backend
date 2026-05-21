from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pymysql
import bcrypt
import os
import datetime

# =========================================================
# APP
# =========================================================
app = Flask(__name__)
CORS(app)

# =========================================================
# CONFIG
# =========================================================
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================================================
# DATABASE
# =========================================================
def database():

    return pymysql.connect(
        host="mysql-bivonys.alwaysdata.net",
        user="bivonys",
        password="modcom2026",
        database="bivonys_edunexus",
        port=3306,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


# =========================================================
# HELPERS
# =========================================================
def success(data=None, message="success"):

    return jsonify({
        "status": "success",
        "message": message,
        "data": data
    })


def error(message="error"):

    return jsonify({
        "status": "error",
        "message": message
    })

# =========================================================
# HOME
# =========================================================
@app.route("/")
def home():

    return "EduNexus Backend Running"

# =========================================================
# STATIC FILES
# =========================================================
@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )

# =========================================================
# GET ALL
# =========================================================
def get_all(table):

    con = database()
    cur = con.cursor()

    cur.execute(f"SELECT * FROM {table}")

    data = cur.fetchall()

    cur.close()
    con.close()

    return success(data)

# =========================================================
# AUTH - SIGNUP
# =========================================================
@app.route("/api/signup", methods=["POST"])
def signup():

    try:

        d = request.json

        name = d.get("name")
        email = d.get("email")
        password = d.get("password")
        phone = d.get("phone")
        role = d.get("role")

        if not name or not email or not password:
            return error("Missing fields")

        con = database()
        cur = con.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        existing = cur.fetchone()

        if existing:

            cur.close()
            con.close()

            return error("Email already exists")

        hashed = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        )

        cur.execute("""
            INSERT INTO users(
                name,
                email,
                phone,
                password,
                role
            )
            VALUES(%s,%s,%s,%s,%s)
        """, (
            name,
            email,
            phone,
            hashed,
            role
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Account created"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# AUTH - SIGNIN
# =========================================================
@app.route("/api/signin", methods=["POST"])
def signin():

    try:

        d = request.json

        email = d.get("email")
        password = d.get("password")

        con = database()
        cur = con.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        cur.close()
        con.close()

        if not user:
            return error("Invalid email")

        stored_password = user["password"]

        if isinstance(stored_password, str):
            stored_password = stored_password.encode()

        valid = bcrypt.checkpw(
            password.encode(),
            stored_password
        )

        if not valid:
            return error("Wrong password")

        user.pop("password", None)

        return success(
            user,
            "Login successful"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# USERS
# =========================================================
@app.route("/api/users", methods=["GET"])
def users():

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            SELECT *
            FROM users
            ORDER BY id DESC
        """)

        data = cur.fetchall()

        cur.close()
        con.close()

        return success(data)

    except Exception as e:
        return error(str(e))

# =========================================================
# UPDATE USER ROLE
# =========================================================
@app.route("/api/users/<int:id>/role", methods=["PUT"])
def update_user_role(id):

    try:

        d = request.json

        role = d.get("role")

        con = database()
        cur = con.cursor()

        cur.execute("""
            UPDATE users
            SET role=%s
            WHERE id=%s
        """, (
            role,
            id
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Role updated"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# DELETE USER
# =========================================================
@app.route("/api/users/<int:id>", methods=["DELETE"])
def delete_user(id):

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            DELETE FROM users
            WHERE id=%s
        """, (
            id,
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="User deleted"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# CLASSES
# =========================================================
@app.route("/api/classes", methods=["POST"])
def create_class():

    try:

        data = request.json

        class_name = data.get("class_name")
        teacher_id = data.get("teacher_id")

        if not class_name:
            return error("Class name required")

        con = database()
        cur = con.cursor()

        cur.execute("""
            INSERT INTO classes
            (
                class_name,
                teacher_id
            )
            VALUES(%s,%s)
        """, (
            class_name,
            teacher_id
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Class created"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# SUBJECTS
# =========================================================
@app.route("/api/subjects", methods=["GET"])
def subjects():

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            SELECT
                subjects.*,
                users.name AS teacher_name
            FROM subjects
            LEFT JOIN users
            ON subjects.teacher_id = users.id
            ORDER BY subjects.id DESC
        """)

        data = cur.fetchall()

        cur.close()
        con.close()

        return success(data)

    except Exception as e:
        return error(str(e))

# =========================================================
# ADD SUBJECT
# =========================================================
@app.route("/api/subjects", methods=["POST"])
def add_subject():

    try:

        d = request.json

        subject_name = d.get("subject_name")
        class_id = d.get("class_id")
        teacher_id = d.get("teacher_id")

        con = database()
        cur = con.cursor()

        cur.execute("""
            INSERT INTO subjects(
                subject_name,
                class_id,
                teacher_id
            )
            VALUES(%s,%s,%s)
        """, (
            subject_name,
            class_id,
            teacher_id
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Subject added"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# DELETE SUBJECT
# =========================================================
@app.route("/api/subjects/<int:id>", methods=["DELETE"])
def delete_subject(id):

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            DELETE FROM subjects
            WHERE id=%s
        """, (
            id,
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Subject deleted"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# ASSIGNMENTS
# =========================================================
@app.route("/api/assignments", methods=["GET"])
def assignments():

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            SELECT
                assignments.*,
                subjects.subject_name,
                users.name AS teacher_name
            FROM assignments
            LEFT JOIN subjects
            ON assignments.subject_id = subjects.id
            LEFT JOIN users
            ON assignments.teacher_id = users.id
            ORDER BY assignments.id DESC
        """)

        data = cur.fetchall()

        cur.close()
        con.close()

        return success(data)

    except Exception as e:
        return error(str(e))


@app.route("/api/assignments", methods=["POST"])
def add_assignment():

    try:

        d = request.json

        con = database()
        cur = con.cursor()

        cur.execute("""
            INSERT INTO assignments(
                subject_id,
                teacher_id,
                title,
                description,
                due_date
            )
            VALUES(%s,%s,%s,%s,%s)
        """, (
            d["subject_id"],
            d["teacher_id"],
            d["title"],
            d["description"],
            d["due_date"]
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Assignment added"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# DELETE ASSIGNMENT
# =========================================================
@app.route("/api/assignments/<int:id>", methods=["DELETE"])
def delete_assignment(id):

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            DELETE FROM assignments
            WHERE id=%s
        """, (
            id,
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Assignment deleted"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# MATERIALS
# =========================================================
@app.route("/api/materials", methods=["GET"])
def materials():

    return get_all("materials")


@app.route("/api/materials", methods=["POST"])
def add_material():

    try:

        title = request.form.get("title")
        subject_id = request.form.get("subject_id")
        uploaded_by = request.form.get("uploaded_by")

        file = request.files["file"]

        filename = (
            str(datetime.datetime.now().timestamp())
            + "_"
            + file.filename
        )

        file.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )
        )

        con = database()
        cur = con.cursor()

        cur.execute("""
            INSERT INTO materials(
                subject_id,
                title,
                file_path,
                uploaded_by
            )
            VALUES(%s,%s,%s,%s)
        """, (
            subject_id,
            title,
            filename,
            uploaded_by
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Material uploaded"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# ATTENDANCE
# =========================================================
@app.route("/api/attendance", methods=["GET"])
def get_attendance():

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            SELECT
                attendance.*,
                subjects.subject_name
            FROM attendance
            LEFT JOIN subjects
            ON attendance.subject_id = subjects.id
            ORDER BY attendance.id DESC
        """)

        data = cur.fetchall()

        cur.close()
        con.close()

        return success(data)

    except Exception as e:
        return error(str(e))


@app.route("/api/attendance", methods=["POST"])
def mark_attendance():

    try:

        data = request.json

        student_id = data.get("student_id")
        subject_id = data.get("subject_id")
        status = data.get("status")

        if not student_id:
            return error("student_id missing")

        if not subject_id:
            return error("subject_id missing")

        if not status:
            return error("status missing")

        con = database()
        cur = con.cursor()

        cur.execute("""
            INSERT INTO attendance
            (
                student_id,
                subject_id,
                status
            )
            VALUES(%s,%s,%s)
        """, (
            student_id,
            subject_id,
            status
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Attendance saved"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# NOTIFICATIONS
# =========================================================
@app.route("/api/notifications", methods=["GET"])
def notifications():

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            SELECT *
            FROM notifications
            ORDER BY id DESC
        """)

        data = cur.fetchall()

        cur.close()
        con.close()

        return success(data)

    except Exception as e:
        return error(str(e))

# =========================================================
# GRADES
# =========================================================
@app.route('/api/grades', methods=['GET'])
def get_grades():

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            SELECT *
            FROM grades
            ORDER BY id DESC
        """)

        data = cur.fetchall()

        cur.close()
        con.close()

        return success(
            data,
            "Grades fetched successfully"
        )

    except Exception as e:
        return error(str(e))


@app.route('/api/grades', methods=['POST'])
def save_grade():

    try:

        data = request.json

        student_id = data.get('student_id')
        assignment_id = data.get('assignment_id')
        marks = data.get('marks')
        feedback = data.get('feedback', '')

        if not student_id or not assignment_id or marks is None:
            return error("All fields are required")

        con = database()
        cur = con.cursor()

        cur.execute("""
            INSERT INTO grades
            (
                student_id,
                assignment_id,
                marks,
                feedback
            )
            VALUES(%s,%s,%s,%s)
        """, (
            student_id,
            assignment_id,
            marks,
            feedback
        ))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Grade saved successfully"
        )

    except Exception as e:
        return error(str(e))


@app.route('/api/grades/<int:id>', methods=['DELETE'])
def delete_grade(id):

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            DELETE FROM grades
            WHERE id=%s
        """, (id,))

        con.commit()

        cur.close()
        con.close()

        return success(
            message="Grade deleted successfully"
        )

    except Exception as e:
        return error(str(e))

# =========================================================
# STUDENT ATTENDANCE PERCENTAGE
# =========================================================
@app.route('/api/student-attendance/<int:student_id>', methods=['GET'])
def student_attendance(student_id):

    try:

        con = database()
        cur = con.cursor()

        cur.execute("""
            SELECT COUNT(*) AS total
            FROM attendance
            WHERE student_id=%s
        """, (student_id,))

        total_data = cur.fetchone()
        total = total_data['total']

        cur.execute("""
            SELECT COUNT(*) AS present_total
            FROM attendance
            WHERE student_id=%s
            AND status='Present'
        """, (student_id,))

        present_data = cur.fetchone()
        present = present_data['present_total']

        percentage = 0

        if total > 0:
            percentage = round((present / total) * 100)

        cur.close()
        con.close()

        return success({
            "total": total,
            "present": present,
            "percentage": percentage
        })

    except Exception as e:
        return error(str(e))

# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
