/* Cottonil Decision Hub – single-page app (vanilla JS). Every number comes from the Flask API (core/ in Python). */
const S = { lang: localStorage.getItem('lang') || 'en', me: null, cache: {} };
const t = (en, ar) => (S.lang === 'ar' ? ar : en);
const $ = (sel, root = document) => root.querySelector(sel);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const M = v => (v / 1e6).toLocaleString('en', { maximumFractionDigits: 1, minimumFractionDigits: 1 }) + 'M';
const K = v => Math.round(v / 1e3).toLocaleString('en') + 'K';
const N = v => Math.round(v).toLocaleString('en');
const P = (v, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d) + '%';
const EGP = () => t('EGP', 'جنيه');

async function api(path, opts = {}) {
  const r = await fetch(path, { credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined });
  if (r.status === 401 && !path.includes('/login')) { S.me = null; renderLogin(); throw new Error('login'); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}
function toast(msg) { const d = document.createElement('div'); d.className = 'toast'; d.textContent = msg; document.body.appendChild(d); setTimeout(() => d.remove(), 2200); }
function setDir() { document.documentElement.lang = S.lang; document.documentElement.dir = S.lang === 'ar' ? 'rtl' : 'ltr'; }
function switchLang() { S.lang = S.lang === 'ar' ? 'en' : 'ar'; localStorage.setItem('lang', S.lang); setDir(); S.me ? route() : renderLogin(); }

/* ------------------------------------------------------------------ login */
function renderLogin() {
  setDir();
  $('#app').innerHTML = `
  <div class="login-wrap"><form class="login" id="loginForm" autocomplete="on">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div class="brand">COTTONIL<small>${t('Decision Hub', 'مركز القرار')}</small></div>
      <button type="button" class="lang-toggle" id="lg">${t('العربية', 'English')}</button></div>
    <h1>${t('Manager sign in', 'دخول المدير')}</h1>
    <p>${t('Problems, solutions and the decisions of the month – from Cottonil’s own data.', 'المشاكل والحلول وقرارات الشهر – من داتا قطنيل نفسها.')}</p>
    <div class="field"><label>${t('Username', 'اسم المستخدم')}</label><input name="username" required autocomplete="username" value=""></div>
    <div class="field"><label>${t('Password', 'كلمة السر')}</label><input name="password" type="password" required autocomplete="current-password"></div>
    <div class="err" id="err"></div>
    <button class="btn block">${t('Sign in', 'دخول')}</button>
    <div class="hint">${t('Accounts: ceo · supply · marketing · finance. The first password is in the README; you will be asked to change it.',
                          'الحسابات: ceo · supply · marketing · finance. أول كلمة سر مكتوبة في الـ README، وهيطلب منك تغيّرها.')}</div>
  </form></div>`;
  $('#lg').onclick = switchLang;
  $('#loginForm').onsubmit = async e => {
    e.preventDefault();
    const f = new FormData(e.target);
    try {
      S.me = await api('/api/login', { method: 'POST', body: { username: f.get('username'), password: f.get('password') } });
      if (location.hash === '#/home' || location.hash === '') { history.replaceState(null, '', '#/home'); route(); } else location.hash = '#/home';
    }
    catch (err) { $('#err').textContent = t('Wrong username or password', 'اسم المستخدم أو كلمة السر غلط'); }
  };
}

function passwordModal(force) {
  if (document.querySelector('.modal-back')) return;
  const back = document.createElement('div');
  back.className = 'modal-back';
  back.innerHTML = `<form class="modal"><h2 style="margin-top:0">${t('Change your password', 'غيّر كلمة السر')}</h2>
    ${force ? `<p class="sub">${t('First sign-in: please choose your own password.', 'أول دخول: اختار كلمة سر خاصة بيك.')}</p>` : ''}
    <div class="field"><label>${t('Current password', 'كلمة السر الحالية')}</label><input name="old" type="password" required></div>
    <div class="field"><label>${t('New password (8+ characters)', 'كلمة السر الجديدة (8 حروف أو أكتر)')}</label><input name="new" type="password" minlength="8" required></div>
    <div class="err"></div><div style="display:flex;gap:8px"><button class="btn">${t('Save', 'حفظ')}</button>
    ${force ? '' : `<button type="button" class="btn ghost" id="cx">${t('Cancel', 'إلغاء')}</button>`}</div></form>`;
  document.body.appendChild(back);
  if (!force) $('#cx', back).onclick = () => back.remove();
  $('form', back).onsubmit = async e => {
    e.preventDefault(); const f = new FormData(e.target);
    try { await api('/api/password', { method: 'POST', body: { old: f.get('old'), new: f.get('new') } }); back.remove(); S.me.must_change = false; toast(t('Password changed', 'اتغيرت كلمة السر')); }
    catch (err) { $('.err', back).textContent = err.message; }
  };
}

/* ------------------------------------------------------------------ shell */
const NAV = () => [
  [t('Overview', 'نظرة عامة'), [['home', '🏠', t('Decisions this month', 'قرارات الشهر')], ['problems', '🧩', t('Problems & solutions', 'المشاكل والحلول')]]],
  [t('Solution tools', 'أدوات الحل'), [['purchase', '🛒', t('Purchase plan (AI)', 'خطة الشراء (AI)')], ['allocation', '🚚', t('Branch allocation', 'توزيع الفروع')],
    ['discount', '🏷️', t('Discount guardrail', 'قواعد الخصم')], ['marketing', '📣', t('Marketing budget & test', 'ميزانية وتجربة التسويق')], ['shipping', '📦', t('Free-shipping rule', 'قاعدة الشحن المجاني')]]],
  [t('Follow-up', 'المتابعة'), [['actions', '✅', t('Action tracker', 'متابعة المهام')], ['gaps', '🛡️', t('Data gaps & requests', 'ثغرات الداتا والطلبات')], ['assistant', '💬', t('Ask the data', 'اسأل الداتا')]]],
];

function shell(page, title, sub, body) {
  setDir();
  const nav = NAV().map(([g, items]) => `<div class="nav-group">${g}</div><div class="nav">${items.map(([id, ic, label]) =>
    `<a href="#/${id}" class="${id === page ? 'active' : ''}">${ic} <span>${label}</span></a>`).join('')}</div>`).join('');
  $('#app').innerHTML = `<div class="shell">
    <aside class="side" id="side"><div class="brand">COTTONIL<small>${t('Decision Hub · HVIA Task 3', 'مركز القرار · HVIA Task 3')}</small></div>${nav}
      <div class="me"><b>${esc(t(S.me.name, S.me.name_ar))}</b>${esc(S.me.role)}
        <div class="row"><button id="lg">${t('العربية', 'English')}</button><button id="pw">${t('Password', 'كلمة السر')}</button><button id="lo">${t('Sign out', 'خروج')}</button></div></div></aside>
    <main><div class="top"><div><button class="menu-btn" id="mb">☰</button><h1>${title}</h1>${sub ? `<p>${sub}</p>` : ''}</div></div><div id="page">${body || '<div class="loading">…</div>'}</div></main></div>`;
  $('#lg').onclick = switchLang;
  $('#lo').onclick = async () => { await api('/api/logout', { method: 'POST' }); S.me = null; renderLogin(); };
  $('#pw').onclick = () => passwordModal(false);
  $('#mb').onclick = () => $('#side').classList.toggle('open');
}

function kpi(label, value, delta, good = true, help = '') {
  const cls = delta == null ? '' : ((delta >= 0) === good ? 'up' : 'down');
  return `<div class="kpi" title="${esc(help)}"><div class="l">${label}</div><div class="v">${value}</div>${delta == null ? '' : `<div class="d ${cls}">${P(delta)} ${t('vs FY2025', 'عن FY2025')}</div>`}</div>`;
}
function table(rows, cols) {
  return `<div class="table-wrap"><table><thead><tr>${cols.map(c => `<th class="${c.n ? 'n' : ''}">${c.label}</th>`).join('')}</tr></thead><tbody>${rows.map(r =>
    `<tr>${cols.map(c => `<td class="${c.n ? 'n' : ''}">${c.f ? c.f(r[c.key], r) : esc(r[c.key])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
const statusChip = s => `<span class="chip ${/^Ready/.test(s) ? 'ready' : s === 'Partial' ? 'partial' : /rejected|reliable/.test(s) ? 'bad' : 'grey'}">${esc(t(s, {
  'Ready': 'جاهز', 'Ready (flat)': 'جاهز (ثابت)', 'Partial': 'جزئي', 'Tested – rejected': 'اتجرّب واترفض', 'Not reliable': 'غير موثوق', 'Not meaningful': 'بلا معنى', 'Not possible': 'غير ممكن' }[s] || s))}</span>`;
const sevChip = s => `<span class="chip ${({ Business: 'business', High: 'high', Medium: 'medium', Unreliable: 'grey' })[s]}">${esc(t(s, { Business: 'اكتشاف بزنس', High: 'عالي', Medium: 'متوسط', Unreliable: 'حقل عشوائي' }[s]))}</span>`;
const OWNERS = { ceo: ['CEO', 'المدير التنفيذي'], supply: ['Supply chain', 'سلسلة الإمداد'], marketing: ['Marketing', 'التسويق'], finance: ['Finance', 'المالية'] };
const owner = u => OWNERS[u] ? t(...OWNERS[u]) : esc(u);
const AREAS = { Sales: 'المبيعات', Marketing: 'التسويق', 'Supply chain': 'سلسلة الإمداد', Finance: 'المالية', Strategy: 'الاستراتيجية', Customers: 'العملاء',
  'E-commerce': 'الأونلاين', HR: 'الموارد البشرية', Operations: 'التشغيل', CEO: 'المدير التنفيذي', 'CEO / Sales': 'المدير التنفيذي / المبيعات' };
const area = a => esc(t(a, AREAS[a] || a));

/* ------------------------------------------------------------------ pages */
async function pageHome() {
  shell('home', t('Decisions this month', 'قرارات الشهر'), t('FY2026 = Oct 2025 – Sep 2026. Every number below is computed from the data, with its source.', 'FY2026 = أكتوبر 2025 – سبتمبر 2026. كل رقم تحت محسوب من الداتا ومعاه مصدره.'));
  const d = await api('/api/overview'); const k = d.kpis;
  $('#page').innerHTML = `
  <div class="hero"><div><div style="opacity:.8">${t('Profit on the table, per year', 'ربح ممكن نرجّعه في السنة')}</div><div class="big">+${M(k.profit_at_stake)} ${EGP()} (+${k.uplift_pct.toFixed(0)}%)</div>
    <p>${t('Cottonil does not need to sell more – it needs its decisions (discounts, marketing, buying, distribution) to follow real demand.',
           'قطنيل مش محتاجة تبيع أكتر – محتاجة قراراتها (الخصم، والتسويق، والشراء، والتوزيع) تمشي مع الطلب الحقيقي.')}</p></div>
    <div><a class="btn" style="background:#fff;color:var(--navy)" href="#/problems">${t('See the problems', 'شوف المشاكل')} (${d.problems_open})</a></div></div>
  <div class="grid g6" style="margin-top:14px">
    ${kpi(t('Net sales FY2026', 'صافي المبيعات FY2026'), M(k.net_sales), k.net_sales_g)}
    ${kpi(t('Gross profit', 'إجمالي الربح'), M(k.gross_profit), k.gross_profit_g)}
    ${kpi(t('Gross margin', 'هامش الربح'), k.margin.toFixed(1) + '%')}
    ${kpi(t('Pieces sold (real growth)', 'القطع المباعة (النمو الحقيقي)'), K(k.units), k.units_g)}
    ${kpi(t('Price per piece', 'سعر القطعة'), P(k.price_g, 0), null)}
    ${kpi(t('Discounts given', 'الخصومات'), M(k.discount), null)}
  </div>
  <div class="grid g2" style="margin-top:14px">
    <div class="card"><h2>${t('This month: 6 decisions', 'الشهر ده: 6 قرارات')}</h2><p class="sub">${t('From the data, in priority order', 'من الداتا، بالترتيب')}</p>
      <ul class="list">${d.decisions.map((x, i) => `<li><span class="num">${i + 1}</span><div><div><a href="#/${x.link}">${esc(t(x.title, x.title_ar))}</a></div><div class="sub" style="margin:0">${area(x.owner)}</div></div></li>`).join('')}</ul></div>
    <div class="card"><h2>${t(`4 actions = +${M(d.bridge.new - d.bridge.base)} profit a year`, `4 إجراءات = +${M(d.bridge.new - d.bridge.base)} ربح في السنة`)}</h2><p class="sub">${t('FY2026 gross profit → after the plan (assumptions on each tool page)', 'إجمالي ربح FY2026 ← بعد الخطة (الافتراضات في صفحة كل أداة)')}</p><div id="wf"></div></div>
  </div>
  <div class="grid g2" style="margin-top:14px">
    <div class="card"><h2>${t('Sales ×15 since FY2019 – pieces only ×2.5', 'المبيعات ×15 من FY2019 – والقطع ×2.5 بس')}</h2><p class="sub">${t('Monthly net sales and gross profit, M EGP', 'المبيعات وإجمالي الربح في الشهر، مليون جنيه')}</p><div id="trend"></div></div>
    <div class="card"><h2>${t('Real growth (pieces) is slowing', 'النمو الحقيقي (القطع) بيبطّأ')}</h2><p class="sub">${t('Growth in pieces sold per fiscal year', 'نمو القطع المباعة لكل سنة مالية')}</p><div id="vol"></div></div>
  </div>`;
  const b = d.bridge;
  Charts.waterfall($('#wf'), t('FY2026 profit', 'ربح FY2026'), b.base, b.actions.map(a => ({ label: t(a.action, a.action_ar), value: a.profit })), t('New profit', 'الربح الجديد'));
  const m = d.monthly;
  Charts.lines($('#trend'), m.map(r => r.month.slice(0, 7)), [
    { name: t('Net sales', 'المبيعات'), color: Charts.C.blue, values: m.map(r => r.net_sales) },
    { name: t('Gross profit', 'إجمالي الربح'), color: Charts.C.orange, values: m.map(r => r.gross_profit) }], { ticks: 8 });
  const fy = d.fy.filter(r => r.units_g != null);
  Charts.bars($('#vol'), fy.map((r, i) => ({ label: 'FY' + String(r.fy).slice(2), value: r.units_g, text: '+' + r.units_g.toFixed(1) + '%', color: i === fy.length - 1 ? Charts.C.orange : Charts.C.blue })), { fmtY: v => v.toFixed(0) + '%' });
  if (S.me.must_change) passwordModal(true);
}

async function pageProblems() {
  shell('problems', t('Problems & solutions', 'المشاكل والحلول'), t('Every problem with its evidence from the data, the root cause, the solution, the owner and the profit impact. Update the status as you go.',
    'كل مشكلة بالدليل من الداتا، والسبب، والحل، والمسؤول، وأثرها على الربح. حدّث الحالة وانت ماشي.'));
  const ps = await api('/api/problems');
  const total = ps.reduce((a, p) => a + p.impact, 0);
  $('#page').innerHTML = `<div class="insight">${t(`${ps.length} problems · ${ps.filter(p => p.status === 'Done').length} done · +${M(total)} EGP/year from the ones with a measurable impact. The others are cash or data problems: they unlock the next decisions.`,
    `${ps.length} مشاكل · ${ps.filter(p => p.status === 'Done').length} خلصت · +${M(total)} جنيه في السنة من اللي أثرها يتقاس. والباقي مشاكل كاش أو داتا: بيفتحوا القرارات الجاية.`)}</div>
  <div class="grid">${ps.map(p => `<div class="card problem">
    <div class="head"><div><h3>${p.id} · ${esc(t(p.title, p.title_ar))}</h3>
      <div class="meta"><span class="chip">${area(p.area)}</span><span class="chip partial">${t('Owner', 'المسؤول')}: ${owner(p.owner)}</span>
      ${p.impact > 0 ? `<span class="impact">+${M(p.impact)} ${EGP()}/${t('yr', 'سنة')}</span>` : `<span class="chip grey">${t('cash / data', 'كاش / داتا')}</span>`}</div></div>
      <select data-p="${p.id}" class="field" style="border:1px solid var(--line);border-radius:8px;padding:6px">${['Open', 'In progress', 'Done'].map(s => `<option value="${s}" ${s === p.status ? 'selected' : ''}>${t(s, { Open: 'مفتوحة', 'In progress': 'شغالين عليها', Done: 'خلصت' }[s])}</option>`).join('')}</select></div>
    <dl><dt>${t('Evidence', 'الدليل')}</dt><dd>${esc(t(p.evidence, p.evidence_ar))}</dd><dt>${t('Root cause', 'السبب')}</dt><dd>${esc(t(p.cause, p.cause_ar))}</dd>
      <dt>${t('Solution', 'الحل')}</dt><dd><b>${esc(t(p.solution, p.solution_ar))}</b></dd></dl>
    <div class="foot">${p.tool && p.tool !== 'home' ? `<a class="btn small" href="#/${p.tool}">${t('Open the tool', 'افتح الأداة')} →</a>` : ''}
      <button class="btn small ghost" data-a="${p.id}">+ ${t('Create an action', 'اعمل مهمة')}</button></div></div>`).join('')}</div>`;
  document.querySelectorAll('select[data-p]').forEach(s => s.onchange = async () => { await api('/api/problems/' + s.dataset.p, { method: 'POST', body: { status: s.value } }); toast(t('Saved', 'اتحفظ')); });
  document.querySelectorAll('button[data-a]').forEach(b => b.onclick = async () => {
    const p = ps.find(x => x.id === b.dataset.a);
    await api('/api/actions', { method: 'POST', body: { title: t(p.solution, p.solution_ar).slice(0, 180), owner: p.owner, problem: p.id, impact: p.impact } });
    toast(t('Action added to the tracker', 'المهمة اتضافت للمتابعة'));
  });
}

function slider(id, label, min, max, step, value, unit = '%') {
  return `<div class="field"><label>${label}</label><div class="range-row"><input type="range" id="${id}" min="${min}" max="${max}" step="${step}" value="${value}"><output id="${id}o">${value}${unit}</output></div></div>`;
}
function bindSlider(id, unit, fn) { const el = $('#' + id); el.oninput = () => { $('#' + id + 'o').textContent = el.value + unit; }; el.onchange = fn; }

async function pagePurchase() {
  shell('purchase', t('Purchase plan from the AI forecast', 'خطة الشراء من توقّع الـ AI'), t('Today Cottonil buys a fixed ~42M pieces a year, the same for every SKU. This plan buys what the forecast says we will sell.',
    'النهارده قطنيل بتشتري كمية ثابتة حوالي 42 مليون قطعة في السنة، ونفس الكمية لكل SKU. الخطة دي بتشتري اللي التوقّع بيقول هنبيعه.'));
  const draw = async () => {
    const svc = $('#svc')?.value || '95', trust = $('#trust')?.checked ? 1 : 0;
    const d = await api(`/api/tools/purchase?service=${svc}&trust=${trust}`);
    const tot = d.plan.reduce((a, r) => ({ f: a.f + r.forecast_3m, b: a.b + r.to_buy, c: a.c + r.current_pattern_buys }), { f: 0, b: 0, c: 0 });
    $('#out').innerHTML = `<div class="grid g4">${kpi(t('Demand ' + d.months[0] + ' – ' + d.months[d.months.length - 1], 'الطلب ' + d.months[0] + ' – ' + d.months[d.months.length - 1]), K(tot.f))}${kpi(t('Plan: buy', 'الخطة: نشتري'), K(tot.b))}
      ${kpi(t('Current pattern per quarter', 'النمط الحالي في الربع'), M(tot.c))}${kpi(t('AI is more accurate by', 'الـ AI أدق بـ'), d.backtest['better_%'].toFixed(0) + '%')}</div>
      <div class="grid g2" style="margin-top:14px"><div class="card"><h2>${t('Backtest on 6 hidden months', 'اختبار على 6 شهور مخفية')}</h2>
        <p class="sub">${t(`AI error ${d.backtest.wape_model}% vs ${d.backtest.wape_naive}% for "same month last year"`, `خطأ الـ AI ${d.backtest.wape_model}% مقابل ${d.backtest.wape_naive}% لـ "زي السنة اللي فاتت"`)}</p><div id="bt"></div></div>
      <div class="card"><h2>${t('What to buy, per category', 'نشتري إيه لكل فئة')}</h2><p class="sub">${t('pieces, next 3 months', 'قطع، التلات شهور الجايين')}</p><div id="cat"></div></div></div>
      <div class="card" style="margin-top:14px"><h2>${t('The plan', 'الخطة')}</h2><p class="sub">${t('to buy = forecast + safety stock' + (trust ? ' − stock on hand' : ''), 'نشتري = التوقّع + مخزون أمان' + (trust ? ' − المخزون الحالي' : ''))}</p>
      ${table(d.plan, [{ key: 'category_en', label: t('Category', 'الفئة') }, { key: 'forecast_3m', label: t('Forecast 3m', 'توقّع 3 شهور'), n: 1, f: N },
        { key: 'safety_stock', label: t('Safety', 'أمان'), n: 1, f: N }, { key: 'stock_on_hand', label: t('Stock on hand', 'المخزون الحالي'), n: 1, f: N },
        { key: 'to_buy', label: t('To buy', 'نشتري'), n: 1, f: v => `<b>${N(v)}</b>` }, { key: 'current_pattern_buys', label: t('Current pattern', 'النمط الحالي'), n: 1, f: N }])}
      <div style="margin-top:12px;display:flex;gap:8px"><a class="btn small" href="/api/export/purchase_plan.csv">⬇️ CSV</a>
      <button class="btn small ghost" id="approve">✅ ${t('Approve → action tracker', 'اعتمد ← المتابعة')}</button></div></div>`;
    const bt = d.backtest_total;
    Charts.lines($('#bt'), bt.map(r => r.month.slice(0, 7)), [
      { name: t('actual', 'الحقيقي'), color: Charts.C.ink, values: bt.map(r => r.units) },
      { name: t('AI model', 'الموديل'), color: Charts.C.blue, values: bt.map(r => r.model) },
      { name: t('same month last year', 'زي السنة اللي فاتت'), color: Charts.C.grey, values: bt.map(r => r.naive), dash: 1 }], { dots: 1 });
    Charts.hbars($('#cat'), d.plan.slice(0, 10).map(r => ({ label: r.category_en, value: r.to_buy })));
    $('#approve').onclick = async () => { await api('/api/actions', { method: 'POST', body: { title: `Approved purchase plan ${d.months[0]} – ${d.months[d.months.length - 1]}: ${N(tot.b)} pieces (service ${svc}%)`, owner: 'supply', problem: 'P04' } }); toast(t('Added to the action tracker', 'اتضافت للمتابعة')); };
  };
  $('#page').innerHTML = `<div class="card"><div class="controls">
    <div class="field"><label>${t('Service level', 'مستوى الخدمة')}</label><select id="svc">${['90', '95', '98', '99'].map(v => `<option ${v === '95' ? 'selected' : ''}>${v}</option>`).join('')}</select></div>
    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="trust"> ${t('Subtract stock on hand (only after a stock count)', 'نطرح المخزون الحالي (بعد الجرد بس)')}</label></div>
    <div class="note">${t('The stock table is not reliable yet (9.3M pieces not accounted for), so by default we do not subtract it.', 'جدول المخزون لسه مش موثوق (9.3 مليون قطعة مش متحسوبة)، فافتراضيًا مش بنطرحه.')}</div></div><div id="out" style="margin-top:14px"><div class="loading">…</div></div>`;
  $('#svc').onchange = draw; $('#trust').onchange = draw; draw();
}

async function pageAllocation() {
  shell('allocation', t('Branch allocation', 'توزيع البضاعة على الفروع'), t('Send each branch November’s forecast for its categories (its FY2026 share) + safety – instead of a fixed quantity.',
    'نبعت لكل فرع توقّع نوفمبر لفئاته (حسب نصيبه في FY2026) + أمان – بدل كمية ثابتة.'));
  let branch = null;
  const draw = async () => {
    const safety = $('#sf')?.value || 10;
    const d = await api(`/api/tools/allocation?safety=${safety}` + (branch ? `&branch=${branch}` : ''));
    branch = d.branch;
    const s = d.saving, sum = d.rows.reduce((a, r) => ({ n: a.n + r.send_next_month, o: a.o + r.sent_per_month_FY2026 }), { n: 0, o: 0 });
    $('#out').innerHTML = `<div class="grid g4">${kpi(t('Pieces moved / year', 'قطع بتتنقل في السنة'), K(s.need) + ' ← ' + K(s.sent))}${kpi(t('Fewer pieces moved', 'قطع أقل'), (-s.cut_pct).toFixed(0) + '%')}
      ${kpi(t('Fewer transfers / year', 'تحويلات أقل في السنة'), N(s.transfers - s.new_transfers))}${kpi(t('Transport saved / year', 'توفير النقل في السنة'), M(s.saving))}</div>
      <div class="grid g2" style="margin-top:14px"><div class="card"><h2>${t('Socks: 27% of sales, 55% of shipments', 'الشرابات: 27% من البيع و 55% من المبعوت')}</h2><p class="sub">${t('% of pieces sold vs sent, FY2019–FY2026', '% من القطع المتباعة مقابل المبعوتة')}</p><div id="mix"></div></div>
      <div class="card"><h2>${t('Branch', 'الفرع')} <select id="br">${d.branches.map(b => `<option value="${b.branch_id}" ${b.branch_id === branch ? 'selected' : ''}>${b.branch_id} · ${esc(b.branch_name_ar)}</option>`).join('')}</select></h2>
        <p class="sub">${t(`November 2026: ${N(sum.n)} pieces vs ${N(sum.o)} sent per month in FY2026`, `نوفمبر 2026: ${N(sum.n)} قطعة مقابل ${N(sum.o)} في الشهر في FY2026`)}</p>
        ${table(d.rows, [{ key: 'category_en', label: t('Category', 'الفئة') }, { key: 'send_next_month', label: t('Send in Nov', 'نبعت في نوفمبر'), n: 1, f: v => `<b>${N(v)}</b>` },
          { key: 'sent_per_month_FY2026', label: t('Sent / month FY2026', 'المبعوت/شهر FY2026'), n: 1, f: N }])}
        <div style="margin-top:12px"><a class="btn small" href="/api/export/allocation_plan.csv">⬇️ ${t('All branches (CSV)', 'كل الفروع (CSV)')}</a></div></div></div>`;
    const mix = d.mix.slice(0, 8);
    $('#mix').innerHTML = '<div id="m1"></div><div class="legend"><span style="--c:#2a78d6">' + t('sold', 'متباع') + '</span><span style="--c:#eb6834">' + t('sent', 'مبعوت') + '</span></div>';
    Charts.hbars($('#m1'), mix.flatMap(r => [{ label: r.category_en, value: r.sold_pct, text: r.sold_pct.toFixed(0) + '%', color: Charts.C.blue },
      { label: '', value: r.sent_pct, text: r.sent_pct.toFixed(0) + '%', color: Charts.C.orange }]), { row: 18 });
    $('#br').onchange = e => { branch = e.target.value; draw(); };
  };
  $('#page').innerHTML = `<div class="card"><div class="controls">${slider('sf', t('Branch safety stock', 'مخزون أمان الفرع'), 0, 50, 5, 10)}</div></div><div id="out" style="margin-top:14px"><div class="loading">…</div></div>`;
  bindSlider('sf', '%', draw); draw();
}

async function pageDiscount() {
  shell('discount', t('Discount guardrail', 'قواعد الخصم'), t('Discounts are random today (54% of lines, every month) and sell no extra pieces. Check any discount against the rule before it is given.',
    'الخصم النهارده عشوائي (54% من السطور، كل شهر) ومش بيبيع قطع زيادة. راجع أي خصم على القاعدة قبل ما يتدّى.'));
  $('#page').innerHTML = `<div class="grid g2"><div class="card"><h2>${t('Check a discount', 'راجع خصم')}</h2>
      <div class="controls"><div class="field"><label>${t('Product price (EGP)', 'سعر المنتج (جنيه)')}</label><input id="pr" type="number" value="400" min="1"></div></div>
      ${slider('ds', t('Discount asked', 'الخصم المطلوب'), 0, 40, 1, 15)}${slider('mx', t('Rule: max without approval', 'القاعدة: أقصى خصم من غير موافقة'), 0, 30, 1, 10)}${slider('fl', t('Rule: floor margin', 'القاعدة: أقل هامش'), 10, 40, 1, 30)}
      <div id="vd"></div></div>
    <div class="card"><h2>${t('Every discount band cuts margin – none sells more', 'كل شريحة خصم بتقلل الهامش – ومفيش واحدة بتبيع أكتر')}</h2><p class="sub">${t('gross margin % by discount on the line (pieces per line on hover)', 'هامش الربح حسب الخصم على السطر')}</p><div id="bands"></div>
      ${slider('st', t('Stop this share of random discounts', 'نوقف النسبة دي من الخصم العشوائي'), 0, 100, 5, 75)}<div id="gain"></div></div></div>`;
  const draw = async () => {
    const q = `price=${$('#pr').value}&discount=${$('#ds').value}&max_discount=${$('#mx').value}&floor_margin=${$('#fl').value}&stop=${$('#st').value}`;
    const d = await api('/api/tools/discount?' + q);
    const cls = { Approve: 'ok', 'Needs approval': 'warn', Reject: 'no' }[d.verdict];
    $('#vd').innerHTML = `<div class="verdict ${cls}">${t(d.verdict, { Approve: 'موافقة', 'Needs approval': 'محتاج موافقة المدير', Reject: 'مرفوض' }[d.verdict])}</div>
      <p class="sub" style="margin-top:10px">${t(`Net price ${N(d.net_price)} EGP · margin ${d.margin.toFixed(1)}% (cost ≈ ${(d.cost_ratio * 100).toFixed(0)}% of list price for every product)`,
        `السعر بعد الخصم ${N(d.net_price)} جنيه · الهامش ${d.margin.toFixed(1)}% (التكلفة حوالي ${(d.cost_ratio * 100).toFixed(0)}% من السعر لكل المنتجات)`)}</p>`;
    Charts.bars($('#bands'), d.bands.map((r, i) => ({ label: r.band || r.index, value: r.margin_pct, text: r.margin_pct.toFixed(1) + '% · ' + r.avg_pieces.toFixed(2), color: i ? Charts.C.orange : Charts.C.blue })), { fmtY: v => v.toFixed(0) + '%', height: 230 });
    const f = d.facts;
    $('#gain').innerHTML = `<div class="grid g2">${kpi(t('Extra profit / year', 'ربح زيادة في السنة'), M(d.gain))}${kpi(t('Pieces per line with / without', 'قطع في السطر بخصم/من غير'), f.pieces_with.toFixed(2) + ' / ' + f.pieces_without.toFixed(2))}</div>`;
  };
  ['ds', 'mx', 'fl', 'st'].forEach(id => bindSlider(id, '%', draw));
  $('#pr').onchange = draw; draw();
}

async function pageMarketing() {
  shell('marketing', t('Marketing budget & holdout test', 'ميزانية التسويق وتجربة الـ Holdout'), t('Campaigns claim far more orders than exist and the budget ignores demand. Plan the budget by demand and prove what works with a holdout test.',
    'الحملات بتنسب لنفسها طلبات أكتر بكتير من الحقيقي، والميزانية مش ماشية مع الطلب. نخطط الميزانية حسب الطلب ونثبت اللي شغال بتجربة Holdout.'));
  $('#page').innerHTML = `<div class="card"><div class="controls">${slider('ct', t('Cut spend with no measured effect', 'نقلل الصرف اللي ملوش أثر'), 0, 50, 5, 25)}${slider('ho', t('Keep for holdout tests', 'نسيب لتجارب الـ Holdout'), 0, 30, 5, 10)}</div></div><div id="out" style="margin-top:14px"><div class="loading">…</div></div>`;
  const draw = async () => {
    const d = await api(`/api/tools/marketing?cut=${$('#ct').value}&holdout=${$('#ho').value}`);
    $('#out').innerHTML = `<div class="grid g4">${kpi(t('FY2026 spend', 'صرف FY2026'), M(d.spend26))}${kpi(t('New budget', 'الميزانية الجديدة'), M(d.budget))}${kpi(t('Saved / year', 'توفير في السنة'), M(d.saved))}
      ${kpi(t('Claimed ÷ real orders', 'المنسوب ÷ الحقيقي'), '×' + d.claimed_x.toFixed(0))}</div>
      <div class="grid g2" style="margin-top:14px"><div class="card"><h2>${t('Budget that follows demand', 'ميزانية ماشية مع الطلب')}</h2><p class="sub">${t('per governorate, M EGP: today vs plan', 'لكل محافظة، مليون جنيه: النهارده مقابل الخطة')}</p>
        ${table(d.gov.slice(0, 12), [{ key: 'governorate_ar', label: t('Governorate', 'المحافظة') }, { key: 'order_share', label: t('% orders', '% الطلبات'), n: 1, f: v => v.toFixed(1) + '%' },
          { key: 'spend', label: t('Today', 'النهارده'), n: 1, f: v => (v / 1e6).toFixed(2) }, { key: 'new_budget', label: t('Plan', 'الخطة'), n: 1, f: v => `<b>${(v / 1e6).toFixed(2)}</b>` }])}</div>
      <div class="card"><h2>${t('The holdout test (4 weeks)', 'تجربة الـ Holdout (4 أسابيع)')}</h2><p class="sub">${t('In each pair of similar governorates, pause ads in the first one; compare real orders after 4 weeks. The difference = what marketing really brings.',
        'في كل زوج محافظات شبه بعض، نوقف الإعلان في الأولى؛ ونقارن الطلبات الحقيقية بعد 4 أسابيع. الفرق = اللي التسويق بيجيبه فعلًا.')}</p>
        ${table(d.pairs, [{ key: 'a', label: t('Pause ads', 'نوقف الإعلان') }, { key: 'orders_a', label: t('orders', 'طلبات'), n: 1, f: N }, { key: 'b', label: t('Keep ads', 'نكمل الإعلان') }, { key: 'orders_b', label: t('orders', 'طلبات'), n: 1, f: N }])}
        <div class="note">${t(`One ledger first: marketing is ${M(d.ledger)} in the expense ledger vs ${M(d.campaigns)} in the campaign table.`, `دفتر واحد الأول: التسويق ${M(d.ledger)} في دفتر المصاريف مقابل ${M(d.campaigns)} في جدول الحملات.`)}</div></div></div>
      <div class="card" style="margin-top:14px"><h2>${t('All channels cost about the same per click', 'كل القنوات تكلفة الضغطة فيها تقريبًا واحدة')}</h2><p class="sub">${t('cost per click, EGP – the data cannot say which channel works; only a test can', 'تكلفة الضغطة بالجنيه – الداتا متقدرش تقول أنهي قناة شغالة؛ التجربة بس اللي تقدر')}</p><div id="cpc"></div></div>`;
    Charts.bars($('#cpc'), d.channels.map(r => ({ label: r.channel, value: r.cpc, text: r.cpc.toFixed(2) })), { height: 220, fmtY: v => v.toFixed(2) });
  };
  bindSlider('ct', '%', draw); bindSlider('ho', '%', draw); draw();
}

async function pageShipping() {
  shell('shipping', t('Free-shipping rule', 'قاعدة الشحن المجاني'), t('Free shipping goes to 14% of online orders of every size – even 13 EGP orders. Set a minimum order.',
    'الشحن المجاني بيروح لـ 14% من طلبات الأونلاين من كل الأحجام – حتى طلب بـ 13 جنيه. نحط حد أدنى للطلب.'));
  $('#page').innerHTML = `<div class="card"><div class="controls">${slider('th', t('Free shipping only above (EGP)', 'شحن مجاني بس فوق (جنيه)'), 250, 2500, 250, 1000, '')}</div></div><div id="out" style="margin-top:14px"></div>`;
  const draw = async () => {
    const d = await api('/api/tools/shipping?threshold=' + $('#th').value);
    $('#out').innerHTML = `<div class="grid g3">${kpi(t('Free shipments below the threshold / year', 'شحنات مجانية تحت الحد في السنة'), N(d.free_below))}${kpi(t('Fees recovered / year', 'رسوم بترجع في السنة'), N(d.saved) + ' ' + EGP())}${kpi(t('Average fee', 'متوسط الرسوم'), d.avg_fee.toFixed(0) + ' ' + EGP())}</div>
      <div class="card" style="margin-top:14px"><h2>${t('Share shipped free, by order size', 'نسبة الشحن المجاني حسب حجم الطلب')}</h2><div id="fs"></div>
      <div class="insight">${t('Small money, but a clear and fair rule – and it removes a random decision.', 'فلوس صغيرة، بس قاعدة واضحة وعادلة – وبتشيل قرار عشوائي.')}</div></div>`;
    Charts.bars($('#fs'), Object.entries(d.free_by_size).map(([k, v]) => ({ label: k, value: v, text: v.toFixed(0) + '%' })), { height: 230, fmtY: v => v.toFixed(0) + '%' });
  };
  bindSlider('th', '', draw); draw();
}

async function pageActions() {
  shell('actions', t('Action tracker', 'متابعة المهام'), t('Every solution becomes a task with an owner and a date. Saved on the server for all managers.', 'كل حل بيبقى مهمة ليها مسؤول وميعاد. محفوظة على السيرفر لكل المديرين.'));
  const d = await api('/api/actions');
  const cols = [['To do', t('To do', 'هنعمل')], ['In progress', t('In progress', 'شغالين')], ['Done', t('Done', 'خلصت')]];
  const next = { 'To do': 'In progress', 'In progress': 'Done', Done: 'To do' };
  $('#page').innerHTML = `<form class="card controls" id="add" style="margin-bottom:14px">
      <div class="field" style="flex:2;min-width:240px"><label>${t('New task', 'مهمة جديدة')}</label><input name="title" required placeholder="${t('e.g. Count stock in BR012', 'مثلًا: جرد فرع BR012')}"></div>
      <div class="field"><label>${t('Owner', 'المسؤول')}</label><select name="owner">${d.owners.map(o => `<option value="${o.username}">${esc(t(o.name, o.name_ar))}</option>`).join('')}</select></div>
      <div class="field"><label>${t('Due', 'الميعاد')}</label><input name="due" type="date"></div><button class="btn">${t('Add', 'إضافة')}</button></form>
    <div class="kanban">${cols.map(([k, label]) => `<div class="col"><h3>${label}<span>${d.actions.filter(a => a.status === k).length}</span></h3>
      ${d.actions.filter(a => a.status === k).map(a => `<div class="task"><div class="t">${esc(a.title)}</div>
        <div class="m"><span>👤 ${owner(a.owner)}</span>${a.due ? `<span>📅 ${esc(a.due)}</span>` : ''}${a.impact > 0 ? `<span class="impact">+${M(a.impact)}</span>` : ''}${a.problem ? `<span>${esc(a.problem)}</span>` : ''}</div>
        <div class="b"><button data-mv="${a.id}" data-to="${next[k]}">${k === 'Done' ? '↺' : '→'} ${t(next[k], { 'In progress': 'شغالين', Done: 'خلصت', 'To do': 'هنعمل' }[next[k]])}</button><button data-del="${a.id}">🗑</button></div></div>`).join('')}</div>`).join('')}</div>
    <div class="card" style="margin-top:14px"><h2>${t('Activity', 'آخر التحديثات')}</h2><ul class="list">${d.log.map(l => `<li><span class="sub" style="margin:0;min-width:130px">${esc(l.when)}</span><span>${owner(l.who)}: ${esc(l.what)}</span></li>`).join('') || '<li>—</li>'}</ul></div>`;
  $('#add').onsubmit = async e => { e.preventDefault(); const f = new FormData(e.target); await api('/api/actions', { method: 'POST', body: Object.fromEntries(f) }); pageActions(); };
  document.querySelectorAll('[data-mv]').forEach(b => b.onclick = async () => { await api('/api/actions/' + b.dataset.mv, { method: 'PUT', body: { status: b.dataset.to } }); pageActions(); });
  document.querySelectorAll('[data-del]').forEach(b => b.onclick = async () => { await api('/api/actions/' + b.dataset.del, { method: 'DELETE' }); pageActions(); });
}

async function pageGaps() {
  shell('gaps', t('Data gaps & requests', 'ثغرات الداتا والطلبات'), t('HVIA proposed 22 apps. We checked each one against the data: what is ready, what is partial, what is impossible – and what data would unlock it.',
    'HVIA اقترحوا 22 تطبيق. راجعنا كل واحد على الداتا: إيه الجاهز، وإيه الجزئي، وإيه المستحيل – وإيه الداتا اللي تفتحه.'));
  const d = await api('/api/gaps');
  const ready = d.readiness.filter(r => /^Ready/.test(r.status)).length;
  $('#page').innerHTML = `<div class="grid g4">${kpi(t('Ideas fully supported', 'أفكار الداتا بتشيلها'), ready + ' / 22')}${kpi(t('Partial', 'جزئي'), d.readiness.filter(r => r.status === 'Partial').length)}
      ${kpi(t('Data issues logged', 'مشاكل داتا متسجلة'), d.dq.length)}${kpi(t('Requests received', 'طلبات وصلت'), d.requests.filter(r => r.status === 'Received').length + ' / ' + d.requests.length)}</div>
    <div class="card" style="margin-top:14px"><h2>${t('What we need from the company', 'محتاجين إيه من الشركة')}</h2>
      ${table(d.requests, [{ key: 'priority', label: t('Priority', 'الأولوية'), f: v => sevChip(v === 'Low' ? 'Unreliable' : v === 'High' ? 'High' : 'Medium').replace(/>[^<]+</, `>${t(v, { High: 'عالية', Medium: 'متوسطة', Low: 'قليلة' }[v])}<`) },
        { key: 'area', label: t('Area', 'المجال') }, { key: 'request', label: t('Request', 'الطلب'), f: (v, r) => esc(t(v, r.request_ar)) },
        { key: 'status', label: t('Status', 'الحالة'), f: (v, r) => `<select data-r="${r.id}">${['To request', 'Requested', 'Received'].map(s => `<option value="${s}" ${s === v ? 'selected' : ''}>${t(s, { 'To request': 'لسه', Requested: 'اتطلب', Received: 'وصل' }[s])}</option>`).join('')}</select>` }])}</div>
    <div class="card" style="margin-top:14px"><h2>${t('The 22 app ideas – readiness', 'الـ 22 فكرة – الجاهزية')}</h2>
      ${table(d.readiness, [{ key: 'page', label: '#', n: 1 }, { key: 'idea', label: t('Idea', 'الفكرة') }, { key: 'status', label: t('Status', 'الحالة'), f: statusChip },
        { key: 'why', label: t('Why', 'ليه') }, { key: 'unlock_with', label: t('Unlock with', 'يتفتح بـ') }])}</div>
    <div class="card" style="margin-top:14px"><h2>${t('Data quality report', 'تقرير جودة الداتا')}</h2><p class="sub">${t('Business = a finding to act on · High = breaks an analysis · Medium = system gap · Unreliable = random field, nothing built on it',
      'اكتشاف بزنس = لازم نتصرف · عالي = بيبوّظ تحليل · متوسط = فجوة في السيستم · حقل عشوائي = مش بنبني عليه حاجة')}</p>
      ${table(d.dq, [{ key: 'id', label: 'ID' }, { key: 'table', label: t('Table', 'الجدول') }, { key: 'issue', label: t('Issue', 'المشكلة') }, { key: 'evidence', label: t('Evidence', 'الدليل') }, { key: 'severity', label: t('Severity', 'الخطورة'), f: sevChip }])}
      <div style="margin-top:12px"><a class="btn small" href="/api/export/data_quality.csv">⬇️ CSV</a></div></div>`;
  document.querySelectorAll('select[data-r]').forEach(s => s.onchange = async () => { await api('/api/gaps/' + s.dataset.r, { method: 'POST', body: { status: s.value } }); toast(t('Saved', 'اتحفظ')); });
}

async function pageAssistant() {
  shell('assistant', t('Ask the data', 'اسأل الداتا'), t('Answers come only from Cottonil’s numbers, with a link to the page that proves them.', 'الإجابات من أرقام قطنيل بس، ومعاها لينك للصفحة اللي بتثبتها.'));
  const qs = S.lang === 'ar' ? ['نعمل إيه الأول؟', 'المبيعات بتزيد ليه؟', 'الخصم بيبيع أكتر؟', 'المخزون فيه مشكلة؟', 'نشتري كام الربع الجاي؟', 'التسويق شغال؟']
    : ['What should we do first?', 'Why do sales grow?', 'Do discounts sell more?', 'Is there a stock problem?', 'How much should we buy next quarter?', 'Does marketing work?'];
  $('#page').innerHTML = `<div class="card"><div class="chat" id="chat"><div class="bubble bot">${t('Hi! Ask me about sales, profit, discounts, stock, purchasing, marketing, customers, branches, shipping, payroll or the data gaps.',
    'أهلًا! اسألني عن المبيعات، الربح، الخصم، المخزون، الشراء، التسويق، العملاء، الفروع، الشحن، المرتبات أو ثغرات الداتا.')}</div></div>
    <div class="suggest">${qs.map(q => `<button>${esc(q)}</button>`).join('')}</div>
    <form class="ask" id="ask"><input name="q" placeholder="${t('Type a question…', 'اكتب سؤالك…')}" autocomplete="off"><button class="btn">${t('Ask', 'اسأل')}</button></form></div>`;
  const ask = async q => {
    if (!q.trim()) return;
    const chat = $('#chat');
    chat.insertAdjacentHTML('beforeend', `<div class="bubble me">${esc(q)}</div>`);
    const r = await api('/api/assistant', { method: 'POST', body: { q, lang: S.lang } });
    chat.insertAdjacentHTML('beforeend', `<div class="bubble bot">${esc(r.answer)}${r.link ? `<br><a href="#/${r.link}">${t('Open the page', 'افتح الصفحة')} →</a>` : ''}</div>`);
    chat.scrollTop = chat.scrollHeight;
  };
  document.querySelectorAll('.suggest button').forEach(b => b.onclick = () => ask(b.textContent));
  $('#ask').onsubmit = e => { e.preventDefault(); const i = e.target.q; ask(i.value); i.value = ''; };
}

/* ------------------------------------------------------------------ router */
const PAGES = { home: pageHome, problems: pageProblems, purchase: pagePurchase, allocation: pageAllocation, discount: pageDiscount,
  marketing: pageMarketing, shipping: pageShipping, actions: pageActions, gaps: pageGaps, assistant: pageAssistant };
function route() {
  if (!S.me) return renderLogin();
  const id = (location.hash.replace('#/', '') || 'home').split('?')[0];
  (PAGES[id] || pageHome)().catch(e => { if (e.message !== 'login') $('#page').innerHTML = `<div class="note">${esc(e.message)}</div>`; });
}
window.addEventListener('hashchange', route);
(async () => { setDir(); try { S.me = await api('/api/me'); route(); } catch (e) { renderLogin(); } })();
