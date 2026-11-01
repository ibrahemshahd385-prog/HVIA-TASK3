import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('👥 Customer 360', '👥 العميل 360'),
         t('Who comes back – and can we trust the customer data enough to build loyalty on it?',
           'مين بيرجع يشتري – وهل داتا العملاء تنفع نبني عليها برنامج ولاء؟'),
         '06_card03_customers · 13_ai_churn_test')

cf = u.customer_facts()
p = u.rfm()
k = st.columns(5)
u.kpi(k[0], t('Active customers FY2026', 'عملاء نشطين FY2026'), f"{cf['active_by_fy'].iloc[-1]:,}")
u.kpi(k[1], t('Bought more than once', 'اشتروا أكتر من مرة'), f'{(p.orders > 1).mean():.0%}')
s = p.spend.sort_values(ascending=False)
u.kpi(k[2], t('Top 20% of customers', 'أعلى 20% عملاء'), f'{s.head(len(s) // 5).sum() / s.sum():.0%}', help=t('share of retail revenue', 'نصيبهم من إيراد القطاعي'))
u.kpi(k[3], t('Orders with no customer', 'طلبات من غير عميل'), f"{cf['guest_share']:.0f}%", inverse=True)
u.kpi(k[4], t('Branches per "loyal" customer', 'فروع لكل عميل "وفي"'), f"{cf['loyal_branches']:.1f}", inverse=True,
      help=t(f"customers with 5+ store visits: {cf['loyal_visits']:.1f} visits in {cf['loyal_branches']:.1f} branches and {cf['loyal_govs']:.1f} governorates",
             f"العملاء اللي زاروا 5 مرات أو أكتر: {cf['loyal_visits']:.1f} زيارة في {cf['loyal_branches']:.1f} فرع و {cf['loyal_govs']:.1f} محافظة"))

tab1, tab2, tab3 = st.tabs([t('Can we trust the customer ID?', 'نقدر نثق في كود العميل؟'), t('RFM segments', 'شرايح RFM'), t('Win-back test list', 'قايمة تجربة الاسترجاع')])
with tab1:
    left, right = st.columns(2)
    with left:
        g = cf['guest_by_channel']
        fig = go.Figure(go.Bar(x=[u.ch_name(c) for c in g.index], y=g.values, marker_color=[u.ORANGE if c == 'Online' else u.BLUE for c in g.index],
                               text=[f'{v:.1f}%' for v in g.values], textposition='outside'))
        fig.update_yaxes(title=t('% of orders without a customer', '% طلبات من غير عميل'), range=[0, 30])
        u.show(u.style(fig, t('19% of orders have no customer – even online, where a phone number is a must', '19% من الطلبات من غير عميل – حتى الأونلاين اللي لازم فيه رقم موبايل')))
    with right:
        st.markdown('#### ' + t('Three signs the ID is weak', '3 علامات إن كود العميل ضعيف'))
        st.markdown(t(f"""
- A customer with 5+ store visits shops in **{cf['loyal_branches']:.1f} different branches** and **{cf['loyal_govs']:.1f} governorates**.
- **{cf['wholesale_by_retail_customers']:.0f}%** of wholesale orders (~24 pieces each) come from customers registered as *Retail*.
- Age band and governorate are spread evenly – they do not describe real people.
""", f"""
- العميل اللي زار 5 مرات أو أكتر بيشتري من **{cf['loyal_branches']:.1f} فرع مختلف** و **{cf['loyal_govs']:.1f} محافظة**.
- **{cf['wholesale_by_retail_customers']:.0f}%** من طلبات الجملة (حوالي 24 قطعة) جاية من عملاء متسجلين *قطاعي*.
- السن والمحافظة متوزعين بالتساوي – مش بيوصفوا ناس حقيقيين.
"""))
        u.insight(t('Fix first: one loyalty ID (phone number) at every till and online checkout, plus a reseller flag. Then personalise.',
                    'نصلّح الأول: كود ولاء واحد (رقم الموبايل) في كل كاشير وفي الأونلاين، وعلامة للتاجر. وبعدين نعمل عروض شخصية.'))

