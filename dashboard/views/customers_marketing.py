import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
cf, p = u.customer_facts(), u.rfm()
mf, ch, g = u.marketing_fy(), u.marketing_channels(), u.governorate_budget()
pf = u.people_facts()

u.hero(t('Chapter 4 · Customers & marketing', 'الفصل 4 · العملاء والتسويق'),
       t('Customers come back – but we cannot see who they are, and marketing spend ignores demand',
         'العملاء بيرجعوا – بس مش شايفين هم مين، وصرف التسويق مش ماشي مع الطلب'),
       t('Loyalty needs a real customer ID first. Marketing needs a test that measures real orders, not platform claims.',
         'الولاء محتاج كود عميل حقيقي الأول. والتسويق محتاج تجربة بتقيس الطلبات الحقيقية، مش اللي المنصات بتقوله.'))

s = p.spend.sort_values(ascending=False)
u.kpis([
    (t('Active customers FY2026', 'عملاء نشطين FY2026'), f"{cf['active_by_fy'].iloc[-1] / 1e3:,.1f}K", '', False),
    (t('Bought more than once', 'اشتروا أكتر من مرة'), f'{(p.orders > 1).mean():.0%}', t(f'top 20% = {s.head(len(s) // 5).sum() / s.sum():.0%} of revenue', f'أعلى 20% = {s.head(len(s) // 5).sum() / s.sum():.0%} من الإيراد'), False),
    (t('Orders with no customer', 'طلبات من غير عميل'), f"{cf['guest_share']:.0f}%", t('even online', 'حتى الأونلاين'), True),
    (t('Branches per loyal customer', 'فروع لكل عميل وفي'), f"{cf['loyal_branches']:.1f}", t(f"{cf['loyal_govs']:.1f} governorates", f"{cf['loyal_govs']:.1f} محافظة"), False),
])

left, right = st.columns(2)
with left, u.card():
    gb = cf['guest_by_channel']
    fig = go.Figure(go.Bar(x=[u.ch_name(c) for c in gb.index], y=gb.values, marker_color=[u.TEAL if c == 'Online' else u.NAVY for c in gb.index],
                           text=[f'{v:.1f}%' for v in gb.values], textposition='outside'))
    fig.update_yaxes(title=t('% of orders without a customer', '% طلبات من غير عميل'), range=[0, 30])
    u.show(u.fig_style(fig, t('No customer on 1 order in 5', 'طلب من كل 5 من غير عميل')))
with right, u.card():
    seg = p.groupby('segment').agg(customers=('orders', 'size'), revenue=('spend', 'sum'))
    seg['pct_rev'] = seg.revenue / seg.revenue.sum() * 100
    seg['pct_cust'] = seg.customers / seg.customers.sum() * 100
    seg = seg.sort_values('pct_rev')
    names = [u.seg_name(x) for x in seg.index]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=names, x=seg.pct_cust, orientation='h', name=t('% of customers', '% من العملاء'), marker_color=u.GREY))
    fig.add_trace(go.Bar(y=names, x=seg.pct_rev, orientation='h', name=t('% of revenue', '% من الإيراد'), marker_color=u.NAVY))
    fig.update_layout(barmode='group')
    u.show(u.fig_style(fig, t('RFM segments (a description, not a prediction)', 'شرايح RFM (وصف مش توقّع)'), height=420, legend=True))
u.note(t(f"{cf['wholesale_by_retail_customers']:.0f}% of wholesale orders (~24 pieces each) come from customers registered as retail. "
         "Fix first: the phone number as a loyalty ID at every till, plus a reseller flag.",
         f"{cf['wholesale_by_retail_customers']:.0f}% من طلبات الجملة (حوالي 24 قطعة) من عملاء متسجلين قطاعي. "
         "نصلّح الأول: رقم الموبايل ككود ولاء في كل كاشير، وعلامة للتاجر."))

