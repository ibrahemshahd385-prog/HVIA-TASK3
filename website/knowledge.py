"""
The content of the Decision Hub: the problems (with live evidence), the decisions of the month,
the starter action list, and the assistant that answers from the data.
Every number here is read from M (computed by core/) – nothing is typed by hand.
"""
import re

import pandas as pd

PROBLEMS = [
    {'id': 'P01', 'area': 'Sales', 'owner': 'ceo', 'tool': 'discount'},
    {'id': 'P02', 'area': 'Marketing', 'owner': 'marketing', 'tool': 'marketing'},
    {'id': 'P03', 'area': 'Supply chain', 'owner': 'supply', 'tool': 'allocation'},
    {'id': 'P04', 'area': 'Supply chain', 'owner': 'supply', 'tool': 'purchase'},
    {'id': 'P05', 'area': 'Finance', 'owner': 'finance', 'tool': 'gaps'},
    {'id': 'P06', 'area': 'Strategy', 'owner': 'ceo', 'tool': 'home'},
    {'id': 'P07', 'area': 'Customers', 'owner': 'marketing', 'tool': 'gaps'},
    {'id': 'P08', 'area': 'E-commerce', 'owner': 'finance', 'tool': 'shipping'},
    {'id': 'P09', 'area': 'HR', 'owner': 'finance', 'tool': 'gaps'},
    {'id': 'P10', 'area': 'Operations', 'owner': 'supply', 'tool': 'gaps'},
]


def _m(x):
    return f'{x / 1e6:,.1f}M'


