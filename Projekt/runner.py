import requests
import time
import os
import psycopg2

def run(username, password, org_id):  
    db_conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "pdfstore"),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASS", "pass"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432)
    )
    cursor = db_conn.cursor()

    LOGIN_URL = "https://apl.gasilec.net/vulkan/proxy/login"
    FETCH_MEMBERS_URL = "https://apl.gasilec.net/vulkan/proxy/Poizvedba/1"
    FETCH_PDF_URL = "https://apl.gasilec.net/vulkan/proxy/Clan/MaticniList"

    session = requests.Session()
    login_data = {
        "username": username,
        "password": password,
        "permanent": "true"
    }
    login_headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-requested-with": "XMLHttpRequest"
    }

    resp = session.post(LOGIN_URL, data=login_data, headers=login_headers)
    if resp.status_code != 200:
        return f"Login failed: {resp.status_code}"

    members_payload = [
        {"poizvedbaKolonaId": 101, "prikaz": True},
        {"poizvedbaKolonaId": 102, "prikaz": True},
        {"poizvedbaKolonaId": 103, "prikaz": True},
        {"poizvedbaKolonaId": 130, "prikaz": False, "poizvedbaOperatorId": 1, "poizvedbaOperatorPogoj1": "1"}
    ]
    members_headers = {
        "Content-Type": "application/*+json",
        "x-requested-with": "XMLHttpRequest"
    }

    resp = session.post(FETCH_MEMBERS_URL, json=members_payload, headers=members_headers)
    members = resp.json().get("value", [])
    if not members:
        return "No members returned."

    count = 0
    for i, member in enumerate(members, 1):
        user_id, name, surname = member["c0"], member["c1"], member["c2"]
        filename = f"{name}_{surname}_{i}.pdf"
        pdf_payload = [{"clanId": user_id, "orgId": org_id}]
        pdf_headers = {
            "Content-Type": "application/*+json",
            "Accept": "application/pdf",
            "x-requested-with": "XMLHttpRequest"
        }

        pdf_resp = session.post(FETCH_PDF_URL, json=pdf_payload, headers=pdf_headers)
        if pdf_resp.status_code == 200:
            cursor.execute(
                "INSERT INTO pdf_files (filename, data) VALUES (%s, %s)",
                (filename, pdf_resp.content)
            )
            count += 1

    db_conn.commit()
    cursor.close()
    db_conn.close()
    print(f"Saved PDF to DB: {filename}")

    return f"{count} PDFs saved to database."