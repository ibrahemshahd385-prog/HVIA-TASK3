import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('🚚 Procurement & Imports', '🚚 المشتريات والاستيراد'),
         t('Do we buy what we sell?', 'بنشتري اللي بنبيعه؟'), '09_card06_purchasing · 12_ai_demand_forecast')

pf = u.purchasing_fy()
s = u.sku_bought_sold()
k = st.columns(4)
u.kpi(k[0], t('Pieces bought FY2026', 'قطع اتشرت FY2026'), f'{pf.bought.iloc[-1] / 1e6:.1f}M')
u.kpi(k[1], t('Pieces sold FY2026', 'قطع اتباعت FY2026'), f'{pf.sold.iloc[-1] / 1e3:,.0f}K')
u.kpi(k[2], t('Bought per sold', 'المشترى لكل متباع'), f'×{pf.ratio.iloc[-1]:.0f}', inverse=True)
u.kpi(k[3], t('SKU correlation bought ↔ sold', 'ارتباط الشراء بالبيع لكل SKU'), f'{s.corr().iloc[0, 1]:.2f}')

left, right = st.columns(2)
with left:
    fig = go.Figure(go.Bar(x=pf.index, y=pf.ratio, marker_color=[u.ORANGE if x == pf.index[-1] else u.BLUE for x in pf.index],
                           text=[f'×{v:.0f}' for v in pf.ratio], textposition='outside'))
    fig.update_yaxes(title=t('pieces bought per piece sold', 'قطع اتشرت لكل قطعة اتباعت'), range=[0, pf.ratio.max() * 1.2])
    u.show(u.style(fig, t('~42M pieces bought every year, while sales doubled', 'حوالي 42 مليون قطعة كل سنة، والمبيعات اتضاعفت')))
with right:
    fig = go.Figure(go.Scatter(x=s.sold / 1e3, y=s.bought / 1e3, mode='markers', marker=dict(color=u.BLUE, size=6, opacity=0.6)))
    fig.update_xaxes(title=t('thousand pieces sold per SKU', 'ألف قطعة اتباعت لكل SKU'))
    fig.update_yaxes(title=t('thousand pieces bought per SKU', 'ألف قطعة اتشرت لكل SKU'), range=[0, s.bought.max() / 1e3 * 1.15])
    u.show(u.style(fig, t('Every SKU gets the same purchase, whatever it sells', 'كل SKU بياخد نفس الشراء، مهما باع')))

u.honest(t(f"Purchase spend in FY2026 = {pf.spend.iloc[-1] / 1e9:.1f}B EGP vs {pf.cogs.iloc[-1] / 1e6:.0f}M cost of goods sold (×{pf.spend.iloc[-1] / pf.cogs.iloc[-1]:.0f}). "
           "Either the unit is not 'piece' (dozen? kg?) or these are not real purchases → first question to the company. We use purchases for comparisons only.",
           f"صرف الشراء في FY2026 = {pf.spend.iloc[-1] / 1e9:.1f} مليار جنيه مقابل {pf.cogs.iloc[-1] / 1e6:.0f} مليون تكلفة البضاعة المباعة (×{pf.spend.iloc[-1] / pf.cogs.iloc[-1]:.0f}). "
           "يا إما الوحدة مش قطعة (دستة؟ كيلو؟) يا إما دي مش مشتريات حقيقية → أول سؤال للشركة. وبنستخدم المشتريات للمقارنة بس."))

c = u.load()
po, im = c['pos'], c['imports']
st.subheader(t('Suppliers & imports – what we can and cannot trust', 'الموردين والاستيراد – نثق في إيه ومنثقش في إيه'))
a, b = st.columns(2)
with a:
    cnt = po.groupby('supplier_id').size()
    st.markdown(t(f"""
- **{po.supplier_id.nunique()} suppliers**, each with {cnt.min()}–{cnt.max()} purchase orders → no main supplier, no negotiation power.
- Declared supplier types (dyes, logistics, machinery…) all supply finished garments → the supplier master needs cleaning.
- Lead time 3–55 days spread evenly → random; no supplier scorecard is possible.
- ✅ Usable: purchase unit cost ≈ **70%** of the cost booked on sales.
""", f"""
- **{po.supplier_id.nunique()} مورد**، كل واحد ليه {cnt.min()}–{cnt.max()} أمر شراء → مفيش مورد رئيسي ولا قوة تفاوض.
- أنواع الموردين (أصباغ، لوجستيات، ماكينات…) كلهم بيوردوا ملابس جاهزة → بيانات الموردين محتاجة تتنضف.
- مدة التوريد من 3 لـ 55 يوم متوزعة بالتساوي → عشوائية؛ مينفعش نعمل تقييم موردين.
- ✅ ينفع: تكلفة الشراء للقطعة حوالي **70%** من التكلفة المسجلة على المبيعات.
"""))
with b:
    y = im[(im.fy >= 2019) & (im.fy <= 2026)].groupby('fy').customs_value_USD.sum() / 1e6
    fig = go.Figure(go.Bar(x=y.index, y=y.values, marker_color=u.GREY))
    fig.update_yaxes(title=t('M USD imported', 'مليون دولار استيراد'))
    fr = im.groupby('container_type').freight_USD.mean()
    u.show(u.style(fig, t(f"Imports flat ~55M USD/yr; 40FT freight = 20FT ({fr.get('40FT', 0):,.0f} vs {fr.get('20FT', 0):,.0f} USD)",
                          f"الاستيراد ثابت حوالي 55 مليون دولار/سنة؛ شحن الـ 40 قدم = الـ 20 قدم"), height=330))
plan, _ = u.plans(1.65, False)
u.insight(t(f'Fix: buy from the AI forecast (page 5 → Purchase plan): forecast + safety stock, per category and month – about {plan.to_buy.sum() / 1e3:,.0f}K pieces for Nov–Jan instead of ~{plan.current_pattern_buys.sum() / 1e6:.1f}M.',
            f'الحل: نشتري من توقّع الـ AI (صفحة 5 ← خطة الشراء): التوقّع + مخزون أمان لكل فئة وشهر – حوالي {plan.to_buy.sum() / 1e3:,.0f} ألف قطعة لنوفمبر–يناير بدل حوالي {plan.current_pattern_buys.sum() / 1e6:.1f} مليون.'))
