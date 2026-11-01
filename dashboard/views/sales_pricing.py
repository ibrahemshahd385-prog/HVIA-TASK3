import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('💰 Sales & Pricing Intelligence', '💰 المبيعات والتسعير'),
         t('Is growth real, what sells, when – and do discounts sell more pieces?',
           'النمو حقيقي؟ إيه اللي بيتباع وإمتى؟ وهل الخصم بيبيع قطع أكتر؟'),
         '04_card01_sales_growth · 05_card02_discounts')

fy = u.fy_summary()
tab1, tab2 = st.tabs([t('Growth, categories & seasons', 'النمو والفئات والمواسم'), t('Discounts', 'الخصومات')])

with tab1:
    k = st.columns(4)
    u.kpi(k[0], t('Net sales growth FY2026', 'نمو المبيعات FY2026'), f'{fy.net_sales_g.iloc[-1]:+.1f}%')
    u.kpi(k[1], t('…from more pieces', '…من قطع أكتر'), f'{fy.units_g.iloc[-1]:+.1f}%')
    u.kpi(k[2], t('…from higher prices', '…من أسعار أعلى'), f'{fy.price_per_unit_g.iloc[-1]:+.1f}%')
    u.kpi(k[3], t('Pieces per order', 'قطع في الطلب'), f'{fy.units.iloc[-1] / fy.orders.iloc[-1]:.1f}')
    left, right = st.columns(2)
    with left:
        g = fy.units_g.dropna()
        fig = go.Figure(go.Bar(x=g.index, y=g, marker_color=[u.ORANGE if x == g.index[-1] else u.BLUE for x in g.index],
                               text=[f'+{v:.1f}%' for v in g], textposition='outside'))
        fig.update_yaxes(title=t('growth in pieces sold, %', 'نمو القطع المباعة %'), range=[0, g.max() * 1.25])
        u.show(u.style(fig, t(f'Real growth is slowing: +{g.iloc[-1]:.1f}% in FY2026', f'النمو الحقيقي بيبطّأ: +{g.iloc[-1]:.1f}% في FY2026')))
    with right:
        cat = u.category_fy(int(fy.index[-1])).sort_values('net_sales')
        fig = go.Figure(go.Bar(y=cat.index, x=cat.share, orientation='h', text=[f'{v:.1f}%' for v in cat.share], textposition='outside',
                               marker_color=[u.ORANGE if c in cat.index[-2:] else u.BLUE for c in cat.index]))
        fig.update_xaxes(title=t('% of FY2026 sales', '% من مبيعات FY2026'))
        u.show(u.style(fig, t(f'Boxers + men tops = {cat.share.iloc[-2:].sum():.0f}% of sales', f'البوكسر + التيشرتات الرجالي = {cat.share.iloc[-2:].sum():.0f}% من المبيعات'), height=480))
    left, right = st.columns(2)
    names_en = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    names_ar = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
    with left:
        s = u.seasonality()
        fig = go.Figure(go.Bar(x=[t(a, b) for a, b in zip(names_en, names_ar)], y=s.values,
                               marker_color=[u.ORANGE if v > 7 else (u.GREY if v < -5 else u.BLUE) for v in s.values]))
        fig.update_yaxes(title=t('% vs an average month', '% مقارنة بالشهر العادي'))
        u.show(u.style(fig, t('Peaks: Nov–Dec and Mar–May · lows: Feb and Oct', 'الذروة: نوفمبر–ديسمبر ومارس–مايو · الأقل: فبراير وأكتوبر')))
    with right:
        w = u.weekday()
        days_ar = {'Saturday': 'السبت', 'Sunday': 'الأحد', 'Monday': 'الاتنين', 'Tuesday': 'التلات', 'Wednesday': 'الأربع', 'Thursday': 'الخميس', 'Friday': 'الجمعة'}
        fig = go.Figure(go.Bar(x=[days_ar[d] if u.is_ar() else d for d in w.index], y=w.values,
                               marker_color=[u.ORANGE if v > 0 else u.BLUE for v in w.values]))
        fig.update_yaxes(title=t('% vs an average day', '% مقارنة باليوم العادي'))
        u.show(u.style(fig, t('Thursday–Saturday are ~7% busier → staff and stock for them', 'الخميس للسبت أعلى بحوالي 7% → جهّزي الناس والبضاعة')))
    u.insight(t('Margin is ~38% in every category and every year because cost is always ~59% of price. '
                'So "product profitability" is the same everywhere – the lever is the discount, next tab.',
                'الهامش حوالي 38% في كل فئة وكل سنة لأن التكلفة دايمًا حوالي 59% من السعر. '
                'يعني ربحية المنتجات واحدة – والرافعة الحقيقية هي الخصم، في التاب الجاية.'))

