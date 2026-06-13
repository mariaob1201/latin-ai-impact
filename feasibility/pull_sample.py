"""
Pull a real sample of LatAm AI works from OpenAlex to local disk.

Lets us prototype charts, test name-based inference on real author lists,
and inspect data quality before scaling up. Uses cursor pagination.

Output: feasibility/data/sample.jsonl  (one work per line, trimmed fields)
        feasibility/data/sample_authors.csv (flattened author rows)

Run: python3 feasibility/pull_sample.py --target 5000
"""

import argparse
import csv
import json
import os
import urllib.parse

import requests

MAILTO = "moros2@wisc.edu"
BASE = "https://api.openalex.org/works"
LATAM = ["mx", "br", "ar", "co", "cl", "pe", "ve", "ec", "gt", "cu",
         "bo", "do", "hn", "py", "ni", "sv", "cr", "pa", "uy", "pr"]
AI_CONCEPT = "C154945302"
FILTER = (f"concepts.id:{AI_CONCEPT},"
          f"institutions.country_code:{'|'.join(LATAM)},"
          f"from_publication_date:2015-01-01,to_publication_date:2025-12-31")

# Only request the fields we need -> smaller, faster responses.
SELECT = ",".join([
    "id", "doi", "title", "publication_year", "type", "language",
    "cited_by_count", "fwci", "citation_normalized_percentile",
    "authorships", "primary_topic", "topics", "funders",
    "open_access", "countries_distinct_count",
])

OUT_DIR = os.path.join(os.path.dirname(__file__), "data")


def trim(work):
    """Keep a compact, analysis-ready slice of each work."""
    return {
        "id": work["id"].rsplit("/", 1)[-1],
        "doi": work.get("doi"),
        "title": work.get("title"),
        "year": work.get("publication_year"),
        "type": work.get("type"),
        "language": work.get("language"),
        "citations": work.get("cited_by_count"),
        "fwci": work.get("fwci"),
        "topic": (work.get("primary_topic") or {}).get("display_name"),
        "field": ((work.get("primary_topic") or {}).get("field") or {}).get("display_name"),
        "countries_count": work.get("countries_distinct_count"),
        "is_oa": (work.get("open_access") or {}).get("is_oa"),
        "authors": [
            {
                "name": a["author"].get("display_name"),
                "id": (a["author"].get("id") or "").rsplit("/", 1)[-1],
                "countries": a.get("countries", []),
                "institutions": [i.get("display_name") for i in a.get("institutions", [])],
            }
            for a in work.get("authorships", [])
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=5000)
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    works_path = os.path.join(OUT_DIR, "sample.jsonl")
    authors_path = os.path.join(OUT_DIR, "sample_authors.csv")

    cursor = "*"
    pulled = 0
    with open(works_path, "w") as wf, open(authors_path, "w", newline="") as af:
        aw = csv.writer(af)
        aw.writerow(["work_id", "year", "topic", "field", "citations", "fwci",
                     "author_name", "author_id", "author_countries", "author_institutions"])
        while pulled < args.target and cursor:
            params = {
                "filter": FILTER, "select": SELECT, "per_page": 200,
                "cursor": cursor, "mailto": MAILTO,
            }
            url = f"{BASE}?{urllib.parse.urlencode(params)}"
            r = requests.get(url, timeout=90)
            r.raise_for_status()
            payload = r.json()
            results = payload["results"]
            if not results:
                break
            for work in results:
                t = trim(work)
                wf.write(json.dumps(t) + "\n")
                for a in t["authors"]:
                    aw.writerow([t["id"], t["year"], t["topic"], t["field"],
                                 t["citations"], t["fwci"], a["name"], a["id"],
                                 "|".join(a["countries"]),
                                 "|".join(filter(None, a["institutions"]))])
            pulled += len(results)
            cursor = payload["meta"].get("next_cursor")
            print(f"  pulled {pulled:,} / {args.target:,}")

    print(f"\nDone. {pulled:,} works -> {works_path}")
    print(f"Flattened authors -> {authors_path}")


if __name__ == "__main__":
    main()
