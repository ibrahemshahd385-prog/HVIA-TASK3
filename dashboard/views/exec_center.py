import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('🎯 Executive Command Center', '🎯 مركز القيادة'),
         t('Sales grow every year – is it real growth, and where is profit leaking?',
           'المبيعات بتزيد كل سنة – هل ده نمو حقيقي، والربح بيضيع فين؟'),
         '04_card01_sales_growth · 05_card02_discounts · 14_card09_story_action_plan')

fy = u.fy_summary()
fys = list(fy.index)
pick = st.selectbox(t('Fiscal year (Oct–Sep)', 'السنة المالية (أكتوبر–سبتمبر)'), fys, index=len(fys) - 1)
row = fy.loc[pick]
prev = fy.loc[fys[fys.index(pick) - 1]] if fys.index(pick) > 0 else None


def delta(col):
    return None if prev is None else f'{(row[col] / prev[col] - 1):+.1%}'


k = st.columns(6)
u.kpi(k[0], t('Net sales', 'صافي المبيعات'), u.money(row.net_sales / 1e6), delta('net_sales'))
u.kpi(k[1], t('Gross profit', 'إجمالي الربح'), u.money(row.gross_profit / 1e6), delta('gross_profit'))
u.kpi(k[2], t('Gross margin', 'هامش الربح'), f'{row.margin_pct:.1f}%',
      help=t('Cost is always ~59% of price, so margin is ~38% in every category. Only discounts move it.',
             'التكلفة دايمًا حوالي 59% من السعر، فالهامش حوالي 38% في كل فئة. الخصم بس اللي بيحرّكه.'))
u.kpi(k[3], t('Pieces sold', 'القطع المباعة'), f'{row.units / 1e3:,.0f}K', delta('units'),
      help=t('Real growth = pieces. Sales growth minus this = price inflation.', 'النمو الحقيقي = القطع. الفرق بينه وبين نمو المبيعات = زيادة الأسعار.'))
u.kpi(k[4], t('Price per piece', 'سعر القطعة'), f'{row.price_per_unit:,.0f} EGP', delta('price_per_unit'))
u.kpi(k[5], t('Discounts given', 'الخصومات'), u.money(row.discount / 1e6), delta('discount'), inverse=True,
      help=t('Discounted lines sell the same number of pieces (card 02).', 'السطور اللي عليها خصم بتبيع نفس عدد القطع (كارت 02).'))

left, right = st.columns([3, 2])
with left:
    m = u.monthly_sales()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m.index, y=m.net_sales / 1e6, name=t('Net sales', 'صافي المبيعات'), mode='lines', line=dict(color=u.BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=m.index, y=m.gross_profit / 1e6, name=t('Gross profit', 'إجمالي الربح'), mode='lines', line=dict(color=u.ORANGE, width=2.5)))
    fig.update_yaxes(title=t('EGP millions per month', 'مليون جنيه في الشهر'))
    u.show(u.style(fig, t('Sales ×15 in 7 years – mostly prices; peaks every Nov–Dec and Mar–May',
                          'المبيعات ×15 في 7 سنين – أغلبها أسعار؛ والذروة كل نوفمبر–ديسمبر ومارس–مايو'), legend=True))
with right:
    idx = fy[['net_sales', 'units', 'price_per_unit']] / fy[['net_sales', 'units', 'price_per_unit']].iloc[0] * 100
    fig = go.Figure()
    for col, color, name in [('net_sales', u.BLUE, t('Net sales', 'المبيعات')), ('price_per_unit', u.ORANGE, t('Price per piece', 'سعر القطعة')),
                             ('units', u.GREY, t('Pieces sold', 'القطع'))]:
        fig.add_trace(go.Scatter(x=idx.index, y=idx[col], name=name, mode='lines+markers', line=dict(color=color, width=2.5)))
    fig.update_yaxes(title=t('Index, FY2019 = 100', 'مؤشر، FY2019 = 100'))
    u.show(u.style(fig, t(f'Pieces only ×{idx.units.iloc[-1] / 100:.1f} – price did the rest',
                          f'القطع ×{idx.units.iloc[-1] / 100:.1f} بس – والباقي أسعار'), legend=True))

