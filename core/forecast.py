"""
AI demand forecast (used by notebook 12, the dashboard and the website – one place only).

Model: HistGradientBoosting (many small decision trees, each one fixes the error of the previous ones)
on monthly pieces sold per category × channel (16 × 3 = 48 series, Nov 2018 → Sep 2026).
Features: last 3 months, same month last year (seasonality), 3- and 12-month averages, month, time trend, category, channel.
Backtest: hide the last 6 months (Apr–Sep 2026), forecast them month by month, compare with
"same month last year" (seasonal naive). WAPE = sum(|error|) / sum(actual).
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

KEYS = ['category_en', 'channel']
FEATURES = ['lag1', 'lag2', 'lag3', 'lag12', 'roll3', 'roll12', 'mon', 't', 'category_en_c', 'channel_c']
FIRST, LAST = '2018-11-01', '2026-09-01'      # complete months only (Oct 2018 and Oct 2026 are partial)


def monthly(c):
    li = c['lines']
    li = li[(li['month'] >= FIRST) & (li['month'] <= LAST)]
    m = li.groupby(KEYS + ['month']).quantity.sum().rename('units').reset_index()
    full = pd.MultiIndex.from_product([sorted(m[k].unique()) for k in KEYS] + [pd.date_range(FIRST, LAST, freq='MS')], names=KEYS + ['month'])
    return m.set_index(KEYS + ['month']).reindex(full, fill_value=0).reset_index().sort_values(KEYS + ['month']).reset_index(drop=True)


def add_features(d):
    d = d.copy()
    g = d.groupby(KEYS).units
    for k in [1, 2, 3, 12]:
        d[f'lag{k}'] = g.shift(k)
    d['roll3'] = g.transform(lambda s: s.shift(1).rolling(3).mean())
    d['roll12'] = g.transform(lambda s: s.shift(1).rolling(12).mean())
    d['mon'] = d.month.dt.month
    d['t'] = (d.month.dt.year - 2018) * 12 + d.month.dt.month
    for k in KEYS:
        d[k + '_c'] = d[k].astype('category').cat.codes
    return d


def train(hist):
    d = add_features(hist).dropna(subset=FEATURES)
    return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=42).fit(d[FEATURES], np.log1p(d.units))


def recursive(model, hist, months):
    """Forecast month by month; each forecast is used as history for the next month."""
    work = hist.copy()
    combos = hist[KEYS].drop_duplicates()
    for mo in months:
        nxt = combos.assign(month=mo, units=np.nan)
        tmp = add_features(pd.concat([work, nxt]).sort_values(KEYS + ['month']).reset_index(drop=True))
        row = tmp[tmp.month == mo]
        nxt = row[KEYS + ['month']].assign(units=np.expm1(model.predict(row[FEATURES])).clip(0))
        work = pd.concat([work, nxt])
    return work[work.month.isin(months)].reset_index(drop=True)


def backtest(c, start='2026-04-01', end=LAST):
    m = monthly(c)
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    hist, truth = m[m.month < start], m[(m.month >= start) & (m.month <= end)]
    pred = recursive(train(hist), hist, pd.date_range(start, end, freq='MS'))
    last_year = m.assign(month=m.month + pd.DateOffset(years=1)).rename(columns={'units': 'naive'})
    out = truth.merge(pred.rename(columns={'units': 'model'}), on=KEYS + ['month']).merge(last_year, on=KEYS + ['month'], how='left')
    wape = lambda col: (out[col] - out.units).abs().sum() / out.units.sum() * 100
    res = {'wape_model': round(wape('model'), 1), 'wape_naive': round(wape('naive'), 1)}
    res['better_%'] = round((1 - res['wape_model'] / res['wape_naive']) * 100, 0)
    return res, out


def forecast(c, horizon=4):
    m = monthly(c)
    months = pd.date_range(pd.Timestamp(LAST) + pd.DateOffset(months=1), periods=horizon, freq='MS')
    return recursive(train(m), m, months), m


def next_months(fc, start=None):
    """The planning window. Today is Nov 2026 and the data is complete to Sep 2026, so the forecast starts in Oct 2026
    and the plan covers the 3 months after it: Nov 2026 – Jan 2027."""
    start = pd.Timestamp(start) if start else fc.month.min() + pd.DateOffset(months=1)
    return start, fc[(fc.month >= start) & (fc.month < start + pd.DateOffset(months=3))]


def plans(c, fc, hist, service_z=1.65, safety_branch=0.10, trust_stock=False, start=None):
    """Purchase plan per category (next 3 months) and allocation plan per branch × category (next month), both from the forecast."""
    start, fq = next_months(fc, start)
    # purchase plan: next 3 months need + safety stock (z × monthly std × √1-month lead time)
    need = fq.groupby('category_en').units.sum()
    recent = hist[hist.month >= pd.Timestamp(LAST) - pd.DateOffset(months=11)].groupby(['category_en', 'month']).units.sum()
    sd = recent.groupby(level=0).std()
    safety = service_z * sd
    stock = c['stock'][c['stock'].month == c['stock'].month.max()].groupby('product_category').closing_units.sum()
    pl = c['po_lines']
    bought_q = pl[pl.fy == 2026].groupby('category_en').quantity.sum() / 4         # what the current pattern buys per quarter
    p = pd.DataFrame({'forecast_3m': need.round(0), 'safety_stock': safety.round(0), 'stock_on_hand': stock}).fillna(0)
    p['to_buy'] = (p.forecast_3m + p.safety_stock - (p.stock_on_hand if trust_stock else 0)).clip(lower=0).round(0)
    p['current_pattern_buys'] = bought_q.reindex(p.index).fillna(0).round(0)
    p['months_of_stock'] = (p.stock_on_hand / (p.forecast_3m / 3)).round(1)
    p = p.sort_values('forecast_3m', ascending=False)
    # allocation plan: next month's forecast split by each branch's share of that category (FY2026) + safety
    li = c['lines']
    share = li[li.fy == 2026].groupby(['category_en', 'branch_id']).quantity.sum()
    share = share / share.groupby(level=0).transform('sum')
    first = fc[fc.month == start].groupby('category_en').units.sum()
    alloc = (share * first.reindex(share.index.get_level_values(0)).values * (1 + safety_branch)).round(0).rename('send_next_month').reset_index()
    sent = c['transfer_lines']
    sent = sent[sent.fy == 2026].groupby(['destination_branch_id', 'category_en']).quantity_units.sum() / 12
    alloc = alloc.merge(sent.rename('sent_per_month_FY2026').round(0).reset_index().rename(columns={'destination_branch_id': 'branch_id'}),
                        on=['branch_id', 'category_en'], how='left').fillna(0)
    return p, alloc
