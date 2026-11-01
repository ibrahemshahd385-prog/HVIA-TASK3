"""
Every business number of the project, calculated in ONE place.
The notebooks show the same steps one by one; the dashboard and the website import these functions,
so a number can never be different in two places.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / 'clean' / 'cottonil_clean.pkl'
FY_FIRST, FY_LAST = 2019, 2026


def load(path=None):
    return pd.read_pickle(path or CLEAN)


def full_years(d, col='fy'):
    return d[(d[col] >= FY_FIRST) & (d[col] <= FY_LAST)]


# ---------------------------------------------------------------- card 01 – sales & growth
def fy_summary(c):
    so, li = full_years(c['orders']), full_years(c['lines'])
    fy = so.groupby('fy').agg(orders=('sales_order_id', 'size'), net_sales=('net_before_tax_EGP', 'sum'), discount=('discount_EGP', 'sum'))
    fy = fy.join(li.groupby('fy').agg(units=('quantity', 'sum'), gross_profit=('margin_EGP', 'sum'), cogs=('cost_line_EGP', 'sum')))
    fy['margin_pct'] = fy.gross_profit / fy.net_sales * 100
    fy['aov'] = fy.net_sales / fy.orders
    fy['price_per_unit'] = fy.net_sales / fy.units
    for col in ['net_sales', 'orders', 'units', 'price_per_unit', 'gross_profit']:
        fy[col + '_g'] = fy[col].pct_change() * 100
    rt = full_years(c['returns']).groupby('fy').refund_amount_EGP.sum()
    fy['refund_pct'] = rt / fy.net_sales * 100
    fy['customers'] = so.groupby('fy').customer_id.nunique()
    return fy


def monthly_sales(c):
    so = c['orders']
    so = so[(so.month >= '2018-11-01') & (so.month <= '2026-09-01')]
    m = so.groupby('month').agg(net_sales=('net_before_tax_EGP', 'sum'), orders=('sales_order_id', 'size'))
    m = m.join(c['lines'].groupby('month').agg(units=('quantity', 'sum'), gross_profit=('margin_EGP', 'sum')))
    return m


def channel_fy(c):
    so = full_years(c['orders'])
    x = so.groupby(['fy', 'channel']).agg(net_sales=('net_before_tax_EGP', 'sum'), orders=('sales_order_id', 'size')).reset_index()
    x['share'] = x.net_sales / x.groupby('fy').net_sales.transform('sum') * 100
    return x


def category_fy(c, fy=FY_LAST):
    li = c['lines']
    x = li[li.fy == fy].groupby('category_en').agg(net_sales=('net_line_EGP', 'sum'), units=('quantity', 'sum'), gross_profit=('margin_EGP', 'sum'))
    x['share'] = x.net_sales / x.net_sales.sum() * 100
    x['margin_pct'] = x.gross_profit / x.net_sales * 100
    return x.sort_values('net_sales', ascending=False)


def seasonality(c):
    so = c['orders']
    s = so[(so.fy >= 2020) & (so.fy <= FY_LAST)].assign(m=lambda d: d.order_date.dt.month).groupby(['fy', 'm']).size().unstack()
    return (s.div(s.mean(axis=1), axis=0).mean() - 1) * 100


def weekday(c):
    so = full_years(c['orders'])
    w = so.groupby(['fy', 'weekday']).size().unstack()
    order = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    return ((w.div(w.mean(axis=1), axis=0).mean() - 1) * 100)[order]


# ---------------------------------------------------------------- card 02 – discounts
def discount_bands(c):
    li = full_years(c['lines'])
    band = pd.cut(li.discount_pct, [-0.001, 0, 0.05, 0.10, 0.15, 0.20, 1], labels=['0%', '1–5%', '6–10%', '11–15%', '16–20%', '20%+'])
    b = li.groupby(band, observed=True).agg(lines=('quantity', 'size'), avg_pieces=('quantity', 'mean'), net=('net_line_EGP', 'sum'), gp=('margin_EGP', 'sum'))
    b['margin_pct'] = b.gp / b.net * 100
    b.index = b.index.astype(str)
    return b


def discount_facts(c):
    li = full_years(c['lines'])
    d26 = li[li.fy == FY_LAST]
    by_month = li.assign(m=li.order_date.dt.month).groupby('m').has_discount.mean() * 100
    return {'share_lines': li.has_discount.mean() * 100,
            'pieces_with': li.loc[li.has_discount, 'quantity'].mean(), 'pieces_without': li.loc[~li.has_discount, 'quantity'].mean(),
            'margin_with': li.loc[li.has_discount, 'margin_EGP'].sum() / li.loc[li.has_discount, 'net_line_EGP'].sum() * 100,
            'margin_without': li.loc[~li.has_discount, 'margin_EGP'].sum() / li.loc[~li.has_discount, 'net_line_EGP'].sum() * 100,
            'corr': li[['discount_pct', 'quantity']].corr().iloc[0, 1],
            'discount_fy26': d26.discount_line_EGP.sum(), 'gp_fy26': d26.margin_EGP.sum(), 'by_month': by_month,
            'by_channel': li.groupby('channel').has_discount.mean() * 100}


# ---------------------------------------------------------------- card 03 – customers
def customer_facts(c):
    so, cu = full_years(c['orders']), c['customers']
    x = so.merge(cu[['customer_id', 'customer_segment']], on='customer_id', how='left')
    st = so[(so.channel == 'Store') & so.customer_id.notna()].merge(c['branches'][['branch_id', 'governorate_ar']], on='branch_id')
    v = st.groupby('customer_id').agg(visits=('sales_order_id', 'size'), branches=('branch_id', 'nunique'), govs=('governorate_ar', 'nunique'))
    v5 = v[v.visits >= 5]
    ws = x[x.channel == 'Wholesale']
    return {'guest_share': so.customer_id.isna().mean() * 100,
            'guest_by_channel': so.groupby('channel').customer_id.apply(lambda s: s.isna().mean() * 100),
            'wholesale_by_retail_customers': (ws.customer_segment == 'Retail').sum() / ws.customer_segment.notna().sum() * 100,
            'loyal_visits': v5.visits.mean(), 'loyal_branches': v5.branches.mean(), 'loyal_govs': v5.govs.mean(), 'loyal_n': len(v5),
            'active_by_fy': so.groupby('fy').customer_id.nunique()}


def rfm(c, snapshot='2026-10-01'):
    so, cu = full_years(c['orders']), c['customers']
    r = so.merge(cu[['customer_id', 'customer_segment']], on='customer_id')
    r = r[r.customer_segment == 'Retail']
    p = r.groupby('customer_id').agg(last=('order_date', 'max'), orders=('sales_order_id', 'size'), spend=('net_before_tax_EGP', 'sum'))
    p['recency_days'] = (pd.Timestamp(snapshot) - p['last']).dt.days
    p['R'] = pd.qcut(p.recency_days, 5, labels=[5, 4, 3, 2, 1]).astype(int)
    p['F'] = pd.qcut(p.orders.rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    p['M'] = pd.qcut(p.spend, 5, labels=[1, 2, 3, 4, 5]).astype(int)
    p['segment'] = np.select(
        [(p.R >= 4) & (p.F >= 4), (p.R >= 3) & (p.F >= 3), (p.R >= 4) & (p.F <= 2), (p.R <= 2) & (p.F >= 4), (p.R <= 2) & (p.F == 3), (p.R == 3)],
        ['Champions', 'Loyal', 'New / Promising', "At Risk (Can't Lose)", 'At Risk', 'Need Attention'], default='Lost')
    return p.reset_index()


def churn_test(c, cutoff='2026-03-31', horizon=182):
    """Can we predict who will NOT buy in the next 6 months? Train on the past only, test on unseen customers."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    so, cu = c['orders'], c['customers']
    r = so.merge(cu[['customer_id', 'customer_segment']], on='customer_id')
    r = r[r.customer_segment == 'Retail']
    cut = pd.Timestamp(cutoff)
    past, fut = r[r.order_date <= cut], r[(r.order_date > cut) & (r.order_date <= cut + pd.Timedelta(days=horizon))]
    f = past.groupby('customer_id').agg(orders=('sales_order_id', 'size'), spend=('net_before_tax_EGP', 'sum'), last=('order_date', 'max'),
                                        first=('order_date', 'min'), discount=('discount_EGP', 'sum'), items=('items_count', 'mean'),
                                        online_share=('channel', lambda s: (s == 'Online').mean()))
    f['recency'] = (cut - f['last']).dt.days
    f['tenure'] = (cut - f['first']).dt.days
    f['orders_180d'] = past[past.order_date > cut - pd.Timedelta(days=180)].groupby('customer_id').size().reindex(f.index).fillna(0)
    f['churn'] = (~f.index.isin(fut.customer_id)).astype(int)
    X = f[['orders', 'spend', 'recency', 'tenure', 'discount', 'items', 'online_share', 'orders_180d']]
    Xtr, Xte, ytr, yte = train_test_split(X, f.churn, test_size=0.25, random_state=42, stratify=f.churn)
    model = HistGradientBoostingClassifier(random_state=42).fit(Xtr, ytr)
    band = pd.cut(f.recency, [-1, 30, 90, 180, 365, 10_000], labels=['< 1 month', '1–3 months', '3–6 months', '6–12 months', '> 1 year'])
    return {'customers': len(f), 'churn_rate': f.churn.mean() * 100,
            'auc_model': roc_auc_score(yte, model.predict_proba(Xte)[:, 1]), 'auc_recency_rule': roc_auc_score(yte, Xte.recency),
            'buy_again_by_recency': (1 - f.groupby(band, observed=True).churn.mean()) * 100}


