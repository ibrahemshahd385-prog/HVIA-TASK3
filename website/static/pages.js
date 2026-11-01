/* Cottonil · Manager board – the working pages: purchase, distribution, pricing, marketing, branches. */

const savedList = (items, render) => items && items.length ? `<div class="tbl-wrap"><table class="tbl"><tbody>${items.map(render).join('')}</tbody></table></div>`
  : `<p class="muted small">${t('Nothing saved yet.', 'لسه مفيش حاجة اتحفظت.')}</p>`;
const weeksAr = w => (w === 1 ? 'أسبوع' : w === 2 ? 'أسبوعين' : `${w} أسابيع`);
const typeName = x => (x === 'Retail branch' ? t('Branch', 'فرع') : t('Point of sale', 'نقطة بيع'));

// ================================================================ Purchase plan
page(/^#\/purchase$/, async (view) => {
  const st = { service: 95, adjust: 0, trust: false, edits: {} };
  const load = async () => render(await api(`/api/purchase?service=${st.service}&adjust=${st.adjust}&trust=${st.trust ? 1 : 0}`));
  const render = d => {
    const m = d.months, rows = d.plan;
    const val = r => (st.edits[r.category_en] ?? r.to_buy);
    const tot = k => rows.reduce((a, r) => a + (k === 'to_buy' ? val(r) : r[k]), 0);
    view.innerHTML = `<div class="page">
      ${head(t('Purchase plan', 'خطة الشراء'), t(`${mon(m[0])} – ${mon(m[2])} · from the demand forecast (error ${d.backtest.wape_model}% on 6 hidden months)`, `${mon(m[0])} – ${mon(m[2])} · من توقّع الطلب (خطأ ${d.backtest.wape_model}% على 6 شهور مخفية)`),
        `<button class="btn" id="pcsv">${I('download')} CSV</button><button class="btn primary" id="psave">${I('save')} ${t('Save plan', 'احفظ الخطة')}</button>`)}
      <div class="card"><div class="controls">
        <div class="field"><label>${t('Service level (how often a category must not run out)', 'مستوى الخدمة (قد إيه الفئة متخلصش)')}</label>${segHTML('service', [[90, '90%'], [95, '95%'], [98, '98%'], [99, '99%']], st.service)}</div>
        <div class="field"><label>${t('Adjust the forecast', 'تعديل على التوقّع')}</label><div class="range"><input type="range" id="padj" min="-20" max="30" step="5" value="${st.adjust}"><output class="num" id="padjo">${sign(st.adjust)}%</output></div></div>
        <label class="switch"><input type="checkbox" id="ptrust" ${st.trust ? 'checked' : ''}><span>${t('Subtract recorded stock (only after a stock count)', 'اطرح المخزون المتسجل (بعد الجرد بس)')}</span></label>
      </div></div>
      <div class="grid g4 mt">
        ${kpi(t('Expected demand', 'الطلب المتوقع'), N(nf(tot('forecast'))), t('pieces in 3 months', 'قطعة في 3 شهور'), false, 'target')}
        ${kpi(t('Plan: buy', 'الخطة: نشتري'), `<span id="kbuy">${N(nf(tot('to_buy')))}</span>`, t('pieces, with safety stock', 'قطعة، بمخزون الأمان'), true, 'cart')}
        ${kpi(t('Usual buying in a quarter', 'الشراء المعتاد في الربع'), N(big(tot('old_pattern'))), t(`×${nf(tot('old_pattern') / tot('forecast'))} the demand`, `×${nf(tot('old_pattern') / tot('forecast'))} الطلب`), false, 'info')}
        ${kpi(t('Recorded stock', 'المخزون المتسجل'), N(big(d.stock_units)), st.trust ? t('subtracted from the plan', 'متطرح من الخطة') : t('not subtracted until counted', 'مش متطرح لحد الجرد'), false, 'box')}
      </div>
      <div class="card mt"><div class="card-head"><div><h3>${t('Quantities by category', 'الكميات لكل فئة')}</h3><p class="sub">${t('“To buy” = forecast + safety stock' + (st.trust ? ' − stock' : '') + '. You can change any number before saving.', '"نشتري" = التوقّع + مخزون الأمان' + (st.trust ? ' − المخزون' : '') + '. تقدر تغيّر أي رقم قبل الحفظ.')}</p></div></div>
        <div class="tbl-wrap"><table class="tbl"><thead><tr><th>${t('Category', 'الفئة')}</th>${m.map(x => `<th class="n">${monOnly(x)}</th>`).join('')}<th class="n">${t('Forecast', 'التوقّع')}</th><th class="n">${t('Same months last year', 'نفس الشهور السنة اللي فاتت')}</th><th class="n">${t('Safety', 'أمان')}</th>${st.trust ? `<th class="n">${t('Stock', 'المخزون')}</th>` : ''}<th class="n">${t('To buy', 'نشتري')}</th><th class="n">${t('Usual buying', 'الشراء المعتاد')}</th></tr></thead>
        <tbody>${rows.map(r => `<tr><td><b>${esc(cat(r.category_en))}</b></td>${m.map(x => `<td class="n">${nf(r[x])}</td>`).join('')}<td class="n">${nf(r.forecast)}</td><td class="n muted">${nf(r.last_year)}</td><td class="n">${nf(r.safety)}</td>${st.trust ? `<td class="n">${nf(r.stock)}</td>` : ''}
          <td class="n"><input class="cell num ${st.edits[r.category_en] != null ? 'changed' : ''}" data-cat="${esc(r.category_en)}" type="number" min="0" step="100" value="${Math.round(val(r))}"></td><td class="n muted">${nf(r.old_pattern)}</td></tr>`).join('')}</tbody>
        <tfoot><tr><td>${t('Total', 'الإجمالي')}</td>${m.map(x => `<td class="n">${nf(tot(x))}</td>`).join('')}<td class="n">${nf(tot('forecast'))}</td><td class="n">${nf(tot('last_year'))}</td><td class="n">${nf(tot('safety'))}</td>${st.trust ? `<td class="n">${nf(tot('stock'))}</td>` : ''}<td class="n" id="tbuy">${nf(tot('to_buy'))}</td><td class="n">${nf(tot('old_pattern'))}</td></tr></tfoot></table></div>
      </div>
      <div class="grid g2 mt">
        <div class="card"><h3>${t('Next three months vs last year', 'الـ 3 شهور الجاية مقابل السنة اللي فاتت')}</h3><p class="sub">${t('pieces, all categories', 'قطع، كل الفئات')}</p><div id="cmon"></div></div>
        <div class="card"><h3>${t('Why we trust the forecast', 'ليه بنثق في التوقّع')}</h3><p class="sub">${t(`Tested on Apr–Sep 2026 without seeing them: error ${d.backtest.wape_model}% vs ${d.backtest.wape_naive}% for “same month last year”.`, `اتختبر على أبريل–سبتمبر 2026 من غير ما يشوفهم: الخطأ ${d.backtest.wape_model}% مقابل ${d.backtest.wape_naive}% لطريقة "زي السنة اللي فاتت".`)}</p><div id="cbt"></div></div>
      </div>
      <div class="card mt"><h3>${t('Saved plans', 'الخطط المحفوظة')}</h3><p class="sub">${t('each saved plan becomes a purchase order you can print or send to the supplier', 'كل خطة محفوظة بتتحول لأمر شراء تطبعه أو تبعته للمورد')}</p>
        ${savedList(d.saved, p => `<tr><td>${N(p.saved)}</td><td>${esc(p.window.split('..').map(mon).join(' – '))}</td><td class="n">${nf(p.total)} ${t('pcs', 'قطعة')}</td><td class="n">${N(p.service + '%')}</td>
          <td class="n"><a class="btn sm primary" href="#/purchase/order/${p.id}">${I('file')} ${t('Purchase order', 'أمر الشراء')}</a> <a class="btn sm" href="/api/purchase/order/${p.id}?format=csv">${I('download')} CSV</a></td></tr>`)}
      </div></div>`;
    Charts.bars($('#cmon'), d.by_month.map(x => mon(x.month)), [{ name: t('same month last year', 'نفس الشهر السنة اللي فاتت'), color: Charts.C.grey, values: d.by_month.map(x => x.last_year) },
      { name: t('forecast', 'التوقّع'), color: Charts.C.navy, values: d.by_month.map(x => x.forecast) }], { height: 230 });
    const bt = d.backtest_total;
    Charts.lines($('#cbt'), bt.map(x => monShort(x.month)), [{ name: t('actual', 'الحقيقي'), color: Charts.C.navy, values: bt.map(x => x.units), dots: true },
      { name: t('AI model', 'الموديل'), color: Charts.C.teal, values: bt.map(x => x.model), dots: true }, { name: t('same month last year', 'زي السنة اللي فاتت'), color: Charts.C.mid, values: bt.map(x => x.naive), dash: true }], { height: 230 });
    onSeg(view, 'service', v => { st.service = +v; st.edits = {}; load(); });
    $('#padj').oninput = e => { $('#padjo').textContent = sign(+e.target.value) + '%'; };
    $('#padj').onchange = e => { st.adjust = +e.target.value; st.edits = {}; load(); };
    $('#ptrust').onchange = e => { st.trust = e.target.checked; st.edits = {}; load(); };
    $$('input.cell', view).forEach(inp => inp.oninput = () => {
      st.edits[inp.dataset.cat] = Math.max(0, +inp.value || 0);
      inp.classList.add('changed');
      const s = rows.reduce((a, r) => a + val(r), 0);
      $('#tbuy').textContent = nf(s); $('#kbuy').innerHTML = N(nf(s));
    });
    $('#pcsv').onclick = () => downloadCSV(rows, [['category_en', 'category'], [r => cat(r.category_en), 'category_name'], ...m.map(x => [x, x]), ['forecast', 'forecast_3m'], ['last_year', 'same_months_last_year'], ['safety', 'safety_stock'], [val, 'to_buy']], 'purchase_plan');
    $('#psave').onclick = async () => {
      await post('/api/purchase/save', { rows: rows.map(r => ({ category_en: r.category_en, forecast: r.forecast, to_buy: val(r) })), window: `${m[0]}..${m[2]}`, service: st.service, trust: st.trust, adjust: st.adjust });
      toast(t('Plan saved – the purchase order is ready', 'الخطة اتحفظت – أمر الشراء جاهز'));
      st.edits = {}; refreshToday(); load();
    };
  };
  await load();
}, 'purchase');

