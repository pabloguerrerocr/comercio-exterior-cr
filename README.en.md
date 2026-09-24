# Costa Rica's foreign trade concentrated instead of diversifying

*[Versión en español](README.md)*

**Between 2010 and 2024 Costa Rican exports more than doubled. At the same time
they became far more dependent on a single country and a single product.**

| | 2010 | 2024 |
|---|---:|---:|
| Total exports | $9.04 bn | **$19.9 bn** |
| Share to the United States | 37.4% | **47.9%** |
| Share to the top 4 destinations | 54.0% | **66.7%** |
| Herfindahl index of destinations | 0.160 | **0.248** |

![Export concentration](figuras/01_concentracion.png)

And the growth has a single author: **chapter 90 of the Harmonized System**
—medical, optical and precision instruments— went from $1,100 M to $8,750 M and
by itself explains **70.5%** of the entire export increase over the period.

![What explains the growth](figuras/02_capitulos.png)

One product, to one country. That is the real exposure of Costa Rica's external
sector, and you cannot see it by looking at the total.

![Trade balance](figuras/03_balanza.png)

## Run it

```bash
pip install pandas requests openpyxl
python 01_bajar.py      # UN COMTRADE API (cached)
python 02_analizar.py   # the findings
python 03_excel.py      # the Excel workbook
python 05_powerbi.py    # the Power BI model
```

## What's inside

| File | What it is |
|---|---|
| `01_bajar.py` | ingestion from UN COMTRADE, with caching and retry on HTTP 429 |
| `02_analizar.py` | concentration (Herfindahl and top-N), dependence and contribution by chapter |
| `03_excel.py` | Excel workbook **with live formulas**, not pasted values |
| `04_power_query.m` | the same ingestion in M, to refresh from Excel |
| `05_powerbi.py` | dimensional model and 10 DAX measures for Power BI |
| `06_figuras.py` | the three figures in this README |
| `Comercio_exterior_CR.xlsx` | the Excel deliverable |

## The Excel workbook

The **Resumen** (summary) sheet has no pasted numbers: every cell is a `SUMIFS`
or a `COUNTIFS` over the data sheets. Change the year in the yellow cell and
everything recalculates. That is a model; a report with pasted values is not.

It also includes the concentration series with its chart and the breakdown by
chapter.

## Power Query

`04_power_query.m` goes straight to the API: paste it into Excel's Advanced
Editor and the table refreshes with one button, without running Python again.

## What it took to figure out the API

None of this is clear in the documentation; it came from testing it:

- `partnerCode='all'` returns **HTTP 400**. The parameter has to be **omitted**.
- The `preview` endpoint cuts off at **500 records** per response, so one year and
  flow combination is requested at a time.
- **It does not return names.** `partnerDesc` and `cmdDesc` come back `null`: names
  come from the reference catalogs, which are a different endpoint.
- It rate-limits with **HTTP 429**. The downloader backs off progressively and
  caches every response, so the second run requests nothing.

## Methodological note

Partner code `0` is "the world": it is the total, not a partner. Regional
aggregates (`es_agregado`) are not countries either. Adding them alongside
countries would count trade twice, so they are excluded from every concentration
calculation and from the Power BI model.

## Data

UN COMTRADE, public and keyless. Costa Rica is reporter 188. 2010-2024.
