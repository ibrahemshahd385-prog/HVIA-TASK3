"""
Cottonil — BI & AI dashboard (HVIA Task 3).
Run it from the project folder:
    cd dashboard
    streamlit run app.py
This file only builds the menu and the language switch. Each page lives in views/.
"""
import streamlit as st
import utils as u

st.set_page_config(page_title='Cottonil BI & AI', page_icon='📊', layout='wide')

with st.sidebar:
    st.radio('Language / اللغة', ['English', u.AR], key='lang', horizontal=True)
t = u.t

pages = {
    t('Overview', 'نظرة عامة'): [
        st.Page('views/exec_center.py', title=t('1 · Executive Command Center', '1 · مركز القيادة'), icon='🎯', default=True),
    ],
    t('Apps', 'التطبيقات'): [
        st.Page('views/sales_pricing.py', title=t('2 · Sales & Pricing Intelligence', '2 · المبيعات والتسعير'), icon='💰'),
        st.Page('views/customers.py', title=t('3 · Customer 360', '3 · العميل 360'), icon='👥'),
        st.Page('views/branches.py', title=t('4 · Branches, Channels & Delivery', '4 · الفروع والقنوات والتوصيل'), icon='🗺️'),
        st.Page('views/inventory.py', title=t('5 · Smart Inventory & AI Forecast', '5 · المخزون الذكي وتوقّع الطلب'), icon='📦'),
        st.Page('views/procurement.py', title=t('6 · Procurement & Imports', '6 · المشتريات والاستيراد'), icon='🚚'),
        st.Page('views/marketing.py', title=t('7 · Marketing ROI', '7 · عائد التسويق'), icon='📣'),
        st.Page('views/people_costs.py', title=t('8 · People & Costs', '8 · الموظفين والمصاريف'), icon='🧑‍💼'),
    ],
    t('Built without being asked', 'بنيناه من غير ما يتطلب'): [
        st.Page('views/data_trust.py', title=t('9 · Data Trust Center', '9 · مركز الثقة في الداتا'), icon='🛡️'),
    ],
}

nav = st.navigation(pages)
with st.sidebar:
    st.caption('Cottonil · Wear it better')
    st.caption(t('Data: Oct 2018 – Oct 2026 · Fiscal year Oct–Sep (FY2026 = Oct 2025 – Sep 2026)',
                 'البيانات: أكتوبر 2018 – أكتوبر 2026 · السنة المالية أكتوبر–سبتمبر'))
    st.caption(t('Built by Shahd Ibrahim · HVIA Task 3', 'إعداد: شهد إبراهيم · HVIA Task 3'))
nav.run()
