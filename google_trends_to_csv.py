"""Google Trends data to CSV in one Actor call.

Usage:
    python google_trends_to_csv.py "bitcoin, ethereum" "solar panels" --geo US --range "today 12-m"

Each argument is one search line: a single term, or up to 5 terms separated by
commas, which Google puts on the same 0-100 scale. One line = one report = one
charge (empty or failed searches are free).

Token: environment variable APIFY_TOKEN, nothing else.
"""
import argparse
import os
import sys

import pandas as pd
from apify_client import ApifyClient

ACTOR = "datafabrik/google-trends-scraper"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("terms", nargs="+", help='search lines, e.g. "bitcoin, ethereum" "solar panels"')
    p.add_argument("--geo", default="", help="ISO country or region code (US, FR, US-CA); empty = worldwide")
    p.add_argument("--range", default="today 12-m", dest="time_range",
                   help="now 1-d, now 7-d, today 1-m, today 3-m, today 12-m, today 5-y, all")
    p.add_argument("--out", default="trends.csv")
    args = p.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("APIFY_TOKEN is not set (Apify Console -> Settings -> API & Integrations)")

    client = ApifyClient(token)
    run = client.actor(ACTOR).call(run_input={
        "searchTerms": args.terms,
        "geo": args.geo,
        "timeRange": args.time_range,
        "dataTypes": ["interestOverTime", "interestByRegion", "relatedQueries"],
        "outputLayout": "rows",  # one row per date, region or related query
    })
    rows = list(client.dataset(run.default_dataset_id).iterate_items())
    if not rows:
        sys.exit("no rows: the terms may have too little search volume for this place and period (not charged)")

    df = pd.DataFrame(rows)
    # recordType is interestOverTime | interestByRegion | relatedQuery; keep the shared columns first
    first = [c for c in ("recordType", "searchTerm", "term", "geo", "timeRange", "date", "value") if c in df.columns]
    df = df[first + [c for c in df.columns if c not in first]]
    df.to_csv(args.out, index=False)
    print(f"{len(df)} rows -> {args.out}")
    print(df["recordType"].value_counts().to_string())


if __name__ == "__main__":
    main()
