"""
What the manager board says in words: the alerts on the Today page, the month's cycle, and «خيط» – the assistant.
Every sentence is built from the numbers in core/, so it changes when the data changes.
"""
import re

import pandas as pd

from core import forecast as F
from core import manager as MG

CAT_AR = {
    'Socks': 'الشرابات', 'Men tops': 'تيشيرتات رجالي', 'Men boxers': 'بوكسرات رجالي', 'Women tops': 'تيشيرتات حريمي', 'Kids underwear': 'داخلي أطفال',
    'Men underwear': 'داخلي رجالي', 'Women underwear': 'داخلي حريمي', 'Girls underwear': 'داخلي بناتي', 'Women bras': 'برا حريمي',
    'Home textiles': 'مفروشات', 'Accessories': 'إكسسوارات', 'Men bottoms': 'بناطيل رجالي', 'Women bottoms': 'بناطيل حريمي',
    'Women pajamas': 'بيجامات حريمي', 'Boys pajamas': 'بيجامات ولادي', 'Girls pajamas': 'بيجامات بناتي',
}
ROLE_AR = {'Store Manager': 'مدير فرع', 'Cashier': 'كاشير', 'Sales Associate': 'بائع', 'Inventory Clerk': 'أمين مخزن', 'Area Manager': 'مدير منطقة'}
MONTH_AR = {1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس', 9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'}


def _m(v):
    return f'{v / 1e6:,.1f}M' if abs(v) >= 1e6 else f'{v / 1e3:,.0f}K'


def _k(v):
    return f'{v / 1e3:,.0f}K' if abs(v) >= 1e3 else f'{v:,.0f}'


def _ark(v):
    return f'{v / 1e3:,.0f} ألف' if abs(v) >= 1e3 else f'{v:,.0f}'


def _ar_m(v):
    return f'{v / 1e6:,.1f} مليون' if abs(v) >= 1e6 else f'{v / 1e3:,.0f} ألف'


def month_name(ts, ar):
    ts = pd.Timestamp(ts)
    return f'{MONTH_AR[ts.month]} {ts.year}' if ar else ts.strftime('%b %Y')


