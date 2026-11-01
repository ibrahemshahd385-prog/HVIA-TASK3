"""
Cottonil Analytics – shared code for every chapter of the dashboard.
  • the clean data, loaded once (cached)
  • the look: 3 colours, cards, chart style, English / العربية
  • cached wrappers around core/ (every number is calculated there, once, for notebooks, dashboard and website)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import analytics as A                                   # noqa: E402
from core import forecast as F                                    # noqa: E402
from core.build_clean import quality_report as _quality_report    # noqa: E402

# ---------------------------------------------------------------- 3 colours, nothing else
NAVY, GREY, TEAL = '#2F4B7C', '#D5DCE6', '#3AA6A0'
MID = '#9AA8BA'          # a darker shade of the same grey, for dashed lines only
INK, MUTED = '#1F2A3C', '#6B778A'

# ---------------------------------------------------------------- language
AR = 'العربية'


def is_ar():
    return st.session_state.get('lang', AR) == AR


def t(en, ar):
    return ar if is_ar() else en


CHANNEL_AR = {'Store': 'الفروع', 'Online': 'أونلاين', 'Wholesale': 'الجملة'}
SEGMENT_AR = {'Champions': 'الأبطال', 'Loyal': 'الأوفياء', 'New / Promising': 'جدد / واعدون',
              "At Risk (Can't Lose)": 'معرّضون للخسارة (مهمين)', 'At Risk': 'معرّضون للخسارة',
              'Need Attention': 'يحتاجون اهتمامًا', 'Lost': 'مفقودون'}
STATUS_AR = {'Ready': 'جاهز', 'Ready (flat)': 'جاهز (ثابت)', 'Partial': 'جزئي', 'Tested – rejected': 'اتجرّب واترفض',
             'Not reliable': 'غير موثوق', 'Not meaningful': 'بلا معنى', 'Not possible': 'غير ممكن'}
SEVERITY_AR = {'Business': 'اكتشاف بزنس', 'High': 'عالي', 'Medium': 'متوسط', 'Unreliable': 'حقل عشوائي'}
MONTHS = (['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
          ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'])


def ch_name(x):
    return CHANNEL_AR.get(x, x) if is_ar() else x


def seg_name(x):
    return SEGMENT_AR.get(x, x) if is_ar() else x


def month_names():
    return MONTHS[1] if is_ar() else MONTHS[0]


# ---------------------------------------------------------------- page look
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"] { background: #F5F7FA; }
[data-testid="stAppViewContainer"] * { font-family: 'Inter', 'IBM Plex Sans Arabic', 'Segoe UI', sans-serif; }
.block-container { padding-top: 1.2rem; max-width: 1240px; }
#MainMenu, footer { visibility: hidden; }
.ct-hero { padding: 6px 2px 10px; }
.ct-eyebrow { color: #3AA6A0; font-weight: 700; letter-spacing: .14em; font-size: 12px; text-transform: uppercase; }
.ct-title { color: #2F4B7C; font-size: 30px; font-weight: 700; margin: 2px 0 4px; line-height: 1.25; }
.ct-sub { color: #6B778A; font-size: 15px; max-width: 820px; }
.ct-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: 8px 0 16px; }
.ct-kpi { background: #fff; border: 1px solid #E6EBF2; border-radius: 14px; padding: 14px 16px; }
.ct-kpi .l { color: #6B778A; font-size: 12.5px; font-weight: 600; }
.ct-kpi .v { color: #2F4B7C; font-size: 26px; font-weight: 700; margin-top: 2px; }
.ct-kpi .s { font-size: 12.5px; margin-top: 2px; color: #6B778A; }
.ct-kpi .s.teal { color: #3AA6A0; font-weight: 600; }
.ct-kpi.accent { border-color: #3AA6A0; box-shadow: inset 0 3px 0 #3AA6A0; }
.ct-note { background: #fff; border: 1px solid #E6EBF2; border-inline-start: 4px solid #3AA6A0; border-radius: 10px; padding: 12px 16px; color: #1F2A3C; margin: 6px 0 14px; }
.ct-caution { background: #fff; border: 1px solid #E6EBF2; border-inline-start: 4px solid #9AA8BA; border-radius: 10px; padding: 12px 16px; color: #1F2A3C; margin: 6px 0 14px; }
.ct-section { color: #2F4B7C; font-size: 19px; font-weight: 700; margin: 18px 0 2px; }
.ct-section-sub { color: #6B778A; font-size: 13.5px; margin-bottom: 8px; }
.ct-story { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin: 6px 0 14px; }
.ct-story div { background: #fff; border: 1px solid #E6EBF2; border-radius: 12px; padding: 12px 14px; color: #1F2A3C; font-size: 14px; }
.ct-story b { color: #2F4B7C; display: block; font-size: 13px; margin-bottom: 2px; }
[data-testid="stVerticalBlockBorderWrapper"] { background: #fff; border-radius: 14px; border-color: #E6EBF2 !important; }
.ct-foot { color: #6B778A; font-size: 12.5px; margin-top: 26px; border-top: 1px solid #E6EBF2; padding-top: 10px; }
</style>"""

