import os
from core.engine import run_job as core_run
from app.sheets import update_job

def run_job(job_id, row, sheet_data):
    """
    This is the ADAPTER.
    It does NOT contain business logic.
    It only connects Sheet -> Core -> Sheet.
    """
    print(f"[WORKER] START {job_id}")
    try:
        # 1. Tell human we started
        update_job(row, "running")
        
        # 🔑 This is the missing line
        output_dir = f"outputs/{job_id}"
        os.makedirs(output_dir, exist_ok=True)

        # 2. Build job dict for core engine
        job_payload = {
            "job_id": job_id,
            "query_url": sheet_data["query_url"],
            "interval": sheet_data["interval"],
            "filenames": sheet_data["filenames"],
            "keywords": sheet_data.get("keywords"),
            "words_count": sheet_data.get("words_count", 0),
            "api_key": os.getenv("SEARCHAPI_KEY"),
            "output_dir": f"outputs/{job_id}",
            "query_identifier": job_id
        }

        # 3. Call REAL brain
        result = core_run(job_payload)

        # 4. Report back to sheet
        update_job(
            row,
            "done",
            str(result["artifacts"])
        )
        print(f"[WORKER] DONE {job_id}")

    except Exception as e:
        update_job(row, "failed", str(e))
        print(f"[WORKER] FAIL {job_id}: {e}")
        raise
