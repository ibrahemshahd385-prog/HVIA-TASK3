"""
Numbers for the manager board (website). Built on the same clean data, analytics and forecast as the notebooks and the dashboard.
Each function returns plain tables the website turns into a plan, an order or a profile.
"""
import numpy as np
import pandas as pd

from core import analytics as A
from core import forecast as F

# nearest distribution centre for every governorate (finished goods only: never the raw-material or returns warehouse)
NEAREST_DC = {
    'القاهرة': 'WH01', 'الإسكندرية': 'WH02', 'مطروح': 'WH02', 'الجيزة': 'WH03', 'الفيوم': 'WH03', 'الدقهلية': 'WH04', 'دمياط': 'WH04',
    'المنيا': 'WH05', 'بني سويف': 'WH05', 'أسيوط': 'WH05', 'سوهاج': 'WH05', 'قنا': 'WH05', 'أسوان': 'WH05', 'البحر الأحمر': 'WH05',
    'الشرقية': 'WH09', 'البحيرة': 'WH10', 'الغربية': 'WH11', 'المنوفية': 'WH11', 'كفر الشيخ': 'WH11', 'الإسماعيلية': 'WH12', 'بورسعيد': 'WH12',
}
Z = {90: 1.28, 95: 1.65, 98: 2.05, 99: 2.33}


def base(c):
    """Everything heavy, computed once when the website starts."""
    li, so, ti, ms = c['lines'], c['orders'], c['transfer_lines'], c['stock']
    br = c['branches'].copy()
    wh = c['warehouses'].set_index('warehouse_id')
    br['dc'] = br.governorate_ar.map(NEAREST_DC).fillna('WH01')
    br['dc_name'] = br.dc.map(wh.warehouse_label)
    # per-branch flows, FY2026 and all time
    f26 = li[li.fy == 2026]
    sold26 = f26.groupby('branch_id').quantity.sum()
    sales26 = so[so.fy == 2026].groupby('branch_id').net_before_tax_EGP.sum()
    sales25 = so[so.fy == 2025].groupby('branch_id').net_before_tax_EGP.sum()
    sent26 = ti[ti.fy == 2026].groupby('destination_branch_id').quantity_units.sum()
    bs = ms[ms.stock_location_type == 'Branch']
    start = bs[bs.month == bs.month.min()].groupby('stock_location_id').closing_units.sum()
    end = bs[bs.month == bs.month.max()].groupby('stock_location_id').closing_units.sum()
    rt = c['returns'].merge(li[['sales_line_id', 'branch_id']], on='sales_line_id', how='left')
    gap = (start + ti.groupby('destination_branch_id').quantity_units.sum() + rt.groupby('branch_id').return_quantity.sum()
           - li.groupby('branch_id').quantity.sum() - end)
    em = c['employees']
    roles = em.pivot_table(index='branch_id', columns='position_en', values='employee_id', aggfunc='count', fill_value=0)
    pre = so[so.before_opening].groupby('branch_id').size()
    t = br.set_index('branch_id')
    t['sales26'], t['sales25'] = sales26, sales25
    t['growth'] = (t.sales26 / t.sales25 - 1) * 100
    t['sold26'], t['sent26'] = sold26, sent26
    t['sent_per_sold'] = t.sent26 / t.sold26
    t['stock_units'] = end
    t['months_cover'] = t.stock_units / (t.sold26 / 12)
    t['stock_gap'] = gap
    t['has_manager'] = roles.get('Store Manager', 0) > 0
    t['has_cashier'] = roles.get('Cashier', 0) > 0
    t['orders_before_opening'] = pre.reindex(t.index).fillna(0).astype(int)
    t = t.fillna({'sent26': 0, 'stock_units': 0})
    # SKU share inside each category (for purchase-order lines)
    sku = f26.groupby(['category_en', 'sku_id', 'product_id']).quantity.sum().rename('sold26').reset_index()
    sku['share'] = sku.sold26 / sku.groupby('category_en').sold26.transform('sum')
    sku = sku.merge(c['skus'][['sku_id', 'size', 'color_ar']], on='sku_id').merge(c['products'][['product_id', 'product_name_ar', 'listed_price_EGP']], on='product_id')
    # what each branch sells of each category (for the allocation split)
    share = f26.groupby(['category_en', 'branch_id']).quantity.sum()
    share = (share / share.groupby(level=0).transform('sum')).rename('share').reset_index()
    old_sent = ti[ti.fy == 2026].groupby(['destination_branch_id', 'category_en']).quantity_units.sum().div(12).rename('sent_month_fy26').reset_index()
    monthly_branch = so[(so.month >= '2024-10-01') & (so.month <= '2026-09-01')].groupby(['branch_id', 'month']).net_before_tax_EGP.sum()
    return {'branches': t.reset_index(), 'sku': sku, 'share': share, 'old_sent': old_sent, 'monthly_branch': monthly_branch,
            'cost_per_transfer': c['transfers'].loc[c['transfers'].fy == 2026, 'transport_cost_EGP'].mean(),
            'pieces_per_transfer': ti[ti.fy == 2026].quantity_units.sum() / (c['transfers'].fy == 2026).sum()}


