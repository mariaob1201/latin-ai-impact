"""
Interactive dashboard: LatAm AI research. Self-contained HTML, no server.

Produces feasibility/figures/dashboard.html with:
  1. Animated choropleth — AI works by country, play across years
  2. Interactive time series — broad vs. narrow (CS-core), hover + zoom
  3. Topic landscape — horizontal bars, hover for exact counts
  4. Country leaderboard race-style bar

Open the HTML in any browser. Charts are zoomable, hoverable, toggleable.

Run: python3 feasibility/dashboard.py
"""

import os
import urllib.parse

import plotly.graph_objects as go
import plotly.express as px
import requests

MAILTO = "moros2@wisc.edu"
BASE = "https://api.openalex.org/works"

# ISO-2 (OpenAlex) -> ISO-3 (Plotly choropleth) for Latin America + Caribbean
ISO = {"mx": "MEX", "br": "BRA", "ar": "ARG", "co": "COL", "cl": "CHL",
       "pe": "PER", "ve": "VEN", "ec": "ECU", "gt": "GTM", "cu": "CUB",
       "bo": "BOL", "do": "DOM", "hn": "HND", "py": "PRY", "ni": "NIC",
       "sv": "SLV", "cr": "CRI", "pa": "PAN", "uy": "URY", "pr": "PRI"}
NAME = {"mx": "Mexico", "br": "Brazil", "ar": "Argentina", "co": "Colombia",
        "cl": "Chile", "pe": "Peru", "ve": "Venezuela", "ec": "Ecuador",
        "gt": "Guatemala", "cu": "Cuba", "bo": "Bolivia", "do": "Dominican Rep.",
        "hn": "Honduras", "py": "Paraguay", "ni": "Nicaragua", "sv": "El Salvador",
        "cr": "Costa Rica", "pa": "Panama", "uy": "Uruguay", "pr": "Puerto Rico"}

C = "concepts.id:C154945302"
L = "institutions.country_code:" + "|".join(ISO)
CS = "primary_topic.field.id:17"
YEARS = list(range(2010, 2026))
FIG_DIR = os.path.join(os.path.dirname(__file__), "figures")

PALETTE = ["#6366F1", "#EC4899", "#14B8A6", "#F59E0B", "#8B5CF6",
           "#EF4444", "#10B981", "#3B82F6"]


def get(filter_str, group_by=None):
    params = {"filter": filter_str, "per_page": 200, "mailto": MAILTO}
    if group_by:
        params["group_by"] = group_by
    r = requests.get(f"{BASE}?{urllib.parse.urlencode(params)}", timeout=90)
    r.raise_for_status()
    return r.json()


def counts_by_year(extra=""):
    f = f"{C},{L}" + (f",{extra}" if extra else "")
    d = {int(x["key"]): x["count"] for x in get(f, "publication_year")["group_by"]
         if x["key"].isdigit()}
    return [d.get(y, 0) for y in YEARS]


# ---------------- fetch ----------------
print("1/4 time series...")
broad = counts_by_year()
narrow = counts_by_year(CS)

def cc(key):
    """group_by key is a URL like .../countries/BR -> 'br'."""
    return key.rsplit("/", 1)[-1].lower()


print("2/4 country totals...")
ctot = {cc(x["key"]): x["count"]
        for x in get(f"{C},{L}", "institutions.country_code")["group_by"]
        if cc(x["key"]) in ISO}

print("3/4 per-country per-year (for animation)...")
by_year_country = {}
for y in YEARS:
    g = get(f"{C},{L},publication_year:{y}", "institutions.country_code")["group_by"]
    by_year_country[y] = {cc(x["key"]): x["count"] for x in g
                          if cc(x["key"]) in ISO}

print("4/4 topics...")
topics = sorted(get(f"{C},{L}", "primary_topic.id")["group_by"],
                key=lambda t: -t["count"])[:10]


# ---------------- build figures ----------------
def fig_timeseries():
    f = go.Figure()
    f.add_trace(go.Scatter(x=YEARS, y=broad, name="Broad AI (all fields)",
                           mode="lines+markers", line=dict(width=3, color=PALETTE[0]),
                           fill="tozeroy", fillcolor="rgba(99,102,241,0.12)"))
    f.add_trace(go.Scatter(x=YEARS, y=narrow, name="Narrow AI (CS core)",
                           mode="lines+markers", line=dict(width=3, color=PALETTE[1])))
    f.update_layout(title="AI research output by year — hover, zoom, toggle series",
                    template="plotly_white", hovermode="x unified",
                    yaxis_title="works", height=420)
    return f