with tab2:
    d = u.discount_facts()
    k = st.columns(4)
    u.kpi(k[0], t('Lines with a discount', 'سطور عليها خصم'), f"{d['share_lines']:.0f}%")
    u.kpi(k[1], t('Pieces per line: with / without', 'قطع في السطر: بخصم / من غير'), f"{d['pieces_with']:.2f} / {d['pieces_without']:.2f}")
    u.kpi(k[2], t('Margin: with / without', 'الهامش: بخصم / من غير'), f"{d['margin_with']:.1f}% / {d['margin_without']:.1f}%")
    u.kpi(k[3], t('FY2026 discounts', 'خصومات FY2026'), u.money(d['discount_fy26'] / 1e6), inverse=True,
          help=t(f"= {d['discount_fy26'] / d['gp_fy26'] * 100:.1f}% of gross profit", f"= {d['discount_fy26'] / d['gp_fy26'] * 100:.1f}% من إجمالي الربح"))
    left, right = st.columns(2)
    with left:
        b = u.discount_bands()
        fig = go.Figure(go.Bar(x=b.index, y=b.margin_pct, marker_color=[u.BLUE] + [u.ORANGE] * (len(b) - 1),
                               text=[f'{m:.1f}%<br>{p:.2f} {t("pcs", "قطعة")}' for m, p in zip(b.margin_pct, b.avg_pieces)], textposition='outside'))
        fig.update_yaxes(title=t('gross margin %', 'هامش الربح %'), range=[0, 50])
        fig.update_xaxes(title=t('discount on the line', 'الخصم على السطر'))
        u.show(u.style(fig, t('Every discount band cuts margin – none sells more pieces', 'كل شريحة خصم بتقلل الهامش – ومفيش شريحة بتبيع أكتر'), height=420))
    with right:
        bm = d['by_month']
        fig = go.Figure(go.Scatter(x=list(range(1, 13)), y=bm.values, mode='lines+markers', line=dict(color=u.BLUE, width=2.5)))
        fig.update_yaxes(title=t('% of lines discounted', '% السطور اللي عليها خصم'), range=[0, 70])
        fig.update_xaxes(title=t('month', 'الشهر'), dtick=1)
        u.show(u.style(fig, t('The same 54% every month – even in peak season: no strategy', 'نفس الـ 54% كل شهر – حتى في الموسم: مفيش استراتيجية'), height=420))
    st.subheader(t('Simulator: replace random discounts with planned ones', 'محاكي: نبدّل الخصم العشوائي بخصم مخطط'))
    stop = st.slider(t('% of random discounts we stop', '% من الخصومات العشوائية اللي نوقفها'), 0, 100, 75, 5, key='disc_stop')
    gain = d['discount_fy26'] * stop / 100
    k = st.columns(3)
    u.kpi(k[0], t('Extra gross profit / year', 'ربح زيادة في السنة'), u.money(gain / 1e6))
    u.kpi(k[1], t('New gross margin', 'الهامش الجديد'), f"{(d['gp_fy26'] + gain) / (d['gp_fy26'] / fy.margin_pct.iloc[-1] * 100 + gain) * 100:.1f}%")
    u.kpi(k[2], t('Pieces we risk losing', 'القطع اللي ممكن نخسرها'), t('~0', 'تقريبًا صفر'),
          help=t(f"Correlation discount ↔ pieces = {d['corr']:.4f}", f"الارتباط بين الخصم والقطع = {d['corr']:.4f}"))
    u.insight(t('Keep discounts only as planned campaigns with a test group and a control group, and never below a floor margin.',
                'نخلي الخصم بس في حملات مخططة فيها مجموعة تجربة ومجموعة مقارنة، ومن غير ما ننزل تحت حد أدنى للهامش.'))
