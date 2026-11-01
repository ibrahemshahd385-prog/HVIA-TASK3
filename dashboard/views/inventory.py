import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
u.header(t('📦 Smart Inventory & AI Forecast', '📦 المخزون الذكي وتوقّع الطلب'),
         t('Do branches get what they sell, does the stock add up – and what should we buy and send next?',
           'الفروع بتستلم اللي بتبيعه؟ المخزون بيقفل؟ ونشتري ونبعت إيه الفترة الجاية؟'),
         '08_card05_inventory_allocation · 12_ai_demand_forecast')

tf = u.transfers_fy()
sf = u.stock_facts()
k = st.columns(5)
u.kpi(k[0], t('Sent ÷ sold, FY2026', 'المبعوت ÷ المتباع FY2026'), f'×{tf.ratio.iloc[-1]:.1f}', inverse=True)
u.kpi(k[1], t('Pieces not accounted for', 'قطع مش متحسوبة'), f"{sf['unaccounted'] / 1e6:.1f}M", inverse=True)
u.kpi(k[2], t('Stock = months of sales', 'المخزون = كام شهر بيع'), f"{sf['months_cover']:.0f}", inverse=True)
u.kpi(k[3], t('Stock value', 'قيمة المخزون'), u.money(sf['stock_value'] / 1e6))
u.kpi(k[4], t('Transport cost FY2026', 'تكلفة النقل FY2026'), u.money(tf.transport_cost.iloc[-1] / 1e6))

tab1, tab2, tab3, tab4 = st.tabs([t('Distribution today', 'التوزيع النهارده'), t('Does the stock add up?', 'المخزون بيقفل؟'),
                                  t('AI demand forecast', 'توقّع الطلب بالـ AI'), t('Purchase & allocation plan', 'خطة الشراء والتوزيع')])
with tab1:
    left, right = st.columns(2)
    with left:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=tf.index, y=tf.sold / 1e6, name=t('Sold', 'اتباع'), marker_color=u.BLUE))
        fig.add_trace(go.Bar(x=tf.index, y=tf.sent / 1e6, name=t('Sent to branches', 'اتبعت للفروع'), marker_color=u.GREY,
                             text=[f'×{r:.1f}' for r in tf.ratio], textposition='outside'))
        fig.update_layout(barmode='group'); fig.update_yaxes(title=t('million pieces', 'مليون قطعة'), range=[0, tf.sent.max() / 1e6 * 1.2])
        u.show(u.style(fig, t('A fixed ~1.6M pieces a year, whatever the branches sell', 'كمية ثابتة حوالي 1.6 مليون قطعة في السنة، مهما الفروع باعت'), legend=True))
    with right:
        mix = u.category_mix().sort_values('sent_pct')
        fig = go.Figure()
        fig.add_trace(go.Bar(y=mix.index, x=mix.sold_pct, orientation='h', name=t('% of pieces sold', '% من المتباع'), marker_color=u.BLUE))
        fig.add_trace(go.Bar(y=mix.index, x=mix.sent_pct, orientation='h', name=t('% of pieces sent', '% من المبعوت'), marker_color=u.ORANGE))
        fig.update_layout(barmode='group')
        u.show(u.style(fig, t(f"Socks: {mix.loc['Socks', 'sold_pct']:.0f}% of sales, {mix.loc['Socks', 'sent_pct']:.0f}% of shipments",
                              f"الشرابات: {mix.loc['Socks', 'sold_pct']:.0f}% من البيع و {mix.loc['Socks', 'sent_pct']:.0f}% من المبعوت"), height=520, legend=True))
    src = sf['source_mix'].sort_values()
    st.markdown(t(f"Shipments follow sales neither per SKU (correlation {sf['sku_corr']:.2f}) nor per branch ({sf['branch_corr']:.2f}). "
                  f"**{src.get('Raw materials', 0) + src.get('Returns', 0):.0f}%** of the pieces leave from the raw-material and returns warehouses, and every branch receives from all 12 warehouses.",
                  f"البضاعة المبعوتة مش ماشية مع البيع لا لكل SKU (ارتباط {sf['sku_corr']:.2f}) ولا لكل فرع ({sf['branch_corr']:.2f}). "
                  f"**{src.get('Raw materials', 0) + src.get('Returns', 0):.0f}%** من القطع طالعة من مخزن الخامات ومخزن المرتجعات، وكل فرع بيستلم من الـ 12 مخزن."))
    safety = st.slider(t('Demand-based rule: send last year’s sales + safety %', 'القاعدة: نبعت مبيعات السنة اللي فاتت + أمان %'), 0, 50, 10, 5)
    al = u.allocation_saving(safety / 100)
    k = st.columns(3)
    u.kpi(k[0], t('Pieces to move', 'القطع اللي هتتنقل'), f"{al['need'] / 1e3:,.0f}K", f"{-al['cut_pct']:.0f}%", inverse=True)
    u.kpi(k[1], t('Transfers / year', 'تحويلات في السنة'), f"{al['new_transfers']:,.0f}", f"{al['new_transfers'] - al['transfers']:,.0f}", inverse=True)
    u.kpi(k[2], t('Transport saved / year', 'توفير النقل في السنة'), u.money(al['saving'] / 1e6))