# ---------------------------------------------------------------- card 04 – branches, channels, delivery
def branch_sales(c, fy=FY_LAST):
    so = c['orders']
    b = so[(so.fy == fy) & (so.channel == 'Store')].groupby('branch_id').net_before_tax_EGP.sum()
    return b.to_frame('store_sales').join(c['branches'].set_index('branch_id')[['branch_name_ar', 'governorate_ar', 'retail_location_type', 'opening_date']])


def shipping_facts(c, fy=FY_LAST):
    sh = full_years(c['shipments'])
    s = sh[sh.fy == fy]
    avg_fee = s.loc[~s.free_shipping, 'shipping_fee_EGP'].mean()
    q = pd.qcut(sh.net_before_tax_EGP, 5, labels=['smallest 20%', '2nd', '3rd', '4th', 'largest 20%'])
    return {'free_share': sh.free_shipping.mean() * 100, 'free_by_size': sh.groupby(q, observed=True).free_shipping.mean() * 100,
            'avg_fee': avg_fee, 'delivery_by_gov': sh.groupby('ship_to_governorate').delivery_days.mean(),
            'delay_by_days': pd.crosstab(sh.delivery_days, sh.fulfillment_status, normalize='index')['Delayed'] * 100,
            'delivery_share': sh.delivery_days.value_counts(normalize=True).sort_index() * 100, 'shipments_fy': len(s)}


