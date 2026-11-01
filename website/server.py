"""
Cottonil · Manager board (لوحة المدير) – the manager website (HVIA Task 3).

One manager account. Every page is a working tool built on the data:
  • Today          – the month's numbers, alerts from the data, and the month's to-do cycle
  • Purchase plan  – demand forecast → quantities to buy → printable purchase order
  • Distribution   – what each branch gets next month, from its nearest warehouse → pick lists
  • Pricing        – discount policy, a discount checker and a promotion planner (test vs control branches)
  • Marketing      – monthly budget by governorate demand + a 4-week holdout test
  • Branches       – a profile for each of the 80 branches
  • Assistant      – «خيط», answers from the numbers and opens the right page
  • Monthly report – one printable page with everything saved this month

Run (from the project folder):   python website/server.py      → http://localhost:8050
Numbers come from core/ – the same functions as the notebooks and the dashboard.
"""
import io
import json
import os
import secrets
import sys
import threading
import uuid
from datetime import date, datetime
from functools import wraps
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, Response, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from core import analytics as A          # noqa: E402
from core import forecast as F           # noqa: E402
from core import manager as MG           # noqa: E402
import knowledge as K                    # noqa: E402

DATA = HERE / 'data'
DATA.mkdir(exist_ok=True)
STATE = DATA / 'board_state.json'
ACCOUNT = DATA / 'manager_account.json'
LOCK = threading.Lock()
VERSION = 'board-v2'

app = Flask(__name__, static_folder=str(HERE / 'static'), static_url_path='/static')
key_file = DATA / 'secret.key'
if not key_file.exists():
    key_file.write_text(secrets.token_hex(32))
app.secret_key = key_file.read_text().strip()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
app.json.sort_keys = False


# ---------------------------------------------------------------- JSON helpers
def clean(o):
    if isinstance(o, pd.DataFrame):
        return [clean(r) for r in o.to_dict('records')]
    if isinstance(o, pd.Series):
        return {str(k.strftime('%Y-%m') if isinstance(k, pd.Timestamp) else k): clean(v) for k, v in o.items()}
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if (o != o or o in (float('inf'), float('-inf'))) else round(float(o), 4)
    if isinstance(o, (pd.Timestamp, datetime, date)):
        return o.strftime('%Y-%m-%d')
    return o


def ok(payload):
    return jsonify(clean(payload))


def num(name, default, lo=None, hi=None):
    try:
        v = float(request.args.get(name, default))
    except (TypeError, ValueError):
        v = float(default)
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


