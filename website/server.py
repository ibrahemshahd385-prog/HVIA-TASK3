"""
Cottonil Decision Hub – the manager website (HVIA Task 3).

What it does: a manager logs in and gets, in one place,
  • the decisions of the month (from the data),
  • every problem we found with its evidence, root cause, solution, owner and EGP impact,
  • working tools that produce the solution (purchase plan, branch allocation, discount guardrail,
    marketing budget + holdout test, free-shipping rule),
  • an action tracker, the data-gap tracker, and an assistant that answers from the data.

Run (from the project folder):   python website/server.py      → http://localhost:8050
Numbers come from core/analytics.py and core/forecast.py – the same functions as the notebooks and the dashboard.
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
from core.build_clean import quality_report  # noqa: E402
import knowledge as K                    # noqa: E402

DATA = HERE / 'data'
DATA.mkdir(exist_ok=True)
STATE = DATA / 'state.json'
USERS = DATA / 'users.json'
LOCK = threading.Lock()

app = Flask(__name__, static_folder=str(HERE / 'static'), static_url_path='/static')
key_file = DATA / 'secret.key'
if not key_file.exists():
    key_file.write_text(secrets.token_hex(32))
app.secret_key = key_file.read_text().strip()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
app.json.sort_keys = False      # keep the order of categories / bands as computed


# ---------------------------------------------------------------- JSON helpers
def clean(o):
    """Make pandas / numpy objects JSON friendly."""
    if isinstance(o, pd.DataFrame):
        return [clean(r) for r in o.reset_index().to_dict('records')] if o.index.name else [clean(r) for r in o.to_dict('records')]
    if isinstance(o, pd.Series):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if (o != o) else round(float(o), 4)
    if isinstance(o, (pd.Timestamp, datetime, date)):
        return o.strftime('%Y-%m-%d')
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def ok(payload):
    return jsonify(clean(payload))


# ---------------------------------------------------------------- users & login
DEFAULT_USERS = [
    ('ceo', 'Chief Executive', 'المدير التنفيذي', 'CEO'),
    ('supply', 'Supply Chain Manager', 'مدير سلسلة الإمداد', 'Supply chain'),
    ('marketing', 'Marketing Manager', 'مدير التسويق', 'Marketing'),
    ('finance', 'Finance Manager', 'المدير المالي', 'Finance'),
]
DEFAULT_PASSWORD = 'Cottonil@2026'


def load_users():
    if not USERS.exists():
        users = {u: {'name': n, 'name_ar': na, 'role': r, 'hash': generate_password_hash(DEFAULT_PASSWORD), 'must_change': True}
                 for u, n, na, r in DEFAULT_USERS}
        USERS.write_text(json.dumps(users, indent=1, ensure_ascii=False), encoding='utf-8')
    return json.loads(USERS.read_text(encoding='utf-8'))


def login_required(f):
    @wraps(f)
    def wrapper(*a, **k):
        if 'user' not in session:
            return jsonify({'error': 'login required'}), 401
        return f(*a, **k)
    return wrapper


@app.post('/api/login')
def login():
    body = request.get_json(force=True, silent=True) or {}
    users = load_users()
    u = users.get(str(body.get('username', '')).strip().lower())
    if not u or not check_password_hash(u['hash'], str(body.get('password', ''))):
        return jsonify({'error': 'wrong username or password'}), 401
    session.clear()
    session['user'] = str(body['username']).strip().lower()
    return me()


@app.post('/api/logout')
def logout():
    session.clear()
    return jsonify({'ok': True})


@app.get('/api/me')
@login_required
def me():
    u = load_users()[session['user']]
    return jsonify({'username': session['user'], 'name': u['name'], 'name_ar': u['name_ar'], 'role': u['role'], 'must_change': u.get('must_change', False)})


@app.post('/api/password')
@login_required
def change_password():
    body = request.get_json(force=True, silent=True) or {}
    new = str(body.get('new', ''))
    if len(new) < 8:
        return jsonify({'error': 'at least 8 characters'}), 400
    with LOCK:
        users = load_users()
        if not check_password_hash(users[session['user']]['hash'], str(body.get('old', ''))):
            return jsonify({'error': 'current password is wrong'}), 400
        users[session['user']].update(hash=generate_password_hash(new), must_change=False)
        USERS.write_text(json.dumps(users, indent=1, ensure_ascii=False), encoding='utf-8')
    return jsonify({'ok': True})


# ---------------------------------------------------------------- data (computed once, cached on disk)
C = None
M = {}


def compute():
    global C, M
    C = A.load()
    cache = ROOT / 'clean' / 'website_cache.pkl'
    stamp = os.path.getmtime(A.CLEAN)
    if cache.exists():
        saved = pd.read_pickle(cache)
        if saved.get('stamp') == stamp:
            M = saved
            print('website: numbers loaded from cache')
            return
    print('website: computing all numbers (first run, ~1 minute)...')
    M = {'stamp': stamp, 'fy': A.fy_summary(C), 'monthly': A.monthly_sales(C), 'channel': A.channel_fy(C), 'discount': A.discount_facts(C),
         'customers': A.customer_facts(C), 'transfers': A.transfers_fy(C), 'mix': A.category_mix(C), 'stock': A.stock_facts(C),
         'purchasing': A.purchasing_fy(C), 'marketing': A.marketing_fy(C), 'channels': A.marketing_channels(C), 'gov': A.governorate_budget(C),
         'people': A.people_facts(C), 'bridge': A.profit_bridge(C), 'readiness': A.readiness(), 'requests': A.data_requests(),
         'dq': quality_report(C), 'category': A.category_fy(C), 'season': A.seasonality(C), 'churn': A.churn_test(C),
         'shipping': A.shipping_facts(C), 'alloc_saving': A.allocation_saving(C)}
    res, bt = F.backtest(C)
    fc, hist = F.forecast(C, horizon=4)
    M.update(backtest=res, backtest_total=bt.groupby('month')[['units', 'model', 'naive']].sum(), forecast=fc, hist=hist)
    pd.to_pickle(M, cache)
    print('website: done')


# ---------------------------------------------------------------- shared state (problems, actions, data requests)
def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding='utf-8'))
    s = {'problems': {p['id']: {'status': 'Open', 'note': ''} for p in K.PROBLEMS},
         'requests': {f'R{i + 1:02d}': {'status': 'To request', 'note': ''} for i in range(len(A.DATA_REQUESTS))},
         'actions': [dict(a, id=uuid.uuid4().hex[:8], created=str(date.today())) for a in K.STARTER_ACTIONS], 'log': []}
    save_state(s)
    return s


def save_state(s):
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(s, indent=1, ensure_ascii=False), encoding='utf-8')
    tmp.replace(STATE)


def log(s, what):
    s['log'] = ([{'when': datetime.now().strftime('%Y-%m-%d %H:%M'), 'who': session.get('user'), 'what': what}] + s.get('log', []))[:200]


# ---------------------------------------------------------------- pages
@app.get('/api/overview')
@login_required
def overview():
    fy, b = M['fy'], M['bridge']
    last, prev = fy.iloc[-1], fy.iloc[-2]
    kpis = {'net_sales': last.net_sales, 'net_sales_g': last.net_sales_g, 'gross_profit': last.gross_profit, 'gross_profit_g': last.gross_profit_g,
            'margin': last.margin_pct, 'units': last.units, 'units_g': last.units_g, 'price_g': last.price_per_unit_g, 'discount': last.discount,
            'customers': last.customers, 'profit_at_stake': b['new'] - b['base'], 'uplift_pct': b['uplift_pct']}
    s = load_state()
    open_actions = [a for a in s['actions'] if a['status'] != 'Done']
    return ok({'kpis': kpis, 'monthly': M['monthly'].reset_index().rename(columns={'month': 'month'}), 'fy': fy.reset_index(),
               'bridge': {'base': b['base'], 'new': b['new'], 'actions': b['actions']},
               'decisions': K.decisions(M), 'open_actions': len(open_actions),
               'problems_open': sum(1 for v in s['problems'].values() if v['status'] != 'Done'),
               'channel': M['channel'][M['channel'].fy == M['channel'].fy.max()]})


@app.get('/api/problems')
@login_required
def problems():
    s = load_state()
    return ok([dict(p, **s['problems'].get(p['id'], {'status': 'Open', 'note': ''})) for p in K.problems(M)])


@app.post('/api/problems/<pid>')
@login_required
def update_problem(pid):
    body = request.get_json(force=True, silent=True) or {}
    with LOCK:
        s = load_state()
        if pid not in s['problems']:
            return jsonify({'error': 'unknown problem'}), 404
        if body.get('status') in ('Open', 'In progress', 'Done'):
            s['problems'][pid]['status'] = body['status']
        if 'note' in body:
            s['problems'][pid]['note'] = str(body['note'])[:1000]
        log(s, f'problem {pid} → {s["problems"][pid]["status"]}')
        save_state(s)
    return jsonify({'ok': True})


# ---------------------------------------------------------------- tools
Z = {'90': 1.28, '95': 1.65, '98': 2.05, '99': 2.33}


@app.get('/api/tools/purchase')
@login_required
def tool_purchase():
    z = Z.get(request.args.get('service', '95'), 1.65)
    trust = request.args.get('trust', '0') == '1'
    plan, _ = F.plans(C, M['forecast'], M['hist'], service_z=z, trust_stock=trust)
    start, fq = F.next_months(M['forecast'])
    return ok({'plan': plan.reset_index().rename(columns={'index': 'category_en'}), 'backtest': M['backtest'],
               'backtest_total': M['backtest_total'].reset_index(), 'months': sorted({m.strftime('%b %Y') for m in fq.month}, key=lambda x: pd.Timestamp('1 ' + x))})


@app.get('/api/tools/allocation')
@login_required
def tool_allocation():
    _, alloc = F.plans(C, M['forecast'], M['hist'], safety_branch=float(request.args.get('safety', 10)) / 100)
    branches = C['branches'][['branch_id', 'branch_name_ar', 'governorate_ar']]
    br = request.args.get('branch') or alloc.branch_id.min()
    x = alloc[alloc.branch_id == br].sort_values('send_next_month', ascending=False)
    total = alloc.groupby('branch_id')[['send_next_month', 'sent_per_month_FY2026']].sum().reset_index().merge(branches, on='branch_id')
    return ok({'branch': br, 'rows': x, 'branches': branches, 'totals': total, 'saving': M['alloc_saving'], 'mix': M['mix'].reset_index()})


@app.get('/api/tools/discount')
@login_required
def tool_discount():
    d = M['discount']
    price = float(request.args.get('price', 400))
    disc = float(request.args.get('discount', 10))
    max_disc = float(request.args.get('max_discount', 10))
    floor = float(request.args.get('floor_margin', 30))
    cost_ratio = 0.59                                      # cost is ~59% of price for every product (card 01)
    net = price * (1 - disc / 100)
    margin = (net - price * cost_ratio) / net * 100 if net else 0
    if margin < floor or disc > 2 * max_disc:
        verdict = 'Reject'
    elif disc > max_disc:
        verdict = 'Needs approval'
    else:
        verdict = 'Approve'
    stop = float(request.args.get('stop', 75))
    return ok({'net_price': net, 'margin': margin, 'verdict': verdict, 'cost_ratio': cost_ratio,
               'facts': {k: d[k] for k in ['share_lines', 'pieces_with', 'pieces_without', 'margin_with', 'margin_without', 'corr', 'discount_fy26', 'gp_fy26']},
               'bands': A.discount_bands(C).reset_index().rename(columns={'discount_pct': 'band'}), 'gain': d['discount_fy26'] * stop / 100})


@app.get('/api/tools/marketing')
@login_required
def tool_marketing():
    g = M['gov'].copy()
    spend26 = M['marketing'].spend.iloc[-1]
    cut = float(request.args.get('cut', 25))
    holdout = float(request.args.get('holdout', 10))
    budget = spend26 * (1 - cut / 100)
    g['new_budget'] = g.order_share / 100 * budget * (1 - holdout / 100)
    # holdout design: pair governorates with similar orders; one of each pair pauses ads for 4 weeks
    srt = g.sort_values('orders', ascending=False).reset_index()
    pairs = [{'a': srt.governorate_ar[i], 'b': srt.governorate_ar[i + 1], 'orders_a': srt.orders[i], 'orders_b': srt.orders[i + 1]}
             for i in range(2, min(len(srt) - 1, 12), 2)]
    return ok({'gov': g.reset_index(), 'spend26': spend26, 'budget': budget, 'saved': spend26 - budget, 'channels': M['channels'].reset_index(),
               'claimed_x': M['marketing'].claimed.sum() / M['marketing'].real_orders.sum(), 'pairs': pairs,
               'ledger': M['people']['marketing_ledger'], 'campaigns': M['people']['marketing_campaigns']})


@app.get('/api/tools/shipping')
@login_required
def tool_shipping():
    th = float(request.args.get('threshold', 1000))
    n, saved = A.free_shipping_saving(C, th)
    sf = M['shipping']
    return ok({'threshold': th, 'free_below': n, 'saved': saved, 'free_share': sf['free_share'], 'free_by_size': sf['free_by_size'],
               'avg_fee': sf['avg_fee'], 'shipments': sf['shipments_fy']})


@app.get('/api/export/<name>.csv')
@login_required
def export(name):
    if name == 'purchase_plan':
        df = F.plans(C, M['forecast'], M['hist'])[0].reset_index().rename(columns={'index': 'category_en'})
    elif name == 'allocation_plan':
        df = F.plans(C, M['forecast'], M['hist'])[1]
    elif name == 'data_quality':
        df = M['dq']
    elif name == 'actions':
        df = pd.DataFrame(load_state()['actions'])
    elif name == 'winback_test':
        p = A.rfm(C)
        df = p[p.segment == "At Risk (Can't Lose)"][['customer_id', 'last', 'orders', 'spend']].copy()
        df['group'] = np.where(np.random.default_rng(42).random(len(df)) < 0.5, 'Test', 'Control')
    else:
        return jsonify({'error': 'unknown export'}), 404
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return Response('﻿' + buf.getvalue(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename=cottonil_{name}.csv'})


# ---------------------------------------------------------------- action tracker
@app.get('/api/actions')
@login_required
def actions():
    s = load_state()
    return jsonify({'actions': s['actions'], 'log': s.get('log', [])[:30],
                    'owners': [{'username': k, 'name': v['name'], 'name_ar': v['name_ar'], 'role': v['role']} for k, v in load_users().items()]})


@app.post('/api/actions')
@login_required
def add_action():
    body = request.get_json(force=True, silent=True) or {}
    title = str(body.get('title', '')).strip()
    if not title:
        return jsonify({'error': 'title required'}), 400
    with LOCK:
        s = load_state()
        a = {'id': uuid.uuid4().hex[:8], 'title': title[:200], 'owner': str(body.get('owner', session['user'])), 'due': str(body.get('due', ''))[:10],
             'status': 'To do', 'problem': str(body.get('problem', ''))[:10], 'impact': float(body.get('impact') or 0), 'created': str(date.today())}
        s['actions'].append(a)
        log(s, f'added action: {a["title"]}')
        save_state(s)
    return jsonify(a)


@app.put('/api/actions/<aid>')
@login_required
def edit_action(aid):
    body = request.get_json(force=True, silent=True) or {}
    with LOCK:
        s = load_state()
        for a in s['actions']:
            if a['id'] == aid:
                for k_ in ('title', 'owner', 'due', 'status'):
                    if k_ in body:
                        a[k_] = str(body[k_])[:200]
                log(s, f'action "{a["title"]}" → {a["status"]}')
                save_state(s)
                return jsonify(a)
    return jsonify({'error': 'not found'}), 404


@app.delete('/api/actions/<aid>')
@login_required
def delete_action(aid):
    with LOCK:
        s = load_state()
        s['actions'] = [a for a in s['actions'] if a['id'] != aid]
        log(s, f'deleted action {aid}')
        save_state(s)
    return jsonify({'ok': True})


# ---------------------------------------------------------------- data gaps
@app.get('/api/gaps')
@login_required
def gaps():
    s = load_state()
    req = M['requests'].copy()
    req['id'] = [f'R{i + 1:02d}' for i in range(len(req))]
    req['status'] = [s['requests'].get(i, {}).get('status', 'To request') for i in req.id]
    return ok({'readiness': M['readiness'], 'requests': req, 'dq': M['dq']})


@app.post('/api/gaps/<rid>')
@login_required
def update_gap(rid):
    body = request.get_json(force=True, silent=True) or {}
    with LOCK:
        s = load_state()
        if rid in s['requests'] and body.get('status') in ('To request', 'Requested', 'Received'):
            s['requests'][rid]['status'] = body['status']
            log(s, f'data request {rid} → {body["status"]}')
            save_state(s)
            return jsonify({'ok': True})
    return jsonify({'error': 'bad request'}), 400


# ---------------------------------------------------------------- assistant
@app.post('/api/assistant')
@login_required
def assistant():
    body = request.get_json(force=True, silent=True) or {}
    return jsonify(K.answer(str(body.get('q', ''))[:500], M, body.get('lang', 'en')))


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
    load_users()
    port = int(os.environ.get('PORT', 8050))
    print(f'\n  Cottonil Decision Hub →  http://localhost:{port}\n  first login: ceo / {DEFAULT_PASSWORD} (you will be asked to change it)\n')
    app.run(host='127.0.0.1', port=port, debug=False, threaded=True)
