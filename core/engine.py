"""
Cloud-safe core engine.

This file contains the PURE business logic.
No FastAPI.
No Celery.
No Redis.
No disk.
No infinite loops.

This function runs ONCE and exits.
"""

import io
import os
import re
import datetime
import pandas as pd
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows

from rss_generator import generate_rss
from trends_fetcher import TrendsFetcher


# =========================
# CONSTANTS (frozen rules)
# =========================

TIMEFRAME_DEFAULT = "today 12-m"
INTERVAL_DEFAULT = 15
INTERVAL_MINIMUM = 1
BREAKOUT_THRESHOLD = 5000

RISING_QUERIES_HEADERS = [
    "dmcla", "Rank", "dmclb", "Rising Related Queries", "dmclc",
    "URL", "dmcld", "Search URL", "dmcle",
    "Increase in Search Frequency %", "dmclf",
    "Breakout", "dmclg",
    "Date Added", "dmclh",
    "Input Query", "dmcli"
]

TOP_QUERIES_HEADERS = [
    "dmcla", "Rank", "dmclb", "Top Related Queries", "dmclc",
    "URL", "dmcld", "Search URL", "dmcle",
    "Popularity %", "dmclf",
    "Date Added", "dmclg",
    "Input Query", "dmclh"
]


# =====================================================
# STEP 1 — Parse one Google Sheet row into job fields
# =====================================================

def process_input_data(query_link, interval, filenames, keywords, words_count):
    import urllib.parse as urlparse

    params = urlparse.parse_qs(urlparse.urlparse(query_link).query)

    query = params["q"][0].split(",")[0]
    category = int(params.get("cat", [0])[0])
    timezone = int(params.get("tz", [420])[0])
    timeframe = params.get("date", [TIMEFRAME_DEFAULT])[0]
    geo = params.get("geo", [""])[0]
    gprop = params.get("gprop", [""])[0]

    if not isinstance(interval, (int, float)):
        interval = INTERVAL_DEFAULT
    elif interval < INTERVAL_MINIMUM:
        interval = INTERVAL_MINIMUM

    if not isinstance(words_count, int) or words_count < 0:
        words_count = 0

    filenames = re.sub(r"\s+", "", filenames).strip(",").split(",")

    if keywords:
        keywords = re.sub(r"\s+", "", str(keywords)).strip(",").split(",")

    return query, category, timeframe, timezone, geo, gprop, interval, filenames, keywords, words_count


# =====================================
# STEP 2 — Fetch data from Google Trends
# =====================================

def get_related_queries(trends_fetcher, query, category, timeframe, timezone, region, search_type):
    data = trends_fetcher.fetch_related_queries(
        q=query,
        cat=category,
        timeframe=timeframe,
        tz=timezone,
        geo=region,
        gprop=search_type
    )

    top_df = pd.DataFrame()
    rising_df = pd.DataFrame()

    if data["top"]:
        top_df = pd.DataFrame(data["top"])[["query", "extracted_value"]]
        top_df.columns = ["query", "value"]

    if data["rising"]:
        rising_df = pd.DataFrame(data["rising"])[["query", "extracted_value"]]
        rising_df.columns = ["query", "value"]

    return rising_df, top_df


# =====================================
# STEP 3 — Filters
# =====================================

def keywords_filter(df, keywords):
    if not keywords or df.empty:
        return df
    pattern = r"\b(?:{})\b".format("|".join(map(re.escape, keywords)))
    return df[df["query"].str.contains(pattern, case=False)]


def unique_queries_filter(df):
    seen = set()
    drop = []

    for i, row in df.iterrows():
        words = row["query"].lower().split()
        if all(w in seen for w in words):
            drop.append(i)
        else:
            seen.update(words)

    return df.drop(drop)


# =====================================
# STEP 4 — Build XLSX in memory
# =====================================

