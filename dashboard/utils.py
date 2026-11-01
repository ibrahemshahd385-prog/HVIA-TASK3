"""
Shared code for every dashboard page (same design as the Sharnoubi dashboard):
  1) load the clean data once (cached)
  2) colours + chart style + KPI cards + English / العربية
  3) cached wrappers around core/analytics.py and core/forecast.py
Every number is calculated in core/ – ONE place for the notebooks, this dashboard and the website.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import analytics as A      # noqa: E402
from core import forecast as F       # noqa: E402
from core.build_clean import quality_report as _quality_report   # noqa: E402

# ---------------------------------------------------------------- colours
BLUE, ORANGE, AQUA, INK = '#2a78d6', '#eb6834', '#1baf7a', '#52514e'
LIGHT_BLUE, GREY, RED, SOFT_GREY = '#b9d3f2', '#9b9a96', '#d03b3b', '#d3d2ce'
# Rule: blue = main, grey = context, orange = the ONE thing each chart wants you to look at
CHANNEL_COLORS = {'Store': GREY, 'Wholesale': BLUE, 'Online': ORANGE}

# ---------------------------------------------------------------- language (English / العربية)
AR = 'العربية'


def is_ar():
    return st.session_state.get('lang', 'English') == AR


def t(en, ar):
    """Return the Arabic text when the user picked Arabic, else the English text."""
    return ar if is_ar() else en


CHANNEL_AR = {'Store': 'الفروع', 'Online': 'أونلاين', 'Wholesale': 'الجملة'}
SEGMENT_AR = {'Champions': 'الأبطال', 'Loyal': 'الأوفياء', 'New / Promising': 'جدد / واعدون',
              "At Risk (Can't Lose)": 'معرّضون للخسارة (لا يمكن خسارتهم)', 'At Risk': 'معرّضون للخسارة',
              'Need Attention': 'يحتاجون اهتمامًا', 'Lost': 'مفقودون'}
STATUS_AR = {'Ready': 'جاهز', 'Ready (flat)': 'جاهز (ثابت)', 'Partial': 'جزئي', 'Tested – rejected': 'اتجرّب واترفض',
             'Not reliable': 'غير موثوق', 'Not meaningful': 'بلا معنى', 'Not possible': 'غير ممكن'}
SEVERITY_AR = {'Business': 'اكتشاف بزنس', 'High': 'عالي', 'Medium': 'متوسط', 'Unreliable': 'حقل عشوائي'}


def ch_name(x):
    return CHANNEL_AR.get(x, x) if is_ar() else x


def seg_name(x):
    return SEGMENT_AR.get(x, x) if is_ar() else x


def apply_language_style():
    """Arabic: right-to-left text and an Arabic font. Charts and sliders keep their normal direction."""
    if not is_ar():
        return
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap');
h1, h2, h3, p, li, label, [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stWidgetLabel"], [data-testid="stSidebarNav"] a span {
    font-family: 'IBM Plex Sans Arabic', 'Segoe UI', sans-serif;
}
h1, h2, h3, [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], [data-testid="stMetricLabel"],
[data-testid="stWidgetLabel"], [data-testid="stAlert"], [data-testid="stExpander"] summary {
    direction: rtl; text-align: right;
}
[data-testid="stSidebarNav"], [data-testid="stSidebarUserContent"] { direction: rtl; text-align: right; }
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------- data
def _find_data_file():
    for p in [ROOT / 'clean' / 'cottonil_clean.pkl', Path(__file__).resolve().parent / 'data' / 'cottonil_clean.pkl']:
        if p.exists():
            return p
    st.error(t('The clean data is missing. In the project folder run:  python core/build_clean.py  (about 20 seconds), then refresh.',
               'الداتا النضيفة مش موجودة. من فولدر المشروع شغّلي:  python core/build_clean.py  (حوالي 20 ثانية)، وبعدين اعملي Refresh.'))
    st.stop()


@st.cache_resource(show_spinner='Loading data...')
def load():
    return A.load(_find_data_file())


# ---------------------------------------------------------------- chart helpers
def style(fig, title, height=380, legend=False):
    """Same look as the notebook charts: title = the insight, light grid, no clutter."""
    fig.update_layout(
        title=dict(text=f'<b>{title}</b>', x=1 if is_ar() else 0, xanchor='right' if is_ar() else 'left',
                   y=0.98, yanchor='top', yref='container', font=dict(size=16, color='#0b0b0b')),
        height=height, margin=dict(l=70, r=20, t=88 if legend else 60, b=10),
        paper_bgcolor='white', plot_bgcolor='white',
        font=dict(family='IBM Plex Sans Arabic, Inter, Segoe UI, sans-serif', size=13, color=INK),
        showlegend=legend, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
        hoverlabel=dict(bgcolor='white'),
    )
    fig.update_xaxes(showgrid=False, linecolor='#d6d5d0', ticks='')
    fig.update_yaxes(gridcolor='#ecebe7', zeroline=False, linecolor='#d6d5d0')
    return fig


def show(fig):
    try:
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def table(df, **kwargs):
    try:
        st.dataframe(df, width='stretch', hide_index=True, **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True, **kwargs)


def kpi(col, label, value, delta=None, inverse=False, help=None):
    """One KPI card. inverse=True means 'going up is bad' (shown in red)."""
    value = str(value)
    if value.endswith(' EGP'):
        value, label = value[:-4], f"{label} ({t('EGP', 'جنيه')})"
    kw = dict(delta=delta, delta_color='inverse' if inverse else 'normal', help=help)
    try:
        col.metric(label, value, border=True, **kw)
    except TypeError:
        col.metric(label, value, **kw)


def header(title, question, source):
    apply_language_style()
    st.title(title)
    st.markdown(f"**{t('Business question:', 'سؤال البزنس:')}** {question}")
    st.caption(f"{t('Source notebooks:', 'النوت بوكس المصدر:')} ⁦{source}⁩")


def insight(text):
    st.info(text, icon='💡')


def honest(text):
    st.warning(text, icon='🧪')


def money(x, unit='M'):
    return f'{x:,.1f}{unit} EGP'


def csv_button(df, label, name):
    st.download_button(label, df.to_csv(index=False).encode('utf-8-sig'), file_name=name, mime='text/csv')


# ---------------------------------------------------------------- cached numbers (all from core/)
@st.cache_data(show_spinner=False)
def fy_summary():
    return A.fy_summary(load())


@st.cache_data(show_spinner=False)
def monthly_sales():
    return A.monthly_sales(load())


@st.cache_data(show_spinner=False)
def channel_fy():
    return A.channel_fy(load())


@st.cache_data(show_spinner=False)
def category_fy(fy):
    return A.category_fy(load(), fy)


@st.cache_data(show_spinner=False)
def seasonality():
    return A.seasonality(load())


@st.cache_data(show_spinner=False)
def weekday():
    return A.weekday(load())


@st.cache_data(show_spinner=False)
def discount_bands():
    return A.discount_bands(load())


@st.cache_data(show_spinner=False)
def discount_facts():
    return A.discount_facts(load())


@st.cache_data(show_spinner=False)
def customer_facts():
    return A.customer_facts(load())


@st.cache_data(show_spinner=False)
def rfm():
    return A.rfm(load())


@st.cache_data(show_spinner='Testing the churn model on unseen customers...')
def churn_test():
    return A.churn_test(load())


@st.cache_data(show_spinner=False)
def branch_sales(fy):
    return A.branch_sales(load(), fy)


@st.cache_data(show_spinner=False)
def shipping_facts():
    return A.shipping_facts(load())


@st.cache_data(show_spinner=False)
def free_shipping_saving(threshold):
    return A.free_shipping_saving(load(), threshold)


@st.cache_data(show_spinner=False)
def transfers_fy():
    return A.transfers_fy(load())


@st.cache_data(show_spinner=False)
def category_mix():
    return A.category_mix(load())


@st.cache_data(show_spinner=False)
def stock_facts():
    return A.stock_facts(load())


@st.cache_data(show_spinner=False)
def allocation_saving(safety):
    return A.allocation_saving(load(), safety)


@st.cache_data(show_spinner=False)
def purchasing_fy():
    return A.purchasing_fy(load())


@st.cache_data(show_spinner=False)
def sku_bought_sold():
    return A.sku_bought_sold(load())


@st.cache_data(show_spinner=False)
def marketing_fy():
    return A.marketing_fy(load())


@st.cache_data(show_spinner=False)
def marketing_channels():
    return A.marketing_channels(load())


@st.cache_data(show_spinner=False)
def governorate_budget():
    return A.governorate_budget(load())


@st.cache_data(show_spinner=False)
def people_facts():
    return A.people_facts(load())


@st.cache_data(show_spinner=False)
def profit_bridge(stop_discount_pct, marketing_cut_pct, alloc_safety_pct, ship_threshold):
    return A.profit_bridge(load(), stop_discount_pct, marketing_cut_pct, alloc_safety_pct, ship_threshold)


@st.cache_data(show_spinner='Training the AI forecast and testing it on 6 hidden months...')
def backtest():
    return F.backtest(load())


@st.cache_data(show_spinner='Forecasting the next months...')
def forecast():
    return F.forecast(load(), horizon=4)


@st.cache_data(show_spinner=False)
def plans(service_z, trust_stock):
    fc, hist = forecast()
    return F.plans(load(), fc, hist, service_z=service_z, trust_stock=trust_stock)


@st.cache_data(show_spinner=False)
def quality_report():
    return _quality_report(load())


def readiness():
    return A.readiness()


def data_requests():
    return A.data_requests()