CSS_AR = """
<style>
[data-testid="stAppViewContainer"] * { font-family: 'IBM Plex Sans Arabic', 'Segoe UI', sans-serif; }
.ct-hero, .ct-kpis, .ct-note, .ct-caution, .ct-section, .ct-section-sub, .ct-story, .ct-foot,
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"], [data-testid="stExpander"] summary { direction: rtl; text-align: right; }
</style>"""


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)
    if is_ar():
        st.markdown(CSS_AR, unsafe_allow_html=True)


def hero(eyebrow, title, sub):
    st.markdown(f'<div class="ct-hero"><div class="ct-eyebrow">{eyebrow}</div><div class="ct-title">{title}</div>'
                f'<div class="ct-sub">{sub}</div></div>', unsafe_allow_html=True)


def kpis(items):
    """items = [(label, value, sub, accent)] → one row of cards."""
    cells = ''.join(f'<div class="ct-kpi{" accent" if acc else ""}"><div class="l">{l}</div><div class="v">{v}</div>'
                    f'<div class="s{" teal" if acc else ""}">{s or "&nbsp;"}</div></div>' for l, v, s, acc in items)
    st.markdown(f'<div class="ct-kpis">{cells}</div>', unsafe_allow_html=True)


def section(title, sub=''):
    st.markdown(f'<div class="ct-section">{title}</div>' + (f'<div class="ct-section-sub">{sub}</div>' if sub else ''), unsafe_allow_html=True)


def note(text):
    st.markdown(f'<div class="ct-note">{text}</div>', unsafe_allow_html=True)


def caution(text):
    st.markdown(f'<div class="ct-caution">🧪 {text}</div>', unsafe_allow_html=True)


def story(items):
    st.markdown('<div class="ct-story">' + ''.join(f'<div><b>{h}</b>{b}</div>' for h, b in items) + '</div>', unsafe_allow_html=True)


def footer(source):
    st.markdown(f'<div class="ct-foot">{t("Source notebooks", "النوت بوكس المصدر")}: ⁦{source}⁩ · '
                f'{t("Fiscal year Oct–Sep · FY2026 = Oct 2025 – Sep 2026", "السنة المالية أكتوبر–سبتمبر · FY2026 = أكتوبر 2025 – سبتمبر 2026")}</div>',
                unsafe_allow_html=True)


def fig_style(fig, title='', height=360, legend=False):
    fig.update_layout(
        title=dict(text=f'<b>{title}</b>' if title else '', x=1 if is_ar() else 0, xanchor='right' if is_ar() else 'left',
                   y=0.97, yanchor='top', yref='container', font=dict(size=15, color=NAVY)),
        height=height, margin=dict(l=60, r=20, t=62 if title else 20, b=10),
        paper_bgcolor='white', plot_bgcolor='white', showlegend=legend,
        font=dict(family='Inter, IBM Plex Sans Arabic, Segoe UI, sans-serif', size=12.5, color=INK),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0), hoverlabel=dict(bgcolor='white'),
        colorway=[NAVY, TEAL, GREY])
    fig.update_xaxes(showgrid=False, linecolor='#E6EBF2', ticks='')
    fig.update_yaxes(gridcolor='#EEF2F7', zeroline=False, linecolor='#E6EBF2')
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


def card():
    return st.container(border=True)


def M(x):
    return f'{x / 1e6:,.1f}M'


def csv_button(df, label, name):
    st.download_button(label, df.to_csv(index=False).encode('utf-8-sig'), file_name=name, mime='text/csv')


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
