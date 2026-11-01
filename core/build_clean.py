"""
Step 3 — cleaning: read the 24 raw CSV files + the public catalog, fix types, add the columns
every analysis needs, and save ONE clean file (clean/cottonil_clean.pkl).

Rule we follow (same as Sharnoubi): we do NOT delete strange rows. We FLAG them, and we write every
issue in outputs/data_quality_report.csv with its evidence, severity and what we do about it.

Run:  python core/build_clean.py  [--raw "path/to/02_TABLES"]
"""
import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / 'Cottonil_project' / 'COTTONIL' / 'COTTONIL_Data' / '02_TABLES'

CHANNEL = {'Retail POS': 'Store', 'E-commerce': 'Online', 'Wholesale / reseller': 'Wholesale'}


def fiscal_year(d):
    """Fiscal year Oct–Sep (same as Sharnoubi): Oct 2025 → FY2026."""
    return d.dt.year + (d.dt.month >= 10).astype(int)


def load_raw(raw_dir):
    raw_dir = Path(raw_dir)
    t = {f[:-4]: pd.read_csv(raw_dir / f, low_memory=False) for f in sorted(os.listdir(raw_dir)) if f.endswith('.csv')}
    cat = raw_dir.parent / '01_CATALOG' / 'PRODUCT_CATALOG_PUBLIC_REFERENCE.csv'
    if cat.exists():
        t['public_catalog'] = pd.read_csv(cat)
    return t


