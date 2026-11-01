# Cottonil – BI & AI for better decisions 📊 (HVIA Task 3)

HVIA Task 3 · Business Intelligence & AI Applications · by **Shahd Ibrahim**

> **The question:** Cottonil's sales grow every year – is it real growth, and where is profit leaking?
> **السؤال:** مبيعات قطنيل بتزيد كل سنة – هل ده نمو حقيقي، والربح بيضيع فين؟

## The answer in one line
**4 decisions could add ~18.9M EGP of gross profit a year (+17%)** – from 110.9M to 129.8M (FY2026) – and every number has its
assumption written next to it, so the manager can change it in the dashboard and the website.
**Cottonil does not need to sell more – it needs its decisions (discounts, marketing, buying, distribution) to follow real demand.**

## What I found
| Area | Finding |
|---|---|
| Growth | Sales ×15 since FY2019 but pieces only ×2.5 – prices did the rest; real growth slowed to **+9.3%** in FY2026 |
| Discounts | **54%** of lines get a random discount; they sell 2.99 pieces vs 2.98 → **13.0M EGP** given away in FY2026 |
| Marketing | A fixed ~29M budget; campaigns claim **×45** the real orders; spend has no link with orders by governorate |
| Distribution | Branches receive a fixed ~1.6M pieces a year (×2.4 of sales); socks are **55%** of shipments vs 27% of sales |
| Purchasing | ~42M pieces bought every year for ~0.6M sold, the same for every SKU (correlation 0.01) |
| Loss / stock | **9.3M pieces** sent to branches are neither sold nor on the shelf → stock count first |
| Customers | 19% of orders have no customer (even online); a "loyal" customer shops in 7 branches |
| Data trust | Of the **22 app ideas** proposed by HVIA, 6 are fully supported by the data; 9 fields are filled at random |

## The dataset split (same method as the Sharnoubi project)
23 tables + 22 HVIA app ideas → **business cards**: one question → one notebook → one dashboard page.

| Card | Question | Notebook | Dashboard page |
|---|---|---|---|
| 01 Sales & growth | Real growth or prices? | `04_card01_sales_growth` | Executive · Sales & Pricing |
| 02 Discounts | Do discounts sell more pieces? | `05_card02_discounts` | Sales & Pricing |
| 03 Customers | Who comes back – can we trust the ID? | `06_card03_customers` + `13_ai_churn_test` | Customer 360 |
| 04 Branches & channels | Which branch / channel creates value? | `07_card04_branches_channels` | Branches & Channels |
| 05 Inventory & allocation | Do branches get what they sell? | `08_card05_inventory_allocation` | Smart Inventory |
| 06 Purchasing & imports | Do we buy what we sell? | `09_card06_purchasing` | Procurement |
| 07 Marketing | Does the money bring real orders? | `10_card07_marketing` | Marketing ROI |
| 08 People & costs | Can we manage staff and costs with this data? | `11_card08_people_costs` | People & Costs |
| AI | How much will we sell next quarter? | `12_ai_demand_forecast` | Smart Inventory |
| 09 Story & plan | How much profit, in EGP? | `14_card09_story_action_plan` | Executive |
| + Data Trust Center | Which of the 22 ideas can the data support? | `15_app_data_trust` | Data Trust Center |

Before the cards: `01_data_understanding` (every table), `02_data_model` (24 relationships, 0 orphans, star schema), `03_data_cleaning` (28-issue quality report).

## What I built
1. **15 notebooks** with real outputs and 24 charts (`outputs/charts`).
2. **Streamlit dashboard** (English / العربية) – 9 pages, AI forecast trained live, what-if sliders, CSV downloads.
3. **Cottonil Decision Hub** – a manager website with login: decisions of the month, 10 problems with evidence → solution → owner → EGP,
   5 working solution tools (purchase plan, branch allocation, discount guardrail, marketing budget + holdout test, free-shipping rule),
   an action tracker, a data-gap tracker and an assistant that answers from the data.
4. **Power BI pack** – star-schema export, loader, 33 DAX measures, theme and a page plan (`powerbi/`).

## Honest by design
- The AI demand forecast was tested on 6 months it never saw: error **8.8% vs 11.2%** for "same month last year" (**21% more accurate**).
- A churn model scored **AUC 0.50** (a coin flip) → **rejected**; a test-vs-control win-back list replaces it.
- Branches sell within ±5% of each other → no branch ranking or site selection from this data.
- Purchase and stock numbers are not realistic in absolute terms → used for comparisons, and listed as questions for the company.

## Run it (Windows)
```bash
pip install -r requirements.txt
python core/build_clean.py          # once: builds clean/cottonil_clean.pkl from Cottonil_project/ (~20 s)
```
- Dashboard: double-click **`run_dashboard.bat`** (or `cd dashboard` → `streamlit run app.py`) → http://localhost:8501
- Website: double-click **`run_website.bat`** (or `python website/server.py`) → http://localhost:8050
  First sign-in: `ceo` / `Cottonil@2026` (also `supply`, `marketing`, `finance`) – you are asked to change the password.

## Project structure
```
core/          build_clean.py (cleaning + quality report) · analytics.py (every number) · forecast.py (AI forecast + plans)
notebooks/     01 → 15, one per step / card
outputs/       charts/*.png · data_quality_report.csv · readiness_22_ideas.csv · purchase & allocation plans
dashboard/     Streamlit: app.py (menu) · utils.py (cached numbers + style) · views/ (one file per page)
website/       Flask: server.py (API + login) · knowledge.py (problems, decisions, assistant) · static/ (the site)
powerbi/       export_star_schema.py · fnLoad.pq · measures.dax · theme · guide
```

## Data note
The raw data (24 CSV files, 2.9M rows, Oct 2018 – Oct 2026) is a **training dataset from HVIA** and is **not** in this repo
(company data; one file is > 100 MB). Put it in `Cottonil_project/COTTONIL/COTTONIL_Data/` next to this file.
`clean/`, `powerbi/data/` and `website/data/` (users, saved actions) are generated locally and never pushed.