u.section(t('Marketing', 'التسويق'))
u.kpis([
    (t('Spend FY2026', 'الصرف FY2026'), u.M(mf.spend.iloc[-1]), t(f'{mf.spend_pct.iloc[-1]:.0f}% of sales', f'{mf.spend_pct.iloc[-1]:.0f}% من المبيعات'), False),
    (t('Claimed ÷ real orders', 'المنسوب ÷ الحقيقي'), f'×{mf.claimed.sum() / mf.real_orders.sum():.0f}', '', True),
    (t('Cost per click', 'تكلفة الضغطة'), f'{ch.cpc.min():.2f}–{ch.cpc.max():.2f}', t('EGP, all channels alike', 'جنيه، كل القنوات زي بعض'), False),
    (t('Spend ↔ orders by governorate', 'الصرف ↔ الطلبات لكل محافظة'), f"{g[['spend', 'orders']].corr().iloc[0, 1]:.2f}", t('no link', 'مفيش علاقة'), False),
])
left, right = st.columns(2)
with left, u.card():
    fig = go.Figure()
    fig.add_trace(go.Bar(x=mf.index, y=mf.net_sales / 1e6, name=t('Net sales', 'المبيعات'), marker_color=u.GREY))
    fig.add_trace(go.Bar(x=mf.index, y=mf.spend / 1e6, name=t('Marketing spend', 'صرف التسويق'), marker_color=u.TEAL))
    fig.update_layout(barmode='group'); fig.update_yaxes(title=t('M EGP', 'مليون جنيه'))
    u.show(u.fig_style(fig, t('A fixed budget, whatever sales do', 'ميزانية ثابتة مهما المبيعات عملت'), legend=True))
with right, u.card():
    hi = {g.orders.idxmax(), g.spend.idxmax()}
    fig = go.Figure(go.Scatter(x=g.orders / 1e3, y=g.spend / 1e6, mode='markers+text', text=[n if n in hi else '' for n in g.index], textposition='top center',
                               marker=dict(color=[u.TEAL if n in hi else u.NAVY for n in g.index], size=11)))
    fig.update_xaxes(title=t('FY2026 orders (thousand)', 'طلبات FY2026 (ألف)')); fig.update_yaxes(title=t('FY2026 spend, M EGP', 'صرف FY2026، مليون'))
    u.show(u.fig_style(fig, t(f'{g.index[0]}: {g.order_share.iloc[0]:.0f}% of orders, {g.spend_share.iloc[0]:.1f}% of spend',
                              f'{g.index[0]}: {g.order_share.iloc[0]:.0f}% من الطلبات و {g.spend_share.iloc[0]:.1f}% من الصرف')))
with u.card():
    cut = st.slider(t('Cut this share of spend that shows no measured effect', 'نقلل النسبة دي من الصرف اللي ملوش أثر'), 0, 50, 25, 5)
    saved = mf.spend.iloc[-1] * cut / 100
    u.kpis([(t('Saved a year', 'توفير في السنة'), u.M(saved), t('EGP', 'جنيه'), True),
            (t('New budget', 'الميزانية الجديدة'), u.M(mf.spend.iloc[-1] - saved), t('split by demand', 'متقسمة حسب الطلب'), False),
            (t('Ledger vs campaigns', 'الدفاتر مقابل الحملات'), f"{pf['marketing_ledger'] / 1e6:.1f}M / {pf['marketing_campaigns'] / 1e6:.0f}M", t('one source of truth needed', 'محتاجين مصدر واحد'), False)])
    g2 = g.assign(new_budget=g.order_share / 100 * (mf.spend.iloc[-1] - saved)).reset_index()
    show_g = g2[['governorate_ar', 'orders', 'order_share', 'spend', 'spend_share', 'new_budget']].round(1)
    show_g.columns = [t('Governorate', 'المحافظة'), t('Orders', 'الطلبات'), t('% orders', '% الطلبات'), t('Spend', 'الصرف'), t('% spend', '% الصرف'), t('Budget by demand', 'الميزانية حسب الطلب')]
    u.table(show_g, height=300)
u.note(t('Judge channels by real orders in holdout tests: pause ads in matched governorates for 4 weeks and compare. Keep only what the test proves.',
         'نقيّم القنوات بالطلبات الحقيقية في تجربة Holdout: نوقف الإعلان في محافظات شبه بعض 4 أسابيع ونقارن، ونكمّل في اللي التجربة تثبته.'))
u.footer('06_card03_customers · 10_card07_marketing')
