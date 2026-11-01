import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
fy = u.fy_summary()
d = u.discount_facts()

u.hero(t('Chapter 2 · Growth & margin', 'الفصل 2 · النمو والهامش'),
       t('Real growth is slowing, and the margin only moves with the discount', 'النمو الحقيقي بيبطّأ، والهامش مش بيتحرك غير مع الخصم'),
       t('Cost is always ~59% of price, so the margin is ~38% in every category and every year. The one lever left is the discount – and today it is random.',
         'التكلفة دايمًا حوالي 59% من السعر، فالهامش حوالي 38% في كل فئة وكل سنة. والرافعة الوحيدة هي الخصم – والنهارده هو عشوائي.'))

u.kpis([
    (t('Sales growth FY2026', 'نمو المبيعات FY2026'), f'{fy.net_sales_g.iloc[-1]:+.1f}%', t('in EGP', 'بالجنيه'), False),
    (t('…from more pieces', '…من قطع أكتر'), f'{fy.units_g.iloc[-1]:+.1f}%', t('the real growth', 'النمو الحقيقي'), True),
    (t('…from higher prices', '…من أسعار أعلى'), f'{fy.price_per_unit_g.iloc[-1]:+.1f}%', t('inflation', 'تضخم'), False),
    (t('Gross margin', 'هامش الربح'), f'{fy.margin_pct.iloc[-1]:.1f}%', t(f'{fy.margin_pct.min():.1f}–{fy.margin_pct.max():.1f}% in 8 years', f'{fy.margin_pct.min():.1f}–{fy.margin_pct.max():.1f}% في 8 سنين'), False),
])

left, right = st.columns(2)
with left, u.card():
    g = fy.units_g.dropna()
    fig = go.Figure(go.Bar(x=[f'FY{str(y)[2:]}' for y in g.index], y=g, marker_color=[u.TEAL if y == g.index[-1] else u.NAVY for y in g.index],
                           text=[f'+{v:.1f}%' for v in g], textposition='outside'))
    fig.update_yaxes(title=t('growth in pieces sold, %', 'نمو القطع المباعة %'), range=[0, g.max() * 1.25])
    u.show(u.fig_style(fig, t('Real growth by year', 'النمو الحقيقي كل سنة')))
with right, u.card():
    cat = u.category_fy(int(fy.index[-1])).sort_values('net_sales')
    fig = go.Figure(go.Bar(y=cat.index, x=cat.share, orientation='h', text=[f'{v:.1f}%' for v in cat.share], textposition='outside',
                           marker_color=[u.TEAL if c in cat.index[-2:] else u.NAVY for c in cat.index]))
    fig.update_xaxes(title=t('% of FY2026 sales', '% من مبيعات FY2026'))
    u.show(u.fig_style(fig, t(f'Boxers + men tops = {cat.share.iloc[-2:].sum():.0f}% of sales', f'البوكسر والتيشرتات الرجالي = {cat.share.iloc[-2:].sum():.0f}% من المبيعات'), height=470))

left, right = st.columns(2)
with left, u.card():
    s = u.seasonality()
    fig = go.Figure(go.Bar(x=u.month_names(), y=s.values, marker_color=[u.TEAL if v > 7 else (u.GREY if v < -5 else u.NAVY) for v in s.values]))
    fig.update_yaxes(title=t('% vs an average month', '% عن الشهر العادي'))
    u.show(u.fig_style(fig, t('Peaks: Nov–Dec and Mar–May', 'الذروة: نوفمبر–ديسمبر ومارس–مايو')))
with right, u.card():
    w = u.weekday()
    days_ar = {'Saturday': 'السبت', 'Sunday': 'الأحد', 'Monday': 'الاتنين', 'Tuesday': 'التلات', 'Wednesday': 'الأربع', 'Thursday': 'الخميس', 'Friday': 'الجمعة'}
    fig = go.Figure(go.Bar(x=[days_ar[x] if u.is_ar() else x for x in w.index], y=w.values, marker_color=[u.TEAL if v > 0 else u.GREY for v in w.values]))
    fig.update_yaxes(title=t('% vs an average day', '% عن اليوم العادي'))
    u.show(u.fig_style(fig, t('Thursday to Saturday are ~7% busier', 'الخميس للسبت أعلى بحوالي 7%')))

