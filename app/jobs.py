import os
from core.engine import run_job as core_run
from app.uploader import upload_artifacts
from app.registry import register_job

def run_job(job_id, row, sheet_data):
    print(f"[WORKER] START {job_id}")

    try:
        register_job(row, "running")

        output_dir = f"outputs/{job_id}"
        os.makedirs(output_dir, exist_ok=True)

        job_payload = {
            "job_id": job_id,
            "query_url": sheet_data["query_url"],
            "interval": sheet_data["interval"],
            "filenames": sheet_data["filenames"],
            "keywords": sheet_data.get("keywords"),
            "words_count": sheet_data.get("words_count", 0),
            "api_key": os.getenv("SEARCHAPI_KEY"),
            "output_dir": output_dir,
            "query_identifier": job_id
        }

        result = core_run(job_payload)

        links = upload_artifacts(result["artifacts"])

        register_job(row, "done", links)

        print(f"[WORKER] DONE {job_id}")

    except Exception as e:
        register_job(row, "failed", error=str(e))
        raise
