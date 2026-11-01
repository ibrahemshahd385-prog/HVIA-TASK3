"""
Cottonil Analytics – the BI & AI dashboard (HVIA Task 3).
Run from the project folder:   cd dashboard   →   streamlit run app.py
This file builds the top menu, the language switch and the shared look. Each chapter lives in views/.
"""
import streamlit as st
import utils as u

st.set_page_config(page_title='Cottonil Analytics', page_icon='🧵', layout='wide', initial_sidebar_state='collapsed')
st.session_state.setdefault('lang', u.AR)
u.apply_style()
t = u.t

brand, lang = st.columns([5, 1.4])
with brand:
    st.markdown(f'<div class="ct-eyebrow" style="padding-top:8px">COTTONIL · {t("Analytics", "تحليلات")}</div>', unsafe_allow_html=True)
with lang:
    st.radio('Language / اللغة', [u.AR, 'English'], key='lang', horizontal=True, label_visibility='collapsed')

pages = [
    st.Page('views/overview.py', title=t('Big picture', 'الصورة الكبيرة'), icon=':material/insights:', default=True),
    st.Page('views/growth.py', title=t('Growth & margin', 'النمو والهامش'), icon=':material/trending_up:'),
    st.Page('views/supply.py', title=t('Stock & supply', 'المخزون والإمداد'), icon=':material/inventory_2:'),
    st.Page('views/customers_marketing.py', title=t('Customers & marketing', 'العملاء والتسويق'), icon=':material/groups:'),
    st.Page('views/ai_lab.py', title=t('AI lab', 'مختبر الـ AI'), icon=':material/neurology:'),
    st.Page('views/trust.py', title=t('Data trust', 'الثقة في الداتا'), icon=':material/verified_user:'),
]
st.navigation(pages, position='top').run()
