from flask import Flask, render_template, request, jsonify
import sqlite3
import json

app = Flask(__name__)


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
    # BASIC INITIAL IMPLEMENTATION
    # Later replace this with your ML model
    # ------------------------------------------------

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
        risk_score += 25
        reasons.append(
            "Recruiter is using a free email service instead of an official company domain."
        )

    # Check suspicious keywords
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

    # Check website
    if not website:
        risk_score += 10
        reasons.append(
            "Company website was not provided."
        )

    # Limit score
    risk_score = min(risk_score, 100)

    # Classification
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