def csv(df, name):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return Response('﻿' + buf.getvalue(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename=cottonil_{name}.csv'})


# ---------------------------------------------------------------- the one manager account
USERNAME, FIRST_PASSWORD = 'manager', 'Cottonil@2026'


def account():
    if not ACCOUNT.exists():
        ACCOUNT.write_text(json.dumps({'username': USERNAME, 'name': 'Manager', 'name_ar': 'المدير', 'hash': generate_password_hash(FIRST_PASSWORD),
                                       'must_change': True}, ensure_ascii=False, indent=1), encoding='utf-8')
    return json.loads(ACCOUNT.read_text(encoding='utf-8'))


def login_required(f):
    @wraps(f)
    def wrapper(*a, **k):
        if session.get('user') != USERNAME:
            return jsonify({'error': 'login required'}), 401
        return f(*a, **k)
    return wrapper


@app.post('/api/login')
def login():
    body = request.get_json(force=True, silent=True) or {}
    acc = account()
    if str(body.get('username', '')).strip().lower() != acc['username'] or not check_password_hash(acc['hash'], str(body.get('password', ''))):
        return jsonify({'error': 'wrong username or password'}), 401
    session.clear()
    session['user'] = USERNAME
    return me()


@app.post('/api/logout')
def logout():
    session.clear()
    return jsonify({'ok': True})


@app.get('/api/me')
@login_required
def me():
    acc = account()
    return jsonify({'username': acc['username'], 'name': acc['name'], 'name_ar': acc['name_ar'], 'must_change': acc.get('must_change', False)})


@app.post('/api/password')
@login_required
def change_password():
    body = request.get_json(force=True, silent=True) or {}
    new = str(body.get('new', ''))
    if len(new) < 8:
        return jsonify({'error': 'at least 8 characters'}), 400
    with LOCK:
        acc = account()
        if not check_password_hash(acc['hash'], str(body.get('old', ''))):
            return jsonify({'error': 'current password is wrong'}), 400
        acc.update(hash=generate_password_hash(new), must_change=False)
        ACCOUNT.write_text(json.dumps(acc, ensure_ascii=False, indent=1), encoding='utf-8')
    return jsonify({'ok': True})


# ---------------------------------------------------------------- numbers (computed once, cached on disk)
C, M = None, {}


def compute():
    global C, M
    C = A.load()
    cache = ROOT / 'clean' / 'board_cache.pkl'
    stamp = (os.path.getmtime(A.CLEAN), VERSION)
    if cache.exists():
        saved = pd.read_pickle(cache)
        if saved.get('stamp') == stamp:
            M = saved
            print('board: numbers loaded from cache')
            return
    print('board: computing the numbers (first run, about a minute)...')
    M = {'stamp': stamp, 'fy': A.fy_summary(C), 'monthly': A.monthly_sales(C), 'season': A.seasonality(C), 'discount': A.discount_facts(C),
         'bands': A.discount_bands(C), 'customers': A.customer_facts(C), 'transfers': A.transfers_fy(C), 'mix': A.category_mix(C),
         'stock': A.stock_facts(C), 'purchasing': A.purchasing_fy(C), 'marketing': A.marketing_fy(C), 'gov': A.governorate_budget(C),
         'people': A.people_facts(C), 'bridge': A.profit_bridge(C), 'base': MG.base(C)}
    res, bt = F.backtest(C)
    fc, hist = F.forecast(C, horizon=4)
    M.update(backtest=res, backtest_total=bt.groupby('month')[['units', 'model', 'naive']].sum(), forecast=fc, hist=hist)
    M['window'] = F.next_months(fc)[0]
    M['plan_default'] = MG.purchase_plan(C, fc, hist)[0]
    pd.to_pickle(M, cache)
    print('board: done')


# ---------------------------------------------------------------- saved work (plans, policy, checklist, notes)
def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding='utf-8'))
    s = {'purchase': [], 'distribution': [], 'policy': None, 'promos': [], 'marketing': [], 'checks': {}, 'notes': {}, 'log': []}
    save_state(s)
    return s


def save_state(s):
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(clean(s), indent=1, ensure_ascii=False), encoding='utf-8')
    tmp.replace(STATE)


def stamp_now():
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def add_saved(kind, item, what, what_ar):
    with LOCK:
        s = load_state()
        item = dict(item, id=uuid.uuid4().hex[:8], saved=stamp_now())
        s[kind] = ([item] + s.get(kind, []))[:30]
        s['log'] = ([{'when': item['saved'], 'what': what, 'what_ar': what_ar}] + s.get('log', []))[:100]
        save_state(s)
    return item


def policy(s=None):
    s = s or load_state()
    return s.get('policy') or {'max_discount': 10, 'floor_margin': 30, 'saved': None}


def cycle_month():
    return M['window'].strftime('%Y-%m')


@app.get('/api/meta')
@login_required
def meta():
    return ok({'cat_ar': K.CAT_AR, 'role_ar': K.ROLE_AR, 'month_ar': K.MONTH_AR, 'data_to': F.LAST, 'window': M['window'],
               'governorates': sorted(M['base']['branches'].governorate_ar.unique())})


