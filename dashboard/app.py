"""
Cottonil Analytics – the BI & AI dashboard (HVIA Task 3).
Run from the project folder:   cd dashboard   →   streamlit run app.py
This file builds the top menu, the language switch and the shared look. Each chapter lives in views/.
"""
import streamlit as st
import utils as u

st.set_page_config(page_title='Cottonil Analytics', page_icon='🧵', layout='wide', initial_sidebar_state='expanded')
st.session_state.setdefault('lang', u.AR)
u.apply_style()
t = u.t

# ── language toggle in sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div class="ct-eyebrow" style="padding:12px 0 8px">COTTONIL · {t("Analytics", "تحليلات")}</div>', unsafe_allow_html=True)
    st.radio('Language / اللغة', [u.AR, 'English'], key='lang', horizontal=True, label_visibility='collapsed')
    st.divider()

pages = [
    st.Page('views/overview.py',             title=t('Big picture',          'الصورة الكبيرة'),     icon='📊',      default=True),
    st.Page('views/growth.py',               title=t('Growth & margin',      'النمو والهامش'),       icon='📈'),
    st.Page('views/supply.py',               title=t('Stock & supply',       'المخزون والإمداد'),    icon='📦'),
    st.Page('views/customers_marketing.py',  title=t('Customers & marketing','العملاء والتسويق'),    icon='👥'),
]
st.navigation(pages, position='sidebar').run()
