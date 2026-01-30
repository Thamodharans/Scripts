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
        # new 
        top_df["query"] = top_df["query"].fillna("").astype(str)

    if data["rising"]:
        rising_df = pd.DataFrame(data["rising"])[["query", "extracted_value"]]
        rising_df.columns = ["query", "value"]
        # new
        rising_df["query"] = rising_df["query"].fillna("").astype(str)

    return rising_df, top_df


# =====================================
# STEP 3 — Filters
# =====================================

def keywords_filter(queries, keywords):
    if keywords is None or queries.empty:
        return queries
    pattern = r'\b(?:{})\b'.format('|'.join(map(re.escape, keywords)))
    # return queries[queries['query'].str.contains(pattern, case=False)]
    return queries[queries['query'].fillna("").str.contains(pattern, case=False)]



def words_count_filter(df, words_count):
    if words_count <= 0:
        return df
    # return df[df["query"].str.split().str.len() >= words_count]
    return df[df["query"].fillna("").str.split().str.len() >= words_count]



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
    Produces ALL feed variants:
    regular, keywords, minimum, unique, small
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

    base = filenames[0] if isinstance(filenames, list) else filenames

    VARIANTS = {
        "": lambda df: df,
        "keywords": lambda df: keywords_filter(df, keywords),
        "minimum": lambda df: words_count_filter(df, words_count),
        "unique": lambda df: unique_queries_filter(df),
        "small": lambda df: df
    }

    for name, transform in VARIANTS.items():
        v_rising = transform(rising_df)
        v_top = transform(top_df)

        suffix = f"_{name}" if name else ""

        # XLSX
        rising_xlsx_bytes = build_xlsx(v_rising, job["query_identifier"], timeframe, geo, rising=True)
        top_xlsx_bytes = build_xlsx(v_top, job["query_identifier"], timeframe, geo, rising=False)

        rising_xlsx_path = os.path.join(output_dir, f"{base}-rising{suffix}.xlsx")
        top_xlsx_path = os.path.join(output_dir, f"{base}-top{suffix}.xlsx")

        with open(rising_xlsx_path, "wb") as f:
            f.write(rising_xlsx_bytes)
        with open(top_xlsx_path, "wb") as f:
            f.write(top_xlsx_bytes)

        # RSS
        rising_rss_bytes = build_rss(rising_xlsx_bytes, f"{base}-rising{suffix}.rss")
        top_rss_bytes = build_rss(top_xlsx_bytes, f"{base}-top{suffix}.rss")

        rising_rss_path = os.path.join(output_dir, f"{base}-rising{suffix}.rss")
        top_rss_path = os.path.join(output_dir, f"{base}-top{suffix}.rss")

        with open(rising_rss_path, "wb") as f:
            f.write(rising_rss_bytes)
        with open(top_rss_path, "wb") as f:
            f.write(top_rss_bytes)

        artifacts[f"{name or 'regular'}/rising.xlsx"] = rising_xlsx_path
        artifacts[f"{name or 'regular'}/top.xlsx"] = top_xlsx_path
        artifacts[f"{name or 'regular'}/rising.rss"] = rising_rss_path
        artifacts[f"{name or 'regular'}/top.rss"] = top_rss_path

    return {
        "status": "success",
        "artifacts": artifacts
    }