with tab2:
    steps = [(t('start stock', 'رصيد البداية'), sf['start']), (t('+ received', '+ المستلم'), sf['received']), (t('+ returns', '+ المرتجع'), sf['returned']),
             (t('− sold', '− المتباع'), -sf['sold']), (t('− end stock', '− رصيد النهاية'), -sf['end'])]
    fig = go.Figure(go.Waterfall(x=[s_[0] for s_ in steps] + [t('= not accounted', '= مش متحسوب')], measure=['absolute'] + ['relative'] * 4 + ['total'],
                                 y=[s_[1] / 1e6 for s_ in steps] + [0], text=[f'{s_[1] / 1e6:+.2f}' for s_ in steps] + [f"{sf['unaccounted'] / 1e6:.1f}"],
                                 textposition='outside', increasing=dict(marker=dict(color=u.BLUE)), decreasing=dict(marker=dict(color=u.GREY)),
                                 totals=dict(marker=dict(color=u.ORANGE)), connector=dict(line=dict(color=u.SOFT_GREY))))
    fig.update_yaxes(title=t('million pieces, branches, Oct 2018 – Oct 2026', 'مليون قطعة، الفروع، 2018–2026'))
    u.show(u.style(fig, t(f"{sf['unaccounted'] / 1e6:.1f}M pieces reached the branches and are neither sold nor on the shelf",
                          f"{sf['unaccounted'] / 1e6:.1f} مليون قطعة وصلت الفروع ومش متباعة ولا على الرف"), height=420))
    u.honest(t('Either the transfers are recorded wrongly, or the stock counts are, or pieces are lost (shrinkage). Each needs a different fix → '
               'start with a physical count in 5 branches. This is the "Loss Prevention" idea – and the biggest gap in the data.',
               'يا إما التحويلات متسجلة غلط، يا إما الجرد، يا إما فيه قطع بتضيع (عجز). وكل حالة ليها حل مختلف → '
               'نبدأ بجرد فعلي في 5 فروع. دي فكرة "منع الفقد"، وأكبر ثغرة في الداتا.'))
    ss = sf['stock_series']
    fig = go.Figure(go.Scatter(x=ss.index, y=ss.values / 1e6, mode='lines', line=dict(color=u.ORANGE, width=2.5)))
    fig.update_yaxes(title=t('million pieces in stock', 'مليون قطعة في المخزون'), range=[0, ss.max() / 1e6 * 1.2])
    u.show(u.style(fig, t('Stock is flat for 8 years while sales more than doubled', 'المخزون ثابت 8 سنين والمبيعات زادت أكتر من الضعف'), height=320))

