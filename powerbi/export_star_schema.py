"""
Export the star schema for Power BI (same model as notebook 02, same numbers as the dashboard).
Run from the project folder:   python powerbi/export_star_schema.py     → powerbi/data/*.csv  (not pushed to GitHub)
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import analytics as A          # noqa: E402
from core import forecast as F           # noqa: E402
from core.build_clean import quality_report  # noqa: E402

OUT = ROOT / 'powerbi' / 'data'
OUT.mkdir(parents=True, exist_ok=True)
c = A.load()


def save(df, name):
    df.to_csv(OUT / f'{name}.csv', index=False, encoding='utf-8-sig')
    print(f'{name:22s} {len(df):>10,} rows')


dates = pd.DataFrame({'date': pd.date_range('2018-10-01', '2027-01-31')})
dates['fy'] = dates.date.dt.year + (dates.date.dt.month >= 10).astype(int)
dates['month_start'] = dates.date.dt.to_period('M').dt.to_timestamp()
dates['month_num'] = dates.date.dt.month
dates['weekday'] = dates.date.dt.day_name()
dates['is_full_fy'] = dates.fy.between(2019, 2026)
save(dates, 'dim_date')
save(c['products'][['product_id', 'product_name_ar', 'category_en', 'audience', 'listed_price_EGP']], 'dim_product')
save(c['skus'][['sku_id', 'product_id', 'size', 'color_ar', 'category_en']], 'dim_sku')
save(c['branches'][['branch_id', 'branch_name_ar', 'governorate_ar', 'city_ar', 'retail_location_type', 'opening_date']], 'dim_branch')
save(c['customers'][['customer_id', 'customer_segment', 'governorate_ar', 'joined_date', 'age_band']], 'dim_customer')
save(c['warehouses'], 'dim_warehouse')
li = c['lines']
li = li.assign(date=li.order_date.dt.normalize())
save(li[['sales_line_id', 'sales_order_id', 'date', 'branch_id', 'customer_id', 'sku_id', 'product_id', 'channel', 'quantity',
         'gross_line_EGP', 'discount_line_EGP', 'net_line_EGP', 'cost_line_EGP', 'margin_EGP', 'has_discount']], 'fact_sales_line')
so = c['orders'].assign(date=lambda d: d.order_date.dt.normalize())
save(so[['sales_order_id', 'date', 'branch_id', 'customer_id', 'channel', 'payment_method', 'items_count', 'gross_EGP', 'discount_EGP',
         'net_before_tax_EGP', 'paid_total_EGP', 'before_opening']], 'fact_order')
save(c['returns'].assign(date=lambda d: d.return_date.dt.normalize())[['return_id', 'sales_line_id', 'date', 'sku_id', 'return_quantity', 'refund_amount_EGP', 'reason']], 'fact_return')
ti = c['transfer_lines'].assign(date=lambda d: d.transfer_date.dt.normalize())
save(ti[['transfer_line_id', 'transfer_id', 'date', 'source_warehouse_id', 'destination_branch_id', 'sku_id', 'quantity_units', 'warehouse_kind']], 'fact_transfer_line')
pl = c['po_lines'].assign(date=lambda d: d.po_date.dt.normalize())
save(pl[['po_line_id', 'po_id', 'date', 'supplier_id', 'sku_id', 'quantity', 'line_cost_EGP']], 'fact_po_line')
save(c['campaigns'].assign(date=lambda d: d.start_date.dt.normalize())[['campaign_id', 'date', 'channel', 'governorate_ar', 'spend_EGP', 'impressions', 'clicks', 'orders_attributed']], 'fact_campaign')
save(c['stock'][['month', 'stock_location_id', 'stock_location_type', 'product_category', 'closing_units', 'closing_stock_value_EGP']].rename(columns={'month': 'date'}), 'fact_stock_month')
fc, hist = F.forecast(c, horizon=4)
plan, alloc = F.plans(c, fc, hist)
save(plan.reset_index().rename(columns={'index': 'category_en'}), 'plan_purchase')
save(alloc, 'plan_allocation')
save(quality_report(c), 'data_quality')
save(A.readiness(), 'readiness_22_ideas')
print('done →', OUT)