# ---------------------------------------------------------------- Today: alerts from the data
def alerts(M, s):
    start, fq = F.next_months(M['forecast'])
    nov = fq[fq.month == start].units.sum()
    se, st, d, g, pp = M['season'], M['stock'], M['discount'], M['gov'], M['people']
    br = M['base']['branches']
    dist = MG.distribution(M['base'], M['forecast'])['totals']
    top_gap = br.sort_values('stock_gap', ascending=False).head(3).branch_name_ar.tolist()
    m1, m2 = start.month, (start + pd.DateOffset(months=1)).month
    cairo = g.iloc[0]
    out = [
        {'id': 'season', 'icon': 'calendar', 'level': 'info',
         'en': f"{start.strftime('%B')} and {(start + pd.DateOffset(months=1)).strftime('%B')} are peak months ({se.loc[m1]:+.0f}% and {se.loc[m2]:+.0f}% vs a normal month)",
         'ar': f'{MONTH_AR[m1]} و{MONTH_AR[m2]} من أعلى شهور السنة ({se.loc[m1]:+.0f}% و {se.loc[m2]:+.0f}% عن الشهر العادي)',
         'sub_en': f'Expected demand: {_k(nov)} pieces in {month_name(start, False)}, {_k(fq.units.sum())} for the quarter.',
         'sub_ar': f'الطلب المتوقع: {_ark(nov)} قطعة في {MONTH_AR[m1]}، و {_ark(fq.units.sum())} للربع كله.', 'link': '#/purchase'},
        {'id': 'alloc', 'icon': 'truck', 'level': 'watch',
         'en': f'Branches need ~{_k(dist["send"])} pieces next month; the usual monthly shipment is {_k(dist["old"])}',
         'ar': f'الفروع محتاجة حوالي {_ark(dist["send"])} قطعة الشهر الجاي، والمعتاد إننا بنبعت {_ark(dist["old"])} في الشهر',
         'sub_en': f'≈{dist["trips_old"] - dist["trips_new"]:,.0f} fewer trips and {_m(dist["transport_saved_month"])} EGP transport a month.',
         'sub_ar': f'يعني حوالي {dist["trips_old"] - dist["trips_new"]:,.0f} نقلة أقل و {_ar_m(dist["transport_saved_month"])} جنيه نقل في الشهر.', 'link': '#/distribution'},
        {'id': 'stock', 'icon': 'box', 'level': 'watch',
         'en': f'{st["unaccounted"] / 1e6:.1f}M pieces sent to branches are neither sold nor on the shelf',
         'ar': f'{st["unaccounted"] / 1e6:.1f} مليون قطعة اتبعتت للفروع ومش ظاهرة لا في البيع ولا في المخزون',
         'sub_en': f'Largest gaps: {", ".join(top_gap)}. A physical count in 5 branches tells which record is wrong.',
         'sub_ar': f'أكبر فرق: {"، ".join(top_gap)}. جرد فعلي في 5 فروع هيقول أنهي سجل الغلط.', 'link': '#/branches?sort=gap'},
        {'id': 'discount', 'icon': 'tag', 'level': 'watch',
         'en': f'{d["share_lines"]:.0f}% of sales lines carry a discount, with the same pieces per line ({d["pieces_with"]:.2f} vs {d["pieces_without"]:.2f})',
         'ar': f'{d["share_lines"]:.0f}% من سطور البيع عليها خصم، ونفس عدد القطع في السطر ({d["pieces_with"]:.2f} مقابل {d["pieces_without"]:.2f})',
         'sub_en': f'FY2026 discounts: {_m(d["discount_fy26"])} EGP. Margin {d["margin_without"]:.1f}% without a discount, {d["margin_with"]:.1f}% with.',
         'sub_ar': f'خصومات FY2026: {_ar_m(d["discount_fy26"])} جنيه. الهامش {d["margin_without"]:.1f}% من غير خصم و {d["margin_with"]:.1f}% بالخصم.', 'link': '#/pricing'},
        {'id': 'marketing', 'icon': 'megaphone', 'level': 'info',
         'en': f'{cairo.name}: {cairo.order_share:.0f}% of orders and {cairo.spend_share:.1f}% of marketing spend',
         'ar': f'{cairo.name}: {cairo.order_share:.0f}% من الطلبات و {cairo.spend_share:.1f}% بس من صرف التسويق',
         'sub_en': 'Spend and orders by governorate are unrelated – the monthly budget can follow demand.',
         'sub_ar': 'الصرف والطلبات في المحافظات مالهمش علاقة ببعض – ميزانية الشهر ممكن تمشي مع الطلب.', 'link': '#/marketing'},
        {'id': 'people', 'icon': 'people', 'level': 'info',
         'en': f'{pp["no_manager"]} branches have no store manager and {pp["no_cashier"]} have no cashier in the staff file',
         'ar': f'{pp["no_manager"]} فرع مالهمش مدير فرع و {pp["no_cashier"]} مالهمش كاشير في ملف الموظفين',
         'sub_en': 'Worth confirming with HR before any staffing decision.', 'sub_ar': 'محتاج نتأكد مع الـ HR قبل أي قرار في الموظفين.', 'link': '#/branches?flag=no_manager'},
    ]
    return out