def clean(t):
    c = {}
    # ---------------------------------------------------------------- dimensions
    br = t['branches'].copy()
    br['opening_date'] = pd.to_datetime(br['opening_date'], format='%m/%d/%Y')
    c['branches'] = br

    cu = t['customers'].copy()
    cu['joined_date'] = pd.to_datetime(cu['joined_date'], format='%m/%d/%Y')
    c['customers'] = cu

    pr = t['products_catalog'].copy()
    c['products'] = pr
    sku = t['sku_variants'].merge(pr[['product_id', 'category_en', 'audience', 'listed_price_EGP']], on='product_id', how='left')
    c['skus'] = sku

    em = t['employees'].copy()
    em['hire_date'] = pd.to_datetime(em['hire_date'], format='%m/%d/%Y')
    c['employees'] = em
    for k in ['warehouses', 'suppliers', 'factories', 'import_partners', 'data_dictionary']:
        c[k] = t[k].copy()
    if 'public_catalog' in t:
        pc = t['public_catalog'].copy()
        pc['in_sales_data'] = pc['product_id'].isin(pr['product_id'])
        c['public_catalog'] = pc

    # ---------------------------------------------------------------- sales
    so = t['sales_orders'].copy()
    so['order_date'] = pd.to_datetime(so['order_date'])
    so['channel'] = so['sales_channel'].map(CHANNEL)
    so['fy'] = fiscal_year(so['order_date'])
    so['month'] = so['order_date'].dt.to_period('M').dt.to_timestamp()
    so['weekday'] = so['order_date'].dt.day_name()
    so = so.merge(br[['branch_id', 'opening_date']], on='branch_id', how='left')
    so['before_opening'] = so['order_date'] < so['opening_date']
    so = so.drop(columns='opening_date')
    c['orders'] = so

    li = t['sales_order_items'].copy()
    li['order_date'] = pd.to_datetime(li['order_date'])
    li = li.merge(so[['sales_order_id', 'channel', 'customer_id', 'fy', 'month']], on='sales_order_id', how='left')
    li = li.merge(sku[['sku_id', 'size', 'color_ar', 'category_en', 'audience']], on='sku_id', how='left')
    li['cost_line_EGP'] = li['unit_cost_EGP'] * li['quantity']
    li['has_discount'] = li['discount_line_EGP'] > 0
    li['discount_pct'] = np.where(li['gross_line_EGP'] > 0, li['discount_line_EGP'] / li['gross_line_EGP'], 0)
    c['lines'] = li

    pay = t['sales_payments'].copy()
    pay['payment_date'] = pd.to_datetime(pay['payment_date'])
    c['payments'] = pay

    rt = t['sales_returns'].copy()
    rt['return_date'] = pd.to_datetime(rt['return_date'])
    rt['fy'] = fiscal_year(rt['return_date'])
    c['returns'] = rt

    sh = t['delivery_shipments'].copy()
    sh['ship_date'] = pd.to_datetime(sh['ship_date'])
    sh['delivery_date'] = pd.to_datetime(sh['delivery_date'])
    sh['delivery_days'] = (sh['delivery_date'] - sh['ship_date']).dt.days
    sh['free_shipping'] = sh['shipping_fee_EGP'] == 0
    sh = sh.merge(so[['sales_order_id', 'net_before_tax_EGP', 'fy']], on='sales_order_id', how='left')
    c['shipments'] = sh

    # ---------------------------------------------------------------- stock & transfers
    ms = t['monthly_stock'].copy()
    ms['month'] = pd.to_datetime(ms['year_month'] + '-01')
    ms['fy'] = fiscal_year(ms['month'])
    c['stock'] = ms

    tr = t['inventory_transfers'].copy()
    tr['transfer_date'] = pd.to_datetime(tr['transfer_date'])
    tr['fy'] = fiscal_year(tr['transfer_date'])
    tr = tr.merge(t['warehouses'][['warehouse_id', 'warehouse_kind']], left_on='source_warehouse_id', right_on='warehouse_id', how='left').drop(columns='warehouse_id')
    c['transfers'] = tr
    ti = t['inventory_transfer_items'].merge(tr[['transfer_id', 'transfer_date', 'fy', 'destination_branch_id', 'source_warehouse_id', 'warehouse_kind']], on='transfer_id', how='left')
    ti = ti.merge(sku[['sku_id', 'product_id', 'category_en']], on='sku_id', how='left')
    c['transfer_lines'] = ti

    # ---------------------------------------------------------------- purchasing & imports
    po = t['purchase_orders'].copy()
    po['po_date'] = pd.to_datetime(po['po_date'])
    po['fy'] = fiscal_year(po['po_date'])
    c['pos'] = po
    pl = t['purchase_order_items'].copy()
    pl['delivery_date'] = pd.to_datetime(pl['delivery_date'])
    pl = pl.merge(po[['po_id', 'po_date', 'fy', 'supplier_id', 'po_status', 'po_purpose']], on='po_id', how='left')
    pl = pl.merge(sku[['sku_id', 'product_id', 'category_en']], on='sku_id', how='left')
    pl['lead_days'] = (pl['delivery_date'] - pl['po_date']).dt.days
    c['po_lines'] = pl

    im = t['import_shipments'].copy()
    im['shipment_date'] = pd.to_datetime(im['shipment_date'], format='%m/%d/%Y')
    im['fy'] = fiscal_year(im['shipment_date'])
    c['imports'] = im

    # ---------------------------------------------------------------- marketing, people, costs
    mk = t['marketing_campaigns'].copy()
    mk['start_date'] = pd.to_datetime(mk['start_date'])
    mk['end_date'] = pd.to_datetime(mk['end_date'])
    mk['fy'] = fiscal_year(mk['start_date'])
    mk['days'] = (mk['end_date'] - mk['start_date']).dt.days + 1
    mk['ctr'] = mk['clicks'] / mk['impressions']
    mk['cpc'] = mk['spend_EGP'] / mk['clicks']
    c['campaigns'] = mk

    pa = t['payroll'].copy()
    pa['pay_month'] = pd.to_datetime(pa['pay_month'] + '-01')
    pa['fy'] = fiscal_year(pa['pay_month'])
    c['payroll'] = pa

    ox = t['operating_expenses'].copy()
    ox['expense_date'] = pd.to_datetime(ox['expense_date'])
    ox['fy'] = fiscal_year(ox['expense_date'])
    ox['month'] = ox['expense_date'].dt.to_period('M').dt.to_timestamp()
    c['opex'] = ox
    return c