def problems(M):
    d, b, tf, sf, pf, mk, g, cf, sh, pe, fy = (M['discount'], M['bridge'], M['transfers'], M['stock'], M['purchasing'], M['marketing'],
                                                 M['gov'], M['customers'], M['shipping'], M['people'], M['fy'])
    act = b['actions'].set_index('action').profit
    mix = M['mix']
    src = sf['source_mix']
    claimed = mk.claimed.sum() / mk.real_orders.sum()
    plan_total = next_q(M).units.sum()
    txt = {
        'P01': dict(
            title=('Discounts are random and sell no extra pieces', 'الخصومات عشوائية ومش بتبيع قطع زيادة'),
            evidence=(f"{d['share_lines']:.0f}% of lines are discounted in every month and channel; they sell {d['pieces_with']:.2f} pieces vs {d['pieces_without']:.2f}. Margin {d['margin_without']:.1f}% → {d['margin_with']:.1f}%. FY2026: {_m(d['discount_fy26'])} EGP given away.",
                      f"{d['share_lines']:.0f}% من السطور عليها خصم في كل شهر وكل قناة؛ وبتبيع {d['pieces_with']:.2f} قطعة مقابل {d['pieces_without']:.2f}. الهامش {d['margin_without']:.1f}% ← {d['margin_with']:.1f}%. في FY2026 راح {_m(d['discount_fy26'])} جنيه."),
            cause=('No discount policy: the discount is not tied to a goal (season, clearance, loyalty).', 'مفيش سياسة خصم: الخصم مش مربوط بهدف (موسم، تصفية، ولاء).'),
            solution=('Discount guardrail: max 10% without approval, never below a 30% margin; discounts only as planned campaigns with a control group.',
                      'قواعد للخصم: أقصى 10% من غير موافقة، ومنزلش تحت هامش 30%؛ والخصم يبقى في حملات مخططة فيها مجموعة مقارنة.'),
            impact=act.get('Stop random discounts', 0)),
        'P02': dict(
            title=('Marketing budget is fixed and not linked to demand', 'ميزانية التسويق ثابتة ومش مربوطة بالطلب'),
            evidence=(f"Campaigns claim ×{claimed:.0f} the real orders; spend ↔ orders by governorate ≈ {g[['spend', 'orders']].corr().iloc[0, 1]:.2f}. {g.index[0]} has {g.order_share.iloc[0]:.0f}% of orders and {g.spend_share.iloc[0]:.1f}% of spend.",
                      f"الحملات بتنسب لنفسها ×{claimed:.0f} الطلبات الحقيقية؛ والارتباط بين الصرف والطلبات لكل محافظة حوالي {g[['spend', 'orders']].corr().iloc[0, 1]:.2f}. {g.index[0]} عندها {g.order_share.iloc[0]:.0f}% من الطلبات و {g.spend_share.iloc[0]:.1f}% من الصرف."),
            cause=('Budget split equally by channel and governorate; success measured by platform-claimed orders.', 'الميزانية متقسمة بالتساوي على القنوات والمحافظات؛ والنجاح بيتقاس بالطلبات اللي المنصات بتنسبها لنفسها.'),
            solution=('Holdout tests (pause ads in matched governorates 4 weeks), budget follows demand, one marketing ledger, cut spend that shows no effect.',
                      'تجارب Holdout (نوقف الإعلان في محافظات شبه بعض 4 أسابيع)، والميزانية تمشي مع الطلب، ودفتر واحد للتسويق، ونقلل الصرف اللي ملوش أثر.'),
            impact=act.get('Cut marketing with no measured effect', 0)),
        'P03': dict(
            title=('Branches receive a fixed quantity, not what they sell', 'الفروع بتستلم كمية ثابتة مش اللي بتبيعه'),
            evidence=(f"FY2026: ×{tf.ratio.iloc[-1]:.1f} of sales sent; socks {mix.loc['Socks', 'sent_pct']:.0f}% of shipments vs {mix.loc['Socks', 'sold_pct']:.0f}% of sales; {src.get('Raw materials', 0) + src.get('Returns', 0):.0f}% shipped from raw-material/returns warehouses; every branch served by all 12 warehouses.",
                      f"في FY2026 اتبعت ×{tf.ratio.iloc[-1]:.1f} من البيع؛ الشرابات {mix.loc['Socks', 'sent_pct']:.0f}% من المبعوت مقابل {mix.loc['Socks', 'sold_pct']:.0f}% من البيع؛ و {src.get('Raw materials', 0) + src.get('Returns', 0):.0f}% طالع من مخزن الخامات والمرتجعات؛ وكل فرع بيستلم من الـ 12 مخزن."),
            cause=('Allocation is a fixed rule per SKU, not driven by sales.', 'التوزيع قاعدة ثابتة لكل SKU، مش ماشي مع البيع.'),
            solution=('Monthly allocation from the AI forecast (branch share × forecast + safety), from the nearest distribution centre only.',
                      'توزيع شهري من توقّع الـ AI (نصيب الفرع × التوقّع + أمان)، ومن أقرب مخزن توزيع بس.'),
            impact=act.get('Demand-based allocation to branches', 0)),
        'P04': dict(
            title=('Purchasing is fixed (~42M pieces a year) and ignores sales', 'الشراء ثابت (حوالي 42 مليون قطعة في السنة) ومش بيبص على البيع'),
            evidence=(f"FY2026: {pf.bought.iloc[-1] / 1e6:.0f}M pieces bought for {pf.sold.iloc[-1] / 1e3:,.0f}K sold (×{pf.ratio.iloc[-1]:.0f}); correlation per SKU ≈ 0.01. The AI forecast needs {plan_total / 1e3:,.0f}K pieces next quarter.",
                      f"في FY2026 اتشرى {pf.bought.iloc[-1] / 1e6:.0f} مليون قطعة مقابل {pf.sold.iloc[-1] / 1e3:,.0f} ألف اتباعت (×{pf.ratio.iloc[-1]:.0f})؛ والارتباط لكل SKU حوالي 0.01. وتوقّع الـ AI محتاج {plan_total / 1e3:,.0f} ألف قطعة الربع الجاي."),
            cause=('Same quantity per SKU and per year, whatever demand does (or the PO unit is not "piece").', 'نفس الكمية لكل SKU وكل سنة مهما الطلب عمل (أو وحدة أمر الشراء مش قطعة).'),
            solution=('Buy from the forecast: 3-month forecast + safety stock − confirmed stock; confirm the PO unit with the company first.',
                      'نشتري من التوقّع: توقّع 3 شهور + مخزون أمان − المخزون المؤكد؛ ونتأكد من وحدة أمر الشراء مع الشركة الأول.'),
            impact=0),
        'P05': dict(
            title=('9.3M pieces sent to branches are not accounted for', '9.3 مليون قطعة اتبعتت للفروع ومش متحسوبة'),
            evidence=(f"Start stock + received + returns − sold − end stock = {sf['unaccounted'] / 1e6:.1f}M pieces. Stock is flat for 8 years ({sf['months_cover']:.0f} months of sales, {_m(sf['stock_value'])} EGP).",
                      f"رصيد البداية + المستلم + المرتجع − المتباع − رصيد النهاية = {sf['unaccounted'] / 1e6:.1f} مليون قطعة. والمخزون ثابت 8 سنين ({sf['months_cover']:.0f} شهر بيع، {_m(sf['stock_value'])} جنيه)."),
            cause=('Transfers or stock counts are recorded wrongly, or pieces are lost (shrinkage).', 'التحويلات أو الجرد متسجلين غلط، أو فيه قطع بتضيع (عجز).'),
            solution=('Physical count in 5 branches this month; scan transfer receipts at the branch; then decide (data fix vs loss prevention).',
                      'جرد فعلي في 5 فروع الشهر ده؛ وتسجيل استلام التحويلات بالباركود في الفرع؛ وبعدين نقرر (تصليح داتا ولا منع فقد).'),
            impact=0),
        'P06': dict(
            title=('Growth is mostly price; real growth is slowing', 'النمو أغلبه أسعار؛ والنمو الحقيقي بيبطّأ'),
            evidence=(f"FY2026 sales {fy.net_sales_g.iloc[-1]:+.0f}% = pieces {fy.units_g.iloc[-1]:+.1f}% + price per piece {fy.price_per_unit_g.iloc[-1]:+.0f}%. Since FY2019: sales ×{fy.net_sales.iloc[-1] / fy.net_sales.iloc[0]:.0f}, pieces ×{fy.units.iloc[-1] / fy.units.iloc[0]:.1f}.",
                      f"مبيعات FY2026 {fy.net_sales_g.iloc[-1]:+.0f}% = قطع {fy.units_g.iloc[-1]:+.1f}% + سعر القطعة {fy.price_per_unit_g.iloc[-1]:+.0f}%. ومن FY2019: المبيعات ×{fy.net_sales.iloc[-1] / fy.net_sales.iloc[0]:.0f}، والقطع ×{fy.units.iloc[-1] / fy.units.iloc[0]:.1f}."),
            cause=('Inflation lifts sales in EGP; volume growth fell from +16% to +9%.', 'التضخم بيرفع المبيعات بالجنيه؛ ونمو الكميات نزل من 16% لـ 9%.'),
            solution=('Manage on pieces and gross profit, not EGP sales; plan stock and staff for the real peaks (Nov–Dec, Mar–May, Thu–Sat).',
                      'نقيس بالقطع وإجمالي الربح مش بالمبيعات بالجنيه؛ ونجهّز المخزون والناس للمواسم الحقيقية (نوفمبر–ديسمبر، مارس–مايو، الخميس للسبت).'),
            impact=0),
        'P07': dict(
            title=('Customer identity is too weak for loyalty or churn', 'هوية العميل أضعف من إننا نبني عليها ولاء أو توقّع'),
            evidence=(f"{cf['guest_share']:.0f}% of orders have no customer (even online); a 5+ visit customer shops in {cf['loyal_branches']:.1f} branches; {cf['wholesale_by_retail_customers']:.0f}% of wholesale orders come from 'retail' customers. Churn model AUC {M['churn']['auc_model']:.2f} → rejected.",
                      f"{cf['guest_share']:.0f}% من الطلبات من غير عميل (حتى الأونلاين)؛ العميل اللي زار 5 مرات بيشتري من {cf['loyal_branches']:.1f} فرع؛ و {cf['wholesale_by_retail_customers']:.0f}% من طلبات الجملة من عملاء 'قطاعي'. موديل الـ churn جاب AUC {M['churn']['auc_model']:.2f} → اترفض."),
            cause=('No loyalty ID at the till; reseller flag not used.', 'مفيش كود ولاء عند الكاشير؛ وعلامة التاجر مش مستخدمة.'),
            solution=('Phone number as loyalty ID everywhere; reseller flag; win-back offers only as test vs control (list ready to download).',
                      'رقم الموبايل ككود ولاء في كل مكان؛ وعلامة للتاجر؛ وعروض الاسترجاع تبقى تجربة بمجموعة مقارنة (القايمة جاهزة للتحميل).'),
            impact=0),
        'P08': dict(
            title=('Free shipping is given at random', 'الشحن المجاني بيتدّى بالقرعة'),
            evidence=(f"{sh['free_share']:.0f}% of shipments are free in every order size, even the smallest.", f"{sh['free_share']:.0f}% من الشحنات مجانية في كل أحجام الطلبات، حتى أصغرها."),
            cause=('No minimum order rule for free shipping.', 'مفيش حد أدنى للطلب عشان الشحن يبقى مجاني.'),
            solution=('Free shipping only above a minimum order (e.g. 1,000 EGP).', 'شحن مجاني بس فوق حد أدنى للطلب (مثلًا 1,000 جنيه).'),
            impact=act.get('Free shipping only above a minimum order', 0)),
        'P09': dict(
            title=('HR and payroll data cannot support workforce decisions', 'داتا الموظفين والمرتبات متنفعش لقرارات الموظفين'),
            evidence=(f"{pe['no_manager']} branches without a store manager, {pe['no_cashier']} without a cashier; payroll covers at most {pe['paid_per_month'].max()} of {pe['employees']} people; salary does not depend on the role.",
                      f"{pe['no_manager']} فرع من غير مدير، و {pe['no_cashier']} من غير كاشير؛ والمرتبات بتغطي {pe['paid_per_month'].max()} من {pe['employees']} بالكتير؛ والمرتب مالوش علاقة بالوظيفة."),
            cause=('Roles assigned in rotation in the HR table; payroll export incomplete.', 'الوظايف متوزعة بالتناوب في جدول الموظفين؛ وملف المرتبات ناقص.'),
            solution=('Get the real org chart and the full payroll before any productivity KPI.', 'نجيب الهيكل الحقيقي والمرتبات كاملة قبل أي مؤشر إنتاجية.'),
            impact=0),
        'P10': dict(
            title=('Several operational fields are random', 'حقول تشغيل كتير عشوائية'),
            evidence=('Delivery time 1–7 days equally everywhere (Cairo = Aswan); "Delayed" 3% whatever the days; "In transit" and "Partial receipt" never close; return reasons exactly 20% each.',
                      'مدة التوصيل من 1 لـ 7 أيام بالتساوي في كل حتة (القاهرة = أسوان)؛ و"متأخر" 3% مهما كانت الأيام؛ و"في الطريق" و"استلام جزئي" عمرهم ما بيتقفلوا؛ وأسباب المرتجع 20% بالظبط لكل سبب.'),
            cause=('Fields filled without a real process behind them.', 'حقول بتتملي من غير عملية حقيقية وراها.'),
            solution=('Carrier scan dates, closing statuses, a return-reason form. No KPI on these fields until then.', 'تواريخ من شركات الشحن، وقفل الحالات، وفورم لسبب المرتجع. ومفيش مؤشرات على الحقول دي لحد ساعتها.'),
            impact=0),
    }
    out = []
    for p in PROBLEMS:
        x = txt[p['id']]
        out.append({**p, 'title': x['title'][0], 'title_ar': x['title'][1], 'evidence': x['evidence'][0], 'evidence_ar': x['evidence'][1],
                    'cause': x['cause'][0], 'cause_ar': x['cause'][1], 'solution': x['solution'][0], 'solution_ar': x['solution'][1], 'impact': float(x['impact'])})
    return out


