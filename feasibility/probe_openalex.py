"""
Feasibility probe: Latinx / Latin American AI research via OpenAlex.

Goal: prove the data exists and is usable before committing to a methodology.
No API key needed. We use the OpenAlex "polite pool" via a mailto param.

What this checks:
  1. Can we isolate AI works from Latin American institutions? (volume + growth)
  2. Which countries / institutions lead?
  3. What does a single record look like (fields available for later analysis)?
  4. International collaboration signal (co-affiliations outside the region).

Run: python3 feasibility/probe_openalex.py
"""

import json
import sys
import urllib.parse

import requests

MAILTO = "moros2@wisc.edu"
BASE = "https://api.openalex.org/works"

# Latin America + Caribbean (ISO-2). Adjust freely.
LATAM = [
    "mx", "br", "ar", "co", "cl", "pe", "ve", "ec", "gt", "cu",
    "bo", "do", "hn", "py", "ni", "sv", "cr", "pa", "uy", "pr",
]

# OpenAlex concept: "Artificial intelligence" (C154945302).
# Concepts are being phased toward "topics," but the AI concept still works
# well as a wide net and lets us compare across the full time range.
AI_CONCEPT = "C154945302"

COUNTRY_FILTER = "institutions.country_code:" + "|".join(LATAM)
AI_FILTER = f"concepts.id:{AI_CONCEPT}"


def get(params):
    params["mailto"] = MAILTO
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    # ---- 1. Volume + growth: AI works from LatAm institutions by year ----
    section("1. AI works from Latin American institutions, by year")
    data = get({
        "filter": f"{AI_FILTER},{COUNTRY_FILTER},from_publication_date:2010-01-01",
        "group_by": "publication_year",
        "per_page": 200,
    })
    rows = sorted(data["group_by"], key=lambda g: g["key"])
    total = sum(g["count"] for g in rows)
    print(f"Total AI works (LatAm institutions, 2010+): {total:,}")
    for g in rows:
        bar = "#" * (g["count"] // max(1, max(r["count"] for r in rows) // 50))
        print(f"  {g['key']}: {g['count']:>7,}  {bar}")

    # ---- 2. Leading countries ----
    section("2. Top countries by AI output (all years)")
    data = get({
        "filter": f"{AI_FILTER},{COUNTRY_FILTER}",
        "group_by": "institutions.country_code",
        "per_page": 200,
    })
    for g in sorted(data["group_by"], key=lambda g: -g["count"])[:20]:
        print(f"  {g['key_display_name']:<25} {g['count']:>8,}")

    # ---- 3. Leading institutions ----
    section("3. Top institutions by AI output")
    data = get({
        "filter": f"{AI_FILTER},{COUNTRY_FILTER}",
        "group_by": "institutions.id",
        "per_page": 25,
    })
    for g in sorted(data["group_by"], key=lambda g: -g["count"])[:20]:
        print(f"  {g['key_display_name']:<45} {g['count']:>7,}")

    # ---- 4. Total corpus available for deeper analysis ----
    section("4. Total corpus size")
    d = get({"filter": f"{AI_FILTER},{COUNTRY_FILTER}", "per_page": 1})
    print(f"  Total matching works available for deeper analysis: "
          f"{d['meta']['count']:,}")

    # ---- 5. Sample record: what fields can we actually use? ----
    section("5. Sample record structure (fields available per work)")
    d = get({
        "filter": f"{AI_FILTER},{COUNTRY_FILTER}",
        "per_page": 1,
        "sort": "cited_by_count:desc",
    })
    work = d["results"][0]
    print(f"  Title: {work['title']}")
    print(f"  Year:  {work['publication_year']}   Citations: {work['cited_by_count']:,}")
    print(f"  Top-level fields available:")
    for k in sorted(work.keys()):
        print(f"    - {k}")
    print("\n  Authorship sample (first author):")
    if work.get("authorships"):
        a = work["authorships"][0]
        print(f"    name: {a['author'].get('display_name')}")
        print(f"    institutions: "
              f"{[i.get('display_name') for i in a.get('institutions', [])]}")
        print(f"    countries: {a.get('countries')}")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"HTTP error: {e}\nBody: {e.response.text[:500]}", file=sys.stderr)
        sys.exit(1)