def full_years(df, col='fy', first=2019, last=2026):
    """Keep complete fiscal years only (FY2019 starts 19 Oct 2018; Oct 2026 has 18 days → dropped)."""
    return df[(df[col] >= first) & (df[col] <= last)]


def quality_report(c):
    """Every issue we found, with the number that proves it. severity:
    Business = not a data error, it IS a finding the company must act on.
    Unreliable = a field filled at random: we do not build any decision on it.
    High = breaks an important analysis.  Medium = gap in the systems to fix."""
    so, li, sh, tr, ti, pl, mk, pa, em, ms, ox = (c[k] for k in ['orders', 'lines', 'shipments', 'transfers', 'transfer_lines',
                                                             'po_lines', 'campaigns', 'payroll', 'employees', 'stock', 'opex'])
    rows = []

    def add(area, table, issue, evidence, severity, action):
        rows.append(dict(id=f'DQ{len(rows) + 1:02d}', area=area, table=table, issue=issue, evidence=evidence, severity=severity, action=action))

    sold = li['quantity'].sum()
    bought = pl['quantity'].sum()
    sku_sold = li.groupby('sku_id')['quantity'].sum()
    sku_bought = pl.groupby('sku_id')['quantity'].sum()
    add('Purchasing', 'purchase_order_items', 'Purchased units are ~100x the units sold',
        f'{bought:,.0f} bought vs {sold:,.0f} sold ({bought / sold:.0f}x)', 'Business',
        'Ask the company which unit is used (piece / dozen / kg). Use PO data for comparisons only.')
    add('Purchasing', 'purchase_order_items', 'Quantity bought per SKU does not follow its sales',
        f'correlation per SKU = {sku_sold.corr(sku_bought):.3f}', 'Business',
        'Replace with a demand-driven purchase plan (forecast + safety stock).')
    tr_units = ti['quantity_units'].sum()
    add('Distribution', 'inventory_transfer_items', 'Branches receive far more than they sell',
        f'{tr_units:,.0f} units sent vs {sold:,.0f} sold ({tr_units / sold:.1f}x)', 'Business',
        'Allocate to branches by their real sales (demand-based allocation).')
    raw_ret = ti['warehouse_kind'].isin(['Raw materials', 'Returns']).mean()
    add('Distribution', 'inventory_transfers', 'Branches receive goods from the raw-material and returns warehouses',
        f'{raw_ret:.0%} of units sent to branches', 'High', 'Only finished-goods / distribution warehouses should ship to branches.')
    add('Sales', 'sales_order_items', 'Discounts do not increase the quantity sold',
        f"{li['has_discount'].mean():.0%} of lines discounted; avg qty {li.loc[li.has_discount, 'quantity'].mean():.2f} vs {li.loc[~li.has_discount, 'quantity'].mean():.2f}",
        'Business', 'Stop random discounts; run discounts only as measured tests.')
    attributed, real = mk['orders_attributed'].sum(), len(so)
    add('Marketing', 'marketing_campaigns', 'Campaigns claim far more orders than exist',
        f'{attributed:,.0f} attributed vs {real:,.0f} real orders ({attributed / real:.1f}x)', 'High',
        'Judge campaigns by cost per click / CTR and by holdout tests, never by attributed orders.')
    pre = so['before_opening']
    add('Branches', 'branches / sales_orders', 'Orders dated before the branch opened',
        f'{pre.sum():,.0f} orders ({pre.mean():.1%}), {so.loc[pre, "net_before_tax_EGP"].sum() / 1e6:.1f}M EGP', 'Medium',
        'Confirm the real opening dates with the company; keep the orders.')
    br_orders = so[so.channel == 'Store'].groupby('branch_id').size()
    add('Branches', 'sales_orders', 'All branches sell almost the same',
        f'store orders per branch {br_orders.min():,} – {br_orders.max():,}', 'Unreliable',
        'No branch ranking or location decision is built on this data.')
    add('Delivery', 'delivery_shipments', '"Delayed" status is not linked to delivery time',
        f"{(sh.loc[sh.delivery_days <= 1, 'fulfillment_status'] == 'Delayed').sum():,} 'Delayed' delivered in ≤1 day; "
        f"{(sh.loc[sh.delivery_days >= 7, 'fulfillment_status'] == 'Delivered').sum():,} 'on time' took 7 days", 'Unreliable',
        'No delivery-delay KPI until the carrier data is fixed.')
    by_gov = sh.groupby('ship_to_governorate')['delivery_days'].mean()
    add('Delivery', 'delivery_shipments', 'Delivery time is the same for every governorate',
        f'{by_gov.min():.2f} – {by_gov.max():.2f} days (Cairo = Aswan)', 'Unreliable', 'Collect real carrier scan dates.')
    small = sh['net_before_tax_EGP'] < sh['net_before_tax_EGP'].quantile(0.25)
    add('Delivery', 'delivery_shipments', 'Free shipping is given at random, even on very small orders',
        f"{sh['free_shipping'].mean():.0%} free overall; {sh.loc[small, 'free_shipping'].mean():.0%} for the smallest 25% of orders", 'Business',
        'Free shipping only above a minimum order value.')
    add('Payments', 'sales_payments', 'Every payment is on the order day, even cash on delivery',
        f"{(c['payments']['payment_date'].values == so.set_index('sales_order_id').loc[c['payments']['sales_order_id'], 'order_date'].values).mean():.0%} same day",
        'Unreliable', 'Payments table is a copy of orders: no cash-collection analysis.')
    add('Purchasing', 'purchase_orders', '"Partial receipt" never closes',
        f"{(c['pos']['po_status'] == 'Partial receipt').mean():.0%} partial in every year, even 2018", 'Unreliable',
        'Not reported as late deliveries.')
    add('Distribution', 'inventory_transfers', '"In transit" never closes',
        f"{(tr['transfer_status'] == 'In transit').mean():.0%} in transit + {(tr['transfer_status'] == 'Partially received').mean():.0%} partial, every year since 2018",
        'Unreliable', 'Not reported as stuck transfers.')
    add('Distribution', 'inventory_transfers', 'Transport cost is random (7 fixed values)',
        f"{tr['transport_cost_EGP'].nunique()} distinct values; same cost for any distance", 'Medium',
        'Use the count of transfers, not the cost per trip, for savings.')
    tot = ms.groupby('month')['closing_units'].sum()
    add('Inventory', 'monthly_stock', 'Monthly stock does not move with what came in and went out',
        f'total closing stock {tot.min() / 1e6:.2f}M – {tot.max() / 1e6:.2f}M units for 8 years', 'High',
        'Ask which is right: stock snapshots or transfers + sales. Stock is used for shares only.')
    by_role = em.groupby('position_en')['salary_base_EGP_2026'].mean()
    add('People', 'employees', 'Salary does not depend on the job',
        f'avg salary by role {by_role.min():,.0f} – {by_role.max():,.0f} EGP; area manager < cashier', 'Unreliable',
        'No salary benchmarking until HR data is fixed.')
    roles = em.pivot_table(index='branch_id', columns='position_en', values='employee_id', aggfunc='count', fill_value=0)
    add('People', 'employees', 'Roles are assigned in rotation: half the branches have no manager, half no cashier',
        f"{(roles.get('Store Manager', 0) == 0).sum()} branches without a store manager, {(roles.get('Cashier', 0) == 0).sum()} without a cashier", 'High',
        'Ask HR for the real org chart.')
    last = pa['pay_month'].max()
    add('People', 'payroll', 'Payroll is incomplete',
        f"{pa.loc[pa.pay_month == last, 'employee_id'].nunique()} of {em['employee_id'].nunique()} employees paid in the last month", 'High',
        'Payroll totals are not used for cost analysis.')
    rent = ox[ox.expense_category == 'Rent'].groupby('branch_or_department_id')['month'].nunique()
    add('Costs', 'operating_expenses', 'Rent is missing in most months for each branch',
        f'each branch has rent in {rent.mean():.0f} of {ox["month"].nunique()} months on average ({rent.min()}–{rent.max()})', 'Medium',
        'Ask finance for the full rent ledger.')
    mk_opex = ox.loc[ox.expense_category == 'Marketing', 'amount_EGP'].sum()
    add('Costs', 'operating_expenses / marketing_campaigns', 'Marketing cost in the expenses ledger ≠ campaign spend',
        f'{mk_opex / 1e6:.1f}M EGP in expenses vs {mk["spend_EGP"].sum() / 1e6:.1f}M in campaigns', 'High',
        'One source of truth for marketing spend (finance ledger).')
    sup = c['suppliers']
    add('Purchasing', 'suppliers', 'Supplier type does not match what they supply',
        f"{sup['material_type'].nunique()} supplier types, all supplying finished garments", 'Medium', 'Clean the supplier master.')
    imp = c['imports']
    add('Imports', 'import_shipments', 'Import freight does not depend on container or country',
        f"40FT avg {imp.loc[imp.container_type == '40FT', 'freight_USD'].mean():,.0f} USD vs 20FT {imp.loc[imp.container_type == '20FT', 'freight_USD'].mean():,.0f} USD",
        'Unreliable', 'No landed-cost model until real freight invoices are available.')
    add('Imports', 'import_shipments', 'Import value is far larger than all sales',
        f"{imp['customs_value_USD'].sum() / 1e6:,.0f}M USD imported vs {so['net_before_tax_EGP'].sum() / 1e9:.2f}B EGP sales", 'High',
        'Ask the company what the import rows represent.')
    add('Factories', 'factories', 'Factories are not linked to any other table', 'no factory_id anywhere', 'Medium',
        'Production / factory apps cannot be built until production data exists.')
    if 'public_catalog' in c:
        pc = c['public_catalog']
        add('Products', 'public catalog', 'Products on the website never appear in sales',
            f"{(~pc['in_sales_data']).sum()} of {len(pc)} public products", 'Medium', 'Ask if they are new products.')
    rr = c['returns']
    add('Returns', 'sales_returns', 'Return reasons are spread evenly (random)',
        f"5 reasons, each {rr['reason'].value_counts(normalize=True).min():.0%}–{rr['reason'].value_counts(normalize=True).max():.0%}", 'Unreliable',
        'Only the total return rate is used; reasons need a real capture form.')
    cu_br = so[so.channel == 'Store'].groupby('customer_id').agg(n=('sales_order_id', 'size'), br=('branch_id', 'nunique'))
    cu_br = cu_br[cu_br.n >= 5]
    add('Customers', 'customers / sales_orders', 'One customer ID shops in many branches and governorates',
        f'customers with 5+ store visits used {cu_br.br.mean():.1f} different branches on average', 'High',
        'Loyalty ID at the till (phone number) before any personalisation.')
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', default=str(DEFAULT_RAW))
    ap.add_argument('--out', default=str(ROOT / 'clean' / 'cottonil_clean.pkl'))
    a = ap.parse_args()
    t = load_raw(a.raw)
    c = clean(t)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pd.to_pickle(c, a.out)
    dq = quality_report(c)
    (ROOT / 'outputs').mkdir(exist_ok=True)
    dq.to_csv(ROOT / 'outputs' / 'data_quality_report.csv', index=False, encoding='utf-8-sig')
    print('saved', a.out, '|', len(c), 'tables |', len(dq), 'quality issues')


if __name__ == '__main__':
    main()