# ---------------------------------------------------------------- Today: the month's cycle
def cycle(M, s):
    month = M['window'].strftime('%Y-%m')
    start, fq = F.next_months(M['forecast'])
    win = f"{start.strftime('%Y-%m')}..{(start + pd.DateOffset(months=2)).strftime('%Y-%m')}"
    checks = s.get('checks', {}).get(month, {})
    pur = next((p for p in s.get('purchase', []) if p.get('window') == win), None)
    dis = next((p for p in s.get('distribution', []) if p.get('month') == month), None)
    mkt = next((p for p in s.get('marketing', []) if p.get('month') == month), None)
    pol = s.get('policy')
    top5 = M['base']['branches'].sort_values('stock_gap', ascending=False).head(5).branch_name_ar.tolist()
    m_en, m_ar = month_name(start, False), MONTH_AR[start.month]
    items = [
        {'id': 'purchase', 'auto': True, 'done': bool(pur), 'when': pur and pur['saved'], 'link': '#/purchase',
         'en': f'Purchase plan for {m_en} – {month_name(start + pd.DateOffset(months=2), False)}', 'ar': f'خطة الشراء من {m_ar} لـ {MONTH_AR[(start + pd.DateOffset(months=2)).month]}',
         'hint_en': f'{_ark(fq.units.sum())} pieces expected', 'hint_ar': f'الطلب المتوقع {_ark(fq.units.sum())} قطعة'},
        {'id': 'distribution', 'auto': True, 'done': bool(dis), 'when': dis and dis['saved'], 'link': '#/distribution',
         'en': f'Distribution plan for {m_en}', 'ar': f'خطة توزيع {m_ar}', 'hint_en': '80 branches, from the nearest warehouse', 'hint_ar': '80 فرع، كل فرع من أقرب مخزن'},
        {'id': 'policy', 'auto': True, 'done': bool(pol), 'when': pol and pol.get('saved'), 'link': '#/pricing',
         'en': 'Discount policy for the season', 'ar': 'سياسة الخصم للموسم', 'hint_en': 'max discount and floor margin', 'hint_ar': 'أقصى خصم وأقل هامش'},
        {'id': 'marketing', 'auto': True, 'done': bool(mkt), 'when': mkt and mkt['saved'], 'link': '#/marketing',
         'en': f'Marketing budget for {m_en}', 'ar': f'ميزانية تسويق {m_ar}', 'hint_en': 'split by demand + holdout test', 'hint_ar': 'متقسمة حسب الطلب + تجربة إيقاف'},
        {'id': 'count', 'auto': False, 'done': bool(checks.get('count')), 'when': None, 'link': '#/branches?sort=gap',
         'en': 'Physical stock count in 5 branches', 'ar': 'جرد فعلي في 5 فروع', 'hint_en': ', '.join(top5), 'hint_ar': '، '.join(top5)},
        {'id': 'report', 'auto': False, 'done': bool(checks.get('report')), 'when': None, 'link': '#/report',
         'en': 'Send the monthly report', 'ar': 'تقرير الشهر', 'hint_en': 'one printable page', 'hint_ar': 'صفحة واحدة للطباعة'},
    ]
    return {'month': month, 'window': win, 'items': items, 'done': sum(i['done'] for i in items)}


# ---------------------------------------------------------------- «خيط» – the assistant
def norm(t):
    t = str(t).lower()
    for a, b in (('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا'), ('ة', 'ه'), ('ى', 'ي'), ('ـ', '')):
        t = t.replace(a, b)
    return t


CAT_WORDS = {
    'Socks': ['socks', 'sock', 'شراب'], 'Men tops': ['men tops', 'تيشيرت رجالي', 'تيشيرتات رجالي'], 'Men boxers': ['boxer', 'بوكسر'],
    'Women tops': ['women tops', 'تيشيرت حريمي', 'تيشيرتات حريمي'], 'Kids underwear': ['kids', 'اطفال'], 'Men underwear': ['men underwear', 'داخلي رجالي'],
    'Women underwear': ['women underwear', 'داخلي حريمي'], 'Girls underwear': ['girls underwear', 'داخلي بناتي'], 'Women bras': ['bra', 'برا ', 'صدري'],
    'Home textiles': ['home', 'مفروشات', 'مفارش'], 'Accessories': ['accessor', 'اكسسوار'], 'Men bottoms': ['men bottoms', 'بناطيل رجالي', 'بنطلون رجالي'],
    'Women bottoms': ['women bottoms', 'بناطيل حريمي', 'بنطلون حريمي'], 'Women pajamas': ['women pajama', 'بيجامات حريمي', 'بيجامه حريمي'],
    'Boys pajamas': ['boys pajama', 'بيجامات ولادي', 'بيجامه ولادي'], 'Girls pajamas': ['girls pajama', 'بيجامات بناتي', 'بيجامه بناتي'],
}
MONTH_WORDS = {11: ['نوفمبر', 'november', 'nov'], 12: ['ديسمبر', 'december', 'dec'], 1: ['يناير', 'january', 'jan']}
TOPICS = [
    ('plan', ['what should', 'first', 'priority', 'نعمل ايه', 'ابدا', 'اولويه', 'الاول', 'المطلوب']),
    ('purchase', ['purchase', 'buy', 'order', 'supplier', 'شراء', 'نشتري', 'اشتري', 'مشتريات', 'مورد', 'امر']),
    ('distribution', ['distribut', 'allocat', 'transfer', 'ship to branch', 'توزيع', 'نبعت', 'تحويل', 'نقل']),
    ('discount', ['discount', 'promo', 'offer', 'price', 'خصم', 'عرض', 'عروض', 'سعر', 'تسعير']),
    ('stock', ['stock', 'inventory', 'missing', 'stock count', 'مخزون', 'جرد', 'عجز', 'ناقص', 'متحسوب']),
    ('marketing', ['marketing', 'campaign', 'ads', 'budget', 'تسويق', 'حمل', 'اعلان', 'ميزاني']),
    ('profit', ['profit', 'margin', 'ربح', 'هامش', 'مكسب']),
    ('sales', ['sales', 'revenue', 'growth', 'مبيعات', 'نمو', 'ايراد', 'بيع']),
    ('forecast', ['forecast', 'predict', 'next', 'demand', 'توقع', 'الجاي', 'الطلب']),
    ('customer', ['customer', 'loyal', 'churn', 'عميل', 'عملاء', 'ولاء']),
    ('people', ['staff', 'employee', 'manager', 'cashier', 'payroll', 'موظف', 'مدير فرع', 'كاشير', 'مرتب']),
    ('branch', ['branch', 'store', 'فرع', 'فروع']),
    ('data', ['data', 'trust', 'quality', 'داتا', 'بيانات', 'ثقه', 'جوده']),
]


