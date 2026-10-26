from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    flash,
)

from database import get_connection
from model_service import predict_with_model, load_model_artifact
from werkzeug.security import generate_password_hash, check_password_hash

from io import BytesIO
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "nephrocare-local-development-key-change-before-deployment")


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter email and password.", "warning")
            return redirect(url_for("login"))

        conn = None
        cursor = None

        try:
            conn = get_connection()

            if conn is None:
                raise RuntimeError("Database connection could not be established.")

            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, fullname, email, mobile, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            )

            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["fullname"] = user["fullname"]
                session["email"] = user["email"]
                session["mobile"] = user["mobile"]

                return redirect(url_for("dashboard"))

            flash("Invalid Email or Password.", "danger")
            return redirect(url_for("login"))

        except Exception as e:
            print("Login Error:", e)
            flash("Unable to login. Please check database connection.", "danger")
            return redirect(url_for("login"))

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template("login.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not fullname or not email or not mobile or not password:
            flash("Please fill all fields.", "warning")
            return redirect(url_for("register"))

        if confirm_password and password != confirm_password:
            flash("Passwords do not match.", "warning")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "warning")
            return redirect(url_for("register"))

        conn = None
        cursor = None

        try:
            conn = get_connection()

            if conn is None:
                raise RuntimeError("Database connection could not be established.")

            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,),
            )

            if cursor.fetchone():
                flash("Email already registered.", "warning")
                return redirect(url_for("register"))

            password_hash = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users
                (fullname, email, mobile, password_hash)
                VALUES (%s, %s, %s, %s)
                """,
                (fullname, email, mobile, password_hash),
            )

            conn.commit()

            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            if conn:
                conn.rollback()

            print("Registration Error:", e)
            flash("Registration failed. Please try again.", "danger")
            return redirect(url_for("register"))

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template("register.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:
        conn = get_connection()

        if conn is None:
            raise RuntimeError("Database connection could not be established.")

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM prediction_history
            WHERE user_id = %s
            """,
            (user_id,),
        )

        row = cursor.fetchone()
        total_reports = row["total"] if row else 0

        cursor.execute(
            """
            SELECT *
            FROM prediction_history
            WHERE user_id = %s
            ORDER BY prediction_date DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        )

        latest_prediction = cursor.fetchone()

        cursor.execute(
            """
            SELECT *
            FROM prediction_history
            WHERE user_id = %s
            ORDER BY prediction_date DESC, id DESC
            LIMIT 5
            """,
            (user_id,),
        )

        recent_predictions = cursor.fetchall()

    except Exception as e:
        print("Dashboard Error:", e)
        total_reports = 0
        latest_prediction = None
        recent_predictions = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    kidney_health = "No Data"
    latest_risk = "No Data"
    latest_confidence = "0%"
    latest_prediction_text = "No prediction yet."

    if latest_prediction:
        latest_risk = latest_prediction.get("risk") or "Unknown"
        latest_confidence = latest_prediction.get("confidence") or "0%"
        latest_prediction_text = latest_prediction.get("prediction") or "Unknown"

        if str(latest_risk).lower() == "high":
            kidney_health = "High Risk"
        elif str(latest_risk).lower() == "medium":
            kidney_health = "Moderate"
        else:
            kidney_health = "Healthy"

    return render_template(
        "dashboard.html",
        username=session.get("fullname", "User"),
        total_reports=total_reports,
        kidney_health=kidney_health,
        ai_status="Active",
        latest_prediction=latest_prediction_text,
        latest_risk=latest_risk,
        latest_confidence=latest_confidence,
        recent_predictions=recent_predictions,
    )


# =========================================================
# PREDICTION PAGE
# =========================================================

@app.route("/prediction")
def prediction():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("prediction.html")


# =========================================================
# MAKE PREDICTION
# =========================================================

@app.route("/predict", methods=["POST"])
def predict():

    if "user_id" not in session:
        return redirect(url_for("login"))

    payload = {
        "hemo": request.form.get("hemo", "").strip(),
        "al": request.form.get("al", "").strip(),
        "sg": request.form.get("sg", "").strip(),
        "sc": request.form.get("sc", "").strip(),
        "pcv": request.form.get("pcv", "").strip(),
        "htn": request.form.get("htn", "no").strip().lower(),
    }

    try:
        hemo = float(payload["hemo"])
        al = float(payload["al"])
        sg = float(payload["sg"])
        sc = float(payload["sc"])
        pcv = float(payload["pcv"])
    except (ValueError, TypeError):
        flash("Please enter valid numeric values.", "danger")
        return redirect(url_for("prediction"))

    if payload["htn"] not in {"yes", "no"}:
        flash("Please select a valid hypertension value.", "danger")
        return redirect(url_for("prediction"))

    try:
        artifact = load_model_artifact()
        result = predict_with_model(payload, artifact)

    except Exception as e:
        print("Prediction Error:", e)
        flash("Prediction could not be completed. Please try again.", "danger")
        return redirect(url_for("prediction"))

    conn = None
    cursor = None

    try:
        conn = get_connection()

        if conn is None:
            raise RuntimeError("Database connection could not be established.")

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO prediction_history
            (
                user_id,
                fullname,
                hemo,
                al,
                sg,
                sc,
                pcv,
                htn,
                prediction,
                risk,
                confidence,
                probability
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                session.get("fullname", "User"),
                hemo,
                al,
                sg,
                sc,
                pcv,
                payload["htn"],
                result["prediction"],
                result["risk"],
                result["confidence"],
                float(result["probability"]),
            ),
        )

        conn.commit()
        prediction_id = cursor.lastrowid

    except Exception as e:
        if conn:
            conn.rollback()

        print("Database Error:", e)
        flash("Prediction was generated, but could not be saved to history.", "danger")
        return redirect(url_for("prediction"))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template(
        "result.html",
        prediction_id=prediction_id,
        hemo=payload["hemo"],
        al=payload["al"],
        sg=payload["sg"],
        sc=payload["sc"],
        pcv=payload["pcv"],
        htn=payload["htn"],
        prediction=result["prediction"],
        risk=result["risk"],
        confidence=result["confidence"],
        color=result.get("color", "primary"),
        probability=result["probability"],
        label=result.get("label", result["prediction"]),
    )


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_connection()

        if conn is None:
            raise RuntimeError("Database connection could not be established.")

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM prediction_history
            WHERE user_id = %s
            ORDER BY prediction_date DESC, id DESC
            """,
            (user_id,),
        )
        history_records = cursor.fetchall()

    except Exception as e:
        print("History Error:", e)
        history_records = []
        flash("Unable to load prediction history.", "danger")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template("history.html", history=history_records)