# ---------------------------------------------------------------- Today
@app.get('/api/today')
@login_required
def today():
    s = load_state()
    fy, base = M['fy'], M['base']
    last = fy.iloc[-1]
    start, fq = F.next_months(M['forecast'])
    nxt = fq[fq.month == start].units.sum()
    hist = M['hist'].groupby('month').units.sum()
    hist = hist[hist.index >= hist.index.max() - pd.DateOffset(months=23)]
    fct = M['forecast'].groupby('month').units.sum()
    br = base['branches']
    watch = br.sort_values('stock_gap', ascending=False).head(6)[['branch_id', 'branch_name_ar', 'governorate_ar', 'stock_gap', 'months_cover', 'has_manager']]
    return ok({'month': cycle_month(), 'today': date.today(),
               'kpis': {'net_sales': last.net_sales, 'net_sales_g': last.net_sales_g, 'units_g': last.units_g, 'price_g': last.price_per_unit_g,
                        'margin': last.margin_pct, 'next_month_demand': nxt, 'quarter_demand': fq.units.sum(), 'stock_value': M['stock']['stock_value'],
                        'months_cover': M['stock']['months_cover']},
               'demand': {'hist': hist, 'forecast': fct},
               'alerts': K.alerts(M, s), 'cycle': K.cycle(M, s), 'watch': watch, 'log': s.get('log', [])[:6]})


@app.post('/api/checks')
@login_required
def set_check():
    body = request.get_json(force=True, silent=True) or {}
    item = str(body.get('item', ''))[:40]
    with LOCK:
        s = load_state()
        s.setdefault('checks', {}).setdefault(cycle_month(), {})[item] = bool(body.get('done'))
        save_state(s)
    return jsonify({'ok': True})


# ---------------------------------------------------------------- Purchase plan
def purchase_args():
    return dict(service=int(num('service', 95)), trust_stock=request.args.get('trust', '0') == '1', adjust_pct=num('adjust', 0, -30, 50))


@app.get('/api/purchase')
@login_required
def purchase():
    a = purchase_args()
    plan, months = MG.purchase_plan(C, M['forecast'], M['hist'], **a)
    pf = M['purchasing']
    hist = M['hist'].groupby('month').units.sum()
    by_month = [{'month': m, 'forecast': plan[m].sum(), 'last_year': hist.get(pd.Timestamp(m + '-01') - pd.DateOffset(years=1), 0)} for m in months]
    return ok({'args': a, 'months': months, 'plan': plan, 'by_month': by_month,'backtest': M['backtest'], 'backtest_total': M['backtest_total'].reset_index(),
               'bought_fy26': pf.bought.iloc[-1], 'sold_fy26': pf.sold.iloc[-1], 'stock_units': M['stock']['stock_units'],
               'saved': [{k: v for k, v in p.items() if k != 'rows'} for p in load_state()['purchase']]})


@app.post('/api/purchase/save')
@login_required
def purchase_save():
    body = request.get_json(force=True, silent=True) or {}
    rows = [{'category_en': str(r['category_en']), 'forecast': float(r.get('forecast', 0)), 'to_buy': max(0.0, float(r.get('to_buy', 0)))}
            for r in body.get('rows', []) if r.get('category_en')]
    if not rows:
        return jsonify({'error': 'empty plan'}), 400
    item = add_saved('purchase', {'window': body.get('window', ''), 'service': body.get('service'), 'trust': body.get('trust'), 'adjust': body.get('adjust'),
                                  'note': str(body.get('note', ''))[:300], 'total': sum(r['to_buy'] for r in rows), 'rows': rows},
                     f"purchase plan saved · {sum(r['to_buy'] for r in rows):,.0f} pieces", f"اتحفظت خطة الشراء · {sum(r['to_buy'] for r in rows):,.0f} قطعة")
    return jsonify({k: v for k, v in item.items() if k != 'rows'})


@app.get('/api/purchase/order/<pid>')
@login_required
def purchase_order(pid):
    p = next((x for x in load_state()['purchase'] if x['id'] == pid), None)
    if not p:
        return jsonify({'error': 'not found'}), 404
    lines = MG.purchase_lines(M['base'], p['rows'])
    if request.args.get('format') == 'csv':
        return csv(lines, f'purchase_order_{pid}')
    return ok({'plan': {k: v for k, v in p.items() if k != 'rows'}, 'rows': p['rows'], 'lines': lines})