# ---------------------------------------------------------------- alerts (every number is computed live)
st.subheader(t('🚨 What needs attention now', '🚨 محتاج تدخل دلوقتي'))
d = u.discount_facts()
tf = u.transfers_fy()
sf = u.stock_facts()
mf = u.marketing_fy()
pf = u.purchasing_fy()
cf = u.customer_facts()
alerts = [
    (t('Discounts', 'الخصومات'), t(f"{d['share_lines']:.0f}% of lines get a discount, yet they sell {d['pieces_with']:.2f} pieces vs {d['pieces_without']:.2f} without – **{d['discount_fy26'] / 1e6:.1f}M EGP** given away in FY2026.",
                                   f"{d['share_lines']:.0f}% من السطور عليها خصم، وبتبيع {d['pieces_with']:.2f} قطعة مقابل {d['pieces_without']:.2f} من غير خصم – **{d['discount_fy26'] / 1e6:.1f} مليون جنيه** راحوا في FY2026."), t('Sales & Pricing', 'المبيعات والتسعير')),
    (t('Distribution', 'التوزيع'), t(f"Branches got **×{tf.ratio.iloc[-1]:.1f}** what they sold in FY2026 – a fixed ~1.6M pieces a year, socks 55% of it.",
                                     f"الفروع استلمت **×{tf.ratio.iloc[-1]:.1f}** من اللي باعته في FY2026 – كمية ثابتة حوالي 1.6 مليون قطعة في السنة، الشرابات 55% منها."), t('Smart Inventory', 'المخزون الذكي')),
    (t('Missing stock', 'مخزون مش متحسوب'), t(f"**{sf['unaccounted'] / 1e6:.1f}M pieces** reached branches and are neither sold nor on the shelf → stock count.",
                                              f"**{sf['unaccounted'] / 1e6:.1f} مليون قطعة** وصلت الفروع ومش متباعة ولا على الرف → جرد."), t('Smart Inventory', 'المخزون الذكي')),
    (t('Purchasing', 'الشراء'), t(f"We buy **{pf.bought.iloc[-1] / 1e6:.0f}M pieces** a year for {pf.sold.iloc[-1] / 1e3:,.0f}K sold, equally for every SKU.",
                                  f"بنشتري **{pf.bought.iloc[-1] / 1e6:.0f} مليون قطعة** في السنة مقابل {pf.sold.iloc[-1] / 1e3:,.0f} ألف اتباعت، وبالتساوي لكل SKU."), t('Procurement', 'المشتريات')),
    (t('Marketing', 'التسويق'), t(f"Campaigns claim **×{mf.claimed.sum() / mf.real_orders.sum():.0f}** the real orders; {mf.spend.iloc[-1] / 1e6:.1f}M spent in FY2026 with no visible link to orders.",
                                  f"الحملات بتنسب لنفسها **×{mf.claimed.sum() / mf.real_orders.sum():.0f}** الطلبات الحقيقية؛ اتصرف {mf.spend.iloc[-1] / 1e6:.1f} مليون في FY2026 من غير علاقة ظاهرة بالطلبات."), t('Marketing ROI', 'عائد التسويق')),
    (t('Customer data', 'داتا العملاء'), t(f"**{cf['guest_share']:.0f}%** of orders have no customer (even online) → loyalty ID first.",
                                           f"**{cf['guest_share']:.0f}%** من الطلبات مفيهاش عميل (حتى الأونلاين) → كود ولاء الأول."), t('Customer 360', 'العميل 360')),
]
for area, text, page in alerts:
    st.markdown(f'- **{area}:** {text} → *{page}*')