# =========================================================
# VIEW INDIVIDUAL REPORT
# =========================================================

@app.route("/view-report/<int:prediction_id>")
def view_report(prediction_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_connection()

        if conn is None:
            raise RuntimeError("Database connection could not be established.")

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM prediction_history
            WHERE id = %s AND user_id = %s
            """,
            (prediction_id, user_id),
        )
        report = cursor.fetchone()

    except Exception as e:
        print("View Report Error:", e)
        report = None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    if not report:
        return render_template("history.html", history=[]), 404

    risk = str(report.get("risk", "")).strip().lower()

    if risk == "high":
        color = "danger"
    elif risk == "medium":
        color = "warning"
    else:
        color = "success"

    return render_template(
        "result.html",
        prediction_id=report["id"],
        hemo=report["hemo"],
        al=report["al"],
        sg=report["sg"],
        sc=report["sc"],
        pcv=report["pcv"],
        htn=report["htn"],
        prediction=report["prediction"],
        risk=report["risk"],
        confidence=report["confidence"],
        probability=report["probability"],
        color=color,
        label=report["prediction"],
    )


# =========================================================
# DOWNLOAD PDF REPORT
# =========================================================

@app.route("/download-report/<int:prediction_id>")
@app.route("/download_report/<int:prediction_id>")
def download_report(prediction_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_connection()

        if conn is None:
            raise RuntimeError("Database connection could not be established.")

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM prediction_history
            WHERE id = %s AND user_id = %s
            """,
            (prediction_id, user_id),
        )
        report = cursor.fetchone()

    except Exception as e:
        print("Download Report Error:", e)
        report = None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    if not report:
        return "Report not found or you do not have permission to access it.", 404

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 80, "NephroCare AI Report")

    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(
        width / 2,
        height - 105,
        "AI Based Chronic Kidney Disease Prediction",
    )

    pdf.line(60, height - 125, width - 60, height - 125)

    y = height - 165

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(
        70,
        y,
        f"Patient Name: {report.get('fullname') or session.get('fullname', 'User')}",
    )

    y -= 25

    pdf.setFont("Helvetica", 12)
    pdf.drawString(70, y, f"Report ID: {report['id']}")

    y -= 25
    pdf.drawString(70, y, f"Date: {report.get('prediction_date', 'N/A')}")

    y -= 50

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(70, y, "Patient Parameters")

    y -= 30

    pdf.setFont("Helvetica", 12)

    parameters = [
        ("Hemoglobin", report["hemo"]),
        ("Albumin", report["al"]),
        ("Specific Gravity", report["sg"]),
        ("Serum Creatinine", report["sc"]),
        ("Packed Cell Volume", report["pcv"]),
        ("Hypertension", report["htn"]),
    ]

    for name, value in parameters:
        pdf.drawString(80, y, f"{name}: {value}")
        y -= 23

    y -= 20

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(70, y, "Prediction Result")

    y -= 30

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(80, y, f"Prediction: {report['prediction']}")

    y -= 25
    pdf.drawString(80, y, f"Risk Level: {report['risk']}")

    y -= 25
    pdf.drawString(80, y, f"Confidence: {report['confidence']}")

    y -= 25
    pdf.drawString(80, y, f"Probability: {report['probability']}")

    y -= 55
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(70, y, "Important: This report is for educational decision-support use only.")

    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawCentredString(
        width / 2,
        50,
        "NephroCare AI provides prediction support and does not replace professional medical advice.",
    )

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"NephroCare_Report_{prediction_id}.pdf",
        mimetype="application/pdf",
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = None
    cursor = None

    try:
        conn = get_connection()

        if conn is None:
            raise RuntimeError("Database connection could not be established.")

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, fullname, email, mobile
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )
        user = cursor.fetchone()

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM prediction_history
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        total_predictions = row["total"] if row else 0

        cursor.execute(
            """
            SELECT risk
            FROM prediction_history
            WHERE user_id = %s
            ORDER BY prediction_date DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        latest = cursor.fetchone()

    except Exception as e:
        print("Profile Error:", e)

        user = {
            "fullname": session.get("fullname", "User"),
            "email": session.get("email", ""),
            "mobile": session.get("mobile", ""),
        }
        total_predictions = 0
        latest = None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    latest_risk = "No Data"

    if latest:
        latest_risk = latest.get("risk") or "No Data"

    return render_template(
        "profile.html",
        user=user,
        total_predictions=total_predictions,
        total_reports=total_predictions,
        latest_risk=latest_risk,
    )


# =========================================================
# RESULT
# =========================================================

@app.route("/result")
def result():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return redirect(url_for("prediction"))


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
