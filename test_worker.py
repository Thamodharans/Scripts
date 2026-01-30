# test_worker.py
from core.engine import run_job
import os
import time
from dotenv import load_dotenv

load_dotenv()

BASE_JOB = {
    "job_id": "TEST-CORE",
    "query_url": "https://trends.google.com/trends/explore?geo=US&q=apple",
    "interval": 5,
    "filenames": "apple",
    "keywords": "iphone",
    "words_count": 3,
    "api_key": os.getenv("SEARCHAPI_KEY"),
    "query_identifier": "TEST-CORE"
}

TOTAL_RUNS = 12
INTERVAL = 5 * 60  # 5 minutes

overall_start = time.time()

for i in range(TOTAL_RUNS):
    run_id = i + 1
    output_dir = f"outputs/TEST-CORE/run-{run_id}"
    os.makedirs(output_dir, exist_ok=True)

    job = {
        **BASE_JOB,
        "output_dir": output_dir,
    }

    print(f"\n=== RUN {run_id}/{TOTAL_RUNS} ===")
    print(f"Output folder: {output_dir}")

    start = time.time()
    result = run_job(job)
    end = time.time()

    exec_time = end - start
    print(f"Execution time: {exec_time:.2f} seconds")
    print("Artifacts:", result["artifacts"])

    if i < TOTAL_RUNS - 1:
        sleep_time = max(0, INTERVAL - exec_time)
        print(f"Sleeping for {sleep_time/60:.2f} minutes...")
        time.sleep(sleep_time)

overall_end = time.time()
total_time = overall_end - overall_start

print("\n=== SUMMARY ===")
print(f"Total time: {total_time/60:.2f} minutes")
print(f"Average execution time: {(total_time / TOTAL_RUNS):.2f} seconds")