# ---------------------------------------------------------------- Distribution
@app.get('/api/distribution')
@login_required
def distribution():
    start, fq = F.next_months(M['forecast'])
    months = sorted(fq.month.unique())
    month = request.args.get('month') or start.strftime('%Y-%m')
    d = MG.distribution(M['base'], M['forecast'], month + '-01', num('safety', 10, 0, 50))
    by_dc = d['branches'].groupby(['dc', 'dc_name']).agg(branches=('branch_id', 'size'), send=('send', 'sum'), old=('old', 'sum')).reset_index()
    if request.args.get('format') == 'csv':
        return csv(d['lines'].merge(M['base']['branches'][['branch_id', 'branch_name_ar', 'dc']], on='branch_id'), f'distribution_{d["month"]}')
    return ok({'months': [m.strftime('%Y-%m') for m in months], 'month': d['month'], 'safety': num('safety', 10, 0, 50), 'totals': d['totals'],
               'branches': d['branches'], 'by_dc': by_dc, 'categories': d['categories'],
               'source_mix': M['stock']['source_mix'], 'saved': load_state()['distribution']})


@app.get('/api/distribution/picklist')
@login_required
def picklist():
    month = request.args.get('month') or M['window'].strftime('%Y-%m')
    d = MG.distribution(M['base'], M['forecast'], month + '-01', num('safety', 10, 0, 50))
    bid = request.args.get('branch')
    ids = [bid] if bid else d['branches'].branch_id.tolist()
    info = M['base']['branches'].set_index('branch_id')
    out = []
    for b in ids:
        if b not in info.index:
            continue
        x = d['lines'][d['lines'].branch_id == b].sort_values('send', ascending=False)
        out.append({'branch_id': b, 'name': info.loc[b, 'branch_name_ar'], 'governorate': info.loc[b, 'governorate_ar'], 'address': info.loc[b, 'address_ar'],
                    'dc': info.loc[b, 'dc'], 'dc_name': info.loc[b, 'dc_name'], 'lines': x[['category_en', 'send', 'sent_month_fy26']], 'total': x.send.sum()})
    return ok({'month': d['month'], 'lists': out})


@app.post('/api/distribution/save')
@login_required
def distribution_save():
    body = request.get_json(force=True, silent=True) or {}
    month = str(body.get('month', ''))[:7]
    d = MG.distribution(M['base'], M['forecast'], month + '-01', float(body.get('safety', 10)))
    item = add_saved('distribution', {'month': d['month'], 'safety': float(body.get('safety', 10)), 'total': d['totals']['send'], 'old': d['totals']['old'],
                                      'trips': d['totals']['trips_new'], 'transport_saved': d['totals']['transport_saved_month'], 'note': str(body.get('note', ''))[:300]},
                     f"distribution plan {d['month']} saved · {d['totals']['send']:,.0f} pieces", f"اتحفظت خطة توزيع {K.MONTH_AR[int(d['month'][5:])]} · {d['totals']['send']:,.0f} قطعة")
    return ok(item)


# ---------------------------------------------------------------- Pricing
@app.get('/api/pricing')
@login_required
def pricing():
    li = C['lines']
    f26 = li[li.fy == 2026]
    price = (f26.groupby('category_en').net_line_EGP.sum() / f26.groupby('category_en').quantity.sum()).sort_values(ascending=False)
    gross_price = (f26.groupby('category_en').gross_line_EGP.sum() / f26.groupby('category_en').quantity.sum()) if 'gross_line_EGP' in f26 else price
    d = M['discount']
    return ok({'policy': policy(), 'bands': M['bands'].reset_index().rename(columns={'discount_pct': 'band'}),
               'facts': {k: d[k] for k in ['share_lines', 'pieces_with', 'pieces_without', 'margin_with', 'margin_without', 'corr', 'discount_fy26', 'gp_fy26']},
               'categories': [{'category_en': k, 'price': gross_price.get(k, v)} for k, v in price.items()], 'promos': load_state()['promos']})