page(/^#\/purchase\/order\/(\w+)$/, async (view, q, id) => {
  const d = await api(`/api/purchase/order/${id}`);
  const p = d.plan, [a, b] = p.window.split('..');
  const groups = {};
  d.lines.forEach(l => (groups[l.category_en] = groups[l.category_en] || []).push(l));
  view.innerHTML = `<div class="page" style="max-width:980px">
    <a class="back no-print" href="#/purchase">${I('back')} ${t('Purchase plan', 'خطة الشراء')}</a>
    ${head(t(`Purchase order PO-${id.toUpperCase()}`, `أمر شراء PO-${id.toUpperCase()}`), t('Cottonil · generated from the saved purchase plan', 'قطنيل · طالع من خطة الشراء المحفوظة'),
      `<a class="btn" href="/api/purchase/order/${id}?format=csv">${I('download')} CSV</a><button class="btn primary" onclick="window.print()">${I('print')} ${t('Print', 'طباعة')}</button>`)}
    <div class="card"><div class="facts" style="margin:0">
      <div><span>${t('Order no.', 'رقم الأمر')}</span><b class="num" style="white-space:nowrap">PO-${id.toUpperCase()}</b></div><div><span>${t('Date', 'التاريخ')}</span><b class="num">${esc(p.saved)}</b></div>
      <div><span>${t('Covers', 'الفترة')}</span><b>${mon(a)} – ${mon(b)}</b></div><div><span>${t('Service level', 'مستوى الخدمة')}</span><b class="num">${p.service}%</b></div>
      <div><span>${t('Total pieces', 'إجمالي القطع')}</span><b class="num">${nf(p.total)}</b></div><div><span>${t('SKU lines', 'أصناف')}</span><b class="num">${nf(d.lines.length)}</b></div></div>
      <p class="small muted" style="margin:12px 0 0">${t('Each category is split across its SKUs by what each SKU sold in FY2026.', 'كل فئة متقسمة على أصنافها حسب اللي كل صنف باعه في FY2026.')}</p></div>
    <div class="card mt"><h3>${t('By category', 'لكل فئة')}</h3><div class="tbl-wrap"><table class="tbl"><thead><tr><th>${t('Category', 'الفئة')}</th><th class="n">${t('Forecast', 'التوقّع')}</th><th class="n">${t('Quantity', 'الكمية')}</th></tr></thead>
      <tbody>${d.rows.map(r => `<tr><td>${esc(cat(r.category_en))}</td><td class="n">${nf(r.forecast)}</td><td class="n"><b>${nf(r.to_buy)}</b></td></tr>`).join('')}</tbody></table></div></div>
    <div class="card mt pagebreak"><h3>${t('Lines', 'الأصناف')}</h3><div class="tbl-wrap"><table class="tbl"><thead><tr><th>SKU</th><th>${t('Product', 'المنتج')}</th><th>${t('Size', 'المقاس')}</th><th>${t('Colour', 'اللون')}</th><th class="n">${t('Qty', 'الكمية')}</th></tr></thead>
      <tbody>${Object.entries(groups).map(([c, ls]) => `<tr><td colspan="5" style="background:var(--navy-t);color:var(--navy);font-weight:600">${esc(cat(c))} · ${N(nf(ls.reduce((s, l) => s + l.quantity, 0)))}</td></tr>` +
        ls.map(l => `<tr><td class="num">${l.sku_id}</td><td style="white-space:normal">${esc(l.product_name_ar)}</td><td>${esc(l.size)}</td><td>${esc(l.color_ar)}</td><td class="n">${nf(l.quantity)}</td></tr>`).join('')).join('')}</tbody></table></div></div>
  </div>`;
}, 'purchase');

// ================================================================ Distribution
function pickHTML(L, month) {
  return `<div class="card-head" style="margin-bottom:8px"><div><h3>${esc(L.name)} <span class="muted small num">${L.branch_id}</span></h3>
      <p class="sub">${esc(L.governorate)} · ${esc(L.address)}</p></div><span class="tag navy">${I('warehouse')} ${esc(L.dc_name)}</span></div>
    <div class="tbl-wrap"><table class="tbl"><thead><tr><th style="width:34px"></th><th>${t('Category', 'الفئة')}</th><th class="n">${t(`Send in ${monOnly(month)}`, `نبعت في ${monOnly(month)}`)}</th><th class="n">${t('Usual per month', 'المعتاد في الشهر')}</th></tr></thead>
    <tbody>${L.lines.map(l => `<tr><td><span style="display:inline-block;width:14px;height:14px;border:1.5px solid var(--grey);border-radius:3px"></span></td><td>${esc(cat(l.category_en))}</td><td class="n"><b>${nf(l.send)}</b></td><td class="n muted">${nf(l.sent_month_fy26)}</td></tr>`).join('')}</tbody>
    <tfoot><tr><td></td><td>${t('Total', 'الإجمالي')}</td><td class="n">${nf(L.total)}</td><td class="n">${nf(L.lines.reduce((a, l) => a + l.sent_month_fy26, 0))}</td></tr></tfoot></table></div>`;
}

