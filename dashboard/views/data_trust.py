import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('🛡️ Data Trust Center', '🛡️ مركز الثقة في الداتا'),
         t('HVIA proposed 22 apps. Which of them can this data honestly support – and what data would unlock the rest?',
           'HVIA اقترحوا 22 تطبيق. أنهي واحد فيهم الداتا تقدر تشيله بأمانة – وإيه الداتا اللي تفتح الباقي؟'),
         '02_data_model · 03_data_cleaning · 15_app_data_trust')
st.caption(t('Built without being asked: before trusting a nice chart, the manager should know which numbers are real.',
             'عملناه من غير ما يتطلب: قبل ما المدير يصدّق رسمة حلوة، لازم يعرف أنهي أرقام حقيقية.'))

r = u.readiness()
dq = u.quality_report()
order = ['Ready', 'Ready (flat)', 'Partial', 'Tested – rejected', 'Not reliable', 'Not meaningful', 'Not possible']
cnt = r.status.value_counts().reindex(order).dropna()
k = st.columns(4)
u.kpi(k[0], t('Ideas fully supported', 'أفكار الداتا بتشيلها'), f"{int(cnt.get('Ready', 0) + cnt.get('Ready (flat)', 0))} / 22")
u.kpi(k[1], t('Partial', 'جزئي'), f"{int(cnt.get('Partial', 0))}")
u.kpi(k[2], t('Not possible / not reliable', 'غير ممكن / غير موثوق'), f"{int(cnt.drop(['Ready', 'Ready (flat)', 'Partial'], errors='ignore').sum())}")
u.kpi(k[3], t('Data quality issues', 'مشاكل جودة الداتا'), f'{len(dq)}')

colors = {'Ready': u.AQUA, 'Ready (flat)': u.AQUA, 'Partial': u.BLUE, 'Tested – rejected': u.ORANGE, 'Not reliable': u.ORANGE, 'Not meaningful': u.GREY, 'Not possible': u.GREY}
fig = go.Figure(go.Bar(y=[u.STATUS_AR.get(s, s) if u.is_ar() else s for s in cnt.index[::-1]], x=cnt.values[::-1], orientation='h',
                       marker_color=[colors[s] for s in cnt.index[::-1]], text=[int(v) for v in cnt.values[::-1]], textposition='outside'))
u.show(u.style(fig, t('The 22 HVIA app ideas, checked against the data', 'الـ 22 فكرة من HVIA، متراجعين على الداتا'), height=330))

tab1, tab2, tab3 = st.tabs([t('22 ideas – readiness', 'الـ 22 فكرة – الجاهزية'), t('Data quality report', 'تقرير جودة الداتا'), t('What to ask the company', 'نسأل الشركة إيه')])
with tab1:
    pick = st.multiselect(t('Status', 'الحالة'), order, default=order, format_func=lambda s: u.STATUS_AR.get(s, s) if u.is_ar() else s)
    x = r[r.status.isin(pick)].copy()
    x.columns = [t('PDF page', 'صفحة'), t('Idea', 'الفكرة'), t('Status', 'الحالة'), t('Why', 'ليه'), t('Data that would unlock it', 'الداتا اللي تفتحها')]
    u.table(x)
with tab2:
    sev = st.multiselect(t('Severity', 'الخطورة'), ['Business', 'High', 'Medium', 'Unreliable'], default=['Business', 'High', 'Medium', 'Unreliable'],
                         format_func=lambda s: u.SEVERITY_AR.get(s, s) if u.is_ar() else s)
    st.markdown(t('**Business** = not an error, a finding to act on · **High** = breaks an important analysis · **Medium** = a system gap · **Unreliable** = filled at random, nothing is built on it',
                  '**اكتشاف بزنس** = مش غلط، ده اكتشاف لازم نتصرف فيه · **عالي** = بيبوّظ تحليل مهم · **متوسط** = فجوة في السيستم · **حقل عشوائي** = متملي بالقرعة ومش بنبني عليه حاجة'))
    u.table(dq[dq.severity.isin(sev)][['id', 'area', 'table', 'issue', 'evidence', 'severity', 'action']])
    u.csv_button(dq, t('⬇️ Download the report (CSV)', '⬇️ نزّلي التقرير (CSV)'), 'cottonil_data_quality_report.csv')
with tab3:
    q = u.data_requests()
    for _, row in q.iterrows():
        icon = {'High': '🔴', 'Medium': '🟠', 'Low': '⚪'}[row.priority]
        st.markdown(f"{icon} **{row.area}:** {row.request_ar if u.is_ar() else row.request}")
u.insight(t('Same honesty as the churn test: we show what works, what does not, and exactly which data would make the rest possible.',
            'نفس أمانة اختبار الـ churn: بنوري إيه اللي شغال، وإيه اللي لأ، وإيه الداتا بالظبط اللي تخلّي الباقي ممكن.'))
