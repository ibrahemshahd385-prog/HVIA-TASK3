import numpy as np
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
res, bt = u.backtest()

u.hero(t('Chapter 5 · AI lab', 'الفصل 5 · مختبر الـ AI'),
       t('One model we trust, one model we rejected', 'موديل بنثق فيه، وموديل رفضناه'),
       t('The demand forecast was tested on 6 months it never saw. The churn model was tested the same way – and failed, so it is not used.',
         'توقّع الطلب اتختبر على 6 شهور ماشافهاش. وموديل الـ churn اتختبر بنفس الطريقة – وفشل، فمش بنستخدمه.'))

u.section(t('Demand forecast', 'توقّع الطلب'), t('HistGradientBoosting · monthly pieces per category × channel (48 series)', 'HistGradientBoosting · القطع الشهرية لكل فئة × قناة (48 سلسلة)'))
u.kpis([(t('AI error (WAPE)', 'خطأ الـ AI (WAPE)'), f"{res['wape_model']}%", t('Apr–Sep 2026, hidden', 'أبريل–سبتمبر 2026، مخفية'), False),
        (t("'Same month last year'", "'زي السنة اللي فاتت'"), f"{res['wape_naive']}%", t('the usual rule', 'الطريقة المعتادة'), False),
        (t('More accurate by', 'أدق بـ'), f"{res['better_%']:.0f}%", '', True)])
left, right = st.columns(2)
with left, u.card():
    tot = bt.groupby('month')[['units', 'model', 'naive']].sum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tot.index, y=tot.units / 1e3, name=t('actual', 'الحقيقي'), mode='lines+markers', line=dict(color=u.NAVY, width=2.4)))
    fig.add_trace(go.Scatter(x=tot.index, y=tot.model / 1e3, name=t('AI model', 'الموديل'), mode='lines+markers', line=dict(color=u.TEAL, width=2.4)))
    fig.add_trace(go.Scatter(x=tot.index, y=tot.naive / 1e3, name=t('same month last year', 'زي السنة اللي فاتت'), mode='lines+markers', line=dict(color=u.MID, dash='dash')))
    fig.update_yaxes(title=t('thousand pieces', 'ألف قطعة'), range=[0, tot.values.max() / 1e3 * 1.2])
    u.show(u.fig_style(fig, t('Backtest on 6 hidden months', 'اختبار على 6 شهور مخفية'), legend=True))
with right, u.card():
    fc, hist = u.forecast()
    cats = sorted(fc.category_en.unique())
    a, b = st.columns(2)
    cat = a.selectbox(t('Category', 'الفئة'), cats, index=cats.index('Socks') if 'Socks' in cats else 0)
    chn = b.selectbox(t('Channel', 'القناة'), ['Store', 'Online', 'Wholesale'], format_func=u.ch_name)
    h = hist[(hist.category_en == cat) & (hist.channel == chn)].tail(24)
    f = fc[(fc.category_en == cat) & (fc.channel == chn)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h.month, y=h.units, name=t('history', 'اللي فات'), line=dict(color=u.NAVY, width=2.4)))
    fig.add_trace(go.Scatter(x=f.month, y=f.units, name=t('forecast', 'التوقّع'), mode='lines+markers', line=dict(color=u.TEAL, width=2.4, dash='dot')))
    fig.update_yaxes(title=t('pieces per month', 'قطع في الشهر'))
    u.show(u.fig_style(fig, t(f'{cat} · {chn}', f'{cat} · {u.ch_name(chn)}'), height=300, legend=True))