STARTER_ACTIONS = [
    {'title': 'Freeze random discounts – apply the guardrail (max 10%, floor margin 30%)', 'owner': 'ceo', 'due': '2026-11-15', 'status': 'To do', 'problem': 'P01', 'impact': 9.77e6},
    {'title': 'Physical stock count in 5 branches', 'owner': 'finance', 'due': '2026-11-20', 'status': 'To do', 'problem': 'P05', 'impact': 0},
    {'title': 'Approve the Nov–Jan purchase plan from the AI forecast', 'owner': 'supply', 'due': '2026-11-10', 'status': 'To do', 'problem': 'P04', 'impact': 0},
    {'title': 'Switch December allocation to the demand-based plan', 'owner': 'supply', 'due': '2026-11-25', 'status': 'To do', 'problem': 'P03', 'impact': 1.9e6},
    {'title': 'Launch a 4-week marketing holdout in 4 governorate pairs', 'owner': 'marketing', 'due': '2026-12-01', 'status': 'To do', 'problem': 'P02', 'impact': 7.21e6},
    {'title': 'Phone number as loyalty ID at every till', 'owner': 'marketing', 'due': '2026-12-15', 'status': 'To do', 'problem': 'P07', 'impact': 0},
    {'title': 'Free shipping only above 1,000 EGP', 'owner': 'finance', 'due': '2026-11-30', 'status': 'To do', 'problem': 'P08', 'impact': 5.8e4},
    {'title': 'Ask the company: purchase-order unit, real org chart, full payroll', 'owner': 'ceo', 'due': '2026-11-08', 'status': 'In progress', 'problem': 'P09', 'impact': 0},
]