def free_shipping_saving(c, threshold=1000, fy=FY_LAST):
    s = c['shipments']
    s = s[s.fy == fy]
    n = int((s.free_shipping & (s.net_before_tax_EGP < threshold)).sum())
    return n, n * s.loc[~s.free_shipping, 'shipping_fee_EGP'].mean()


# ---------------------------------------------------------------- card 05 – inventory & allocation
def transfers_fy(c):
    li, ti, tr = full_years(c['lines']), full_years(c['transfer_lines']), full_years(c['transfers'])
    y = pd.DataFrame({'sold': li.groupby('fy').quantity.sum(), 'sent': ti.groupby('fy').quantity_units.sum(),
                      'transfers': tr.groupby('fy').size(), 'transport_cost': tr.groupby('fy').transport_cost_EGP.sum()})
    y['ratio'] = y.sent / y.sold
    return y


def category_mix(c):
    li, ti = full_years(c['lines']), full_years(c['transfer_lines'])
    return pd.DataFrame({'sold_pct': li.groupby('category_en').quantity.sum() / li.quantity.sum() * 100,
                         'sent_pct': ti.groupby('category_en').quantity_units.sum() / ti.quantity_units.sum() * 100}).sort_values('sent_pct', ascending=False)


def stock_facts(c):
    ms, ti, li = c['stock'], c['transfer_lines'], c['lines']
    bs = ms[ms.stock_location_type == 'Branch']
    start = bs[bs.month == bs.month.min()].closing_units.sum()
    end = bs[bs.month == bs.month.max()].closing_units.sum()
    received, sold, returned = ti.quantity_units.sum(), li.quantity.sum(), c['returns'].return_quantity.sum()
    last = ms[ms.month == ms.month.max()]
    monthly_sold = full_years(li).query('fy == @FY_LAST').quantity.sum() / 12
    monthly_cogs = full_years(li).query('fy == @FY_LAST').cost_line_EGP.sum() / 12
    total = ms.groupby('month').closing_units.sum()
    return {'start': start, 'received': received, 'returned': returned, 'sold': sold, 'end': end,
            'unaccounted': start + received + returned - sold - end,
            'stock_units': last.closing_units.sum(), 'stock_value': last.closing_stock_value_EGP.sum(),
            'months_cover': last.closing_units.sum() / monthly_sold, 'need_value_3m': monthly_cogs * 3,
            'stock_series': total, 'sku_corr': li.groupby('sku_id').quantity.sum().corr(ti.groupby('sku_id').quantity_units.sum()),
            'branch_corr': li.groupby('branch_id').quantity.sum().corr(ti.groupby('destination_branch_id').quantity_units.sum()),
            'source_mix': ti.groupby('warehouse_kind').quantity_units.sum() / ti.quantity_units.sum() * 100}