page(/^#\/distribution$/, async (view, q) => {
  const st = { month: q.get('month') || '', safety: 10, search: '' };
  const openPick = async bid => {
    const p = await api(`/api/distribution/picklist?branch=${bid}&month=${st.month}&safety=${st.safety}`);
    const L = p.lists[0];
    if (!L) return;
    modal(`<h2>${t('Pick list', 'قايمة التجهيز')} · ${mon(p.month)}</h2><p class="muted small">${t('what the warehouse prepares for this branch', 'اللي المخزن يجهّزه للفرع ده')}</p>${pickHTML(L, p.month)}
      <div class="modal-actions"><a class="btn" href="#/branches/${bid}" data-close>${I('store')} ${t('Branch profile', 'ملف الفرع')}</a><a class="btn primary" href="#/distribution/print?branch=${bid}&month=${p.month}&safety=${st.safety}" data-close>${I('print')} ${t('Print', 'طباعة')}</a></div>`);
  };
  const load = async () => { const d = await api(`/api/distribution?month=${st.month}&safety=${st.safety}`); st.month = d.month; render(d); };
  const render = d => {
    const T = d.totals, sm = d.source_mix;
    const off = (sm['Raw materials'] || 0) + (sm['Returns'] || 0);
    view.innerHTML = `<div class="page">
      ${head(t('Distribution plan', 'خطة التوزيع'), t(`${mon(d.month)} · each branch gets its expected demand + safety, from its nearest distribution warehouse`, `${mon(d.month)} · كل فرع ياخد طلبه المتوقع + أمان، من أقرب مخزن توزيع ليه`),
        `<a class="btn" href="/api/distribution?format=csv&month=${d.month}&safety=${st.safety}">${I('download')} CSV</a><a class="btn" href="#/distribution/print?month=${d.month}&safety=${st.safety}">${I('print')} ${t('All pick lists', 'كل قوايم التجهيز')}</a><button class="btn primary" id="dsave">${I('save')} ${t('Save plan', 'احفظ الخطة')}</button>`)}
      <div class="card"><div class="controls">
        <div class="field"><label>${t('Month', 'الشهر')}</label>${segHTML('month', d.months.map(x => [x, mon(x)]), d.month)}</div>
        <div class="field"><label>${t('Safety on top of demand', 'أمان فوق الطلب')}</label><div class="range"><input type="range" id="dsafe" min="0" max="30" step="5" value="${st.safety}"><output class="num" id="dsafeo">${st.safety}%</output></div></div>
      </div></div>
      <div class="grid g4 mt">
        ${kpi(t('Pieces to send', 'قطع هتتبعت'), N(nf(T.send)), t(`usual month: ${nf(T.old)}`, `الشهر المعتاد: ${nf(T.old)}`), true, 'truck')}
        ${kpi(t('Trips', 'نقلات'), N(nf(T.trips_new)), t(`instead of ${nf(T.trips_old)}`, `بدل ${nf(T.trips_old)}`), false, 'calendar')}
        ${kpi(t('Transport saved this month', 'توفير النقل الشهر ده'), N(big(T.transport_saved_month)), t('EGP', 'جنيه'), false, 'target')}
        ${kpi(t('From raw-material / returns warehouses', 'من مخزن الخامات والمرتجعات'), N('0%'), t(`today: ${nf(off)}% of shipments`, `النهارده: ${nf(off)}% من التحويلات`), false, 'warehouse')}
      </div>
      <div class="card mt"><h3>${t('Warehouses', 'المخازن')}</h3><p class="sub">${t('every branch is served by the distribution warehouse of its region', 'كل فرع بيستلم من مخزن التوزيع بتاع منطقته')}</p>
        <div class="tiles">${d.by_dc.map(w => `<div class="tile"><b>${esc(w.dc_name)}</b><div class="num">${nf(w.send)}</div><span>${t(`pieces · ${w.branches} branches`, `قطعة · ${w.branches} فرع`)}</span></div>`).join('')}</div></div>
      <div class="grid g-7-5 mt">
        <div class="card"><div class="card-head"><div><h3>${t('Branches', 'الفروع')}</h3><p class="sub">${t('click a branch for its pick list', 'اضغط على الفرع عشان قايمة التجهيز')}</p></div>
          <label class="ask" style="max-width:220px">${I('search')}<input id="dsearch" placeholder="${t('Search', 'دوّر')}" value="${esc(st.search)}"></label></div>
          <div class="tbl-wrap" style="max-height:640px"><table class="tbl"><thead><tr><th>${t('Branch', 'الفرع')}</th><th>${t('Warehouse', 'المخزن')}</th><th class="n">${t('Send', 'نبعت')}</th><th class="n">${t('Usual', 'المعتاد')}</th><th class="n">${t('Change', 'التغيير')}</th></tr></thead>
          <tbody id="dbody"></tbody></table></div></div>
        <div class="card"><h3>${t('By category', 'لكل فئة')}</h3><p class="sub">${t('plan vs the usual monthly shipment', 'الخطة مقابل التحويل الشهري المعتاد')}</p>
          <div class="tbl-wrap"><table class="tbl"><thead><tr><th>${t('Category', 'الفئة')}</th><th class="n">${t('Plan', 'الخطة')}</th><th class="n">${t('Usual', 'المعتاد')}</th><th class="n">${t('Change', 'التغيير')}</th></tr></thead>
          <tbody>${d.categories.map(c => `<tr><td>${esc(cat(c.category_en))}</td><td class="n"><b>${nf(c.send)}</b></td><td class="n muted">${nf(c.old)}</td><td class="n">${N(sign((c.send / c.old - 1) * 100) + '%')}</td></tr>`).join('')}</tbody></table></div></div>
      </div>
      <div class="card mt"><h3>${t('Saved plans', 'الخطط المحفوظة')}</h3>
        ${savedList(d.saved, p => `<tr><td>${N(p.saved)}</td><td>${mon(p.month)}</td><td class="n">${nf(p.total)} ${t('pcs', 'قطعة')}</td><td class="n">${t('safety', 'أمان')} ${N(nf(p.safety) + '%')}</td>
          <td class="n"><a class="btn sm" href="#/distribution/print?month=${p.month}&safety=${p.safety}">${I('print')} ${t('Pick lists', 'قوايم التجهيز')}</a></td></tr>`)}</div>
    </div>`;
    const drawRows = () => {
      const s = st.search.trim();
      $('#dbody').innerHTML = d.branches.filter(b => !s || b.branch_name_ar.includes(s) || b.branch_id.toLowerCase().includes(s.toLowerCase()) || b.governorate_ar.includes(s))
        .map(b => `<tr class="click" data-b="${b.branch_id}"><td><b>${esc(b.branch_name_ar)}</b> <span class="muted small">${esc(b.governorate_ar)}</span></td><td class="small">${esc(b.dc_name)}</td>
          <td class="n"><b>${nf(b.send)}</b></td><td class="n muted">${nf(b.old)}</td><td class="n">${N(sign(b.change_pct) + '%')}</td></tr>`).join('');
      $$('[data-b]', view).forEach(r => r.onclick = () => openPick(r.dataset.b));
    };
    drawRows();
    onSeg(view, 'month', v => { st.month = v; load(); });
    $('#dsafe').oninput = e => { $('#dsafeo').textContent = e.target.value + '%'; };
    $('#dsafe').onchange = e => { st.safety = +e.target.value; load(); };
    $('#dsearch').oninput = e => { st.search = e.target.value; drawRows(); };
    $('#dsave').onclick = async () => { await post('/api/distribution/save', { month: d.month, safety: st.safety }); toast(t('Distribution plan saved', 'خطة التوزيع اتحفظت')); refreshToday(); load(); };
  };
  await load();
  if (q.get('branch')) openPick(q.get('branch'));
}, 'distribution');

