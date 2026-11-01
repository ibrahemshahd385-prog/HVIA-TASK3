import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('🗺️ Branches, Channels & Delivery', '🗺️ الفروع والقنوات والتوصيل'),
         t('Which branch or channel creates value – and is delivery a real problem?',
           'أنهي فرع أو قناة بتعمل قيمة – والتوصيل مشكلة حقيقية ولا لأ؟'),
         '07_card04_branches_channels')

b = u.branch_sales(2026)
cv = b.store_sales.std() / b.store_sales.mean() * 100
pre = u.load()['orders'].before_opening
k = st.columns(4)
u.kpi(k[0], t('Branches', 'الفروع'), f'{len(b)}')
u.kpi(k[1], t('Spread of store sales', 'الفرق بين الفروع'), f'±{cv:.1f}%', help=t('coefficient of variation, FY2026', 'معامل الاختلاف، FY2026'))
u.kpi(k[2], t('Orders before the branch opened', 'طلبات قبل افتتاح الفرع'), f'{pre.sum():,}', inverse=True, help=f'{pre.mean():.1%}')
ch = u.channel_fy()
online = ch[(ch.fy == ch.fy.max()) & (ch.channel == 'Online')].share.iloc[0]
u.kpi(k[3], t('Online share FY2026', 'نصيب الأونلاين FY2026'), f'{online:.1f}%')

tab1, tab2, tab3 = st.tabs([t('Branches', 'الفروع'), t('Channels', 'القنوات'), t('Delivery, shipping & returns', 'التوصيل والشحن والمرتجعات')])
with tab1:
    bs = b.sort_values('store_sales')
    fig = go.Figure(go.Bar(x=list(range(len(bs))), y=bs.store_sales / 1e6, marker_color=u.BLUE,
                           hovertext=bs.branch_name_ar + ' · ' + bs.governorate_ar, hoverinfo='text+y'))
    fig.update_xaxes(showticklabels=False, title=t('80 branches, sorted', '80 فرع مترتبين'))
    fig.update_yaxes(title=t('FY2026 store sales, M EGP', 'مبيعات الفرع FY2026، مليون'), range=[0, bs.store_sales.max() / 1e6 * 1.15])
    u.show(u.style(fig, t(f'All 80 branches sell almost the same (±{cv:.1f}%) – a branch ranking would be noise',
                          f'الـ 80 فرع بيبيعوا تقريبًا زي بعض (±{cv:.1f}%) – ترتيب الفروع هيبقى عشوائي')))
    u.honest(t('Honest limit: we do **not** rank branches or choose a new store location from this data. The "Branch Performance" and '
               '"New Store Expansion" ideas need real branch traffic, size, rent, demographics and confirmed opening dates (see the Data Trust Center).',
               'حد صريح: **مش** هنرتّب الفروع ولا نختار مكان فرع جديد من الداتا دي. فكرة "أداء الفروع" و"التوسع" محتاجين زيارات الفروع، '
               'ومساحتها، وإيجارها، وبيانات السكان، وتواريخ افتتاح مؤكدة (شوفي مركز الثقة في الداتا).'))
    u.table(b.sort_values('store_sales', ascending=False).head(10).reset_index().assign(store_sales=lambda d: (d.store_sales / 1e6).round(2),
            opening_date=lambda d: d.opening_date.dt.date)[['branch_id', 'branch_name_ar', 'governorate_ar', 'retail_location_type', 'opening_date', 'store_sales']])