def allocation_saving(c, safety=0.10, fy=FY_LAST):
    li, ti, tr = c['lines'], c['transfer_lines'], c['transfers']
    need = li[li.fy == fy].quantity.sum() * (1 + safety)
    sent = ti[ti.fy == fy].quantity_units.sum()
    n = (tr.fy == fy).sum()
    per_transfer = sent / n
    new_n = need / per_transfer
    return {'sent': sent, 'need': need, 'cut_pct': (1 - need / sent) * 100, 'transfers': n, 'new_transfers': new_n,
            'saving': (n - new_n) * tr.loc[tr.fy == fy, 'transport_cost_EGP'].mean()}


# ---------------------------------------------------------------- card 06 – purchasing
def purchasing_fy(c):
    li, pl = full_years(c['lines']), full_years(c['po_lines'])
    y = pd.DataFrame({'sold': li.groupby('fy').quantity.sum(), 'bought': pl.groupby('fy').quantity.sum(),
                      'spend': pl.groupby('fy').line_cost_EGP.sum(), 'cogs': li.groupby('fy').cost_line_EGP.sum()})
    y['ratio'] = y.bought / y.sold
    return y


def sku_bought_sold(c):
    return pd.DataFrame({'sold': c['lines'].groupby('sku_id').quantity.sum(), 'bought': c['po_lines'].groupby('sku_id').quantity.sum()}).dropna()


# ---------------------------------------------------------------- card 07 – marketing
def marketing_fy(c):
    mk, so = full_years(c['campaigns']), full_years(c['orders'])
    y = pd.DataFrame({'spend': mk.groupby('fy').spend_EGP.sum(), 'net_sales': so.groupby('fy').net_before_tax_EGP.sum(),
                      'claimed': mk.groupby('fy').orders_attributed.sum(), 'real_orders': so.groupby('fy').size()})
    y['spend_pct'] = y.spend / y.net_sales * 100
    y['claimed_x'] = y.claimed / y.real_orders
    return y


def marketing_channels(c):
    mk = full_years(c['campaigns'])
    ch = mk.groupby('channel').agg(spend=('spend_EGP', 'sum'), impressions=('impressions', 'sum'), clicks=('clicks', 'sum'), claimed=('orders_attributed', 'sum'))
    ch['cpc'] = ch.spend / ch.clicks
    ch['ctr'] = ch.clicks / ch.impressions * 100
    ch['spend_share'] = ch.spend / ch.spend.sum() * 100
    return ch.sort_values('cpc')


