import traceback
from fastapi import FastAPI, HTTPException
from app.sheets import get_sheets_service
import os

from core.engine import run_job

app = FastAPI()
SHEET_ID = os.getenv("SHEET_ID")


BASE_DIR = os.path.abspath("artifacts")
os.makedirs(BASE_DIR, exist_ok=True)

@app.get("/")
def health():
    return {"status": "ok"}





@app.post("/run")
def run(job: dict):
    api_key = os.getenv("SEARCHAPI_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="SEARCHAPI_KEY not configured on server"
        )

    job["api_key"] = api_key
    job["output_dir"] = BASE_DIR  # enforce where files must go

    try:
        result = run_job(job)

        # Hard validation: files must exist
        artifacts = []
        for filename in result["artifacts"].keys():
            path = os.path.join(BASE_DIR, filename)

            if not os.path.exists(path):
                raise HTTPException(
                    status_code=500,
                    detail=f"Artifact not created on disk: {filename}"
                )

            artifacts.append(path)

        return {
            "status": "success",
            "artifacts": artifacts
        }

    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="External API timeout (SearchAPI)"
        )

    except ConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Failed to connect to SearchAPI"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/read")
def read_sheet():
    service = get_sheets_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=SHEET_ID,
        range="Sheet1!A1:Z100"
    ).execute()
    values = result.get("values", [])
    return {"data": values}

@app.post("/write")
def write_sheet():
    service = get_sheets_service()
    sheet = service.spreadsheets()

    body = {
        "values": [["Hello", "From", "FastAPI"]]
    }

    sheet.values().append(
        spreadsheetId=SHEET_ID,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body=body
    ).execute()

    return {"status": "written"}