page(/^#\/distribution\/print$/, async (view, q) => {
  const p = await api(`/api/distribution/picklist?month=${q.get('month') || ''}&safety=${q.get('safety') || 10}${q.get('branch') ? '&branch=' + q.get('branch') : ''}`);
  view.innerHTML = `<div class="page" style="max-width:900px">
    <a class="back no-print" href="#/distribution">${I('back')} ${t('Distribution plan', 'خطة التوزيع')}</a>
    ${head(t(`Pick lists · ${mon(p.month)}`, `قوايم التجهيز · ${mon(p.month)}`), t(`${p.lists.length} branches · one page per branch`, `${p.lists.length} فرع · صفحة لكل فرع`), `<button class="btn primary" onclick="window.print()">${I('print')} ${t('Print', 'طباعة')}</button>`)}
    ${p.lists.map((L, i) => `<div class="card ${i ? 'mt pagebreak' : ''}">${pickHTML(L, p.month)}
      <div class="grid g2 mt small muted"><div>${t('Prepared by', 'جهّزه')}: ____________</div><div>${t('Received by (branch)', 'استلمه (الفرع)')}: ____________</div></div></div>`).join('')}
  </div>`;
}, 'distribution');

// ================================================================ Pricing & discounts
page(/^#\/pricing$/, async (view, q) => {
  const d = await api('/api/pricing');
  const cats = d.categories, f = d.facts;
  const st = { cat: q.get('category') || 'Socks', disc: 10, weeks: 2, ccat: cats[0].category_en, price: Math.round(cats[0].price), cdisc: 15 };
  const pol = d.policy;
  view.innerHTML = `<div class="page">
    ${head(t('Pricing & discounts', 'التسعير والخصم'), t('One discount policy, a check before any discount, and promotions planned as tests.', 'سياسة واحدة للخصم، ومراجعة قبل أي خصم، والعروض بتتخطط كتجربة.'))}
    <div class="grid g-5-7">
      <div class="grid" style="align-content:start">
        <div class="card"><h3>${t('Discount policy', 'سياسة الخصم')}</h3><p class="sub">${pol.saved ? t('saved ', 'اتحفظت ') + N(pol.saved) : t('suggested values – save to adopt them', 'قيم مقترحة – احفظها عشان تبقى السياسة')}</p>
          <form id="polf" class="controls">
            <div class="field"><label>${t('Max discount without your approval', 'أقصى خصم من غير موافقتك')}</label><input type="number" name="max" min="0" max="50" value="${pol.max_discount}" style="width:120px"></div>
            <div class="field"><label>${t('Margin never below', 'الهامش ميقلش عن')}</label><input type="number" name="floor" min="0" max="40" value="${pol.floor_margin}" style="width:120px"></div>
            <button class="btn primary">${I('save')} ${t('Save policy', 'احفظ السياسة')}</button></form></div>
        <div class="card"><h3>${t('Check a discount', 'راجع خصم')}</h3><p class="sub">${t('before a branch or the website applies it', 'قبل ما فرع أو الموقع يطبّقه')}</p>
          <div class="controls">
            <div class="field"><label>${t('Category', 'الفئة')}</label><select id="ccat">${cats.map(c => `<option value="${esc(c.category_en)}">${esc(cat(c.category_en))}</option>`).join('')}</select></div>
            <div class="field"><label>${t('Price (EGP)', 'السعر (جنيه)')}</label><input type="number" id="cprice" min="1" value="${st.price}" style="width:110px"></div>
            <div class="field"><label>${t('Discount %', 'الخصم %')}</label><input type="number" id="cdisc" min="0" max="90" value="${st.cdisc}" style="width:90px"></div>
          </div><div id="verdict" class="mt"></div></div>
      </div>
      <div class="card"><h3>${t('Margin by discount size', 'الهامش حسب حجم الخصم')}</h3><p class="sub">${t('FY2019–FY2026, all sales lines', 'FY2019–FY2026، كل سطور البيع')}</p><div id="cband"></div>
        <div class="facts">
          <div><span>${t('Lines with a discount', 'سطور عليها خصم')}</span><b class="num">${nf(f.share_lines)}%</b></div>
          <div><span>${t('Pieces per line, with / without', 'قطع في السطر، بخصم / من غير')}</span><b class="num">${nf(f.pieces_with, 2)} / ${nf(f.pieces_without, 2)}</b></div>
          <div><span>${t('Discounts FY2026', 'خصومات FY2026')}</span><b class="num">${big(f.discount_fy26)}</b></div>
          <div><span>${t('Share of gross profit', 'من إجمالي الربح')}</span><b class="num">${nf(f.discount_fy26 / f.gp_fy26 * 100, 1)}%</b></div>
        </div></div>
    </div>
    <div class="card mt"><div class="card-head"><div><h3>${t('Plan a promotion', 'خطط لعرض')}</h3><p class="sub">${t('what it costs, how much it must sell to pay for itself, and which branches test it', 'هيتكلف كام، ولازم يبيع قد إيه عشان يغطي نفسه، وأنهي فروع تجرّبه')}</p></div>
      <div class="actions no-print" style="display:flex;gap:8px"><a class="btn" id="pcsv2">${I('download')} ${t('Branch groups (CSV)', 'مجموعات الفروع (CSV)')}</a><button class="btn primary" id="psave2">${I('save')} ${t('Save test', 'احفظ التجربة')}</button></div></div>
      <div class="controls">
        <div class="field"><label>${t('Category', 'الفئة')}</label><select id="pcat">${cats.map(c => `<option value="${esc(c.category_en)}" ${c.category_en === st.cat ? 'selected' : ''}>${esc(cat(c.category_en))}</option>`).join('')}</select></div>
        <div class="field"><label>${t('Discount', 'الخصم')}</label><div class="range"><input type="range" id="pdisc" min="5" max="30" step="5" value="${st.disc}"><output class="num" id="pdisco">${st.disc}%</output></div></div>
        <div class="field"><label>${t('Duration', 'المدة')}</label>${segHTML('weeks', [[1, t('1 week', 'أسبوع')], [2, t('2 weeks', 'أسبوعين')], [4, t('4 weeks', '4 أسابيع')]], st.weeks)}</div>
      </div><div id="promo" class="mt"></div></div>
    <div class="card mt"><h3>${t('Saved promotion tests', 'تجارب العروض المحفوظة')}</h3>
      ${savedList(d.promos, p => `<tr><td>${N(p.saved)}</td><td>${esc(cat(p.category))}</td><td class="n">−${N(nf(p.discount) + '%')}</td><td class="n">${t(p.weeks + ' weeks', weeksAr(p.weeks))}</td><td class="n">${N(egp(p.cost))}</td><td class="n">${t('needs', 'محتاج')} ${N(sign(p.uplift_needed_pct) + '%')}</td></tr>`)}</div>
  </div>`;
  const bands = d.bands;
  Charts.bars($('#cband'), bands.map(b => b.band), [{ name: t('margin %', 'الهامش %'), color: Charts.C.navy, colors: bands.map((b, i) => (i === 0 ? Charts.C.teal : Charts.C.navy)), values: bands.map(b => b.margin_pct) }],
    { height: 230, fmt: v => nf(v, 1) + '%', fmtY: v => nf(v) + '%' });
  const check = debounce(async () => {
    const r = await api(`/api/pricing/check?price=${$('#cprice').value}&discount=${$('#cdisc').value}`);
    const word = { ok: t('Allowed', 'مسموح'), approval: t('Needs your approval', 'محتاج موافقتك'), reject: t('Rejected', 'مرفوض') }[r.verdict];
    const why = r.verdict === 'ok' ? t('within the policy', 'جوه السياسة') : r.verdict === 'approval' ? t(`above ${pol.max_discount}% – your call`, `أكتر من ${pol.max_discount}% – القرار ليك`)
      : r.margin < pol.floor_margin ? t(`margin would fall to ${nf(r.margin, 1)}%, below ${pol.floor_margin}%`, `الهامش هينزل لـ ${nf(r.margin, 1)}%، أقل من ${pol.floor_margin}%`) : t('more than twice the max discount', 'أكتر من ضعف أقصى خصم');
    $('#verdict').innerHTML = `<div class="verdict ${r.verdict}"><div><div class="big">${word}</div><div class="small muted">${why}</div></div><div class="spacer"></div>
      <div class="facts" style="margin:0;grid-template-columns:repeat(2,minmax(110px,1fr))"><div><span>${t('Price after discount', 'السعر بعد الخصم')}</span><b class="num">${nf(r.net_price)}</b></div><div><span>${t('Margin', 'الهامش')}</span><b class="num">${nf(r.margin, 1)}%</b></div></div></div>`;
  });
  $('#ccat').onchange = e => { $('#cprice').value = Math.round(cats.find(c => c.category_en === e.target.value).price); check(); };
  $('#cprice').oninput = check; $('#cdisc').oninput = check; check();
  $('#polf').onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    Object.assign(pol, await post('/api/pricing/policy', { max_discount: +fd.get('max'), floor_margin: +fd.get('floor') }));
    toast(t('Policy saved', 'السياسة اتحفظت')); refreshToday(); check();
  };
  const promo = debounce(async () => {
    const r = await api(`/api/pricing/promo?category=${encodeURIComponent(st.cat)}&discount=${st.disc}&weeks=${st.weeks}`);
    const hist = (r.evidence.pieces_with / r.evidence.pieces_without - 1) * 100;
    const test = r.groups.filter(g => g.group === 'Test'), ctrl = r.groups.filter(g => g.group === 'Control');
    $('#pcsv2').href = `/api/pricing/promo?category=${encodeURIComponent(st.cat)}&discount=${st.disc}&weeks=${st.weeks}&format=csv`;
    $('#promo').innerHTML = `<div class="facts" style="margin:0">
        <div><span>${t('Cost of the discount', 'تكلفة الخصم')}</span><b class="num">${egp(r.cost)}</b></div>
        <div><span>${t('Sales must rise by', 'البيع لازم يزيد')}</span><b class="num">${sign(r.uplift_needed_pct)}%</b></div>
        <div><span>${t('Extra pieces needed', 'قطع زيادة محتاجينها')}</span><b class="num">${nf(r.extra_pieces_needed)}</b></div>
        <div><span>${t('What discounts did so far', 'الخصم عمل إيه لحد دلوقتي')}</span><b class="num">${sign(hist, 1)}%</b></div></div>
      <div class="note mt">${I('info')}<div>${N(t(`To pay for itself this promotion must sell ${nf(r.uplift_needed_pct)}% more ${cat(r.category)} for ${r.weeks} weeks. So far discounted lines sold the same pieces as full-price ones, so we run it in ${test.length} branches and keep ${ctrl.length} similar branches as they are. After ${r.weeks} weeks, compare pieces per branch in the two groups – roll it out only if the gap is above ${nf(r.uplift_needed_pct)}%.`,
        `عشان يغطي تكلفته، العرض لازم يبيع ${cat(r.category)} أكتر بـ ${nf(r.uplift_needed_pct)}% لمدة ${weeksAr(r.weeks)}. ولحد دلوقتي السطور اللي عليها خصم باعت نفس القطع زي اللي من غير خصم، فنعمله في ${test.length} فرع ونسيب ${ctrl.length} فرع شبههم زي ما هم. بعد ${weeksAr(r.weeks)} نقارن القطع في الفرع بين المجموعتين – ونعمّمه بس لو الفرق أكتر من ${nf(r.uplift_needed_pct)}%.`))}</div></div>
      <div class="groups mt"><div><h3>${t('Test – promotion on', 'تجربة – عليها العرض')} · ${N(test.length)}</h3><ul>${test.map(g => `<li><span>${esc(g.branch_name_ar)}</span><span class="muted">${esc(g.governorate_ar)}</span></li>`).join('')}</ul></div>
        <div><h3>${t('Control – no promotion', 'مقارنة – من غير عرض')} · ${N(ctrl.length)}</h3><ul>${ctrl.map(g => `<li><span>${esc(g.branch_name_ar)}</span><span class="muted">${esc(g.governorate_ar)}</span></li>`).join('')}</ul></div></div>`;
  });
  $('#pcat').onchange = e => { st.cat = e.target.value; promo(); };
  $('#pdisc').oninput = e => { $('#pdisco').textContent = e.target.value + '%'; st.disc = +e.target.value; promo(); };
  onSeg(view, 'weeks', v => { st.weeks = +v; promo(); });
  $('#psave2').onclick = async () => { await post('/api/pricing/promo/save', { category: st.cat, discount: st.disc, weeks: st.weeks }); toast(t('Promotion test saved', 'تجربة العرض اتحفظت')); route(); };
  promo();
}, 'pricing');