with tab3:
    res, bt = u.backtest()
    k = st.columns(3)
    u.kpi(k[0], t('AI model error (WAPE)', 'خطأ الموديل (WAPE)'), f"{res['wape_model']}%")
    u.kpi(k[1], t("'Same month last year' error", "خطأ 'زي السنة اللي فاتت'"), f"{res['wape_naive']}%")
    u.kpi(k[2], t('More accurate by', 'أدق بـ'), f"{res['better_%']:.0f}%")
    tot = bt.groupby('month')[['units', 'model', 'naive']].sum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tot.index, y=tot.units / 1e3, name=t('actual', 'الحقيقي'), mode='lines+markers', line=dict(color=u.INK, width=2.5)))
    fig.add_trace(go.Scatter(x=tot.index, y=tot.model / 1e3, name=t('AI model', 'موديل الـ AI'), mode='lines+markers', line=dict(color=u.BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=tot.index, y=tot.naive / 1e3, name=t('same month last year', 'زي السنة اللي فاتت'), mode='lines+markers', line=dict(color=u.GREY, dash='dash')))
    fig.update_yaxes(title=t('thousand pieces', 'ألف قطعة'), range=[0, tot.values.max() / 1e3 * 1.2])
    u.show(u.style(fig, t('Backtest: 6 months the model never saw (Apr–Sep 2026)', 'اختبار: 6 شهور الموديل ماشافهاش (أبريل–سبتمبر 2026)'), legend=True))
    fc, hist = u.forecast()
    cats = sorted(fc.category_en.unique())
    a, b = st.columns(2)
    cat = a.selectbox(t('Category', 'الفئة'), cats, index=cats.index('Socks') if 'Socks' in cats else 0)
    chn = b.selectbox(t('Channel', 'القناة'), ['Store', 'Online', 'Wholesale'], format_func=u.ch_name)
    h = hist[(hist.category_en == cat) & (hist.channel == chn)].tail(24)
    f = fc[(fc.category_en == cat) & (fc.channel == chn)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h.month, y=h.units, name=t('history', 'اللي فات'), mode='lines', line=dict(color=u.BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=f.month, y=f.units, name=t('forecast', 'التوقّع'), mode='lines+markers', line=dict(color=u.ORANGE, width=2.5, dash='dot')))
    fig.update_yaxes(title=t('pieces per month', 'قطع في الشهر'))
    u.show(u.style(fig, t(f'{cat} · {chn}: forecast Oct 2026 – Jan 2027 = {f.units.sum():,.0f} pieces', f'{cat} · {u.ch_name(chn)}: التوقّع أكتوبر 2026 – يناير 2027 = {f.units.sum():,.0f} قطعة'), legend=True))

with tab4:
    a, b = st.columns(2)
    level = a.select_slider(t('Service level (chance of not running out)', 'مستوى الخدمة (احتمال ما نخلصش)'), ['90%', '95%', '98%', '99%'], '95%')
    z = {'90%': 1.28, '95%': 1.65, '98%': 2.05, '99%': 2.33}[level]
    trust = b.toggle(t('Subtract stock on hand (only after a stock count)', 'نطرح المخزون الحالي (بعد الجرد بس)'), value=False)
    plan, alloc = u.plans(z, trust)
    k = st.columns(3)
    u.kpi(k[0], t('Demand Nov 2026 – Jan 2027', 'الطلب نوفمبر 2026 – يناير 2027'), f'{plan.forecast_3m.sum() / 1e3:,.0f}K')
    u.kpi(k[1], t('Plan: buy', 'الخطة: نشتري'), f'{plan.to_buy.sum() / 1e3:,.0f}K')
    u.kpi(k[2], t('Current pattern buys per quarter', 'النمط الحالي بيشتري في الربع'), f'{plan.current_pattern_buys.sum() / 1e6:,.1f}M', inverse=True)
    show_plan = plan.reset_index().rename(columns={'index': 'category_en'})
    u.table(show_plan.round(0))
    u.csv_button(show_plan, t('⬇️ Download the purchase plan (CSV)', '⬇️ نزّلي خطة الشراء (CSV)'), 'cottonil_purchase_plan.csv')
    st.markdown('#### ' + t('Allocation plan – November 2026, per branch', 'خطة التوزيع – نوفمبر 2026 لكل فرع'))
    br = st.selectbox(t('Branch', 'الفرع'), sorted(alloc.branch_id.unique()))
    x = alloc[alloc.branch_id == br].sort_values('send_next_month', ascending=False)
    u.kpi(st.columns(3)[0], t('Send next month', 'نبعت الشهر الجاي'), f'{x.send_next_month.sum():,.0f}', f'{x.send_next_month.sum() - x.sent_per_month_FY2026.sum():,.0f}')
    u.table(x)
    u.csv_button(alloc, t('⬇️ Download the allocation plan for all branches (CSV)', '⬇️ نزّلي خطة التوزيع لكل الفروع (CSV)'), 'cottonil_allocation_plan.csv')
