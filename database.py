import sqlite3

def create_database():
    conn = sqlite3.connect("jobshield.db")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            company_name TEXT,
            recruiter_email TEXT,
            salary TEXT,
            location TEXT,
            website TEXT,
            job_description TEXT,
            prediction TEXT,
            risk_score INTEGER,
            reasons TEXT
        )
    """)

    conn.commit()
    conn.close()

create_database()