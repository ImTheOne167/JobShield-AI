from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import joblib
from pathlib import Path

app = Flask(__name__)


# =========================================================
# LOAD ML MODEL
# =========================================================

MODEL_DIR = Path(__file__).resolve().parent / "model"

try:
    ml_model = joblib.load(MODEL_DIR / "job_model.pkl")
    ml_vectorizer = joblib.load(MODEL_DIR / "vectorizer.pkl")
    ML_AVAILABLE = True
except Exception:
    ml_model = None
    ml_vectorizer = None
    ML_AVAILABLE = False


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    conn = sqlite3.connect("jobshield.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM job_analysis")
    jobs_analyzed = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM job_analysis
        WHERE prediction = 'Genuine'
    """)
    safe_jobs = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM job_analysis
        WHERE prediction = 'Suspicious'
    """)
    suspicious_jobs = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM job_analysis
        WHERE prediction = 'Fake'
    """)
    fake_jobs = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        jobs_analyzed=jobs_analyzed,
        safe_jobs=safe_jobs,
        suspicious_jobs=suspicious_jobs,
        fake_jobs=fake_jobs
    )


# =========================================================
# ANALYZE PAGE
# =========================================================

@app.route("/analyze-page")
def analyze_page():
    return render_template("analyze.html")


# =========================================================
# MY ANALYSES PAGE
# =========================================================

@app.route("/my-analyses")
def my_analyses():

    conn = sqlite3.connect("jobshield.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            job_title,
            company_name,
            recruiter_email,
            salary,
            location,
            website,
            job_description,
            prediction,
            risk_score,
            reasons
        FROM job_analysis
        ORDER BY rowid DESC
    """)

    analyses = cursor.fetchall()

    conn.close()

    analysis_list = []

    for analysis in analyses:

        item = dict(analysis)

        try:
            item["reasons"] = json.loads(item["reasons"])
        except:
            item["reasons"] = []

        analysis_list.append(item)

    return render_template(
        "my_analyses.html",
        analyses=analysis_list
    )


# =========================================================
# RECRUITER VERIFICATION PAGE
# =========================================================

@app.route("/recruiter-verify")
def recruiter_verify():
    return render_template("recruiter_verify.html")


# =========================================================
# VERIFY RECRUITER
# =========================================================

@app.route("/verify-recruiter", methods=["POST"])
def verify_recruiter():

    data = request.get_json()

    recruiter_name = data.get("recruiter_name", "")
    recruiter_email = data.get("recruiter_email", "")
    company_name = data.get("company_name", "")
    linkedin = data.get("linkedin", "")

    risk_score = 10
    reasons = []

    # Check recruiter email
    free_email_domains = [
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "outlook.com"
    ]

    email_domain = recruiter_email.split("@")[-1].lower()

    if email_domain in free_email_domains:
        risk_score += 40
        reasons.append(
            "Recruiter is using a free email service instead of an official company email."
        )

    # LinkedIn check
    if not linkedin:
        risk_score += 20
        reasons.append(
            "LinkedIn profile was not provided."
        )

    # Company name check
    if not company_name:
        risk_score += 20
        reasons.append(
            "Company name was not provided."
        )

    risk_score = min(risk_score, 100)

    if risk_score >= 60:
        verification = "Suspicious"
    elif risk_score >= 30:
        verification = "Needs Verification"
    else:
        verification = "Likely Genuine"

    if not reasons:
        reasons.append(
            "No major suspicious indicators were detected."
        )

    return jsonify({
        "recruiter_name": recruiter_name,
        "recruiter_email": recruiter_email,
        "company_name": company_name,
        "linkedin": linkedin,
        "verification": verification,
        "risk_score": risk_score,
        "reasons": reasons
    })


# =========================================================
# KNOWLEDGE BASE
# =========================================================

@app.route("/knowledge-base")
def knowledge_base():
    return render_template("knowledge_base.html")


# =========================================================
# ANALYZE JOB PAGE
# IMPORTANT:
# Using analyze.html because analyze_job.html was deleted.
# =========================================================

@app.route("/analyze-job")
def analyze_job_page():
    return render_template("analyze.html")


# =========================================================
# ABOUT PAGE
# =========================================================

@app.route("/about")
def about():
    return render_template("about.html")


# =========================================================
# ANALYZE JOB
# =========================================================

