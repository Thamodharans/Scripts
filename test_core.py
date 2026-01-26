# test_worker.py
from app.jobs import run_job

fake_sheet_data = {
    "query_url": "https://trends.google.com/trends/explore?geo=US&q=google",
    "interval": 10,
    "filenames": "google",
    "keywords": "google,gmail,youtube",
    "words_count": 3
}

run_job("TEST-WORKER", 2, fake_sheet_data)
