import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

CREDS_FILE = os.getenv("GOOGLE_CREDS_FILE")

if not CREDS_FILE:
    raise RuntimeError("GOOGLE_CREDS_FILE not set")

creds = Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=SCOPES
)

def get_sheets_service():
    return build("sheets", "v4", credentials=creds)

def get_drive_service():
    return build("drive", "v3", credentials=creds)