def governorate_budget(c, fy=FY_LAST):
    mk, so = c['campaigns'], c['orders']
    o = so[so.fy == fy].merge(c['branches'][['branch_id', 'governorate_ar']], on='branch_id')
    g = pd.DataFrame({'spend': mk[mk.fy == fy].groupby('governorate_ar').spend_EGP.sum(), 'orders': o.groupby('governorate_ar').size()}).fillna(0)
    g['spend_share'] = g.spend / g.spend.sum() * 100
    g['order_share'] = g.orders / g.orders.sum() * 100
    g['budget_if_demand'] = g.order_share / 100 * g.spend.sum()
    return g.sort_values('orders', ascending=False)


# ---------------------------------------------------------------- card 08 – people & costs
def people_facts(c):
    em, pa, ox = c['employees'], c['payroll'], c['opex']
    roles = em.pivot_table(index='branch_id', columns='position_en', values='employee_id', aggfunc='count', fill_value=0)
    rent = ox[ox.expense_category == 'Rent'].groupby('branch_or_department_id').month.nunique()
    return {'employees': len(em), 'no_manager': int((roles['Store Manager'] == 0).sum()), 'no_cashier': int((roles['Cashier'] == 0).sum()),
            'area_managers': int((em.position_en == 'Area Manager').sum()),
            'salary_by_role': em.groupby('position_en').salary_base_EGP_2026.mean().sort_values(ascending=False),
            'paid_per_month': pa.groupby('pay_month').employee_id.nunique(),
            'payroll_fy26': pa[pa.fy == FY_LAST].net_paid_EGP.sum(), 'base_list_year': em.salary_base_EGP_2026.sum() * 12,
            'rent_months_avg': rent.mean(), 'months': ox.month.nunique(),
            'opex_pct': full_years(ox).groupby('fy').amount_EGP.sum() / full_years(c['orders']).groupby('fy').net_before_tax_EGP.sum() * 100,
            'marketing_ledger': ox.loc[ox.expense_category == 'Marketing', 'amount_EGP'].sum(), 'marketing_campaigns': c['campaigns'].spend_EGP.sum()}


# ---------------------------------------------------------------- card 09 – the action plan
def profit_bridge(c, stop_discount_pct=75, marketing_cut_pct=25, alloc_safety_pct=10, ship_threshold=1000, volume_growth_pct=None):
    fy = fy_summary(c)
    base = fy.gross_profit.loc[FY_LAST]
    d = discount_facts(c)
    mk = marketing_fy(c).spend.loc[FY_LAST]
    al = allocation_saving(c, alloc_safety_pct / 100)
    n_ship, ship = free_shipping_saving(c, ship_threshold)
    actions = pd.DataFrame([
        ('Stop random discounts', 'إيقاف الخصومات العشوائية', 'Sales', d['discount_fy26'] * stop_discount_pct / 100,
         f'{stop_discount_pct}% of FY2026 discounts ({d["discount_fy26"] / 1e6:.1f}M); discounted lines sell the same pieces'),
        ('Cut marketing with no measured effect', 'تقليل التسويق اللي ملوش أثر', 'Marketing', mk * marketing_cut_pct / 100,
         f'{marketing_cut_pct}% of FY2026 spend ({mk / 1e6:.1f}M); spend ↔ orders ≈ 0'),
        ('Demand-based allocation to branches', 'توزيع البضاعة على الفروع حسب البيع', 'Supply chain', al['saving'],
         f'{al["cut_pct"]:.0f}% fewer pieces moved → {al["transfers"] - al["new_transfers"]:,.0f} fewer transfers'),
        ('Free shipping only above a minimum order', 'شحن مجاني بحد أدنى للطلب', 'E-commerce', ship,
         f'{n_ship:,} free shipments under {ship_threshold:,} EGP'),
    ], columns=['action', 'action_ar', 'owner', 'profit', 'assumption'])
    new = base + actions.profit.sum()
    g = (fy.units_g.loc[FY_LAST] if volume_growth_pct is None else volume_growth_pct) / 100
    disc_gain = actions.profit.iloc[0]
    breakeven = disc_gain / (base + disc_gain) * 100        # % of volume we could lose before stopping discounts stops paying
    scenarios = pd.DataFrame({'scenario': ['A · do nothing', 'B · the plan', 'C · the plan, and we lose 5% of volume'],
                              'scenario_ar': ['أ · من غير تغيير', 'ب · الخطة', 'ج · الخطة ونخسر 5% من الكميات'],
                              'profit': [base * (1 + g), new * (1 + g), (base + disc_gain) * (1 + g) * 0.95 + actions.profit.iloc[1:].sum()]})
    return {'base': base, 'actions': actions, 'new': new, 'uplift_pct': (new / base - 1) * 100, 'breakeven_volume_loss': breakeven,
            'scenarios': scenarios, 'growth': g * 100}


