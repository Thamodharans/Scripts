import os
from datetime import datetime
from app.google import get_sheets_service
from dotenv import load_dotenv
load_dotenv()


SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = "jobs"   # use your real tab name

def get_enabled_jobs():
    service = get_sheets_service()
    data = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:H"
    ).execute().get("values", [])

    jobs = []
    for i, row in enumerate(data[1:], start=2):
        toggle = row[4] if len(row) > 4 else ""
        status = row[7] if len(row) > 7 else ""

        # only brand new jobs
        if toggle.upper() == "ON" and status in ["", "pending"]:
            jobs.append({
                "row": i,
                "job_id": row[0] if len(row) > 0 else "",
                "query_url": row[1] if len(row) > 1 else "",
                "interval": int(row[2]) if len(row) > 2 else 0,
                "filenames": row[3] if len(row) > 3 else "",
                "keywords": row[5] if len(row) > 5 else "",
                "words_count": int(row[6]) if len(row) > 6 else 0,
            })
    return jobs


def set_job_id(row, job_id):
    service = get_sheets_service()
    body = {"values": [[job_id]]}
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A{row}",
        valueInputOption="RAW",
        body=body
    ).execute()


def update_job(row, status, output=""):
    service = get_sheets_service()
    values = [[status, str(datetime.utcnow()), output]]
    body = {"values": values}
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!H{row}:J{row}",
        valueInputOption="RAW",
        body=body
    ).execute()