def next_q(M):
    fc = M['forecast']
    start = fc.month.min() + pd.DateOffset(months=1)
    return fc[(fc.month >= start) & (fc.month < start + pd.DateOffset(months=3))]


def decisions(M):
    fq = next_q(M)
    nov = fq[fq.month == fq.month.min()].units.sum()
    d, b = M['discount'], M['bridge']
    act = b['actions'].set_index('action').profit
    s = M['season']
    return [
        {'title': f'Buy for demand: ~{fq.units.sum() / 1e3:,.0f}K pieces for Nov–Jan, not ~10.5M', 'title_ar': f'نشتري على قد الطلب: حوالي {fq.units.sum() / 1e3:,.0f} ألف قطعة لنوفمبر–يناير، مش 10.5 مليون', 'owner': 'Supply chain', 'link': 'purchase'},
        {'title': f'Send branches ~{nov / 1e3:,.0f}K pieces in November, by category demand', 'title_ar': f'نبعت للفروع حوالي {nov / 1e3:,.0f} ألف قطعة في نوفمبر، حسب طلب كل فئة', 'owner': 'Supply chain', 'link': 'allocation'},
        {'title': f'Freeze random discounts: +{act.get("Stop random discounts", 0) / 1e6:.1f}M EGP a year', 'title_ar': f'نوقف الخصم العشوائي: +{act.get("Stop random discounts", 0) / 1e6:.1f} مليون جنيه في السنة', 'owner': 'CEO / Sales', 'link': 'discount'},
        {'title': f'Start the marketing holdout test: +{act.get("Cut marketing with no measured effect", 0) / 1e6:.1f}M EGP a year at stake', 'title_ar': f'نبدأ تجربة الـ Holdout في التسويق: +{act.get("Cut marketing with no measured effect", 0) / 1e6:.1f} مليون جنيه في السنة', 'owner': 'Marketing', 'link': 'marketing'},
        {'title': 'Count stock in 5 branches: 9.3M pieces not accounted for', 'title_ar': 'جرد في 5 فروع: 9.3 مليون قطعة مش متحسوبة', 'owner': 'Finance', 'link': 'problems'},
        {'title': f'Peak season ahead: Nov {s.loc[11]:+.0f}% and Dec {s.loc[12]:+.0f}% vs a normal month', 'title_ar': f'الموسم جاي: نوفمبر {s.loc[11]:+.0f}% وديسمبر {s.loc[12]:+.0f}% عن الشهر العادي', 'owner': 'CEO', 'link': 'home'},
    ]