with tab2:
    left, right = st.columns(2)
    with left:
        fig = go.Figure()
        for c_ in ['Store', 'Wholesale', 'Online']:
            x = ch[ch.channel == c_]
            fig.add_trace(go.Scatter(x=x.fy, y=x.share, name=u.ch_name(c_), mode='lines+markers', line=dict(color=u.CHANNEL_COLORS[c_], width=2.5)))
        fig.update_yaxes(title=t('% of net sales', '% من المبيعات'), range=[0, 60])
        u.show(u.style(fig, t('The channel mix has not moved in 8 years', 'نصيب القنوات ماتحركش في 8 سنين'), legend=True))
    with right:
        li, so = u.load()['lines'], u.load()['orders']
        upo = (li.groupby('channel').quantity.sum() / so.groupby('channel').size()).reindex(['Store', 'Online', 'Wholesale'])
        fig = go.Figure(go.Bar(x=[u.ch_name(c_) for c_ in upo.index], y=upo.values, marker_color=[u.GREY, u.GREY, u.BLUE],
                               text=[f'{v:.1f}' for v in upo.values], textposition='outside'))
        fig.update_yaxes(title=t('pieces per order', 'قطع في الطلب'), range=[0, upo.max() * 1.25])
        u.show(u.style(fig, t('A wholesale order is ~24 pieces vs ~4.3 – a real B2B pattern', 'طلب الجملة حوالي 24 قطعة مقابل 4.3 – نمط جملة حقيقي')))

with tab3:
    sf = u.shipping_facts()
    left, right = st.columns(2)
    with left:
        ds = sf['delivery_share']
        fig = go.Figure(go.Bar(x=[str(i) for i in ds.index], y=ds.values, marker_color=u.GREY))
        fig.update_yaxes(title=t('% of shipments', '% من الشحنات'), range=[0, 20])
        fig.update_xaxes(title=t('delivery days', 'أيام التوصيل'))
        u.show(u.style(fig, t(f"Every delivery time 1–7 days is ~14% – Cairo {sf['delivery_by_gov'].min():.1f} = Aswan {sf['delivery_by_gov'].max():.1f} days",
                              f"كل مدة من 1 لـ 7 أيام حوالي 14% – القاهرة زي أسوان (حوالي 4 أيام)")))
        u.honest(t('Delivery time and the "Delayed" status are random (3% delayed whatever the days) → no delivery KPI until real carrier scans exist.',
                   'مدة التوصيل وحالة "متأخر" عشوائيين (3% متأخر مهما كانت الأيام) → مفيش مؤشر توصيل لحد ما يبقى فيه تواريخ حقيقية من شركات الشحن.'))
    with right:
        fb = sf['free_by_size']
        fig = go.Figure(go.Bar(x=[str(i) for i in fb.index], y=fb.values, marker_color=u.BLUE, text=[f'{v:.0f}%' for v in fb.values], textposition='outside'))
        fig.update_yaxes(title=t('% shipped free', '% شحن مجاني'), range=[0, 25])
        fig.update_xaxes(title=t('order size (quintiles)', 'حجم الطلب'))
        u.show(u.style(fig, t('Free shipping goes to 14% of orders of every size', 'الشحن المجاني بيروح لـ 14% من الطلبات من كل الأحجام')))
        th = st.select_slider(t('Free shipping only above (EGP)', 'شحن مجاني فوق (جنيه)'), [500, 750, 1000, 1500, 2000], 1000)
        n, saved = u.free_shipping_saving(th)
        st.markdown(t(f'→ **{n:,}** free shipments a year fall below {th:,} EGP = **{saved:,.0f} EGP** of fees recovered. Small money, but a clear rule.',
                      f'→ **{n:,}** شحنة مجانية في السنة تحت {th:,} جنيه = **{saved:,.0f} جنيه** رسوم بترجع. فلوس صغيرة، بس قاعدة واضحة.'))
    fy = u.fy_summary()
    st.markdown(t(f"**Returns:** refunds are a stable {fy.refund_pct.min():.1f}–{fy.refund_pct.max():.1f}% of sales every year; the 5 reasons are exactly ~20% each → a real reason form is needed.",
                  f"**المرتجعات:** الاسترداد ثابت {fy.refund_pct.min():.1f}–{fy.refund_pct.max():.1f}% من المبيعات كل سنة؛ والـ 5 أسباب كل واحد حوالي 20% بالظبط → محتاجين فورم حقيقي للسبب."))