@app.post('/api/pricing/policy')
@login_required
def pricing_policy():
    body = request.get_json(force=True, silent=True) or {}
    p = {'max_discount': min(50.0, max(0.0, float(body.get('max_discount', 10)))), 'floor_margin': min(40.0, max(0.0, float(body.get('floor_margin', 30)))),
         'saved': stamp_now()}
    with LOCK:
        s = load_state()
        s['policy'] = p
        s['log'] = ([{'when': p['saved'], 'what': f"discount policy saved · max {p['max_discount']:.0f}% · floor margin {p['floor_margin']:.0f}%",
                      'what_ar': f"اتحفظت سياسة الخصم · أقصى خصم {p['max_discount']:.0f}% · أقل هامش {p['floor_margin']:.0f}%"}] + s.get('log', []))[:100]
        save_state(s)
    return jsonify(p)


@app.get('/api/pricing/check')
@login_required
def pricing_check():
    p = policy()
    return ok(MG.check_discount(num('price', 300, 1), num('discount', 10, 0, 90), p['max_discount'], p['floor_margin']))


@app.get('/api/pricing/promo')
@login_required
def pricing_promo():
    cat = request.args.get('category', 'Socks')
    r = MG.promo_plan(C, M['base'], cat, num('discount', 10, 1, 50), int(num('weeks', 2, 1, 8)))
    if request.args.get('format') == 'csv':
        return csv(r['groups'], f'promo_test_control_{cat}')
    r['policy'] = policy()
    r['evidence'] = {'pieces_with': M['discount']['pieces_with'], 'pieces_without': M['discount']['pieces_without']}
    return ok(r)


@app.post('/api/pricing/promo/save')
@login_required
def promo_save():
    body = request.get_json(force=True, silent=True) or {}
    cat = str(body.get('category', 'Socks'))
    r = MG.promo_plan(C, M['base'], cat, float(body.get('discount', 10)), int(body.get('weeks', 2)))
    item = add_saved('promos', {'category': cat, 'discount': r['discount'], 'weeks': r['weeks'], 'cost': r['cost'], 'uplift_needed_pct': r['uplift_needed_pct'],
                                'test_branches': int((r['groups'].group == 'Test').sum()), 'start': str(body.get('start', ''))[:10]},
                     f"promotion test saved · {cat} −{r['discount']:.0f}% · {r['weeks']} weeks", f"اتحفظت تجربة عرض · {K.CAT_AR.get(cat, cat)} −{r['discount']:.0f}% · {({1: 'أسبوع', 2: 'أسبوعين'}).get(r['weeks'], str(r['weeks']) + ' أسابيع')}")
    return ok(item)


# ---------------------------------------------------------------- Marketing
@app.get('/api/marketing')
@login_required
def marketing():
    mf = M['marketing']
    today_month = mf.spend.iloc[-1] / 12
    budget = num('budget', round(today_month * 0.75, -4), 0)
    g, pairs = MG.marketing_plan(M['gov'], budget, int(num('pairs', 4, 0, 5)))
    if request.args.get('format') == 'csv':
        return csv(g[['governorate_ar', 'orders', 'order_share', 'spend', 'spend_share', 'today_month', 'plan', 'test', 'plan_test_month']], 'marketing_plan')
    return ok({'budget': budget, 'today_month': today_month, 'spend_fy26': mf.spend.iloc[-1], 'claimed_x': mf.claimed.sum() / mf.real_orders.sum(),
               'gov': g, 'pairs': pairs, 'saved': load_state()['marketing']})