def build_xlsx(df, query_identifier, timeframe, region, rising=True):
    buffer = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active

    headers = RISING_QUERIES_HEADERS if rising else TOP_QUERIES_HEADERS
    ws.append(headers)

    row_index = 1

    for _, row in df.iterrows():
        trends_url = f"https://trends.google.com/trends/explore?q={row['query']}&date={timeframe}&geo={region}"
        search_url = f"https://www.google.com/search?q={row['query']}"
        timestamp = datetime.datetime.now().strftime("%I:%M:%S %p %d-%m-%Y")

        if rising:
            breakout = "Breakout" if row["value"] >= BREAKOUT_THRESHOLD else row["value"]
            record = [
                "", row_index, "", row["query"], "",
                trends_url, "", search_url, "",
                row["value"], "", breakout, "",
                timestamp, "", query_identifier, ""
            ]
        else:
            record = [
                "", row_index, "", row["query"], "",
                trends_url, "", search_url, "",
                row["value"], "", timestamp, "",
                query_identifier, ""
            ]

        ws.append(record)
        row_index += 1

    wb.save(buffer)
    return buffer.getvalue()


# =====================================
# STEP 5 — Build RSS in memory
# =====================================

def build_rss(xlsx_bytes, filename):
    buffer = io.BytesIO()
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
    ws = wb.active
    generate_rss(ws, filename, buffer, len(RISING_QUERIES_HEADERS))
    return buffer.getvalue()


# ==========================================================
# MAIN ENGINE — THIS IS WHAT FASTAPI / CELERY WILL CALL
# ==========================================================


def run_job(job: dict) -> dict:
    """
    Runs ONE job.
    Always writes artifacts to disk.
    """
    print("WORKER STARTED FOR:", job["job_id"])
    output_dir = job["output_dir"]
    artifacts = {}

    # 1. Parse input
    query, category, timeframe, tz, geo, gprop, interval, filenames, keywords, words_count = \
        process_input_data(
            job["query_url"],
            job["interval"],
            job["filenames"],
            job.get("keywords"),
            job.get("words_count", 0)
        )

    # 2. Fetch data
    trends_fetcher = TrendsFetcher(api_key=job["api_key"])
    rising_df, top_df = get_related_queries(
        trends_fetcher,
        query,
        category,
        timeframe,
        tz,
        geo,
        gprop
    )

    # 3. Generate XLSX (bytes)
    rising_xlsx_bytes = build_xlsx(rising_df, job["query_identifier"], timeframe, geo, rising=True)
    top_xlsx_bytes = build_xlsx(top_df, job["query_identifier"], timeframe, geo, rising=False)

    # 4. Write XLSX to disk
    base = job["filenames"]
    rising_xlsx_path = os.path.join(output_dir,  f"{base}-rising.xlsx")
    with open(rising_xlsx_path, "wb") as f:
        f.write(rising_xlsx_bytes)

    top_xlsx_path = os.path.join(output_dir,  f"{base}-top.xlsx")
    with open(top_xlsx_path, "wb") as f:
        f.write(top_xlsx_bytes)

    # 5. Generate RSS (bytes)
    rising_rss_bytes = build_rss(rising_xlsx_bytes,  f"{base}-rising.rss")
    top_rss_bytes = build_rss(top_xlsx_bytes,  f"{base}-top.rss")

    # 6. Write RSS to disk
    rising_rss_path = os.path.join(output_dir, f"{base}-rising.rss")
    with open(rising_rss_path, "wb") as f:
        f.write(rising_rss_bytes)

    top_rss_path = os.path.join(output_dir, f"{base}-top.rss")
    with open(top_rss_path, "wb") as f:
        f.write(top_rss_bytes)

    # 7. Return real paths
    artifacts["rising.xlsx"] = rising_xlsx_path
    artifacts["top.xlsx"] = top_xlsx_path
    artifacts["rising.rss"] = rising_rss_path
    artifacts["top.rss"] = top_rss_path

    return {
        "status": "success",
        "artifacts": artifacts
    }
