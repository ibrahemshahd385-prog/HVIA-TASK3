# Power BI pack – Cottonil (HVIA Task 3)

Same star schema as `notebooks/02_data_model.ipynb`, same numbers as the Streamlit dashboard.

## 1. Export the data (once, ~15 seconds)
```bash
python powerbi/export_star_schema.py      # → powerbi/data/*.csv  (kept out of GitHub by .gitignore)
```

## 2. Load
1. Power BI Desktop → **Home › Manage Parameters › New**: `DataFolder` (Text) = `C:\Users\start\OneDrive\Desktop\HVIA-TASK3\powerbi\data\`
2. **New Source › Blank Query › Advanced Editor** → paste `fnLoad.pq` → rename the query `fnLoad`.
3. For each table: **New Source › Blank Query** → `= fnLoad("fact_sales_line")` → rename to the same name.
   Tables: `dim_date, dim_product, dim_sku, dim_branch, dim_customer, dim_warehouse, fact_sales_line, fact_order, fact_return,
   fact_transfer_line, fact_po_line, fact_campaign, fact_stock_month, plan_purchase, plan_allocation, data_quality, readiness_22_ideas`.

## 3. Relationships (Model view, all one-to-many, single direction)
| From (many) | To (one) |
|---|---|
| fact_sales_line[date], fact_order[date], fact_return[date], fact_transfer_line[date], fact_po_line[date], fact_campaign[date], fact_stock_month[date] | dim_date[date] |
| fact_sales_line[sku_id], fact_return[sku_id], fact_transfer_line[sku_id], fact_po_line[sku_id] | dim_sku[sku_id] |
| fact_sales_line[product_id], dim_sku[product_id] | dim_product[product_id] |
| fact_sales_line[branch_id], fact_order[branch_id], fact_transfer_line[destination_branch_id] | dim_branch[branch_id] |
| fact_sales_line[customer_id], fact_order[customer_id] | dim_customer[customer_id] |
| fact_transfer_line[source_warehouse_id] | dim_warehouse[warehouse_id] |

Mark `dim_date` as the date table. Filter `dim_date[is_full_fy] = TRUE` on yearly pages (FY2019–FY2026).

## 4. Measures and theme
- **Modeling › New table** `_Measures = {0}` → paste the measures from `measures.dax` one by one.
- **View › Themes › Browse** → `Cottonil_theme.json` (three colours: navy = main, light grey = context, teal = the one thing to look at).

## 5. Pages (same story as the Streamlit dashboard)
1. Executive – KPIs, monthly sales vs profit, Real Growth % (pieces) vs Price Growth %.
2. Sales & pricing – category share, seasonality (month_num), discount bands vs margin.
3. Inventory – Sent per Sold by FY, sold % vs sent % by category, Stock Units, plan_allocation.
4. Procurement – Bought per Sold, plan_purchase.
5. Marketing – Spend % of Sales, Claimed per Real Order, Cost per Click by channel.
6. Data trust – readiness_22_ideas and data_quality tables.

> Why Streamlit too? It runs the Python AI forecast and the what-if tools live. Power BI gets the same results as tables (`plan_*`).
