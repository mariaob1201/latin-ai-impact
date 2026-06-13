"""
Prototype visualizations: LatAm AI research over time + topic landscape.

Pulls full-corpus aggregates from OpenAlex (group_by, so these are real totals,
not just the 5k sample) and renders a multi-panel figure.

Panels:
  A. Time series  — AI output by year, broad net vs. narrow (CS-only)
  B. Topic landscape — top AI subfields by volume
  C. Topic momentum — yearly growth of the top subfields (which are rising?)
  D. AI share of CS — narrow AI works as % of broad, over time

Output: feasibility/figures/overview.png
Run: python3 feasibility/visualize.py
"""

import os
import urllib.parse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import requests

MAILTO = "moros2@wisc.edu"
BASE = "https://api.openalex.org/works"
LATAM = ["mx", "br", "ar", "co", "cl", "pe", "ve", "ec", "gt", "cu",
         "bo", "do", "hn", "py", "ni", "sv", "cr", "pa", "uy", "pr"]
C = "concepts.id:C154945302"
L = "institutions.country_code:" + "|".join(LATAM)
CS = "primary_topic.field.id:17"  # Computer Science field
YEARS = list(range(2010, 2026))   # trim partial 2026+
FIG_DIR = os.path.join(os.path.dirname(__file__), "figures")


def get(filter_str, group_by=None):
    params = {"filter": filter_str, "per_page": 200, "mailto": MAILTO}
    if group_by:
        params["group_by"] = group_by
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    return r.json()


def counts_by_year(extra=""):
    f = f"{C},{L}" + (f",{extra}" if extra else "")
    g = get(f, group_by="publication_year")["group_by"]
    d = {int(x["key"]): x["count"] for x in g if x["key"].isdigit()}
    return [d.get(y, 0) for y in YEARS]


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    print("Fetching time series...")
    broad = counts_by_year()
    narrow = counts_by_year(CS)

    print("Fetching top topics...")
    topics = get(f"{C},{L}", group_by="primary_topic.id")["group_by"]
    topics = sorted(topics, key=lambda t: -t["count"])[:8]
    topic_names = [t["key_display_name"] for t in topics]
    topic_counts = [t["count"] for t in topics]

    print("Fetching topic momentum (per-topic by year)...")
    momentum = {}
    for t in topics[:5]:
        tid = t["key"].rsplit("/", 1)[-1]
        g = get(f"{C},{L},primary_topic.id:{tid}", group_by="publication_year")["group_by"]
        d = {int(x["key"]): x["count"] for x in g if x["key"].isdigit()}
        momentum[t["key_display_name"]] = [d.get(y, 0) for y in YEARS]

    # ---------------- render ----------------
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid"
                  in plt.style.available else "default")
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    fig.suptitle("Latin American AI Research — Feasibility Prototype "
                 "(OpenAlex, institutions in LATAM)", fontsize=15, fontweight="bold")

    # A. Time series broad vs narrow
    ax = axes[0, 0]
    ax.plot(YEARS, broad, marker="o", lw=2.2, label="Broad AI net (all fields)")
    ax.plot(YEARS, narrow, marker="s", lw=2.2, label="Narrow AI (Computer Science only)")
    ax.fill_between(YEARS, narrow, alpha=0.12)
    ax.set_title("A. AI output by year", fontweight="bold")
    ax.set_ylabel("works")
    ax.legend()

    # B. Top topics
    ax = axes[0, 1]
    y = range(len(topic_names))
    ax.barh(list(y), topic_counts, color="#4C72B0")
    ax.set_yticks(list(y))
    ax.set_yticklabels([n[:38] for n in topic_names], fontsize=9)
    ax.invert_yaxis()
    ax.set_title("B. Top AI subfields (all years)", fontweight="bold")
    ax.set_xlabel("works")

    # C. Topic momentum
    ax = axes[1, 0]
    for name, series in momentum.items():
        ax.plot(YEARS, series, marker=".", lw=1.8, label=name[:30])
    ax.set_title("C. Topic momentum — top 5 subfields by year", fontweight="bold")
    ax.set_ylabel("works")
    ax.legend(fontsize=8)

    # D. AI-CS share of broad net
    ax = axes[1, 1]
    share = [100 * n / b if b else 0 for n, b in zip(narrow, broad)]
    ax.plot(YEARS, share, marker="D", color="#C44E52", lw=2.2)
    ax.set_title("D. CS-core AI as % of broad AI net", fontweight="bold")
    ax.set_ylabel("percent")
    ax.set_ylim(0, max(share) * 1.3)

    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out = os.path.join(FIG_DIR, "overview.png")
    fig.savefig(out, dpi=140)
    print(f"\nSaved: {out}")
    print(f"  Broad 2010->2025: {broad[0]:,} -> {broad[-1]:,}")
    print(f"  Narrow 2010->2025: {narrow[0]:,} -> {narrow[-1]:,}")


if __name__ == "__main__":
    main()
