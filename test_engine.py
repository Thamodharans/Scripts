import os
from core.engine import run_job

job = {
    "query_url": "https://trends.google.com/trends/explore?q=bitcoin",
    "interval": 15,
    "filenames": "crypto",
    "query_identifier": "crypto_us",
    "keywords": "ai",
    "words_count": 2,
    "api_key": os.getenv("SEARCHAPI_KEY")
}


result = run_job(job)

print("STATUS:", result["status"])
print("FILES:", result["artifacts"].keys())

for name, data in result["artifacts"].items():
    with open(name, "wb") as f:
        f.write(data)
    print("Wrote", name)



for i in range(15):
    run_job(job)
    print("Run", i, "OK")
