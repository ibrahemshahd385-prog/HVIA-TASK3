import streamlit as st
import plotly.graph_objects as go
import utils as u

t = u.t
tf, sf, pf = u.transfers_fy(), u.stock_facts(), u.purchasing_fy()
s = u.sku_bought_sold()

u.hero(t('Chapter 3 · Stock & supply', 'الفصل 3 · المخزون والإمداد'),
       t('We buy and ship fixed quantities – not what sells', 'بنشتري ونبعت كميات ثابتة – مش اللي بيتباع'),
       t('Purchases and transfers are the same every year and for every SKU. And the stock does not add up: millions of pieces are missing.',
         'الشراء والتحويلات نفس الكمية كل سنة ولكل SKU. والمخزون مش بيقفل: ملايين القطع مش متحسوبة.'))

u.kpis([
    (t('Sent ÷ sold, FY2026', 'المبعوت ÷ المتباع FY2026'), f'×{tf.ratio.iloc[-1]:.1f}', t('a fixed 1.6M pieces a year', '1.6 مليون قطعة ثابتة في السنة'), False),
    (t('Pieces not accounted for', 'قطع مش متحسوبة'), f"{sf['unaccounted'] / 1e6:.1f}M", t('sent − sold − on shelf', 'المبعوت − المتباع − اللي على الرف'), True),
    (t('Stock = months of sales', 'المخزون = كام شهر بيع'), f"{sf['months_cover']:.0f}", u.M(sf['stock_value']) + t(' EGP', ' جنيه'), False),
    (t('Bought ÷ sold, FY2026', 'المشترى ÷ المتباع FY2026'), f'×{pf.ratio.iloc[-1]:.0f}', t(f'SKU correlation {s.corr().iloc[0, 1]:.2f}', f'ارتباط الـ SKU {s.corr().iloc[0, 1]:.2f}'), False),
])

u.section(t('Distribution to branches', 'التوزيع على الفروع'))
left, right = st.columns(2)
with left, u.card():
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tf.index, y=tf.sold / 1e6, name=t('Sold', 'اتباع'), marker_color=u.NAVY))
    fig.add_trace(go.Bar(x=tf.index, y=tf.sent / 1e6, name=t('Sent to branches', 'اتبعت للفروع'), marker_color=u.GREY,
                         text=[f'×{r:.1f}' for r in tf.ratio], textposition='outside'))
    fig.update_layout(barmode='group'); fig.update_yaxes(title=t('million pieces', 'مليون قطعة'), range=[0, tf.sent.max() / 1e6 * 1.2])
    u.show(u.fig_style(fig, t('Same quantity every year', 'نفس الكمية كل سنة'), legend=True))
with right, u.card():
    mix = u.category_mix().sort_values('sent_pct').tail(10)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=mix.index, x=mix.sold_pct, orientation='h', name=t('% of pieces sold', '% من المتباع'), marker_color=u.NAVY))
    fig.add_trace(go.Bar(y=mix.index, x=mix.sent_pct, orientation='h', name=t('% of pieces sent', '% من المبعوت'), marker_color=u.TEAL))
    fig.update_layout(barmode='group')
    u.show(u.fig_style(fig, t(f"Socks: {mix.loc['Socks', 'sold_pct']:.0f}% of sales, {mix.loc['Socks', 'sent_pct']:.0f}% of shipments",
                              f"الشرابات: {mix.loc['Socks', 'sold_pct']:.0f}% من البيع و {mix.loc['Socks', 'sent_pct']:.0f}% من المبعوت"), height=460, legend=True))
src = sf['source_mix']
u.note(t(f"Shipments follow sales neither per SKU ({sf['sku_corr']:.2f}) nor per branch ({sf['branch_corr']:.2f}); "
         f"{src.get('Raw materials', 0) + src.get('Returns', 0):.0f}% leave from the raw-material and returns warehouses; every branch is served by all 12 warehouses.",
         f"التحويلات مش ماشية مع البيع لا لكل SKU ({sf['sku_corr']:.2f}) ولا لكل فرع ({sf['branch_corr']:.2f})؛ و "
         f"{src.get('Raw materials', 0) + src.get('Returns', 0):.0f}% طالع من مخزن الخامات والمرتجعات؛ وكل فرع بيستلم من الـ 12 مخزن."))