u.section(t('The discount', 'الخصم'), t('Every second line gets one – does it sell anything?', 'سطر من كل اتنين عليه خصم – هل بيبيع حاجة؟'))
u.kpis([
    (t('Lines discounted', 'سطور عليها خصم'), f"{d['share_lines']:.0f}%", t('same share every month', 'نفس النسبة كل شهر'), False),
    (t('Pieces per line', 'قطع في السطر'), f"{d['pieces_with']:.2f} / {d['pieces_without']:.2f}", t('with / without discount', 'بخصم / من غير'), True),
    (t('Margin', 'الهامش'), f"{d['margin_with']:.1f}% / {d['margin_without']:.1f}%", t('with / without discount', 'بخصم / من غير'), False),
    (t('Discounts FY2026', 'خصومات FY2026'), u.M(d['discount_fy26']), t(f"= {d['discount_fy26'] / d['gp_fy26'] * 100:.1f}% of gross profit", f"= {d['discount_fy26'] / d['gp_fy26'] * 100:.1f}% من إجمالي الربح"), False),
])
left, right = st.columns(2)
with left, u.card():
    b = u.discount_bands()
    fig = go.Figure(go.Bar(x=b.index, y=b.margin_pct, marker_color=[u.NAVY] + [u.TEAL] * (len(b) - 1),
                           text=[f'{m:.1f}%<br>{p:.2f} {t("pcs", "قطعة")}' for m, p in zip(b.margin_pct, b.avg_pieces)], textposition='outside'))
    fig.update_yaxes(title=t('gross margin %', 'هامش الربح %'), range=[0, 50])
    fig.update_xaxes(title=t('discount on the line', 'الخصم على السطر'))
    u.show(u.fig_style(fig, t('Each band cuts margin, none sells more', 'كل شريحة بتقلل الهامش، ومفيش واحدة بتبيع أكتر'), height=400))
with right, u.card():
    bm = d['by_month']
    fig = go.Figure(go.Scatter(x=u.month_names(), y=bm.values, mode='lines+markers', line=dict(color=u.NAVY, width=2.4)))
    fig.update_yaxes(title=t('% of lines discounted', '% السطور عليها خصم'), range=[0, 70])
    u.show(u.fig_style(fig, t('54% in every month, even in the peak', '54% في كل شهر، حتى في الموسم'), height=400))

with u.card():
    stop = st.slider(t('What if we stop this share of random discounts?', 'لو وقفنا النسبة دي من الخصم العشوائي؟'), 0, 100, 75, 5, key='g_stop')
    gain = d['discount_fy26'] * stop / 100
    net26 = d['gp_fy26'] / fy.margin_pct.iloc[-1] * 100
    u.kpis([(t('Extra gross profit a year', 'ربح زيادة في السنة'), u.M(gain), t('discounts sold no extra pieces', 'الخصم ماكانش بيبيع قطع زيادة'), True),
            (t('New gross margin', 'الهامش الجديد'), f"{(d['gp_fy26'] + gain) / (net26 + gain) * 100:.1f}%", '', False),
            (t('Pieces we risk losing', 'قطع ممكن نخسرها'), t('~0', 'تقريبًا صفر'), t(f"correlation {d['corr']:.4f}", f"الارتباط {d['corr']:.4f}"), False)])
u.note(t('Discounts only as planned campaigns, with a test group and a control group, and never below a floor margin.',
         'الخصم يبقى في حملات مخططة بس، فيها مجموعة تجربة ومجموعة مقارنة، ومن غير ما ننزل تحت حد أدنى للهامش.'))
u.footer('04_card01_sales_growth · 05_card02_discounts')
