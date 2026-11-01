import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('📣 Marketing ROI', '📣 عائد التسويق'),
         t('Does the marketing money bring real orders?', 'فلوس التسويق بتجيب طلبات حقيقية؟'), '10_card07_marketing')

mf = u.marketing_fy()
ch = u.marketing_channels()
g = u.governorate_budget()
pf = u.people_facts()
k = st.columns(4)
u.kpi(k[0], t('Spend FY2026', 'الصرف FY2026'), u.money(mf.spend.iloc[-1] / 1e6))
u.kpi(k[1], t('Spend as % of sales', 'الصرف % من المبيعات'), f'{mf.spend_pct.iloc[-1]:.0f}%', help=t(f'FY2019: {mf.spend_pct.iloc[0]:.0f}%', f'FY2019: {mf.spend_pct.iloc[0]:.0f}%'))
u.kpi(k[2], t('Claimed ÷ real orders', 'المنسوب ÷ الحقيقي'), f'×{mf.claimed.sum() / mf.real_orders.sum():.0f}', inverse=True)
u.kpi(k[3], t('Spend ↔ orders by governorate', 'الصرف ↔ الطلبات لكل محافظة'), f"{g[['spend', 'orders']].corr().iloc[0, 1]:.2f}")

left, right = st.columns(2)
with left:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=mf.index, y=mf.spend / 1e6, name=t('Marketing spend', 'صرف التسويق'), marker_color=u.ORANGE))
    fig.add_trace(go.Bar(x=mf.index, y=mf.net_sales / 1e6, name=t('Net sales', 'المبيعات'), marker_color=u.LIGHT_BLUE))
    fig.update_layout(barmode='group'); fig.update_yaxes(title=t('M EGP', 'مليون جنيه'))
    u.show(u.style(fig, t('A fixed ~25–30M budget every year, whatever sales do', 'ميزانية ثابتة حوالي 25–30 مليون كل سنة مهما المبيعات عملت'), legend=True))
with right:
    fig = go.Figure(go.Bar(x=mf.index, y=mf.claimed_x, marker_color=u.ORANGE, text=[f'×{v:.0f}' for v in mf.claimed_x], textposition='outside'))
    fig.update_yaxes(title=t('orders claimed per real order', 'طلبات منسوبة لكل طلب حقيقي'), range=[0, mf.claimed_x.max() * 1.2])
    u.show(u.style(fig, t('Campaigns claim 30–73 times the real orders', 'الحملات بتنسب لنفسها 30–73 ضعف الطلبات الحقيقية')))

left, right = st.columns(2)
with left:
    fig = go.Figure(go.Bar(x=ch.index, y=ch.cpc, marker_color=u.BLUE, text=[f'{v:.2f}' for v in ch.cpc], textposition='outside'))
    fig.update_yaxes(title=t('cost per click, EGP', 'تكلفة الضغطة، جنيه'), range=[0, ch.cpc.max() * 1.3])
    u.show(u.style(fig, t(f'All channels cost {ch.cpc.min():.2f}–{ch.cpc.max():.2f} EGP per click – no clear winner',
                          f'كل القنوات بين {ch.cpc.min():.2f} و {ch.cpc.max():.2f} جنيه للضغطة – مفيش قناة كسبانة')))
with right:
    fig = go.Figure(go.Scatter(x=g.orders / 1e3, y=g.spend / 1e6, mode='markers+text', text=[n if n in (g.orders.idxmax(), g.spend.idxmax()) else '' for n in g.index],
                               textposition='top center', marker=dict(color=[u.ORANGE if n in (g.orders.idxmax(), g.spend.idxmax()) else u.BLUE for n in g.index], size=11)))
    fig.update_xaxes(title=t('FY2026 orders (thousand)', 'طلبات FY2026 (ألف)')); fig.update_yaxes(title=t('FY2026 spend, M EGP', 'صرف FY2026، مليون'))
    top = g.index[0]
    u.show(u.style(fig, t(f'Spend ignores demand: {top} has {g.order_share.iloc[0]:.0f}% of orders and {g.spend_share.iloc[0]:.1f}% of spend',
                          f'الصرف مش ماشي مع الطلب: {top} عندها {g.order_share.iloc[0]:.0f}% من الطلبات و {g.spend_share.iloc[0]:.1f}% بس من الصرف')))

st.subheader(t('Budget simulator', 'محاكي الميزانية'))
cut = st.slider(t('Cut % of spend that shows no measured effect', '% نقلله من الصرف اللي ملوش أثر مقاس'), 0, 50, 25, 5)
saved = mf.spend.iloc[-1] * cut / 100
k = st.columns(3)
u.kpi(k[0], t('Saved / year', 'توفير في السنة'), u.money(saved / 1e6))
u.kpi(k[1], t('New budget', 'الميزانية الجديدة'), u.money((mf.spend.iloc[-1] - saved) / 1e6))
u.kpi(k[2], t('Ledger vs campaigns', 'الدفاتر مقابل الحملات'), f"{pf['marketing_ledger'] / 1e6:.1f}M / {pf['marketing_campaigns'] / 1e6:.0f}M", inverse=True,
      help=t('Marketing in the expense ledger vs the campaign table (all years) – one source of truth is needed.', 'التسويق في دفتر المصاريف مقابل جدول الحملات – محتاجين مصدر واحد.'))
g2 = g.assign(new_budget=g.order_share / 100 * (mf.spend.iloc[-1] - saved))
show_g = g2.reset_index()[['governorate_ar', 'orders', 'order_share', 'spend', 'spend_share', 'new_budget']].round(1)
show_g.columns = [t('Governorate', 'المحافظة'), t('Orders', 'الطلبات'), t('% orders', '% الطلبات'), t('Spend', 'الصرف'), t('% spend', '% الصرف'), t('Budget if it follows demand', 'الميزانية لو ماشية مع الطلب')]
u.table(show_g)
u.insight(t('The plan: (1) one marketing ledger; (2) holdout tests – pause ads in matched governorates for 4 weeks and compare real orders; '
            '(3) budget follows demand; (4) keep only what the tests prove. Judge channels by CPC/CTR and holdouts, never by claimed orders.',
            'الخطة: (1) دفتر واحد للتسويق؛ (2) تجارب Holdout – نوقف الإعلان في محافظات شبه بعض 4 أسابيع ونقارن الطلبات الحقيقية؛ '
            '(3) الميزانية تمشي مع الطلب؛ (4) نكمّل بس في اللي التجربة تثبته. ونقيّم القنوات بتكلفة الضغطة والتجارب، مش بالطلبات المنسوبة.'))