# ---------------------------------------------------------------- purchase plan
def purchase_plan(c, fc, hist, service=95, trust_stock=False, adjust_pct=0.0):
    start, fq = F.next_months(fc)
    fq = fq.assign(units=fq.units * (1 + adjust_pct / 100))
    months = sorted(fq.month.unique())
    by_month = fq.pivot_table(index='category_en', columns='month', values='units', aggfunc='sum')
    by_month.columns = [m.strftime('%Y-%m') for m in by_month.columns]
    recent = hist[hist.month >= pd.Timestamp(F.LAST) - pd.DateOffset(months=11)].groupby(['category_en', 'month']).units.sum()
    safety = Z.get(int(service), 1.65) * recent.groupby(level=0).std()
    ly = hist[hist.month.isin([m - pd.DateOffset(years=1) for m in months])].groupby('category_en').units.sum()
    stock = c['stock'][c['stock'].month == c['stock'].month.max()].groupby('product_category').closing_units.sum()
    pl = c['po_lines']
    p = by_month.copy()
    p['forecast'] = by_month.sum(axis=1)
    p['last_year'] = ly
    p['safety'] = safety
    p['stock'] = stock
    p['to_buy'] = (p.forecast + p.safety - (p.stock if trust_stock else 0)).clip(lower=0)
    p['old_pattern'] = pl[pl.fy == 2026].groupby('category_en').quantity.sum() / 4
    p = p.fillna(0).round(0).sort_values('forecast', ascending=False).reset_index().rename(columns={'index': 'category_en'})
    return p, [m.strftime('%Y-%m') for m in months]


def purchase_lines(base_, plan_rows):
    """Turn category quantities into SKU lines (each SKU gets its FY2026 share of its category)."""
    q = pd.DataFrame(plan_rows)[['category_en', 'to_buy']]
    lines = base_['sku'].merge(q, on='category_en')
    lines['quantity'] = (lines.to_buy * lines.share).round(0)
    lines = lines[lines.quantity > 0]
    return lines[['category_en', 'sku_id', 'product_name_ar', 'size', 'color_ar', 'quantity']].sort_values(['category_en', 'quantity'], ascending=[True, False])


# ---------------------------------------------------------------- distribution
def distribution(base_, fc, month=None, safety_pct=10):
    start, fq = F.next_months(fc)
    month = pd.Timestamp(month) if month else start
    need = fc[fc.month == month].groupby('category_en').units.sum().rename('demand').reset_index()
    a = base_['share'].merge(need, on='category_en')
    a['send'] = (a.share * a.demand * (1 + safety_pct / 100)).round(0)
    a = a.merge(base_['old_sent'].rename(columns={'destination_branch_id': 'branch_id'}), on=['branch_id', 'category_en'], how='left').fillna({'sent_month_fy26': 0})
    b = base_['branches'][['branch_id', 'branch_name_ar', 'governorate_ar', 'dc', 'dc_name']]
    per_branch = a.groupby('branch_id').agg(send=('send', 'sum'), old=('sent_month_fy26', 'sum')).reset_index().merge(b, on='branch_id')
    per_branch['change_pct'] = (per_branch.send / per_branch.old - 1) * 100
    per_cat = a.groupby('category_en').agg(send=('send', 'sum'), old=('sent_month_fy26', 'sum')).reset_index().sort_values('old', ascending=False)
    trips_new = per_branch.send.sum() / base_['pieces_per_transfer']
    trips_old = per_branch.old.sum() / base_['pieces_per_transfer']
    return {'month': month.strftime('%Y-%m'), 'branches': per_branch.sort_values('send', ascending=False), 'categories': per_cat, 'lines': a,
            'totals': {'send': per_branch.send.sum(), 'old': per_branch.old.sum(), 'trips_new': trips_new, 'trips_old': trips_old,
                       'transport_saved_month': (trips_old - trips_new) * base_['cost_per_transfer']}}


# ---------------------------------------------------------------- pricing
def check_discount(price, discount, max_discount=10, floor_margin=30, cost_ratio=0.59):
    net = price * (1 - discount / 100)
    margin = (net - price * cost_ratio) / net * 100 if net else 0
    verdict = 'reject' if (margin < floor_margin or discount > 2 * max_discount) else ('approval' if discount > max_discount else 'ok')
    return {'net_price': net, 'margin': margin, 'verdict': verdict, 'margin_after_full': (price - price * cost_ratio) / price * 100}