# ---------------------------------------------------------------- data trust center (built without being asked)
READINESS = [
    # (page in the HVIA PDF, idea, status, why, what data would unlock it)
    (2, 'Executive Dashboard', 'Ready', 'Sales, margin, growth and seasonality are consistent and close to the cent.', '—'),
    (3, 'Sales Performance Intelligence', 'Ready', 'Real signals: growth, Nov–Dec and Mar–May peaks, Thu–Sat, category mix.', '—'),
    (4, 'Branch Performance Optimization', 'Not meaningful', 'All 80 branches sell within ±5%; 7% of orders before opening.', 'Real branch sales, traffic, size (m²), opening dates'),
    (5, 'Inventory & Warehouse Intelligence', 'Partial', 'Stock is flat for 8 years; 9.3M pieces not accounted for.', 'Physical stock count, transfer receipts'),
    (6, 'Customer Segmentation & Loyalty', 'Partial', '19% of orders have no customer; one ID shops in ~7 branches; age/gender random.', 'Loyalty ID (phone) at the till'),
    (7, 'Demand Forecasting & Product Planning', 'Ready', 'Built: AI forecast 21% more accurate than last year’s same month.', '—'),
    (8, 'Supply Chain & Logistics Visibility', 'Partial', 'Statuses never close (in transit 6%, partial 33%); delivery days random.', 'Carrier scans, receipt dates'),
    (9, 'Procurement & Supplier Analytics', 'Partial', 'Quantities ~100× sales; supplier types and lead times random.', 'Confirmed purchase units, supplier master'),
    (10, 'Returns & Quality Control', 'Partial', 'Return rate is real (~1.6%), reasons are random (20% each).', 'Return reason form, QC defects'),
    (11, 'Sustainability & ESG Analytics', 'Not possible', 'No energy, water, carbon or material data at all.', 'Utility bills, material sourcing data'),
    (12, 'New Store Expansion & Site Selection', 'Not possible', 'No demographics, competitors or rent; branch sales are equal.', 'Census, competitor map, rents'),
    (13, 'Price Optimization & Promotion Intelligence', 'Partial', 'Built: discounts proven to add no pieces. Price elasticity cannot be estimated (prices only follow inflation).', 'Planned price tests'),
    (14, 'Omnichannel Commerce & Digital Analytics', 'Partial', 'Online share frozen at 12.5%; no web/app traffic data.', 'Web analytics, app events'),
    (15, 'Marketing ROI & Campaign Performance', 'Partial', 'Campaigns claim ×45 the real orders; only spend, CTR and CPC are usable.', 'Holdout tests, UTM-tagged orders'),
    (16, 'Product Profitability & Margin Intelligence', 'Ready (flat)', 'Cost is always 59% of price → margin 38% everywhere; only discounts move it.', 'Real landed cost per SKU'),
    (17, 'Workforce Productivity & Store Operations', 'Not reliable', 'Roles assigned in rotation; payroll covers ≤225 of 640 people.', 'HR org chart, full payroll, shifts'),
    (18, 'Smart Replenishment & Auto Allocation', 'Ready', 'Built: allocation from the forecast, −55% pieces moved.', 'Stock count to subtract on-hand'),
    (19, 'Customer Lifetime Value & Churn Prediction', 'Tested – rejected', 'Churn model AUC 0.50 = coin flip; CLV only descriptive.', 'Loyalty ID + a win-back test'),
    (20, 'Visual Merchandising & Planogram Analytics', 'Not possible', 'No store layout, display or shelf data.', 'Planograms, store audits'),
    (21, 'Loss Prevention & Shrinkage Control', 'Partial', 'Strong signal: 9.3M pieces sent to branches are neither sold nor on shelf.', 'Stock count, CCTV/incident logs'),
    (22, 'Wholesale & Distributor Performance', 'Partial', '98% of wholesale orders come from customers registered as retail.', 'Reseller flag and accounts'),
    (23, 'AI-Powered Business Assistant', 'Ready', 'Built in the manager website: answers from the data with the source.', '—'),
]


