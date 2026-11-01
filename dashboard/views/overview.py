import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
fy = u.fy_summary()
last, prev = fy.iloc[-1], fy.iloc[-2]
idx = fy[['net_sales', 'units', 'price_per_unit']] / fy[['net_sales', 'units', 'price_per_unit']].iloc[0] * 100

u.hero(t('Chapter 1 · The big picture', 'الفصل 1 · الصورة الكبيرة'),
       t(f'Sales grew ×{idx.net_sales.iloc[-1] / 100:.0f} in 7 years – pieces only ×{idx.units.iloc[-1] / 100:.1f}',
         f'المبيعات زادت ×{idx.net_sales.iloc[-1] / 100:.0f} في 7 سنين – والقطع ×{idx.units.iloc[-1] / 100:.1f} بس'),
       t('Most of the growth is price. And four everyday decisions – discounts, marketing, distribution and purchasing – do not follow real demand.',
         'أغلب النمو أسعار. وأربع قرارات يومية – الخصم والتسويق والتوزيع والشراء – مش ماشية مع الطلب الحقيقي.'))

u.kpis([
    (t('Net sales FY2026', 'صافي المبيعات FY2026'), u.M(last.net_sales), t(f'{last.net_sales_g:+.0f}% vs FY2025', f'{last.net_sales_g:+.0f}% عن FY2025'), False),
    (t('Gross profit', 'إجمالي الربح'), u.M(last.gross_profit), t(f'margin {last.margin_pct:.1f}%', f'هامش {last.margin_pct:.1f}%'), False),
    (t('Real growth (pieces)', 'النمو الحقيقي (القطع)'), f'{last.units_g:+.1f}%', t(f'price per piece {last.price_per_unit_g:+.0f}%', f'سعر القطعة {last.price_per_unit_g:+.0f}%'), True),
    (t('Customers', 'العملاء'), f'{last.customers / 1e3:,.1f}K', t(f'{(last.customers / prev.customers - 1) * 100:+.0f}% vs FY2025', f'{(last.customers / prev.customers - 1) * 100:+.0f}% عن FY2025'), False),
    (t('Discounts given', 'الخصومات'), u.M(last.discount), t('no extra pieces sold', 'من غير قطع زيادة'), False),
])

left, right = st.columns([3, 2])
with left, u.card():
    m = u.monthly_sales()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m.index, y=m.net_sales / 1e6, name=t('Net sales', 'صافي المبيعات'), line=dict(color=u.NAVY, width=2.4)))
    fig.add_trace(go.Scatter(x=m.index, y=m.gross_profit / 1e6, name=t('Gross profit', 'إجمالي الربح'), line=dict(color=u.TEAL, width=2.4)))
    fig.update_yaxes(title=t('M EGP per month', 'مليون جنيه في الشهر'))
    u.show(u.fig_style(fig, t('Every month, Nov 2018 – Sep 2026', 'كل شهر، نوفمبر 2018 – سبتمبر 2026'), legend=True))
with right, u.card():
    fig = go.Figure()
    for col, color, name in [('net_sales', u.NAVY, t('Net sales', 'المبيعات')), ('price_per_unit', u.TEAL, t('Price per piece', 'سعر القطعة')),
                             ('units', u.MID, t('Pieces sold', 'القطع'))]:
        fig.add_trace(go.Scatter(x=idx.index, y=idx[col], name=name, mode='lines+markers', line=dict(color=color, width=2.4)))
    fig.update_yaxes(title=t('index, FY2019 = 100', 'مؤشر، FY2019 = 100'))
    u.show(u.fig_style(fig, t('Price did most of the growth', 'الأسعار عملت أغلب النمو'), legend=True))