// ================================================================ Marketing budget
page(/^#\/marketing$/, async (view) => {
  const st = { budget: null, pairs: 4 };
  const load = async () => { const d = await api(`/api/marketing?pairs=${st.pairs}${st.budget != null ? '&budget=' + st.budget : ''}`); st.budget = d.budget; render(d); };
  const render = d => {
    const g = d.gov, chg = (d.budget / d.today_month - 1) * 100, paused = g.reduce((a, r) => a + r.plan - r.plan_test_month, 0);
    const top = [...g].sort((a, b) => b.orders - a.orders).slice(0, 12);
    const testTag = x => x === 'pause' ? `<span class="tag solid">${t('paused 4 weeks', 'متوقف 4 أسابيع')}</span>` : x === 'control' ? `<span class="tag teal">${t('comparison', 'مقارنة')}</span>` : '';
    view.innerHTML = `<div class="page">
      ${head(t('Marketing budget', 'ميزانية التسويق'), t('The month’s budget follows each governorate’s orders, and a 4-week holdout measures what ads really add.', 'ميزانية الشهر بتمشي مع طلبات كل محافظة، وتجربة إيقاف 4 أسابيع بتقيس الإعلان بيزوّد قد إيه فعلاً.'),
        `<a class="btn" href="/api/marketing?format=csv&budget=${d.budget}&pairs=${st.pairs}">${I('download')} CSV</a><button class="btn primary" id="msave">${I('save')} ${t('Save budget', 'احفظ الميزانية')}</button>`)}
      <div class="card"><div class="controls">
        <div class="field"><label>${t('Budget for the month (EGP)', 'ميزانية الشهر (جنيه)')}</label><div style="display:flex;gap:6px;flex-wrap:wrap">
          <input type="number" id="mbud" step="50000" min="0" value="${Math.round(d.budget)}" style="width:150px">
          <button class="btn sm" data-b="${Math.round(d.today_month)}">${t('today’s level', 'زي النهارده')}</button><button class="btn sm" data-b="${Math.round(d.today_month * 0.75)}">−25%</button><button class="btn sm" data-b="${Math.round(d.today_month * 0.6)}">−40%</button></div></div>
        <div class="field"><label>${t('Holdout pairs', 'أزواج التجربة')}</label>${segHTML('pairs', [0, 1, 2, 3, 4, 5].map(x => [x, x]), st.pairs)}</div>
      </div></div>
      <div class="grid g4 mt">
        ${kpi(t('Budget this month', 'ميزانية الشهر'), N(big(d.budget)), t(`${sign(chg)}% vs today’s ${big(d.today_month)}`, `${sign(chg)}% عن ${big(d.today_month)} النهارده`), true, 'megaphone')}
        ${kpi(t('Saved in a year at this level', 'توفير في السنة بالمستوى ده'), N(big(Math.max(0, (d.today_month - d.budget) * 12))), t('EGP', 'جنيه'), false, 'target')}
        ${kpi(t('Paused during the test', 'متوقف أثناء التجربة'), N(big(paused)), t(`${d.pairs.length} governorates · 4 weeks`, `${d.pairs.length} محافظة · 4 أسابيع`), false, 'calendar')}
        ${kpi(t('What campaigns claim', 'اللي الحملات بتقوله'), N('×' + nf(d.claimed_x)), t('the real orders', 'الطلبات الحقيقية'), false, 'info')}
      </div>
      <div class="grid g-7-5 mt">
        <div class="card"><h3>${t('Budget by governorate', 'الميزانية لكل محافظة')}</h3><p class="sub">${t('share of FY2026 orders × the month’s budget', 'نصيبها من طلبات FY2026 × ميزانية الشهر')}</p>
          <div class="tbl-wrap"><table class="tbl"><thead><tr><th>${t('Governorate', 'المحافظة')}</th><th class="n">${t('% of orders', '% الطلبات')}</th><th class="n">${t('Spend today / month', 'الصرف النهارده / شهر')}</th><th class="n">${t('Plan / month', 'الخطة / شهر')}</th><th>${t('Test', 'التجربة')}</th></tr></thead>
          <tbody>${g.map(r => `<tr><td><b>${esc(r.governorate_ar)}</b></td><td class="n">${nf(r.order_share, 1)}%</td><td class="n muted">${nf(r.today_month)}</td><td class="n"><b>${nf(r.plan)}</b></td><td>${testTag(r.test)}</td></tr>`).join('')}</tbody>
          <tfoot><tr><td>${t('Total', 'الإجمالي')}</td><td class="n">100%</td><td class="n">${nf(d.today_month)}</td><td class="n">${nf(d.budget)}</td><td></td></tr></tfoot></table></div></div>
        <div class="grid" style="align-content:start">
          <div class="card"><h3>${t('Orders vs spend today', 'الطلبات مقابل الصرف النهارده')}</h3><p class="sub">${t('% of the total, top 12 governorates', '% من الإجمالي، أكبر 12 محافظة')}</p><div id="mchart"></div></div>
          <div class="card"><h3>${t('Holdout test · 4 weeks', 'تجربة الإيقاف · 4 أسابيع')}</h3><p class="sub">${t('pairs with similar orders; Cairo and Alexandria stay on', 'أزواج طلباتها قريبة؛ القاهرة والإسكندرية مكمّلين')}</p>
            ${d.pairs.length ? `<div class="pairs">${d.pairs.map(p => `<div class="pair"><div><span class="tag solid">${t('pause', 'نوقف')}</span> <b>${esc(p.pause)}</b></div><span class="vs">${t('vs', 'قصاد')}</span><div><span class="tag teal">${t('keep', 'نكمّل')}</span> <b>${esc(p.keep)}</b></div></div>`).join('')}</div>
            <div class="note teal mt">${I('info')}<div>${t('After 4 weeks compare the change in orders in each pair. If the paused side did not drop, those ads were not adding orders.', 'بعد 4 أسابيع نقارن التغيير في الطلبات في كل زوج. لو المحافظة اللي وقفناها ماقلّتش، يبقى الإعلان ده مكانش بيزوّد طلبات.')}</div></div>` : `<p class="muted">${t('No test this month.', 'مفيش تجربة الشهر ده.')}</p>`}</div>
        </div>
      </div>
      <div class="card mt"><h3>${t('Saved budgets', 'الميزانيات المحفوظة')}</h3>
        ${savedList(d.saved, p => `<tr><td>${N(p.saved)}</td><td>${mon(p.month)}</td><td class="n">${N(egp(p.budget))}</td><td class="n">${N(p.pairs.length)} ${t('test pairs', 'أزواج تجربة')}</td></tr>`)}</div>
    </div>`;
    Charts.hbars($('#mchart'), top.map(r => r.governorate_ar), [{ name: t('% of orders', '% الطلبات'), color: Charts.C.navy, values: top.map(r => r.order_share) },
      { name: t('% of spend', '% الصرف'), color: Charts.C.grey, values: top.map(r => r.spend_share) }], { labelWidth: 96, fmt: v => nf(v, 1) + '%' });
    $('#mbud').onchange = e => { st.budget = Math.max(0, +e.target.value || 0); load(); };
    $$('[data-b]', view).forEach(b => b.onclick = () => { st.budget = +b.dataset.b; load(); });
    onSeg(view, 'pairs', v => { st.pairs = +v; load(); });
    $('#msave').onclick = async () => { await post('/api/marketing/save', { budget: st.budget, pairs: st.pairs }); toast(t('Marketing budget saved', 'ميزانية التسويق اتحفظت')); refreshToday(); load(); };
  };
  await load();
}, 'marketing');

