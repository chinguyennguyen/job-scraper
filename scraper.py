# scraper.py
import pandas as pd
from jobspy import scrape_jobs
from config import cfg
from filter import score_job

SEARCH_TERMS = cfg["search_terms"]
HOURS_OLD    = cfg["hours_old"]
COLS_TO_SAVE = ["title", "company", "location", "score", "search_term", "job_url", "date_posted"]


def scrape_city(city_config):
    location       = city_config["location"]
    country_indeed = city_config["country_indeed"]
    filter_german  = city_config["filter_german"]
    filter_swedish = city_config["filter_swedish"]

    print(f"\n{'='*60}")
    print(f"  Scraping: {location}")
    print(f"{'='*60}")

    all_jobs = []

    for term in SEARCH_TERMS:
        print(f"\n  Searching: '{term}'...")
        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed"],
                search_term=term,
                location=location,
                results_wanted=30,
                hours_old=HOURS_OLD,
                country_indeed=country_indeed,
                linkedin_fetch_description=True,
                verbose=0,
            )
            jobs["search_term"] = term
            all_jobs.append(jobs)
            print(f"    → {len(jobs)} results")
        except Exception as e:
            print(f"    ✗ Failed for '{term}': {e}")

    if not all_jobs:
        print(f"  No results for {location}. Skipping.")
        return None

    df = pd.concat(all_jobs, ignore_index=True)

    # deduplicate
    if "job_url" in df.columns:
        df = df.drop_duplicates(subset=["job_url"])
    df = df.drop_duplicates(subset=["title", "company"])
    print(f"\n  Total unique jobs before filtering: {len(df)}")

    # score and filter
    df["score"] = df.apply(
        lambda row: score_job(row, filter_german, filter_swedish), axis=1
    )
    df = df[df["score"] >= 0].sort_values("score", ascending=False)
    print(f"  Relevant jobs after filtering: {len(df)}")

    # keep only useful columns
    cols_available = [c for c in COLS_TO_SAVE if c in df.columns]
    df_out = df[cols_available].copy()
    df_out["city"]       = location
    df_out["date_found"] = pd.Timestamp.now().strftime("%Y-%m-%d")

    # print top results
    print(f"\n  Top results for {location}:")
    print(f"  {'SCORE':<7} {'COMPANY':<25} TITLE")
    print(f"  {'-'*70}")
    for _, job in df_out.head(10).iterrows():
        company = str(job.get("company", ""))[:24]
        title   = str(job.get("title",   ""))[:45]
        score   = job.get("score", 0)
        star    = "⭐" if any(c in str(job.get("company", "")).lower() for c in cfg["scoring"]["priority_companies"]) else "  "
        print(f"  {star}[{score}]  {company:<25} {title}")

    return df_out