@app.route("/analyze", methods=["POST"])
def analyze_job():

    data = request.get_json()

    job_title = data.get("job_title", "")
    company = data.get("company", "")
    recruiter_email = data.get("recruiter_email", "")
    salary = data.get("salary", "")
    website = data.get("website", "")
    location = data.get("location", "")
    description = data.get("description", "")

    # ------------------------------------------------
    # INITIAL RULE-BASED RISK SCORE
    # ------------------------------------------------

    risk_score = 10
    reasons = []

    # ------------------------------------------------
    # ML MODEL PREDICTION
    # ------------------------------------------------

    ml_risk = 0

    if ML_AVAILABLE:

        # Combine information available from the website
        # into text for the trained TF-IDF model.
        ml_text = " ".join([
            job_title,
            company,
            description,
            location,
            website,
            salary
        ])

        try:
            ml_features = ml_vectorizer.transform([ml_text])

            # Probability of class 1 = fraudulent
            class_probabilities = ml_model.predict_proba(ml_features)[0]

            if 1 in ml_model.classes_:
                fraud_index = list(ml_model.classes_).index(1)
                ml_risk = class_probabilities[fraud_index] * 100

        except Exception:
            ml_risk = 0

    # ------------------------------------------------
    # RULE-BASED CHECK: RECRUITER EMAIL
    # ------------------------------------------------

    free_email_domains = [
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "outlook.com"
    ]

    email_domain = recruiter_email.split("@")[-1].lower()

    if email_domain in free_email_domains:
        risk_score += 25
        reasons.append(
            "Recruiter is using a free email service instead of an official company domain."
        )

    # ------------------------------------------------
    # RULE-BASED CHECK: SUSPICIOUS KEYWORDS
    # ------------------------------------------------

    suspicious_words = [
        "registration fee",
        "security deposit",
        "guaranteed job",
        "guaranteed placement",
        "pay money",
        "immediate joining",
        "earn 1 lakh",
        "no experience required"
    ]

    description_lower = description.lower()

    detected_words = []

    for word in suspicious_words:
        if word in description_lower:
            risk_score += 10
            detected_words.append(word)

    if detected_words:
        reasons.append(
            "Suspicious keywords detected: "
            + ", ".join(detected_words)
        )

    # ------------------------------------------------
    # RULE-BASED CHECK: WEBSITE
    # ------------------------------------------------

    if not website:
        risk_score += 10
        reasons.append(
            "Company website was not provided."
        )

    # Limit rule-based score
    risk_score = min(risk_score, 100)

    # ------------------------------------------------
    # COMBINE RULE-BASED + ML RISK
    # ------------------------------------------------

    if ML_AVAILABLE:
        risk_score = int(
            (risk_score * 0.4) +
            (ml_risk * 0.6)
        )

        # Add ML explanation when the model detects
        # a relatively high fraud probability.
        if ml_risk >= 70:
            reasons.append(
                "The machine learning model estimated a high probability of a fraudulent job posting."
            )
        elif ml_risk >= 40:
            reasons.append(
                "The machine learning model detected some characteristics associated with fraudulent job postings."
            )

    risk_score = min(max(risk_score, 0), 100)

    # ------------------------------------------------
    # FINAL CLASSIFICATION
    # ------------------------------------------------

    if risk_score >= 60:
        prediction = "Fake"
    elif risk_score >= 30:
        prediction = "Suspicious"
    else:
        prediction = "Genuine"

    if not reasons:
        reasons.append(
            "No major suspicious indicators were detected in the submitted information."
        )

    # ------------------------------------------------
    # SAVE ANALYSIS TO DATABASE
    # ------------------------------------------------

    conn = sqlite3.connect("jobshield.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO job_analysis (
            job_title,
            company_name,
            recruiter_email,
            salary,
            location,
            website,
            job_description,
            prediction,
            risk_score,
            reasons
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_title,
        company,
        recruiter_email,
        salary,
        location,
        website,
        description,
        prediction,
        risk_score,
        json.dumps(reasons)
    ))

    conn.commit()
    conn.close()

    # ------------------------------------------------
    # SEND RESULT BACK TO WEBSITE
    # ------------------------------------------------

    return jsonify({
        "job_title": job_title,
        "company": company,
        "prediction": prediction,
        "risk_score": risk_score,
        "reasons": reasons,
        "recruiter_email": recruiter_email,
        "website": website,
        "location": location,
        "salary": salary
    })


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)