def fig_choropleth():
    iso3 = [ISO[c] for c in ISO]
    frames, slider_steps = [], []
    for y in YEARS:
        z = [by_year_country[y].get(c, 0) for c in ISO]
        text = [NAME[c] for c in ISO]
        frames.append(go.Frame(
            data=[go.Choropleth(locations=iso3, z=z, text=text,
                                 colorscale="Viridis", zmin=0,
                                 zmax=max(ctot.values()) * 0.5,
                                 colorbar_title="works")],
            name=str(y)))
        slider_steps.append(dict(method="animate", label=str(y),
                                 args=[[str(y)], dict(mode="immediate",
                                       frame=dict(duration=300, redraw=True),
                                       transition=dict(duration=150))]))
    first = [by_year_country[YEARS[0]].get(c, 0) for c in ISO]
    f = go.Figure(
        data=[go.Choropleth(locations=iso3, z=first, text=[NAME[c] for c in ISO],
                            colorscale="Viridis", zmin=0,
                            zmax=max(ctot.values()) * 0.5, colorbar_title="works")],
        frames=frames)
    f.update_layout(
        title="AI works by country — press ▶ to animate across years",
        template="plotly_white", height=560,
        geo=dict(scope="world", projection_type="natural earth",
                 lataxis_range=[-58, 35], lonaxis_range=[-120, -30],
                 showcountries=True, countrycolor="white"),
        updatemenus=[dict(type="buttons", showactive=False, x=0.05, y=0.05,
                          buttons=[dict(label="▶ Play", method="animate",
                                        args=[None, dict(frame=dict(duration=600,
                                              redraw=True), fromcurrent=True)]),
                                   dict(label="❚❚ Pause", method="animate",
                                        args=[[None], dict(mode="immediate",
                                              frame=dict(duration=0, redraw=False))])])],
        sliders=[dict(active=0, steps=slider_steps, x=0.1, len=0.85,
                      currentvalue=dict(prefix="Year: "))])
    return f


def fig_topics():
    names = [t["key_display_name"] for t in topics][::-1]
    vals = [t["count"] for t in topics][::-1]
    f = go.Figure(go.Bar(x=vals, y=names, orientation="h",
                         marker=dict(color=vals, colorscale="Tealgrn"),
                         hovertemplate="%{y}<br>%{x:,} works<extra></extra>"))
    f.update_layout(title="Top AI subfields (all years)",
                    template="plotly_white", height=460,
                    margin=dict(l=260))
    return f


def fig_country_bar():
    items = sorted(ctot.items(), key=lambda kv: kv[1])
    names = [NAME[c] for c, _ in items]
    vals = [v for _, v in items]
    f = go.Figure(go.Bar(x=vals, y=names, orientation="h",
                         marker=dict(color=vals, colorscale="Sunsetdark"),
                         hovertemplate="%{y}<br>%{x:,} works<extra></extra>"))
    f.update_layout(title="Country leaderboard (institutions in country, any co-author)",
                    template="plotly_white", height=560, margin=dict(l=120))
    return f


# ---------------- assemble HTML ----------------
os.makedirs(FIG_DIR, exist_ok=True)
out = os.path.join(FIG_DIR, "dashboard.html")
figs = [fig_choropleth(), fig_timeseries(), fig_topics(), fig_country_bar()]

blocks = []
for i, fig in enumerate(figs):
    blocks.append(fig.to_html(full_html=False,
                              include_plotlyjs=("cdn" if i == 0 else False)))

total = sum(ctot.values())
html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Latin American AI Research — Interactive</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; margin:0;
          background:#0f172a; color:#e2e8f0; }}
  header {{ padding:28px 40px; background:linear-gradient(135deg,#6366f1,#ec4899); }}
  h1 {{ margin:0; font-size:26px; color:white; }}
  .sub {{ color:rgba(255,255,255,.85); margin-top:6px; font-size:14px; }}
  .stat {{ display:inline-block; margin:18px 24px 0 0; }}
  .stat b {{ font-size:24px; display:block; color:white; }}
  .stat span {{ font-size:12px; color:rgba(255,255,255,.8); }}
  .card {{ background:white; border-radius:14px; margin:24px 40px;
           padding:8px; box-shadow:0 8px 24px rgba(0,0,0,.3); }}
  footer {{ padding:20px 40px; font-size:12px; color:#94a3b8; }}
</style></head><body>
<header>
  <h1>Latin American AI Research — Interactive Feasibility Prototype</h1>
  <div class="sub">Source: OpenAlex · institutions in 20 LatAm/Caribbean countries ·
   AI concept C154945302 · 2010–2025</div>
  <div>
    <div class="stat"><b>{total:,}</b><span>AI works (all years)</span></div>
    <div class="stat"><b>{broad[-1]:,}</b><span>works in 2025</span></div>
    <div class="stat"><b>{broad[-1]/broad[0]:.1f}×</b><span>growth since 2010</span></div>
    <div class="stat"><b>{100*narrow[-1]/broad[-1]:.0f}%</b><span>CS-core share (2025)</span></div>
  </div>
</header>
<div class="card">{blocks[0]}</div>
<div class="card">{blocks[1]}</div>
<div class="card">{blocks[2]}</div>
<div class="card">{blocks[3]}</div>
<footer>Prototype · counts include any work with ≥1 institution in the region
 (so co-authored international work appears under every contributing country).
 Recent years subject to OpenAlex indexing lag.</footer>
</body></html>"""

with open(out, "w") as f:
    f.write(html)
print(f"\nSaved interactive dashboard: {out}")
print(f"Open with: open {out}")
