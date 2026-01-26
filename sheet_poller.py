import time
import uuid
from app.sheets import get_enabled_jobs, set_job_id, update_job
from app.task_queue import queue
from app.jobs import run_job

print("Watching Google Sheet...")
print("=== Watching Google Sheet ===")

while True:
    jobs = get_enabled_jobs()
    print(f"[POLL] Found {len(jobs)} enabled jobs")

    for job in jobs:
        row = job["row"]
        job_id = job["job_id"]

        # generate once
        if not job_id:
            job_id = f"JOB-{str(uuid.uuid4())[:6]}"
            set_job_id(row, job_id)

        update_job(row, "queued")
        print(f"[QUEUE] {job_id}")

        payload = {
            "query_url": job["query_url"],
            "interval": job["interval"],
            "filenames": job["filenames"],
            "keywords": job.get("keywords"),
            "words_count": job.get("words_count", 0),
        }

        queue.enqueue(run_job, job_id, row, payload)

    time.sleep(10)