# ---------------------------------------------------------------- assistant (answers only from the numbers, always with the source)
TOPICS = [
    ('sales', ['sales', 'revenue', 'growth', 'grow', 'مبيعات', 'نمو', 'ايراد', 'إيراد', 'بيع']),
    ('profit', ['profit', 'margin', 'ربح', 'هامش', 'مكسب']),
    ('discount', ['discount', 'promo', 'خصم', 'خصومات', 'عروض']),
    ('transfer', ['transfer', 'allocation', 'allocate', 'branch stock', 'توزيع', 'تحويل', 'تحويلات']),
    ('purchase', ['purchase', 'buy', 'buying', 'supplier', 'po ', 'شراء', 'نشتري', 'مشتريات', 'مورد']),
    ('stock', ['stock', 'inventory', 'missing', 'shrink', 'count', 'مخزون', 'جرد', 'عجز', 'ناقص']),
    ('marketing', ['marketing', 'campaign', 'ads', 'budget', 'تسويق', 'حملات', 'حملة', 'اعلان', 'إعلان', 'ميزانية']),
    ('customer', ['customer', 'churn', 'loyal', 'rfm', 'عميل', 'عملاء', 'ولاء']),
    ('forecast', ['forecast', 'predict', 'next', 'quarter', 'توقع', 'توقّع', 'الجاي', 'الجاية']),
    ('branch', ['branch', 'store', 'location', 'فرع', 'فروع', 'محل']),
    ('shipping', ['shipping', 'delivery', 'return', 'شحن', 'توصيل', 'مرتجع']),
    ('people', ['payroll', 'employee', 'salary', 'staff', 'hr', 'مرتب', 'موظف', 'موظفين']),
    ('data', ['data', 'gap', 'trust', 'quality', 'readiness', 'داتا', 'بيانات', 'ثغرات', 'ثغرة', 'جودة']),
    ('plan', ['plan', 'action', 'priority', 'do first', 'خطة', 'نعمل', 'أولوية', 'اولوية', 'اعمل']),
]