with tab2:
    seg = p.groupby('segment').agg(customers=('orders', 'size'), revenue=('spend', 'sum'), avg_orders=('orders', 'mean'))
    seg['pct_rev'] = seg.revenue / seg.revenue.sum() * 100
    seg['pct_cust'] = seg.customers / seg.customers.sum() * 100
    seg = seg.sort_values('pct_rev')
    fig = go.Figure()
    fig.add_trace(go.Bar(y=[u.seg_name(s_) for s_ in seg.index], x=seg.pct_cust, orientation='h', name=t('% of customers', '% من العملاء'), marker_color=u.LIGHT_BLUE))
    fig.add_trace(go.Bar(y=[u.seg_name(s_) for s_ in seg.index], x=seg.pct_rev, orientation='h', name=t('% of revenue', '% من الإيراد'), marker_color=u.BLUE))
    fig.update_layout(barmode='group')
    u.show(u.style(fig, t('RFM: who bought recently, how often and how much (a description, not a prediction)',
                          'RFM: مين اشترى قريب، وكام مرة، وبكام (وصف مش توقّع)'), height=440, legend=True))
    ct = u.churn_test()
    u.honest(t(f"**Honest test – churn model rejected.** We trained an AI model on orders up to 31 Mar 2026 to predict who would not buy in the next 6 months. "
               f"AUC = **{ct['auc_model']:.2f}** (0.5 = coin flip); the simple rule 'older last purchase = riskier' gets {ct['auc_recency_rule']:.2f}. "
               f"Customers come back at ~{ct['buy_again_by_recency'].mean():.0f}% whatever their last purchase date. So the segments above describe the past; they do not predict.",
               f"**اختبار بأمانة – موديل الـ churn اترفض.** درّبنا موديل AI على الطلبات لحد 31 مارس 2026 عشان يتوقّع مين مش هيشتري في الـ 6 شهور الجاية. "
               f"AUC = **{ct['auc_model']:.2f}** (0.5 = رمي عملة)؛ والقاعدة البسيطة 'آخر شراء أقدم = أخطر' جابت {ct['auc_recency_rule']:.2f}. "
               f"العملاء بيرجعوا بنسبة حوالي {ct['buy_again_by_recency'].mean():.0f}% مهما كان آخر شراء. يعني الشرايح وصف للي حصل، مش توقّع."))
    b = ct['buy_again_by_recency']
    fig = go.Figure(go.Bar(x=[str(i) for i in b.index], y=b.values, marker_color=u.BLUE, text=[f'{v:.0f}%' for v in b.values], textposition='outside'))
    fig.update_yaxes(title=t('% who bought again in 6 months', '% اللي رجعوا اشتروا في 6 شهور'), range=[0, 60])
    fig.update_xaxes(title=t('time since last purchase', 'من إمتى آخر شراء'))
    u.show(u.style(fig, t('The return rate is flat – nothing in the data predicts who leaves', 'نسبة الرجوع ثابتة – مفيش حاجة في الداتا بتتوقّع مين هيمشي'), height=340))

with tab3:
    st.markdown(t("Because no model can predict who leaves, we **test** instead: the *At Risk (Can't Lose)* customers are split at random into two halves. "
                  "**Test** gets the win-back offer, **Control** gets nothing. After 3 months the difference in their return rate = the real effect of the offer.",
                  "عشان مفيش موديل يقدر يتوقّع مين هيمشي، **بنجرّب**: عملاء *معرّضون للخسارة (لا يمكن خسارتهم)* بيتقسموا عشوائي نصين. "
                  "**Test** ياخدوا عرض الاسترجاع، و **Control** مياخدوش حاجة. بعد 3 شهور الفرق في نسبة رجوعهم = الأثر الحقيقي للعرض."))
    lst = p[p.segment == "At Risk (Can't Lose)"][['customer_id', 'last', 'orders', 'spend', 'recency_days']].copy()
    rng = np.random.default_rng(42)
    lst['group'] = np.where(rng.random(len(lst)) < 0.5, 'Test', 'Control')
    lst = lst.sort_values('spend', ascending=False)
    k = st.columns(3)
    u.kpi(k[0], t('Customers in the list', 'عملاء في القايمة'), f'{len(lst):,}')
    u.kpi(k[1], t('Test / Control', 'تجربة / مقارنة'), f"{(lst.group == 'Test').sum():,} / {(lst.group == 'Control').sum():,}")
    u.kpi(k[2], t('Their past spend', 'صرفهم اللي فات'), u.money(lst.spend.sum() / 1e6))
    u.table(lst.head(200).assign(last=lst['last'].dt.date, spend=lst.spend.round(0)))
    u.csv_button(lst, t('⬇️ Download the test list (CSV)', '⬇️ نزّلي قايمة التجربة (CSV)'), 'cottonil_winback_test_control.csv')