def _find_branch(q, br):
    m = re.search(r'br\s*0*(\d{1,3})', q)
    if m:
        bid = f'BR{int(m.group(1)):03d}'
        if bid in set(br.branch_id):
            return bid
    hits = [(len(n), b) for b, n in zip(br.branch_id, br.branch_name_ar) if norm(n) in q]
    return max(hits)[1] if hits else None


def _find_cat(q):
    for cat, words in CAT_WORDS.items():
        if any(norm(w) in q for w in words) or norm(CAT_AR[cat]) in q:
            return cat
    return None


def answer(q, M, s, lang='ar'):
    ar = lang == 'ar'
    t = (lambda en, a: a if ar else en)
    qn = norm(q)
    br = M['base']['branches']
    fc = M['forecast']
    start, fq = F.next_months(fc)

    # 1) a branch
    bid = _find_branch(qn, br)
    if bid:
        r = br.set_index('branch_id').loc[bid]
        nxt = MG.distribution(M['base'], fc)['lines']
        send = nxt[nxt.branch_id == bid].send.sum()
        staff = t('no store manager on file' if not r.has_manager else 'no cashier on file' if not r.has_cashier else 'full roles on file',
                  'مفيش مدير فرع في الملف' if not r.has_manager else 'مفيش كاشير في الملف' if not r.has_cashier else 'الوظايف كاملة في الملف')
        return {'answer': t(f'{r.branch_name_ar} ({bid}, {r.governorate_ar}) sold {_m(r.sales26)} EGP in FY2026 ({r.growth:+.0f}%). It received ×{r.sent_per_sold:.1f} what it sold, '
                            f'and next month it needs {send:,.0f} pieces from {r.dc_name}.',
                            f'{r.branch_name_ar} ({bid}، {r.governorate_ar}) باع بـ {_ar_m(r.sales26)} جنيه في FY2026 ({r.growth:+.0f}%). استلم ×{r.sent_per_sold:.1f} من اللي باعه، '
                            f'والشهر الجاي محتاج {send:,.0f} قطعة من {r.dc_name}.'),
                'facts': [[t('Stock cover', 'المخزون يكفي'), t(f'{r.months_cover:.1f} months', f'{r.months_cover:.1f} شهر')],
                          [t('Pieces not accounted for', 'قطع مش متحسوبة'), f'{r.stock_gap:,.0f}'], [t('Staff', 'الموظفين'), staff]],
                'links': [{'href': f'#/branches/{bid}', 'en': 'Open branch profile', 'ar': 'افتح ملف الفرع'},
                          {'href': f'#/distribution?branch={bid}', 'en': 'Pick list', 'ar': 'قايمة التجهيز'}]}

    # 2) a category
    cat = _find_cat(qn)
    if cat:
        f3 =fq[fq.category_en == cat].groupby('month').units.sum()
        ly = M['hist'][(M['hist'].category_en == cat) & M['hist'].month.isin([m - pd.DateOffset(years=1) for m in f3.index])].units.sum()
        mix = M['mix']
        sold_pct = mix.loc[cat, 'sold_pct'] if cat in mix.index else float('nan')
        sent_pct = mix.loc[cat, 'sent_pct'] if cat in mix.index else float('nan')
        name = CAT_AR[cat] if ar else cat
        return {'answer': t(f'{name}: {f3.sum():,.0f} pieces expected for {month_name(start, False)} – {month_name(f3.index.max(), False)} '
                            f'({(f3.sum() / ly - 1) * 100:+.0f}% vs the same months last year). It is {sold_pct:.0f}% of pieces sold and {sent_pct:.0f}% of pieces shipped.',
                            f'{name}: متوقع {f3.sum():,.0f} قطعة من {MONTH_AR[start.month]} لـ {MONTH_AR[f3.index.max().month]} '
                            f'({(f3.sum() / ly - 1) * 100:+.0f}% عن نفس الشهور السنة اللي فاتت). وهي {sold_pct:.0f}% من القطع المتباعة و {sent_pct:.0f}% من القطع المبعوتة.'),
                'facts': [[month_name(m, ar), f'{v:,.0f}'] for m, v in f3.items()],
                'links': [{'href': '#/purchase', 'en': 'Purchase plan', 'ar': 'خطة الشراء'},
                          {'href': f'#/pricing?category={cat}', 'en': 'Plan a promotion', 'ar': 'خطط لعرض'}]}

    # 3) a governorate
    g = M['gov']
    gov = next((x for x in sorted(g.index, key=len, reverse=True) if norm(x) in qn), None)
    if gov:
        r = g.loc[gov]
        nb = (br.governorate_ar == gov).sum()
        dc = br[br.governorate_ar == gov].dc_name.iloc[0] if nb else '-'
        return {'answer': t(f'{gov}: {nb} branches served from {dc}. {r.order_share:.1f}% of FY2026 orders and {r.spend_share:.1f}% of marketing spend.',
                            f'{gov}: {nb} فرع بيستلموا من {dc}. {r.order_share:.1f}% من طلبات FY2026 و {r.spend_share:.1f}% من صرف التسويق.'),
                'facts': [[t('Orders FY2026', 'طلبات FY2026'), f'{r.orders:,.0f}'], [t('Spend FY2026', 'صرف FY2026'), f'{r.spend:,.0f}']],
                'links': [{'href': '#/marketing', 'en': 'Marketing budget', 'ar': 'ميزانية التسويق'},
                          {'href': f'#/branches?gov={gov}', 'en': 'Its branches', 'ar': 'فروعها'}]}

    # 4) a month of the plan
    mon = next((m for m, words in MONTH_WORDS.items() if any(w in qn for w in words)), None)
    if mon:
        x = fq[fq.month.dt.month == mon]
        if len(x):
            top = x.groupby('category_en').units.sum().sort_values(ascending=False).head(4)
            mts = x.month.iloc[0]
            return {'answer': t(f'{month_name(mts, False)}: about {x.units.sum():,.0f} pieces expected across all channels. Top categories:',
                                f'{month_name(mts, True)}: متوقع حوالي {x.units.sum():,.0f} قطعة في كل القنوات. أكتر فئات:'),
                    'facts': [[CAT_AR[c] if ar else c, f'{v:,.0f}'] for c, v in top.items()],
                    'links': [{'href': f'#/distribution?month={mts.strftime("%Y-%m")}', 'en': 'Distribution for this month', 'ar': 'توزيع الشهر ده'}]}

    # 5) topics
    topic = next((name for name, words in TOPICS if any(norm(w) in qn for w in words)), None)
    fy, d, st, b = M['fy'], M['discount'], M['stock'], M['bridge']
    last = fy.iloc[-1]
    cyc = cycle(M, s)
    left = [i for i in cyc['items'] if not i['done']]
    R = {
        'plan': (f"This month: {', '.join(i['en'] for i in left) or 'everything is done'}.",
                 f"المطلوب الشهر ده: {'، '.join(i['ar'] for i in left) or 'كله اتعمل'}.", [{'href': '#/today', 'en': 'Today', 'ar': 'النهارده'}]),
        'purchase': (f"For {month_name(start, False)} – Jan the forecast needs {_k(fq.units.sum())} pieces; with 95% safety stock we buy about {_k(M['plan_default'].to_buy.sum())}. "
                     f"The usual pattern is ~{M['purchasing'].bought.iloc[-1] / 4e6:.1f}M pieces a quarter.",
                     f"من {MONTH_AR[start.month]} لـ يناير التوقّع محتاج {_ark(fq.units.sum())} قطعة؛ وبمخزون أمان 95% نشتري حوالي {_ark(M['plan_default'].to_buy.sum())}. "
                     f"والمعتاد حوالي {M['purchasing'].bought.iloc[-1] / 4e6:.1f} مليون قطعة في الربع.", [{'href': '#/purchase', 'en': 'Purchase plan', 'ar': 'خطة الشراء'}]),
        'distribution': (f"Branches got ×{M['transfers'].ratio.iloc[-1]:.1f} what they sold in FY2026. Next month each branch gets its own demand + 10%, from the nearest warehouse.",
                         f"الفروع استلمت ×{M['transfers'].ratio.iloc[-1]:.1f} من اللي باعته في FY2026. الشهر الجاي كل فرع ياخد طلبه + 10%، من أقرب مخزن ليه.",
                         [{'href': '#/distribution', 'en': 'Distribution plan', 'ar': 'خطة التوزيع'}]),
        'stock': (f"Recorded stock is {st['stock_units'] / 1e6:.2f}M pieces ({_m(st['stock_value'])} EGP) and {st['unaccounted'] / 1e6:.1f}M pieces sent to branches are not accounted for. "
                  "Until a count confirms the stock, the purchase plan does not subtract it.",
                  f"المخزون المتسجل {st['stock_units'] / 1e6:.2f} مليون قطعة ({_ar_m(st['stock_value'])} جنيه)، و {st['unaccounted'] / 1e6:.1f} مليون قطعة اتبعتت للفروع ومش متحسوبة. "
                  "لحد ما الجرد يأكد المخزون، خطة الشراء مش بتطرحه.", [{'href': '#/branches?sort=gap', 'en': 'Branches by gap', 'ar': 'الفروع حسب الفرق'}]),
        'discount': (f"{d['share_lines']:.0f}% of lines are discounted and pieces per line do not change ({d['pieces_with']:.2f} vs {d['pieces_without']:.2f}). "
                     f"The current policy: max {policy_of(s)['max_discount']:.0f}%, margin never below {policy_of(s)['floor_margin']:.0f}%.",
                     f"{d['share_lines']:.0f}% من السطور عليها خصم وعدد القطع مش بيتغير ({d['pieces_with']:.2f} مقابل {d['pieces_without']:.2f}). "
                     f"السياسة الحالية: أقصى خصم {policy_of(s)['max_discount']:.0f}%، والهامش ميقلش عن {policy_of(s)['floor_margin']:.0f}%.",
                     [{'href': '#/pricing', 'en': 'Pricing', 'ar': 'التسعير والخصم'}]),
        'marketing': (f"FY2026 spend was {_m(M['marketing'].spend.iloc[-1])} EGP; campaigns claim ×{M['marketing'].claimed.sum() / M['marketing'].real_orders.sum():.0f} the real orders. "
                      "The board splits the monthly budget by orders and pauses ads in matched governorates to measure the real effect.",
                      f"صرف FY2026 كان {_ar_m(M['marketing'].spend.iloc[-1])} جنيه؛ والحملات بتنسب لنفسها ×{M['marketing'].claimed.sum() / M['marketing'].real_orders.sum():.0f} الطلبات الحقيقية. "
                      "اللوحة بتقسم ميزانية الشهر حسب الطلبات وبتوقف الإعلان في محافظات شبه بعض عشان نقيس الأثر الحقيقي.",
                      [{'href': '#/marketing', 'en': 'Marketing budget', 'ar': 'ميزانية التسويق'}]),
        'profit': (f"FY2026 gross profit {_m(last.gross_profit)} EGP, margin {last.margin_pct:.1f}%. Discounts, marketing and allocation together can add about {_m(b['new'] - b['base'])} a year.",
                   f"إجمالي ربح FY2026 {_ar_m(last.gross_profit)} جنيه، والهامش {last.margin_pct:.1f}%. الخصم والتسويق والتوزيع مع بعض ممكن يزوّدوا حوالي {_ar_m(b['new'] - b['base'])} في السنة.",
                   [{'href': '#/report', 'en': 'Monthly report', 'ar': 'تقرير الشهر'}]),
        'sales': (f"FY2026 net sales {_m(last.net_sales)} EGP ({last.net_sales_g:+.0f}%). Pieces grew {last.units_g:+.1f}%; the rest is price ({last.price_per_unit_g:+.0f}% per piece).",
                  f"صافي مبيعات FY2026 {_ar_m(last.net_sales)} جنيه ({last.net_sales_g:+.0f}%). القطع زادت {last.units_g:+.1f}%؛ والباقي أسعار ({last.price_per_unit_g:+.0f}% في سعر القطعة).",
                  [{'href': '#/today', 'en': 'Today', 'ar': 'النهارده'}]),
        'forecast': (f"The forecast was tested on 6 months it never saw: error {M['backtest']['wape_model']}% vs {M['backtest']['wape_naive']}% for 'same month last year'. "
                     f"Next 3 months: {_k(fq.units.sum())} pieces.",
                     f"التوقّع اتختبر على 6 شهور ماشافهاش: الخطأ {M['backtest']['wape_model']}% مقابل {M['backtest']['wape_naive']}% لطريقة 'زي السنة اللي فاتت'. "
                     f"الـ 3 شهور الجاية: {_ark(fq.units.sum())} قطعة.", [{'href': '#/purchase', 'en': 'Purchase plan', 'ar': 'خطة الشراء'}]),
        'customer': (f"{M['customers']['guest_share']:.0f}% of orders have no customer attached, and a returning customer appears in {M['customers']['loyal_branches']:.1f} branches – "
                     "so customer numbers are kept out of decisions until the phone number is used as a loyalty ID.",
                     f"{M['customers']['guest_share']:.0f}% من الطلبات من غير عميل، والعميل اللي بيرجع بيظهر في {M['customers']['loyal_branches']:.1f} فرع – "
                     "عشان كده أرقام العملاء برا القرارات لحد ما رقم الموبايل يبقى كود الولاء.", []),
        'people': (f"{M['people']['no_manager']} branches have no store manager and {M['people']['no_cashier']} no cashier on file; payroll covers at most {M['people']['paid_per_month'].max()} of {M['people']['employees']} people.",
                   f"{M['people']['no_manager']} فرع من غير مدير فرع و {M['people']['no_cashier']} من غير كاشير في الملف؛ والمرتبات بتغطي {M['people']['paid_per_month'].max()} من {M['people']['employees']} بالكتير.",
                   [{'href': '#/branches?flag=no_manager', 'en': 'Branches without a manager', 'ar': 'فروع من غير مدير'}]),
        'branch': ("All 80 branches sell within about ±5% of each other, so the board follows them by stock, shipments and staff rather than by ranking. Ask me about any branch by name.",
                   "الـ 80 فرع بيبيعوا قريب من بعض (حوالي ±5%)، فاللوحة بتتابعهم بالمخزون والتحويلات والموظفين مش بالترتيب. اسألني عن أي فرع باسمه.",
                   [{'href': '#/branches', 'en': 'Branches', 'ar': 'الفروع'}]),
        'data': ("Sales, prices, costs, transfers and stock are reliable enough to plan with. Delivery times, return reasons and payroll look random, so the board does not use them.",
                 "المبيعات والأسعار والتكلفة والتحويلات والمخزون ينفع نخطط بيهم. مدة التوصيل وأسباب المرتجع والمرتبات شكلها عشوائي، فاللوحة مش بتستخدمهم.", []),
    }
    if topic is None:
        return {'answer': t('I answer from Cottonil’s numbers. Ask about a branch (e.g. “Zamalek”), a category (“socks”), a governorate, a month (“December”), '
                            'or purchasing, distribution, stock, discounts, marketing, sales, profit.',
                            'أنا بجاوب من أرقام قطنيل. اسألني عن فرع (مثلاً "الزمالك")، فئة ("الشرابات")، محافظة، شهر ("ديسمبر")، '
                            'أو الشراء، التوزيع، المخزون، الخصم، التسويق، المبيعات، الربح.'), 'links': [], 'facts': []}
    en, a, links = R[topic]
    return {'answer': a if ar else en, 'links': links, 'facts': []}


def policy_of(s):
    return s.get('policy') or {'max_discount': 10, 'floor_margin': 30}
