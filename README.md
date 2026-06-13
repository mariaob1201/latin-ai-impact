# Latin American / Latinx AI Research Impact — Feasibility Memo

**Status:** Feasibility phase complete. Data confirmed available, usable, and rich.
**Last updated:** 2026-06-13

## Question

Can we analyze and visualize Latinx / Latin American contributions to AI research
and their impact, using only public data? **Yes.**

## Definition (multi-lens, by design)

"Latinx contribution to AI" has no clean field in any dataset, so we triangulate:

1. **Geography** — work affiliated with Latin American institutions. *Cleanest, most
   defensible.* Captures region, not ethnicity.
2. **Hispanic-Serving Institutions (HSIs)** — US output from federally designated HSIs.
   US-pipeline proxy. *(source: ED HSI list — not yet pulled)*
3. **Name-based inference** — probabilistic ethnicity from author names. *Powerful but
   fraught; always disclosed as a limitation, never ground truth.* Author names + IDs
   are present in the sample, so this is testable.
4. **Self-ID / degrees** — US Census/IPEDS Hispanic-Latino CS-degree completions.
   Accurate, coarse. *(source: IPEDS — not yet pulled)*
5. **US ↔ LatAm linked work (both directions)** — works where a US and a LatAm
   institution co-appear: US research drawing on/collaborating with LatAm science *and*
   LatAm research drawing on/collaborating with US science (collaboration / diaspora
   signal, bidirectional). Falls out of the geography pull for free.

## Primary data source: OpenAlex

Free, no API key, ~250M works. We use the "polite pool" (`mailto` param).

### What we found (probe + 5k-work sample, 2015–2025)

| Finding | Value |
|---|---|
| AI works tied to LatAm institutions (total) | **360,840** |
| Since 2010 | ~292,000 |
| Growth 2010→2025 | 9,200 → 23,500/yr (~2.5×) |
| Country leaders | Brazil (169K), Mexico (77K), **US (40K, collab signal)**, Colombia, Chile, Argentina |
| Top institution | Universidade de São Paulo (21,593) |
| FWCI present | **100%** of sampled works |
| Author country coverage | **96%** of author rows |

### Per-record fields available (analysis-ready)

- `authorships` → author name + `id` + `countries` + `institutions` (powers geography **and** name-inference lenses)
- `fwci`, `citation_normalized_percentile` → **citation-equity** questions, pre-normalized by field/year
- `funders` → funding flows
- `topics` / `concepts` / `sustainable_development_goals` → subfield + societal-impact framing
- `referenced_works` / `related_works` → influence & collaboration networks

## Limitations found (must carry into any analysis)

- **The AI concept is a wide net.** In the sample, primary fields are CS (1,180) and
  Engineering (1,080) but also Medicine (515), Env. Science, Agriculture, Business. The
  top-cited sampled work was a *physics/medicine* paper (Geant4). For a *narrow* "AI
  research" definition, filter to `field = Computer Science` or specific AI topics.
- **LatAm institution ≠ Latinx researcher.** Geography lens is solid; ethnicity needs
  name inference layered on, with caveats stated.
- **Partial recent years.** 2026–2027 records exist but are incomplete/erroneous — trim.

## Research questions this can credibly answer

- Growth of LatAm AI output vs. global trend; by country and subfield.
- Citation equity: FWCI/percentile of LatAm work vs. global mean.
- Collaboration networks: domestic vs. international, top partner countries (US, Spain, France).
- Topic focus: do LatAm researchers concentrate on distinct problems (Spanish/Portuguese
  NLP, agriculture, public health)?
- US pipeline (with IPEDS/HSI): Hispanic/Latino CS-degree trends; HSI research contribution.

## Prototype visualizations (`feasibility/figures/overview.png`)

Four panels, full-corpus aggregates (not just the sample):

- **A. Output by year** — broad AI tripled (9.2K→23.5K); narrow CS-core AI grew slower (2.7K→5.7K).
- **B. Top subfields** — neural networks, control systems, optimization dominate
  (engineering-inflected AI profile).
- **C. Topic momentum** — "Neural Networks and Applications" is the breakout subfield,
  rising sharply after ~2017 (deep-learning wave reaching the region).
- **D. CS-core as % of broad AI** — **declined ~30%→24%**: a real, defensible thesis that
  LatAm AI is increasingly *applied* (medicine, agriculture, engineering), not just CS.

Caveat: the 2024 dip is OpenAlex indexing lag (recent years backfill), not a real decline.

## Repo layout

```
feasibility/
  probe_openalex.py     # aggregate probe — counts, growth, leaders, record shape
  pull_sample.py        # pulls a real sample to disk (cursor-paginated)
  visualize.py          # multi-panel time-series + topic figure
  data/                 # (gitignored) sample.jsonl + sample_authors.csv
  figures/
    overview.png        # prototype dashboard
```

## Next steps (not yet done)

1. Add IPEDS Hispanic/Latino CS-degree pull (US self-ID lens).
2. Add ED HSI institution list (HSI lens).
3. Prototype name-based inference on `sample_authors.csv` (test, measure, caveat).
4. First visualizations: growth curve, country choropleth, collaboration network.
5. Decide narrow vs. broad "AI" definition per question (CS-field filter vs. wide net).