// ================================================================ Branches
const SORTS = [['gap', 'Pieces not accounted for', 'قطع مش متحسوبة'], ['cover', 'Stock cover', 'المخزون يكفي'], ['ratio', 'Received ÷ sold', 'المستلم ÷ المتباع'], ['growth', 'Growth', 'النمو'], ['sales', 'Sales', 'المبيعات'], ['name', 'Name', 'الاسم']];
page(/^#\/branches$/, async (view, q) => {
  const d = S.cache.branches || (S.cache.branches = await api('/api/branches'));
  const B = d.branches;
  const st = { s: '', gov: q.get('gov') || '', flag: q.get('flag') || '', sort: q.get('sort') || 'gap' };
  const govs = [...new Set(B.map(b => b.governorate_ar))].sort((a, b) => B.filter(x => x.governorate_ar === b).length - B.filter(x => x.governorate_ar === a).length);
  const maxGap = Math.max(...B.map(b => b.stock_gap));
  view.innerHTML = `<div class="page">
    ${head(t('Branches', 'الفروع'), t(`${B.length} branches in ${govs.length} governorates · open any branch for its profile`, `${B.length} فرع في ${govs.length} محافظة · افتح أي فرع عشان ملفه`), `<a class="btn" href="/api/branches?format=csv">${I('download')} CSV</a>`)}
    <div class="card"><div class="controls">
      <label class="ask" style="max-width:260px">${I('search')}<input id="bs" placeholder="${t('Branch name or code', 'اسم الفرع أو الكود')}"></label>
      <div class="field"><label>${t('Governorate', 'المحافظة')}</label><select id="bgov"><option value="">${t('All', 'الكل')}</option>${govs.map(g => `<option ${g === st.gov ? 'selected' : ''}>${esc(g)}</option>`).join('')}</select></div>
      <div class="field"><label>${t('Staff file', 'ملف الموظفين')}</label>${segHTML('flag', [['', t('All', 'الكل')], ['no_manager', t('No store manager', 'من غير مدير')], ['no_cashier', t('No cashier', 'من غير كاشير')]], st.flag)}</div>
      <div class="field"><label>${t('Sort by', 'رتّب حسب')}</label><select id="bsort">${SORTS.map(s => `<option value="${s[0]}" ${s[0] === st.sort ? 'selected' : ''}>${t(s[1], s[2])}</option>`).join('')}</select></div>
      <span class="chip" id="bcount"></span>
    </div></div>
    <div class="card mt" style="padding:0"><div class="tbl-wrap" style="border:0;max-height:calc(100vh - 290px)"><table class="tbl"><thead><tr>
      <th>${t('Branch', 'الفرع')}</th><th>${t('Governorate', 'المحافظة')}</th><th>${t('Type', 'النوع')}</th><th class="n">${t('Sales FY2026 (M EGP)', 'مبيعات FY2026 (مليون)')}</th><th class="n">${t('Growth', 'النمو')}</th>
      <th class="n">${t('Received ÷ sold', 'المستلم ÷ المتباع')}</th><th class="n">${t('Stock cover', 'المخزون يكفي')}</th><th class="n">${t('Pieces not accounted for', 'قطع مش متحسوبة')}</th><th>${t('Staff file', 'ملف الموظفين')}</th></tr></thead><tbody id="bbody"></tbody></table></div></div>
  </div>`;
  const key = { gap: b => -b.stock_gap, cover: b => -b.months_cover, ratio: b => -b.sent_per_sold, growth: b => -b.growth, sales: b => -b.sales26, name: b => b.branch_name_ar };
  const draw = () => {
    const s = st.s.trim().toLowerCase();
    const rows = B.filter(b => (!s || b.branch_name_ar.toLowerCase().includes(s) || b.branch_id.toLowerCase().includes(s)) && (!st.gov || b.governorate_ar === st.gov)
      && (!st.flag || (st.flag === 'no_manager' ? !b.has_manager : !b.has_cashier)))
      .sort((a, b) => { const ka = key[st.sort](a), kb = key[st.sort](b); return typeof ka === 'string' ? ka.localeCompare(kb, 'ar') : ka - kb; });
    $('#bcount').innerHTML = `${N(rows.length)} ${t('branches', 'فرع')}`;
    $('#bbody').innerHTML = rows.map(b => `<tr class="click" data-go="#/branches/${b.branch_id}">
      <td><b>${esc(b.branch_name_ar)}</b> <span class="muted small num">${b.branch_id}</span></td><td>${esc(b.governorate_ar)}</td><td><span class="tag">${typeName(b.retail_location_type)}</span></td>
      <td class="n">${nf(b.sales26 / 1e6, 2)}</td><td class="n">${N(sign(b.growth) + '%')}</td><td class="n">${N('×' + nf(b.sent_per_sold, 1))}</td><td class="n">${N(nf(b.months_cover, 1))} ${t('mo', 'شهر')}</td>
      <td class="n"><div class="bar-cell"><span>${nf(b.stock_gap)}</span><i style="width:${Math.round(60 * b.stock_gap / maxGap)}px"></i></div></td>
      <td>${!b.has_manager ? `<span class="tag navy">${t('no store manager', 'من غير مدير فرع')}</span>` : !b.has_cashier ? `<span class="tag navy">${t('no cashier', 'من غير كاشير')}</span>` : `<span class="tag teal">${t('complete', 'كامل')}</span>`}</td></tr>`).join('');
    $$('[data-go]', view).forEach(r => r.onclick = () => { location.hash = r.dataset.go; });
  };
  $('#bs').oninput = e => { st.s = e.target.value; draw(); };
  $('#bgov').onchange = e => { st.gov = e.target.value; draw(); };
  $('#bsort').onchange = e => { st.sort = e.target.value; draw(); };
  onSeg(view, 'flag', v => { st.flag = v; draw(); });
  draw();
}, 'branches');