# ---------------------------------------------------------------- action plan
st.subheader(t('💰 Action plan: how much profit is on the table?', '💰 خطة العمل: قد إيه ربح ممكن نرجّعه؟'))
with st.expander(t('Adjust the assumptions (every number below updates live)', 'غيّري الافتراضات (كل الأرقام تحت بتتحدّث فورًا)'), expanded=False):
    a, b, c3, d4 = st.columns(4)
    stop = a.slider(t('Stop % of random discounts', '% من الخصومات العشوائية اللي نوقفها'), 0, 100, 75, 5)
    cut = b.slider(t('Cut % of marketing with no effect', '% تقليل التسويق اللي ملوش أثر'), 0, 50, 25, 5)
    safety = c3.slider(t('Branch safety stock %', 'مخزون أمان الفروع %'), 0, 50, 10, 5)
    ship = d4.select_slider(t('Free shipping only above (EGP)', 'شحن مجاني فوق (جنيه)'), [500, 750, 1000, 1500, 2000], 1000)
pb = u.profit_bridge(stop, cut, safety, ship)
acts = pb['actions']
names = [t(a_, b_) for a_, b_ in zip(acts.action, acts.action_ar)]
fig = go.Figure(go.Waterfall(
    x=[t('FY2026 profit', 'ربح FY2026')] + names + [t('New profit', 'الربح الجديد')],
    measure=['absolute'] + ['relative'] * len(acts) + ['total'],
    y=[pb['base'] / 1e6] + list(acts.profit / 1e6) + [0],
    text=[f"{pb['base'] / 1e6:.1f}"] + [f'+{v / 1e6:.1f}' for v in acts.profit] + [f"{pb['new'] / 1e6:.1f}"], textposition='outside',
    connector=dict(line=dict(color=u.SOFT_GREY)),
    increasing=dict(marker=dict(color=u.BLUE)), totals=dict(marker=dict(color=u.ORANGE)), decreasing=dict(marker=dict(color=u.RED))))
fig.update_yaxes(title=t('M EGP per year', 'مليون جنيه في السنة'), range=[0, pb['new'] / 1e6 * 1.12])
u.show(u.style(fig, t(f"{len(acts)} actions = +{(pb['new'] - pb['base']) / 1e6:.1f}M EGP profit a year (+{pb['uplift_pct']:.0f}%)",
                      f"{len(acts)} إجراءات = +{(pb['new'] - pb['base']) / 1e6:.1f} مليون جنيه ربح في السنة (+{pb['uplift_pct']:.0f}%)"), height=430))
show_tbl = acts.assign(profit=(acts.profit / 1e6).round(2))
show_tbl = show_tbl[['action_ar' if u.is_ar() else 'action', 'owner', 'profit', 'assumption']]
show_tbl.columns = [t('Action', 'الإجراء'), t('Owner', 'المسؤول'), t('M EGP / year', 'مليون/سنة'), t('Assumption', 'الافتراض')]
u.table(show_tbl)

k = st.columns(4)
sc = pb['scenarios']
for i, (_, r) in enumerate(sc.iterrows()):
    u.kpi(k[i], t(r.scenario, r.scenario_ar) + ' (FY2027)', u.money(r.profit / 1e6))
u.kpi(k[3], t('Breakeven volume loss', 'نقطة التعادل'), f"{pb['breakeven_volume_loss']:.1f}%",
      help=t('Stopping discounts stays profitable unless we lose more than this share of volume. The evidence says we lose ~0%.',
             'إيقاف الخصم يفضل مكسب إلا لو خسرنا أكتر من النسبة دي من الكميات. والدليل بيقول إننا مش هنخسر حاجة تقريبًا.'))
st.caption(t(f"FY2027 assumes pieces grow {pb['growth']:.1f}% (like FY2026) at FY2026 prices. Cash not included: up to "
             f"{(sf['stock_value'] - sf['need_value_3m']) / 1e6:,.0f}M EGP of stock above a 3-month need – only after a stock count.",
             f"FY2027 بافتراض إن القطع تزيد {pb['growth']:.1f}% (زي FY2026) بأسعار FY2026. ومش محسوب: لحد "
             f"{(sf['stock_value'] - sf['need_value_3m']) / 1e6:,.0f} مليون جنيه مخزون زيادة عن احتياج 3 شهور – بعد الجرد بس."))
