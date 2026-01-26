# test_core.py
from core.engine import run_job
import os
from dotenv import load_dotenv
load_dotenv()



job = {
    "job_id": "TEST-CORE",
    "query_url": "https://trends.google.com/trends/explore?geo=US&q=apple",
    "interval": 10,
    "filenames": "apple",
    "keywords": "iphone",
    "words_count": 3,
    "api_key": os.getenv("SEARCHAPI_KEY"),
    "output_dir": "outputs/TEST-CORE",
    "query_identifier": "TEST-CORE"
}

os.makedirs(job["output_dir"], exist_ok=True)
result = run_job(job)

print(result)