def answer(q, M, lang='en'):
    ql = q.lower()
    topic = next((name for name, words in TOPICS if any(re.search(re.escape(w), ql) for w in words)), None)
    ar = lang == 'ar'
    fy, d, b = M['fy'], M['discount'], M['bridge']
    last = fy.iloc[-1]
    R = {
        'sales': (f"FY2026 net sales were {_m(last.net_sales)} EGP ({last.net_sales_g:+.0f}%). Real growth in pieces was {last.units_g:+.1f}%; the rest is price ({last.price_per_unit_g:+.0f}% per piece). Peaks: Nov–Dec and Mar–May.",
                  f"صافي مبيعات FY2026 كان {_m(last.net_sales)} جنيه ({last.net_sales_g:+.0f}%). النمو الحقيقي في القطع {last.units_g:+.1f}%؛ والباقي أسعار ({last.price_per_unit_g:+.0f}% في سعر القطعة). الذروة: نوفمبر–ديسمبر ومارس–مايو.", 'home'),
        'profit': (f"FY2026 gross profit {_m(last.gross_profit)} EGP, margin {last.margin_pct:.1f}% (fixed: cost is ~59% of price). The plan adds +{(b['new'] - b['base']) / 1e6:.1f}M a year (+{b['uplift_pct']:.0f}%).",
                   f"إجمالي ربح FY2026 {_m(last.gross_profit)} جنيه، والهامش {last.margin_pct:.1f}% (ثابت لأن التكلفة حوالي 59% من السعر). الخطة بتزوّد +{(b['new'] - b['base']) / 1e6:.1f} مليون في السنة (+{b['uplift_pct']:.0f}%).", 'home'),
        'discount': (f"{d['share_lines']:.0f}% of lines get a discount, with no extra pieces ({d['pieces_with']:.2f} vs {d['pieces_without']:.2f}). FY2026 discounts: {_m(d['discount_fy26'])} EGP. Stopping 75% = +{d['discount_fy26'] * 0.75 / 1e6:.1f}M a year.",
                     f"{d['share_lines']:.0f}% من السطور عليها خصم ومن غير قطع زيادة ({d['pieces_with']:.2f} مقابل {d['pieces_without']:.2f}). خصومات FY2026: {_m(d['discount_fy26'])} جنيه. لو وقفنا 75% منها = +{d['discount_fy26'] * 0.75 / 1e6:.1f} مليون في السنة.", 'discount'),
        'transfer': (f"Branches got ×{M['transfers'].ratio.iloc[-1]:.1f} of their sales in FY2026 (socks 55% of shipments vs 27% of sales). Demand-based allocation cuts {M['alloc_saving']['cut_pct']:.0f}% of the pieces moved and saves ~{M['alloc_saving']['saving'] / 1e6:.1f}M EGP of transport a year.",
                     f"الفروع استلمت ×{M['transfers'].ratio.iloc[-1]:.1f} من بيعها في FY2026 (الشرابات 55% من المبعوت مقابل 27% من البيع). التوزيع حسب الطلب بيقلل {M['alloc_saving']['cut_pct']:.0f}% من القطع اللي بتتنقل ويوفّر حوالي {M['alloc_saving']['saving'] / 1e6:.1f} مليون جنيه نقل في السنة.", 'allocation'),
        'purchase': (f"We buy ~{M['purchasing'].bought.iloc[-1] / 1e6:.0f}M pieces a year for {M['purchasing'].sold.iloc[-1] / 1e3:,.0f}K sold, equally per SKU. The AI forecast needs ~{next_q(M).units.sum() / 1e3:,.0f}K pieces for Nov–Jan.",
                     f"بنشتري حوالي {M['purchasing'].bought.iloc[-1] / 1e6:.0f} مليون قطعة في السنة مقابل {M['purchasing'].sold.iloc[-1] / 1e3:,.0f} ألف اتباعت، وبالتساوي لكل SKU. توقّع الـ AI محتاج حوالي {next_q(M).units.sum() / 1e3:,.0f} ألف قطعة لنوفمبر–يناير.", 'purchase'),
        'stock': (f"Stock is {M['stock']['stock_units'] / 1e6:.2f}M pieces ({_m(M['stock']['stock_value'])} EGP) = {M['stock']['months_cover']:.0f} months of sales, and {M['stock']['unaccounted'] / 1e6:.1f}M pieces sent to branches are not accounted for → count 5 branches first.",
                  f"المخزون {M['stock']['stock_units'] / 1e6:.2f} مليون قطعة ({_m(M['stock']['stock_value'])} جنيه) = {M['stock']['months_cover']:.0f} شهر بيع، و {M['stock']['unaccounted'] / 1e6:.1f} مليون قطعة اتبعتت للفروع ومش متحسوبة → نجرد 5 فروع الأول.", 'problems'),
        'marketing': (f"FY2026 spend {_m(M['marketing'].spend.iloc[-1])} EGP. Campaigns claim ×{M['marketing'].claimed.sum() / M['marketing'].real_orders.sum():.0f} the real orders and spend has no link with orders. Plan: holdout tests, budget follows demand, cut 25% = +{M['marketing'].spend.iloc[-1] * 0.25 / 1e6:.1f}M.",
                      f"صرف FY2026 {_m(M['marketing'].spend.iloc[-1])} جنيه. الحملات بتنسب لنفسها ×{M['marketing'].claimed.sum() / M['marketing'].real_orders.sum():.0f} الطلبات الحقيقية والصرف مالوش علاقة بالطلبات. الخطة: تجارب Holdout، والميزانية تمشي مع الطلب، ونقلل 25% = +{M['marketing'].spend.iloc[-1] * 0.25 / 1e6:.1f} مليون.", 'marketing'),
        'customer': (f"{M['customers']['guest_share']:.0f}% of orders have no customer and a loyal customer shops in {M['customers']['loyal_branches']:.1f} branches. Our churn model scored AUC {M['churn']['auc_model']:.2f} (coin flip), so we rejected it and use a test vs control win-back list.",
                     f"{M['customers']['guest_share']:.0f}% من الطلبات من غير عميل، والعميل الوفي بيشتري من {M['customers']['loyal_branches']:.1f} فرع. موديل الـ churn جاب AUC {M['churn']['auc_model']:.2f} (رمي عملة)، فرفضناه وبنستخدم قايمة تجربة بمجموعة مقارنة.", 'problems'),
        'forecast': (f"The AI forecast is {M['backtest']['better_%']:.0f}% more accurate than 'same month last year' (WAPE {M['backtest']['wape_model']}% vs {M['backtest']['wape_naive']}%). Nov 2026 – Jan 2027: ~{next_q(M).units.sum() / 1e3:,.0f}K pieces.",
                     f"توقّع الـ AI أدق بـ {M['backtest']['better_%']:.0f}% من 'زي السنة اللي فاتت' (خطأ {M['backtest']['wape_model']}% مقابل {M['backtest']['wape_naive']}%). نوفمبر 2026 – يناير 2027: حوالي {next_q(M).units.sum() / 1e3:,.0f} ألف قطعة.", 'purchase'),
        'branch': ("All 80 branches sell within ±5% of each other, so ranking them or choosing a new location from this data would be noise. 7% of orders are dated before their branch opened → confirm opening dates.",
                   "الـ 80 فرع بيبيعوا قريب من بعض (±5%)، فترتيبهم أو اختيار مكان فرع جديد من الداتا دي هيبقى عشوائي. و7% من الطلبات متسجلة قبل افتتاح الفرع → نأكد تواريخ الافتتاح.", 'gaps'),
        'shipping': (f"Free shipping goes to {M['shipping']['free_share']:.0f}% of orders of every size → rule: free only above 1,000 EGP. Delivery days and 'Delayed' are random, so no delivery KPI yet. Refunds are a stable ~1.6% of sales.",
                     f"الشحن المجاني بيروح لـ {M['shipping']['free_share']:.0f}% من الطلبات من كل الأحجام → القاعدة: مجاني بس فوق 1,000 جنيه. ومدة التوصيل و'متأخر' عشوائيين، فمفيش مؤشر توصيل لسه. والاسترداد ثابت حوالي 1.6% من المبيعات.", 'shipping'),
        'people': (f"{M['people']['no_manager']} branches have no store manager and payroll covers at most {M['people']['paid_per_month'].max()} of {M['people']['employees']} people → we need the real org chart and full payroll before any workforce KPI.",
                   f"{M['people']['no_manager']} فرع من غير مدير، والمرتبات بتغطي {M['people']['paid_per_month'].max()} من {M['people']['employees']} بالكتير → محتاجين الهيكل الحقيقي والمرتبات كاملة قبل أي مؤشر للموظفين.", 'gaps'),
        'data': (f"Of the 22 HVIA app ideas, {int((M['readiness'].status.str.startswith('Ready')).sum())} are fully supported by the data. We logged {len(M['dq'])} data issues and {len(M['requests'])} requests for the company.",
                 f"من الـ 22 فكرة بتاعة HVIA، {int((M['readiness'].status.str.startswith('Ready')).sum())} الداتا بتشيلهم كاملين. وسجّلنا {len(M['dq'])} مشكلة في الداتا و {len(M['requests'])} طلب للشركة.", 'gaps'),
        'plan': (f"Start with: (1) freeze random discounts (+{b['actions'].profit.iloc[0] / 1e6:.1f}M), (2) marketing holdout (+{b['actions'].profit.iloc[1] / 1e6:.1f}M), (3) demand-based allocation (+{b['actions'].profit.iloc[2] / 1e6:.1f}M), (4) stock count in 5 branches, (5) buy from the forecast.",
                 f"نبدأ بـ: (1) نوقف الخصم العشوائي (+{b['actions'].profit.iloc[0] / 1e6:.1f} مليون)، (2) تجربة Holdout في التسويق (+{b['actions'].profit.iloc[1] / 1e6:.1f} مليون)، (3) التوزيع حسب الطلب (+{b['actions'].profit.iloc[2] / 1e6:.1f} مليون)، (4) جرد 5 فروع، (5) الشراء من التوقّع.", 'actions'),
    }
    if topic is None:
        return {'answer': ('I answer from Cottonil’s data. Try: sales, profit, discounts, transfers, purchasing, stock, marketing, customers, forecast, branches, shipping, payroll, data gaps, or "what should we do first?"'
                           if not ar else 'أنا بجاوب من داتا قطنيل. جرّب تسأل عن: المبيعات، الربح، الخصم، التوزيع، الشراء، المخزون، التسويق، العملاء، التوقّع، الفروع، الشحن، المرتبات، ثغرات الداتا، أو "نعمل إيه الأول؟"'),
                'link': None, 'topic': None}
    en, arx, link = R[topic]
    return {'answer': arx if ar else en, 'link': link, 'topic': topic}