u.section(t('Where the profit leaks', 'الربح بيضيع فين'), t('Four decisions that run on fixed rules instead of demand', 'أربع قرارات ماشية بقواعد ثابتة بدل الطلب'))
d = u.discount_facts()
tf, mf, pf = u.transfers_fy(), u.marketing_fy(), u.purchasing_fy()
u.story([
    (t('Discounts', 'الخصم'), t(f"{d['share_lines']:.0f}% of lines, every month, and they sell {d['pieces_with']:.2f} pieces vs {d['pieces_without']:.2f} without.",
                                f"{d['share_lines']:.0f}% من السطور كل شهر، وبتبيع {d['pieces_with']:.2f} قطعة مقابل {d['pieces_without']:.2f} من غير خصم.")),
    (t('Marketing', 'التسويق'), t(f'A fixed ~{mf.spend.iloc[-1] / 1e6:.0f}M a year; campaigns claim ×{mf.claimed.sum() / mf.real_orders.sum():.0f} the real orders.',
                                  f'ميزانية ثابتة حوالي {mf.spend.iloc[-1] / 1e6:.0f} مليون في السنة؛ والحملات بتنسب لنفسها ×{mf.claimed.sum() / mf.real_orders.sum():.0f} الطلبات الحقيقية.')),
    (t('Distribution', 'التوزيع'), t(f'Branches get a fixed ~1.6M pieces a year: ×{tf.ratio.iloc[-1]:.1f} of what they sell.',
                                     f'الفروع بتستلم حوالي 1.6 مليون قطعة ثابتة في السنة: ×{tf.ratio.iloc[-1]:.1f} من بيعها.')),
    (t('Purchasing', 'الشراء'), t(f'~{pf.bought.iloc[-1] / 1e6:.0f}M pieces bought a year for {pf.sold.iloc[-1] / 1e3:,.0f}K sold, equal for every SKU.',
                                  f'حوالي {pf.bought.iloc[-1] / 1e6:.0f} مليون قطعة في السنة مقابل {pf.sold.iloc[-1] / 1e3:,.0f} ألف اتباعت، وبالتساوي لكل SKU.')),
])

u.section(t('What the fixes are worth', 'الحلول تساوي كام'), t('FY2026 gross profit → after four decisions. Move the assumptions; everything updates.',
                                                                  'إجمالي ربح FY2026 ← بعد أربع قرارات. حرّكي الافتراضات وكل حاجة تتحسب تاني.'))
with u.card():
    a, b, c3, d4 = st.columns(4)
    stop = a.slider(t('Stop % of random discounts', '% من الخصم العشوائي نوقفه'), 0, 100, 75, 5)
    cut = b.slider(t('Cut % of marketing with no effect', '% نقلله من التسويق اللي ملوش أثر'), 0, 50, 25, 5)
    safety = c3.slider(t('Branch safety stock %', 'مخزون أمان الفروع %'), 0, 50, 10, 5)
    ship = d4.select_slider(t('Free shipping above (EGP)', 'شحن مجاني فوق (جنيه)'), [500, 750, 1000, 1500, 2000], 1000)
    pb = u.profit_bridge(stop, cut, safety, ship)
    acts = pb['actions']
    fig = go.Figure(go.Waterfall(
        x=[t('FY2026 profit', 'ربح FY2026')] + [t(a_, b_) for a_, b_ in zip(acts.action, acts.action_ar)] + [t('New profit', 'الربح الجديد')],
        measure=['absolute'] + ['relative'] * len(acts) + ['total'], y=[pb['base'] / 1e6] + list(acts.profit / 1e6) + [0],
        text=[f"{pb['base'] / 1e6:.1f}"] + [f'+{v / 1e6:.1f}' for v in acts.profit] + [f"{pb['new'] / 1e6:.1f}"], textposition='outside',
        connector=dict(line=dict(color=u.GREY)), increasing=dict(marker=dict(color=u.NAVY)), totals=dict(marker=dict(color=u.TEAL)),
        decreasing=dict(marker=dict(color=u.GREY))))
    fig.update_yaxes(title=t('M EGP per year', 'مليون جنيه في السنة'), range=[0, pb['new'] / 1e6 * 1.12])
    u.show(u.fig_style(fig, t(f"+{(pb['new'] - pb['base']) / 1e6:.1f}M EGP a year (+{pb['uplift_pct']:.0f}%)",
                              f"+{(pb['new'] - pb['base']) / 1e6:.1f} مليون جنيه في السنة (+{pb['uplift_pct']:.0f}%)"), height=400))
sc = pb['scenarios']
u.kpis([(t(r.scenario, r.scenario_ar) + ' · FY2027', u.M(r.profit), '', i == 1) for i, (_, r) in enumerate(sc.iterrows())] +
       [(t('Breakeven volume loss', 'نقطة التعادل'), f"{pb['breakeven_volume_loss']:.1f}%",
         t('stopping discounts pays unless we lose more volume than this', 'إيقاف الخصم مكسب إلا لو خسرنا كميات أكتر من كده'), False)])
sf = u.stock_facts()
u.note(t(f"Not counted above: up to {(sf['stock_value'] - sf['need_value_3m']) / 1e6:,.0f}M EGP of cash sits in stock above a 3-month need – "
         "but only a physical count can confirm it (chapter 3).",
         f"مش محسوب فوق: لحد {(sf['stock_value'] - sf['need_value_3m']) / 1e6:,.0f} مليون جنيه كاش واقفين في مخزون زيادة عن احتياج 3 شهور – "
         "بس الجرد بس هو اللي يأكد الرقم (الفصل 3)."))
u.footer('04_card01_sales_growth · 14_card09_story_action_plan')