with u.card():
    safety = st.slider(t('Rule: send each branch its sales + safety %', 'القاعدة: نبعت لكل فرع بيعه + أمان %'), 0, 50, 10, 5)
    al = u.allocation_saving(safety / 100)
    u.kpis([(t('Pieces to move a year', 'قطع تتنقل في السنة'), f"{al['need'] / 1e3:,.0f}K", t(f"{-al['cut_pct']:.0f}% vs today", f"{-al['cut_pct']:.0f}% عن النهارده"), False),
            (t('Transfers a year', 'تحويلات في السنة'), f"{al['new_transfers']:,.0f}", t(f"instead of {al['transfers']:,}", f"بدل {al['transfers']:,}"), False),
            (t('Transport saved a year', 'توفير النقل في السنة'), u.M(al['saving']), t('EGP', 'جنيه'), True)])

u.section(t('Does the stock add up?', 'المخزون بيقفل؟'), t('Branches, Oct 2018 – Oct 2026', 'الفروع، أكتوبر 2018 – أكتوبر 2026'))
with u.card():
    steps = [(t('start stock', 'رصيد البداية'), sf['start']), (t('+ received', '+ المستلم'), sf['received']), (t('+ returns', '+ المرتجع'), sf['returned']),
             (t('− sold', '− المتباع'), -sf['sold']), (t('− end stock', '− رصيد النهاية'), -sf['end'])]
    fig = go.Figure(go.Waterfall(x=[x[0] for x in steps] + [t('not accounted', 'مش متحسوب')], measure=['absolute'] + ['relative'] * 4 + ['total'],
                                 y=[x[1] / 1e6 for x in steps] + [0], text=[f'{x[1] / 1e6:+.2f}' for x in steps] + [f"{sf['unaccounted'] / 1e6:.1f}"],
                                 textposition='outside', increasing=dict(marker=dict(color=u.NAVY)), decreasing=dict(marker=dict(color=u.GREY)),
                                 totals=dict(marker=dict(color=u.TEAL)), connector=dict(line=dict(color=u.GREY))))
    fig.update_yaxes(title=t('million pieces', 'مليون قطعة'))
    u.show(u.fig_style(fig, t(f"{sf['unaccounted'] / 1e6:.1f}M pieces are neither sold nor on the shelf", f"{sf['unaccounted'] / 1e6:.1f} مليون قطعة مش متباعة ولا على الرف"), height=400))
u.caution(t('Either transfers are recorded wrongly, or stock counts are, or pieces are lost. Each needs a different fix – the first step is a physical count in 5 branches.',
            'يا إما التحويلات متسجلة غلط، يا إما الجرد، يا إما فيه قطع بتضيع. وكل حالة ليها حل – وأول خطوة جرد فعلي في 5 فروع.'))

u.section(t('Purchasing', 'الشراء'))
left, right = st.columns(2)
with left, u.card():
    fig = go.Figure(go.Bar(x=pf.index, y=pf.ratio, marker_color=[u.TEAL if x == pf.index[-1] else u.NAVY for x in pf.index],
                           text=[f'×{v:.0f}' for v in pf.ratio], textposition='outside'))
    fig.update_yaxes(title=t('pieces bought per piece sold', 'قطع اتشرت لكل قطعة اتباعت'), range=[0, pf.ratio.max() * 1.2])
    u.show(u.fig_style(fig, t('~42M pieces bought every year', 'حوالي 42 مليون قطعة كل سنة')))
with right, u.card():
    fig = go.Figure(go.Scatter(x=s.sold / 1e3, y=s.bought / 1e3, mode='markers', marker=dict(color=u.NAVY, size=6, opacity=0.55)))
    fig.update_xaxes(title=t('thousand pieces sold per SKU', 'ألف قطعة اتباعت لكل SKU'))
    fig.update_yaxes(title=t('thousand bought per SKU', 'ألف اتشرت لكل SKU'), range=[0, s.bought.max() / 1e3 * 1.15])
    u.show(u.fig_style(fig, t('Every SKU gets the same purchase', 'كل SKU بياخد نفس الشراء')))
u.caution(t(f"Purchase spend FY2026 = {pf.spend.iloc[-1] / 1e9:.1f}B EGP vs {pf.cogs.iloc[-1] / 1e6:.0f}M cost of goods sold. Either the unit is not 'piece' or these are not real purchases – the first question for the company.",
            f"صرف الشراء FY2026 = {pf.spend.iloc[-1] / 1e9:.1f} مليار جنيه مقابل {pf.cogs.iloc[-1] / 1e6:.0f} مليون تكلفة المباع. يا إما الوحدة مش قطعة يا إما دي مش مشتريات حقيقية – أول سؤال للشركة."))
u.note(t('The demand-based purchase and allocation plans are in the AI lab chapter.', 'خطة الشراء والتوزيع المبنية على الطلب موجودة في فصل مختبر الـ AI.'))
u.footer('08_card05_inventory_allocation · 09_card06_purchasing')