def readiness():
    return pd.DataFrame(READINESS, columns=['page', 'idea', 'status', 'why', 'unlock_with'])


DATA_REQUESTS = [
    ('High', 'Purchasing', 'What unit do purchase orders use (piece, dozen, kg)? 42M pieces a year vs 0.6M sold.', 'طلبات الشراء بوحدة إيه (قطعة ولا دستة ولا كيلو)؟ 42 مليون قطعة في السنة مقابل 0.6 مليون اتباعت.'),
    ('High', 'Inventory', 'Physical stock count in 5 branches: 9.3M pieces sent are neither sold nor on shelf.', 'جرد فعلي في 5 فروع: 9.3 مليون قطعة اتبعتت ومش متباعة ولا على الرف.'),
    ('High', 'Customers', 'Capture a customer ID (phone) on every order – 19% have none, even online.', 'تسجيل رقم العميل (الموبايل) في كل طلب: 19% من الطلبات مفيهاش عميل، حتى الأونلاين.'),
    ('High', 'HR', 'Real org chart and full payroll: 40 branches without a manager, payroll covers ≤225 of 640.', 'الهيكل الوظيفي الحقيقي والمرتبات كاملة: 40 فرع من غير مدير، والمرتبات بتغطي 225 من 640 بالكتير.'),
    ('High', 'Marketing', 'One marketing ledger: 11.8M in expenses vs 219.5M in campaigns.', 'سجل واحد لصرف التسويق: 11.8 مليون في المصاريف مقابل 219.5 مليون في الحملات.'),
    ('Medium', 'Branches', 'Confirm branch opening dates: 38,040 orders are dated before opening.', 'تأكيد تواريخ افتتاح الفروع: 38,040 طلب متسجلين قبل الافتتاح.'),
    ('Medium', 'Delivery', 'Carrier scan dates: delivery time and "Delayed" are random today.', 'تواريخ الشحن الفعلية من شركات الشحن: مدة التوصيل وحالة التأخير عشوائيين.'),
    ('Medium', 'Imports', 'What do import rows represent (450M USD vs 0.84B EGP sales)? Add quantity and SKU.', 'سطور الاستيراد بتمثل إيه (450 مليون دولار مقابل 0.84 مليار جنيه مبيعات)؟ ونضيف الكمية والـ SKU.'),
    ('Medium', 'Returns', 'A return-reason form: today each reason is exactly 20%.', 'فورم لسبب المرتجع: كل سبب دلوقتي 20% بالظبط.'),
    ('Medium', 'Factories', 'Production data per factory (nothing links to the 6 factories).', 'داتا إنتاج لكل مصنع (الـ 6 مصانع مش مربوطين بحاجة).'),
    ('Low', 'Products', '99 products on the website never appear in sales – new or discontinued?', '99 منتج على الموقع مش موجودين في المبيعات: جداد ولا اتوقفوا؟'),
]


def data_requests():
    return pd.DataFrame(DATA_REQUESTS, columns=['priority', 'area', 'request', 'request_ar'])