def promo_plan(c, base_, category, discount, weeks, cost_ratio=0.59):
    li = c['lines']
    f26 = li[(li.fy == 2026) & (li.category_en == category)]
    weekly_net = f26.net_line_EGP.sum() / 52
    weekly_pcs = f26.quantity.sum() / 52
    price = f26.net_line_EGP.sum() / f26.quantity.sum()
    cost = weekly_net * weeks * discount / 100
    margin_piece_after = price * (1 - discount / 100) - price * cost_ratio
    extra_needed = cost / margin_piece_after if margin_piece_after > 0 else float('inf')
    uplift_needed = extra_needed / (weekly_pcs * weeks) * 100
    # test / control: branches sorted by this category's sales, alternated → two groups with the same size and mix
    sh = base_['share'][base_['share'].category_en == category].sort_values('share', ascending=False).reset_index(drop=True)
    sh['group'] = np.where(sh.index % 2 == 0, 'Test', 'Control')
    sh = sh.merge(base_['branches'][['branch_id', 'branch_name_ar', 'governorate_ar']], on='branch_id')
    return {'category': category, 'discount': discount, 'weeks': weeks, 'cost': cost, 'avg_price': price, 'weekly_pieces': weekly_pcs,
            'extra_pieces_needed': extra_needed, 'uplift_needed_pct': uplift_needed, 'groups': sh[['branch_id', 'branch_name_ar', 'governorate_ar', 'group']],
            'test_share': sh[sh.group == 'Test'].share.sum() * 100}


# ---------------------------------------------------------------- marketing
def marketing_plan(g, monthly_budget, pairs_n=4):
    """Monthly budget split by each governorate's share of orders, plus a 4-week holdout test:
    governorates are paired by similar orders (Cairo and Alexandria are too big to pause), one of each pair pauses ads."""
    g = g.copy()
    g['today_month'] = g.spend / 12
    g['plan'] = g.order_share / 100 * monthly_budget
    srt = g.sort_values('orders', ascending=False).reset_index()
    pairs = []
    for k, i in enumerate(range(2, min(len(srt) - 1, 2 + 2 * pairs_n), 2)):
        a, b = srt.iloc[i], srt.iloc[i + 1]
        pause, keep = (a, b) if k % 2 == 0 else (b, a)          # alternate, so the paused side is not always the bigger one
        pairs.append({'pause': pause.governorate_ar, 'keep': keep.governorate_ar, 'orders_pause': pause.orders, 'orders_keep': keep.orders})
    status = {p['pause']: 'pause' for p in pairs} | {p['keep']: 'control' for p in pairs}
    g = g.reset_index()
    g['test'] = g.governorate_ar.map(status).fillna('run')
    g['plan_test_month'] = np.where(g.test == 'pause', 0, g.plan)
    return g, pairs


# ---------------------------------------------------------------- branch profile
def branch_profile(c, base_, bid, fc):
    t = base_['branches'].set_index('branch_id')
    if bid not in t.index:
        return None
    row = t.loc[bid]
    li = c['lines']
    f26 = li[(li.fy == 2026) & (li.branch_id == bid)]
    ti = c['transfer_lines']
    s26 = ti[(ti.fy == 2026) & (ti.destination_branch_id == bid)]
    mix = pd.DataFrame({'sold_pct': f26.groupby('category_en').quantity.sum() / f26.quantity.sum() * 100,
                        'sent_pct': s26.groupby('category_en').quantity_units.sum() / max(s26.quantity_units.sum(), 1) * 100}).fillna(0)
    mix = mix.sort_values('sold_pct', ascending=False).reset_index().rename(columns={'index': 'category_en'})
    ch = c['orders'][(c['orders'].fy == 2026) & (c['orders'].branch_id == bid)].groupby('channel').net_before_tax_EGP.sum()
    stock = c['stock'][(c['stock'].stock_location_id == bid) & (c['stock'].month == c['stock'].month.max())][['product_category', 'closing_units', 'closing_stock_value_EGP']]
    monthly_cat = f26.groupby('category_en').quantity.sum() / 12
    stock['months_cover'] = stock.closing_units / stock.product_category.map(monthly_cat)
    src = s26.groupby('source_warehouse_id').quantity_units.sum().sort_values(ascending=False)
    em = c['employees'][c['employees'].branch_id == bid][['employee_id', 'employee_name_ar', 'position_en', 'hire_date']]
    dist = distribution(base_, fc)
    nxt = dist['lines'][dist['lines'].branch_id == bid][['category_en', 'send', 'sent_month_fy26']].sort_values('send', ascending=False)
    monthly = base_['monthly_branch'].loc[bid] if bid in base_['monthly_branch'].index.get_level_values(0) else pd.Series(dtype=float)
    return {'info': row.to_dict() | {'branch_id': bid}, 'mix': mix, 'channels': ch, 'stock': stock.sort_values('closing_units', ascending=False),
            'sources': src, 'staff': em, 'next_month': nxt, 'next_month_label': dist['month'], 'monthly': monthly}
