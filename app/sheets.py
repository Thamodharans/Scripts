import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_FILE = os.getenv("GOOGLE_CREDS")

def get_sheets_service():
    creds = Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)
    return service
