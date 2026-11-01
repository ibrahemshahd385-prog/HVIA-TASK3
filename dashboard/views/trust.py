import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
r, dq = u.readiness(), u.quality_report()
order = ['Ready', 'Ready (flat)', 'Partial', 'Tested – rejected', 'Not reliable', 'Not meaningful', 'Not possible']
cnt = r.status.value_counts().reindex(order).dropna()
ready = int(cnt.get('Ready', 0) + cnt.get('Ready (flat)', 0))

u.hero(t('Chapter 6 · Data trust', 'الفصل 6 · الثقة في الداتا'),
       t(f'Of HVIA’s 22 app ideas, the data fully supports {ready}', f'من الـ 22 فكرة بتاعة HVIA، الداتا بتشيل {ready} بس كاملين'),
       t('Before trusting a good-looking chart, the manager should know which numbers are real – and what data would unlock the rest.',
         'قبل ما المدير يصدّق رسمة حلوة، لازم يعرف أنهي أرقام حقيقية – وإيه الداتا اللي تفتح الباقي.'))

u.kpis([(t('Fully supported', 'جاهزين'), f'{ready} / 22', '', True),
        (t('Partial', 'جزئي'), f"{int(cnt.get('Partial', 0))}", '', False),
        (t('Not possible / not reliable', 'غير ممكن / غير موثوق'), f"{22 - ready - int(cnt.get('Partial', 0))}", '', False),
        (t('Data quality issues', 'ملاحظات جودة'), f'{len(dq)}', t(f"{(dq.severity == 'Unreliable').sum()} random fields", f"{(dq.severity == 'Unreliable').sum()} حقول عشوائية"), False)])

left, right = st.columns([2, 3])
with left, u.card():
    colors = {'Ready': u.TEAL, 'Ready (flat)': u.TEAL, 'Partial': u.NAVY}
    fig = go.Figure(go.Bar(y=[u.STATUS_AR.get(s, s) if u.is_ar() else s for s in cnt.index[::-1]], x=cnt.values[::-1], orientation='h',
                           marker_color=[colors.get(s, u.GREY) for s in cnt.index[::-1]], text=[int(v) for v in cnt.values[::-1]], textposition='outside'))
    u.show(u.fig_style(fig, t('The 22 ideas, checked', 'الـ 22 فكرة بعد المراجعة'), height=340))
with right, u.card():
    x = r.copy()
    x['status'] = [u.STATUS_AR.get(s, s) if u.is_ar() else s for s in x.status]
    x.columns = [t('Page', 'صفحة'), t('Idea', 'الفكرة'), t('Status', 'الحالة'), t('Why', 'ليه'), t('Unlock with', 'يتفتح بـ')]
    u.table(x, height=340)

u.section(t('What the company should send us', 'نطلب إيه من الشركة'))
q = u.data_requests()
u.story([(('● ' if row.priority == 'High' else '○ ') + row.area, row.request_ar if u.is_ar() else row.request) for _, row in q.iterrows()])

u.section(t('Fields we do not build decisions on', 'حقول مش بنبني عليها قرارات'))
left, right = st.columns(2)
with left, u.card():
    b = u.branch_sales(2026).sort_values('store_sales')
    fig = go.Figure(go.Bar(x=list(range(len(b))), y=b.store_sales / 1e6, marker_color=u.NAVY, hovertext=b.branch_name_ar, hoverinfo='text+y'))
    fig.update_xaxes(showticklabels=False, title=t('80 branches, sorted', '80 فرع مترتبين'))
    fig.update_yaxes(title=t('FY2026 store sales, M EGP', 'مبيعات الفرع FY2026، مليون'), range=[0, b.store_sales.max() / 1e6 * 1.15])
    cv = b.store_sales.std() / b.store_sales.mean() * 100
    u.show(u.fig_style(fig, t(f'Branches sell within ±{cv:.0f}% – no ranking', f'الفروع بتبيع في حدود ±{cv:.0f}% – مفيش ترتيب'), height=320))
with right, u.card():
    pf = u.people_facts()
    pm = pf['paid_per_month']
    fig = go.Figure(go.Scatter(x=pm.index, y=pm.values, line=dict(color=u.TEAL, width=2.4)))
    fig.add_hline(y=pf['employees'], line=dict(color=u.MID, dash='dash'))
    fig.update_yaxes(title=t('employees paid in the month', 'موظفين اتقبضوا في الشهر'), range=[0, 700])
    u.show(u.fig_style(fig, t(f"Payroll covers at most {pm.max()} of {pf['employees']}", f"المرتبات بتغطي {pm.max()} من {pf['employees']} بالكتير"), height=320))
sf = u.shipping_facts()
u.story([
    (t('HR roles', 'الوظايف'), t(f"{pf['no_manager']} branches without a store manager, {pf['no_cashier']} without a cashier; salary does not depend on the job.",
                                 f"{pf['no_manager']} فرع من غير مدير و {pf['no_cashier']} من غير كاشير؛ والمرتب مالوش علاقة بالوظيفة.")),
    (t('Delivery', 'التوصيل'), t(f"1–7 days spread evenly everywhere (Cairo = Aswan, ~{sf['delivery_by_gov'].mean():.0f} days); 'Delayed' is 3% whatever the time.",
                                 f"من 1 لـ 7 أيام بالتساوي في كل حتة (القاهرة = أسوان، حوالي {sf['delivery_by_gov'].mean():.0f} أيام)؛ و'متأخر' 3% مهما كانت المدة.")),
    (t('Statuses', 'الحالات'), t("'In transit' and 'Partial receipt' never close, every year since 2018.", "'في الطريق' و'استلام جزئي' عمرهم ما بيتقفلوا، كل سنة من 2018.")),
    (t('Return reasons', 'أسباب المرتجع'), t('Five reasons, exactly 20% each.', 'خمس أسباب، كل واحد 20% بالظبط.')),
])

with st.expander(t('Full data quality report', 'تقرير جودة الداتا كامل')):
    u.table(dq[['id', 'area', 'table', 'issue', 'evidence', 'severity', 'action']])
    u.csv_button(dq, t('⬇ Report (CSV)', '⬇ التقرير (CSV)'), 'cottonil_data_quality_report.csv')
u.footer('02_data_model · 03_data_cleaning · 11_card08_people_costs · 15_app_data_trust')
