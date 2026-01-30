from core.engine import run_job
import os
from dotenv import load_dotenv
load_dotenv()

job = {
    "job_id": "TEST",
    "query_url": "https://trends.google.com/trends/explore?geo=US&q=apple",
    "interval": 5,
    "filenames": "apple",
    "keywords": ["iphone"],
    "words_count": 2,
    "api_key": os.getenv("SEARCHAPI_KEY"),
    "query_identifier": "APPLE",
    "output_dir": "test_outputs"
}

os.makedirs("test_outputs", exist_ok=True)
result = run_job(job)

print("Generated:")
for k,v in result["artifacts"].items():
    print(k, "→", v)