page(/^#\/branches\/(BR\d+)$/, async (view, q, bid) => {
  const d = await api('/api/branches/' + bid);
  const b = d.info, pe = d.peers;
  const vs = (v, med, unit = '') => t(`branch median ${med}${unit}`, `الوسيط بين الفروع ${med}${unit}`);
  const months = Object.entries(d.monthly);
  const ROLES = ['Store Manager', 'Cashier', 'Inventory Clerk', 'Sales Associate', 'Area Manager'];
  const staff = [...d.staff].sort((x, y) => ROLES.indexOf(x.position_en) - ROLES.indexOf(y.position_en));
  const offKinds = ['Raw materials', 'Returns'];
  const srcTotal = d.sources.reduce((a, s) => a + s.units, 0);
  const off = d.sources.filter(s => offKinds.includes(s.kind)).reduce((a, s) => a + s.units, 0);
  view.innerHTML = `<div class="page">
    <a class="back" href="#/branches">${I('back')} ${t('Branches', 'الفروع')}</a>
    <div class="head"><div class="bp-head"><div class="bp-mark">${I('store')}</div><div><h1>${esc(b.branch_name_ar)}</h1>
      <div class="meta"><span class="num">${b.branch_id}</span><span>${typeName(b.retail_location_type)}</span><span>${esc(b.governorate_ar)} · ${esc(b.city_ar)}</span><span>${esc(b.address_ar)}</span><span>${t('opened', 'افتتح')} ${N(String(b.opening_date).slice(0, 10))}</span></div></div></div>
      <div class="actions"><span class="chip navy">${I('warehouse')} ${esc(b.dc_name)}</span><a class="btn" href="#/assistant?q=${encodeURIComponent(b.branch_name_ar)}">${I('spark')} ${t('Ask Khayt', 'اسأل خيط')}</a></div></div>
    <div class="grid g4">
      ${kpi(t('Sales FY2026', 'مبيعات FY2026'), N(big(b.sales26, 2)), `<span class="up">${N(sign(b.growth) + '%')}</span> · ${vs(0, big(pe.sales26_median, 2))}`, true)}
      ${kpi(t('Received ÷ sold', 'المستلم ÷ المتباع'), N('×' + nf(b.sent_per_sold, 1)), t(`${nf(b.sent26)} received, ${nf(b.sold26)} sold · median ×${nf(pe.sent_per_sold_median, 1)}`, `استلم ${nf(b.sent26)} وباع ${nf(b.sold26)} · الوسيط ×${nf(pe.sent_per_sold_median, 1)}`))}
      ${kpi(t('Stock cover', 'المخزون يكفي'), N(nf(b.months_cover, 1)) + ' ' + t('months', 'شهر'), t(`${nf(b.stock_units)} pieces on record · median ${nf(pe.cover_median, 1)}`, `${nf(b.stock_units)} قطعة متسجلة · الوسيط ${nf(pe.cover_median, 1)}`))}
      ${kpi(t('Pieces not accounted for', 'قطع مش متحسوبة'), N(nf(b.stock_gap)), t(`since 2018 · median ${nf(pe.gap_median)}`, `من 2018 · الوسيط ${nf(pe.gap_median)}`))}
    </div>
    <div class="grid g-7-5 mt">
      <div class="card"><h3>${t('Monthly sales', 'المبيعات الشهرية')}</h3><p class="sub">${t('net, EGP · last 24 months', 'صافي، جنيه · آخر 24 شهر')}</p><div id="bmon"></div></div>
      <div class="card"><h3>${t('What it sells vs what it receives', 'بيبيع إيه مقابل بيستلم إيه')}</h3><p class="sub">${t('% of pieces, FY2026 · top 8 categories', '% من القطع، FY2026 · أكبر 8 فئات')}</p><div id="bmix"></div></div>
    </div>
    <div class="grid g2 mt">
      <div class="card"><h3>${t('Recorded stock', 'المخزون المتسجل')}</h3><p class="sub">${t('last count on file, with months of sales it covers', 'آخر رصيد متسجل، وبيكفي كام شهر بيع')}</p>
        <div class="tbl-wrap"><table class="tbl"><thead><tr><th>${t('Category', 'الفئة')}</th><th class="n">${t('Pieces', 'قطع')}</th><th class="n">${t('Value (EGP)', 'القيمة (جنيه)')}</th><th class="n">${t('Covers', 'يكفي')}</th></tr></thead>
        <tbody>${d.stock.map(s => `<tr><td>${esc(cat(s.product_category))}</td><td class="n">${nf(s.closing_units)}</td><td class="n">${nf(s.closing_stock_value_EGP)}</td><td class="n"><div class="bar-cell"><span>${nf(s.months_cover, 1)}</span><i class="${s.months_cover > 12 ? 't' : ''}" style="width:${Math.min(60, Math.round(s.months_cover * 2))}px"></i></div></td></tr>`).join('')}</tbody></table></div></div>
      <div class="card"><h3>${t('Where its shipments come from', 'التحويلات بتيجي منين')}</h3><p class="sub">${t('FY2026 · the plan ships from', 'FY2026 · الخطة بتبعت من')} ${esc(b.dc_name)}</p>
        <div class="tbl-wrap"><table class="tbl"><tbody>${d.sources.map(s => `<tr><td>${esc(s.name)}</td><td>${offKinds.includes(s.kind) ? `<span class="tag navy">${s.kind === 'Returns' ? t('returns', 'مرتجعات') : t('raw material', 'خامات')}</span>` : s.warehouse_id === b.dc ? `<span class="tag teal">${t('nearest', 'الأقرب')}</span>` : ''}</td>
          <td class="n">${nf(s.units)}</td><td class="n muted">${nf(s.units / srcTotal * 100)}%</td></tr>`).join('')}</tbody></table></div>
        ${off ? `<p class="small muted" style="margin:10px 0 0">${t(`${nf(off / srcTotal * 100)}% came from warehouses that should not ship finished goods to branches.`, `${nf(off / srcTotal * 100)}% جه من مخازن المفروض متبعتش منتج تام للفروع.`)}</p>` : ''}</div>
    </div>
    <div class="grid g-7-5 mt">
      <div class="card"><h3>${t('Staff on file', 'الموظفين في الملف')} · ${N(staff.length)}</h3><p class="sub">${t('from the HR file; salaries are not used (they look random)', 'من ملف الـ HR؛ المرتبات مش مستخدمة (شكلها عشوائي)')}</p>
        <div class="staff">${!b.has_manager ? `<div class="person missing"><div class="av">?</div><div><b>${t('No store manager', 'مفيش مدير فرع')}</b><span>${t('confirm with HR', 'نتأكد مع الـ HR')}</span></div></div>` : ''}
          ${!b.has_cashier ? `<div class="person missing"><div class="av">?</div><div><b>${t('No cashier', 'مفيش كاشير')}</b><span>${t('confirm with HR', 'نتأكد مع الـ HR')}</span></div></div>` : ''}
          ${staff.map(p => `<div class="person"><div class="av">${esc(p.employee_name_ar.trim().charAt(0))}</div><div><b>${esc(p.employee_name_ar)}</b><span>${esc(role(p.position_en))} · ${N(String(p.hire_date).slice(0, 4))}</span></div></div>`).join('')}</div></div>
      <div class="card"><div class="card-head"><div><h3>${t(`Next shipment · ${mon(d.next_month_label)}`, `التحويل الجاي · ${mon(d.next_month_label)}`)}</h3><p class="sub">${t('demand + 10% safety, from', 'الطلب + 10% أمان، من')} ${esc(b.dc_name)}</p></div>
          <a class="btn sm" href="#/distribution/print?branch=${bid}&month=${d.next_month_label}">${I('print')} ${t('Pick list', 'قايمة التجهيز')}</a></div>
        <div class="tbl-wrap"><table class="tbl"><thead><tr><th>${t('Category', 'الفئة')}</th><th class="n">${t('Send', 'نبعت')}</th><th class="n">${t('Usual', 'المعتاد')}</th></tr></thead>
        <tbody>${d.next_month.map(r => `<tr><td>${esc(cat(r.category_en))}</td><td class="n"><b>${nf(r.send)}</b></td><td class="n muted">${nf(r.sent_month_fy26)}</td></tr>`).join('')}</tbody>
        <tfoot><tr><td>${t('Total', 'الإجمالي')}</td><td class="n">${nf(d.next_month.reduce((a, r) => a + r.send, 0))}</td><td class="n">${nf(d.next_month.reduce((a, r) => a + r.sent_month_fy26, 0))}</td></tr></tfoot></table></div></div>
    </div>
    <div class="card mt"><h3>${t('Notes', 'ملاحظات')}</h3><p class="sub">${t('visits, count results, anything to follow up – they appear in the monthly report', 'زيارات، نتيجة الجرد، أي حاجة للمتابعة – بتظهر في تقرير الشهر')}</p>
      <textarea class="input notes" id="bnote" placeholder="${t('e.g. stock count on the 10th', 'مثلاً: جرد يوم 10')}">${esc(d.note)}</textarea>
      <div style="display:flex;gap:10px;align-items:center;margin-top:8px"><button class="btn primary" id="bsave">${I('save')} ${t('Save note', 'احفظ الملاحظة')}</button>
      ${b.orders_before_opening ? `<span class="small muted">${t(`${nf(b.orders_before_opening)} orders are dated before this branch opened – the opening date needs checking.`, `${nf(b.orders_before_opening)} طلب متسجل قبل افتتاح الفرع – تاريخ الافتتاح محتاج مراجعة.`)}</span>` : ''}</div></div>
  </div>`;
  Charts.lines($('#bmon'), months.map(x => monShort(x[0])), [{ name: t('net sales', 'صافي المبيعات'), color: Charts.C.navy, values: months.map(x => x[1]) }], { height: 240 });
  const mix = d.mix.slice(0, 8);
  Charts.hbars($('#bmix'), mix.map(m => cat(m.category_en)), [{ name: t('% of pieces sold', '% من المتباع'), color: Charts.C.navy, values: mix.map(m => m.sold_pct) },
    { name: t('% of pieces received', '% من المستلم'), color: Charts.C.teal, values: mix.map(m => m.sent_pct) }], { labelWidth: 112, fmt: v => nf(v) + '%' });
  $('#bsave').onclick = async () => { await post(`/api/branches/${bid}/note`, { note: $('#bnote').value }); toast(t('Note saved', 'الملاحظة اتحفظت')); };
}, 'branches');