with u.card():
    st.markdown('**' + t('Purchase plan · Nov 2026 – Jan 2027', 'خطة الشراء · نوفمبر 2026 – يناير 2027') + '**')
    a, b = st.columns(2)
    level = a.select_slider(t('Service level', 'مستوى الخدمة'), ['90%', '95%', '98%', '99%'], '95%')
    trust = b.toggle(t('Subtract stock on hand (after a stock count)', 'نطرح المخزون الحالي (بعد الجرد)'), value=False)
    plan, alloc = u.plans({'90%': 1.28, '95%': 1.65, '98%': 2.05, '99%': 2.33}[level], trust)
    u.kpis([(t('Demand', 'الطلب'), f'{plan.forecast_3m.sum() / 1e3:,.0f}K', t('pieces, 3 months', 'قطعة، 3 شهور'), False),
            (t('Plan: buy', 'الخطة: نشتري'), f'{plan.to_buy.sum() / 1e3:,.0f}K', t('with safety stock', 'بمخزون الأمان'), True),
            (t('Current pattern per quarter', 'النمط الحالي في الربع'), f'{plan.current_pattern_buys.sum() / 1e6:,.1f}M', '', False)])
    show_plan = plan.reset_index().rename(columns={'index': 'category_en'})
    u.table(show_plan.round(0), height=320)
    u.csv_button(show_plan, t('⬇ Purchase plan (CSV)', '⬇ خطة الشراء (CSV)'), 'cottonil_purchase_plan.csv')
    st.markdown('**' + t('Allocation plan · November 2026', 'خطة التوزيع · نوفمبر 2026') + '**')
    br = st.selectbox(t('Branch', 'الفرع'), sorted(alloc.branch_id.unique()))
    x = alloc[alloc.branch_id == br].sort_values('send_next_month', ascending=False)
    u.table(x, height=280)
    u.csv_button(alloc, t('⬇ Allocation plan, all branches (CSV)', '⬇ خطة التوزيع لكل الفروع (CSV)'), 'cottonil_allocation_plan.csv')

u.section(t('Churn model – tested and rejected', 'موديل الـ churn – اتجرّب واترفض'))
ct = u.churn_test()
u.kpis([(t('AUC – AI model', 'AUC – الموديل'), f"{ct['auc_model']:.2f}", t('0.5 = coin flip', '0.5 = رمي عملة'), True),
        (t('AUC – simple rule', 'AUC – القاعدة البسيطة'), f"{ct['auc_recency_rule']:.2f}", t('older last purchase = riskier', 'آخر شراء أقدم = أخطر'), False),
        (t('Customers tested', 'عملاء اتجرّبوا'), f"{ct['customers']:,}", t('cut-off 31 Mar 2026', 'نقطة القطع 31 مارس 2026'), False)])
left, right = st.columns(2)
with left, u.card():
    b = ct['buy_again_by_recency']
    fig = go.Figure(go.Bar(x=[str(i) for i in b.index], y=b.values, marker_color=u.NAVY, text=[f'{v:.0f}%' for v in b.values], textposition='outside'))
    fig.update_yaxes(title=t('% who bought again in 6 months', '% رجعوا اشتروا في 6 شهور'), range=[0, 60])
    u.show(u.fig_style(fig, t('Same return rate whatever the last purchase', 'نفس نسبة الرجوع مهما كان آخر شراء'), height=330))
with right, u.card():
    st.markdown(t("Because nothing predicts who leaves, we **test** instead: the *At Risk (Can't Lose)* customers are split at random. "
                  "**Test** gets the win-back offer, **Control** gets nothing. After 3 months the difference = the real effect.",
                  "عشان مفيش حاجة بتتوقّع مين هيمشي، **بنجرّب**: عملاء *معرّضون للخسارة (مهمين)* بيتقسموا عشوائي. "
                  "**Test** ياخدوا العرض، و **Control** مياخدوش. بعد 3 شهور الفرق = الأثر الحقيقي."))
    lst = u.rfm()
    lst = lst[lst.segment == "At Risk (Can't Lose)"][['customer_id', 'last', 'orders', 'spend']].copy()
    lst['group'] = np.where(np.random.default_rng(42).random(len(lst)) < 0.5, 'Test', 'Control')
    st.markdown(t(f"**{len(lst):,}** customers · {(lst.group == 'Test').sum():,} test / {(lst.group == 'Control').sum():,} control",
                  f"**{len(lst):,}** عميل · {(lst.group == 'Test').sum():,} تجربة / {(lst.group == 'Control').sum():,} مقارنة"))
    u.csv_button(lst, t('⬇ Win-back test list (CSV)', '⬇ قايمة تجربة الاسترجاع (CSV)'), 'cottonil_winback_test_control.csv')
u.footer('12_ai_demand_forecast · 13_ai_churn_test')