@app.post('/api/marketing/save')
@login_required
def marketing_save():
    body = request.get_json(force=True, silent=True) or {}
    budget = float(body.get('budget', 0))
    g, pairs = MG.marketing_plan(M['gov'], budget, int(body.get('pairs', 4)))
    item = add_saved('marketing', {'month': cycle_month(), 'budget': budget, 'pairs': pairs, 'paused_budget': g.plan.sum() - g.plan_test_month.sum(),
                                   'note': str(body.get('note', ''))[:300]}, f'marketing budget saved · {budget:,.0f} EGP / month · {len(pairs)} test pairs',
                     f'اتحفظت ميزانية التسويق · {budget:,.0f} جنيه في الشهر · {len(pairs)} أزواج تجربة')
    return ok(item)


# ---------------------------------------------------------------- Branches
@app.get('/api/branches')
@login_required
def branches():
    b = M['base']['branches'].drop(columns=['opening_date']).assign(opening=M['base']['branches'].opening_date)
    if request.args.get('format') == 'csv':
        return csv(b, 'branches')
    return ok({'branches': b, 'notes': load_state().get('notes', {})})


@app.get('/api/branches/<bid>')
@login_required
def branch(bid):
    p = MG.branch_profile(C, M['base'], bid, M['forecast'])
    if p is None:
        return jsonify({'error': 'not found'}), 404
    wh = C['warehouses'].set_index('warehouse_id')
    p['sources'] = [{'warehouse_id': k, 'name': wh.loc[k, 'warehouse_label'], 'kind': wh.loc[k, 'warehouse_kind'], 'units': v} for k, v in p['sources'].items()]
    p['note'] = load_state().get('notes', {}).get(bid, '')
    br = M['base']['branches']
    p['peers'] = {'sales26_median': br.sales26.median(), 'cover_median': br.months_cover.median(), 'gap_median': br.stock_gap.median(),
                  'sent_per_sold_median': br.sent_per_sold.median()}
    return ok(p)


@app.post('/api/branches/<bid>/note')
@login_required
def branch_note(bid):
    body = request.get_json(force=True, silent=True) or {}
    with LOCK:
        s = load_state()
        s.setdefault('notes', {})[bid] = str(body.get('note', ''))[:1000]
        save_state(s)
    return jsonify({'ok': True})


# ---------------------------------------------------------------- Assistant
@app.post('/api/assistant')
@login_required
def assistant():
    body = request.get_json(force=True, silent=True) or {}
    return ok(K.answer(str(body.get('q', ''))[:500], M, load_state(), body.get('lang', 'ar')))


# ---------------------------------------------------------------- Monthly report
@app.get('/api/report')
@login_required
def report():
    s = load_state()
    fy = M['fy']
    month = cycle_month()
    start, fq = F.next_months(M['forecast'])
    b = M['bridge']
    return ok({'month': month, 'generated': stamp_now(), 'fy': fy.reset_index().tail(3), 'cycle': K.cycle(M, s), 'alerts': K.alerts(M, s),
               'purchase': next(({k: v for k, v in p.items()} for p in s['purchase']), None),
               'distribution': next((p for p in s['distribution'] if p['month'] == month), None),
               'policy': policy(s), 'promos': s['promos'][:3], 'marketing': next((p for p in s['marketing'] if p['month'] == month), None),
               'forecast_quarter': fq.groupby('month').units.sum(), 'backtest': M['backtest'],
               'bridge': {'base': b['base'], 'new': b['new'], 'actions': b['actions'][['action', 'action_ar', 'profit']]},
               'notes': {k: v for k, v in s.get('notes', {}).items() if v}})


# ---------------------------------------------------------------- the single page
@app.get('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    if not A.CLEAN.exists():
        print('Clean data not found → building it (about 20 seconds)...')
        from core import build_clean
        build_clean.main()
    compute()
    account()
    port = int(os.environ.get('PORT', 8050))
    print(f'\n  Cottonil · Manager board →  http://localhost:{port}\n  first login: {USERNAME} / {FIRST_PASSWORD} (you will be asked to change it)\n')
    app.run(host='127.0.0.1', port=port, debug=False, threaded=True)
