/* Cottonil · Manager board – shell, helpers, login, router, Today, assistant, report. Pages for the tools are in pages.js. */
const S = { lang: (() => { try { return localStorage.getItem('lang') || 'ar'; } catch (e) { return 'ar'; } })(), me: null, meta: null, today: null, chat: [], cache: {} };
const t = (en, ar) => (S.lang === 'ar' ? ar : en);
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---------------------------------------------------------------- dark mode
function applyDark(on) {
  document.documentElement.classList.toggle('dark', on);
  try { localStorage.setItem('dark', on ? '1' : '0'); } catch(e) {}
}
function isDark() { try { return localStorage.getItem('dark') === '1'; } catch(e) { return false; } }
applyDark(isDark());


// ---------------------------------------------------------------- numbers & names
const nf = (v, d = 0) => (v == null || isNaN(v) ? '–' : Number(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }));
// numbers inside Arabic text keep their own left-to-right order (dates, %, ×, signs)
const NUM_RE = /(?<![A-Za-z\d.,])[+−\-×]?\d[\d,.:\-\/]*%?/g;
const N = (x) => esc(x).replace(NUM_RE, m => `<span class="num">${m}</span>`);
const sign = (v, d = 0) => (v > 0 ? '+' : v < 0 ? '−' : '') + nf(Math.abs(v), d);
const big = (v, d = 1) => {
  const a = Math.abs(v);
  if (a >= 1e9) return S.lang === 'ar' ? `${nf(v / 1e9, 1)} مليار` : `${nf(v / 1e9, 1)}B`;
  if (a >= 1e6) return S.lang === 'ar' ? `${nf(v / 1e6, d)} مليون` : `${nf(v / 1e6, d)}M`;
  if (a >= 1e4) return S.lang === 'ar' ? `${nf(v / 1e3, 0)} ألف` : `${nf(v / 1e3, 0)}K`;
  return nf(v);
};
const egp = v => t(`${big(v)} EGP`, `${big(v)} جنيه`);
const pcs = v => t(`${big(v)} pieces`, `${big(v)} قطعة`);
const cat = c => (S.lang === 'ar' && S.meta ? S.meta.cat_ar[c] || c : c);
const role = r => (S.lang === 'ar' && S.meta ? S.meta.role_ar[r] || r : r);
const MON_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MON_AR = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
const ym = s => { const [y, m] = String(s).slice(0, 7).split('-').map(Number); return { y, m }; };
const mon = s => { const { y, m } = ym(s); return t(`${MON_EN[m - 1]} ${y}`, `${MON_AR[m - 1]} ${y}`); };
const monOnly = s => { const { m } = ym(s); return t(MON_EN[m - 1], MON_AR[m - 1]); };
const monShort = s => { const { y, m } = ym(s); return t(`${MON_EN[m - 1]} ${String(y).slice(2)}`, `${MON_AR[m - 1]} ${String(y).slice(2)}`); };
const dateLong = d => new Date(d).toLocaleDateString(S.lang === 'ar' ? 'ar-EG-u-nu-latn' : 'en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

// ---------------------------------------------------------------- icons (Lucide-style, inline)
const ICONS = {
  dashboard: '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
  cart: '<circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>',
  truck: '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.62l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>',
  tag: '<path d="M12.59 2.59A2 2 0 0 0 11.17 2H4a2 2 0 0 0-2 2v7.17a2 2 0 0 0 .59 1.42l8.7 8.7a2.43 2.43 0 0 0 3.42 0l6.58-6.58a2.43 2.43 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r="1"/>',
  megaphone: '<path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/>',
  store: '<path d="m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"/><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/><path d="M2 7h20"/><path d="M22 7v3a2 2 0 0 1-2 2 2.7 2.7 0 0 1-2-1 2.7 2.7 0 0 1-2 1 2.7 2.7 0 0 1-2-1 2.7 2.7 0 0 1-2 1 2.7 2.7 0 0 1-2-1 2.7 2.7 0 0 1-2 1 2.7 2.7 0 0 1-2-1 2.7 2.7 0 0 1-2 1 2 2 0 0 1-2-2V7"/>',
  spark: '<path d="M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.14-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5l1.58-6.14a.5.5 0 0 1 .96 0l1.58 6.14a2 2 0 0 0 1.44 1.44l6.14 1.58a.5.5 0 0 1 0 .96l-6.14 1.58a2 2 0 0 0-1.44 1.44l-1.58 6.14a.5.5 0 0 1-.96 0z"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
  bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
  calendar: '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
  box: '<path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/><path d="M12 22V12"/><path d="m3.3 7 7.7 4.73a2 2 0 0 0 2 0L20.7 7"/>',
  people: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  arrow: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  back: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>',
  key: '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/>',
  print: '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 9V3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6"/><rect x="6" y="14" width="12" height="8" rx="1"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
  save: '<path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/><path d="M7 3v4a1 1 0 0 0 1 1h7"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  send: '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
  globe: '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
  warehouse: '<path d="M22 8.35V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.35A2 2 0 0 1 3.26 6.5l8-3.2a2 2 0 0 1 1.48 0l8 3.2A2 2 0 0 1 22 8.35Z"/><path d="M6 18h12"/><path d="M6 14h12"/><rect width="12" height="12" x="6" y="10"/>',
  menu: '<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
  target: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
  list: '<path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/>',
};
// add moon/sun icons
ICONS.moon = '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>';
ICONS.sun = '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>';

const I = (name, cls = '') => `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ''}</svg>`;

// ---------------------------------------------------------------- api, toast, modal, csv
async function api(url, opts = {}) {
  const r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin', ...opts });
  if (r.status === 401 && !url.endsWith('/api/login')) { S.me = null; renderLogin(); throw new Error('login'); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}
const post = (url, body) => api(url, { method: 'POST', body: JSON.stringify(body || {}) });

function toast(msg) {
  $$('.toast').forEach(x => x.remove());
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = I('check') + esc(msg);
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2600);
}

function modal(html, onMount) {
  const bg = document.createElement('div');
  bg.className = 'modal-bg';
  bg.innerHTML = `<div class="modal">${html}</div>`;
  const close = () => bg.remove();
  bg.addEventListener('click', e => { if (e.target === bg || e.target.closest('[data-close]')) close(); });
  document.body.appendChild(bg);
  onMount && onMount(bg, close);
  return close;
}

function downloadCSV(rows, cols, name) {
  const head = cols.map(c => c[1]).join(',');
  const body = rows.map(r => cols.map(c => { const v = typeof c[0] === 'function' ? c[0](r) : r[c[0]]; return /[",\n]/.test(String(v ?? '')) ? `"${String(v).replace(/"/g, '""')}"` : (v ?? ''); }).join(',')).join('\n');
  const blob = new Blob(['﻿' + head + '\n' + body], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `cottonil_${name}.csv`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

const R = x => (/[<>]/.test(String(x)) ? x : N(x));     // plain text → numbers isolated; HTML passes through
const kpi = (label, value, sub = '', accent = false, icon = '') =>
  `<div class="card kpi ${accent ? 'accent' : ''}"><div class="l">${icon ? I(icon) : ''}${R(label)}</div><div class="v">${R(value)}</div><div class="s">${R(sub)}</div></div>`;
const head = (title, sub, actions = '') => `<div class="head"><div><h1>${R(title)}</h1>${sub ? `<p>${R(sub)}</p>` : ''}</div><div class="actions no-print">${actions}</div></div>`;
const segHTML = (name, opts, val) => `<div class="seg" data-seg="${name}">${opts.map(([v, l]) => `<button type="button" data-v="${v}" class="${String(v) === String(val) ? 'on' : ''}">${l}</button>`).join('')}</div>`;
function onSeg(root, name, fn) {
  const el = $(`[data-seg="${name}"]`, root);
  el && el.addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; $$('button', el).forEach(x => x.classList.toggle('on', x === b)); fn(b.dataset.v); });
}
const debounce = (fn, ms = 250) => { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; };

// ---------------------------------------------------------------- login & shell
function setLang(l) {
  S.lang = l;
  try { localStorage.setItem('lang', l); } catch (e) { /* private window */ }
  document.documentElement.lang = l;
  document.documentElement.dir = l === 'ar' ? 'rtl' : 'ltr';
  document.title = t('Cottonil · Manager board', 'قطونيل · لوحة المدير');
}

function renderLogin() {
  setLang(S.lang);
  $('#app').innerHTML = `
  <div class="login">
    <div class="login-art">
      <div class="brand"><div class="mark">ق</div><div><b style="color:#fff">${t('Cottonil', 'قطونيل')}</b><span style="color:#C9D4E6">${t('Manager board', 'لوحة المدير')}</span></div></div>
      <div>
        <h1>${t('Run the month from one place.', 'إدارة الشهر من مكان واحد.')}</h1>
        <p>${t('Every number comes from the company data, and every page ends with something you can use: a purchase order, a pick list, a budget.',
              'كل رقم جاي من داتا الشركة، وكل صفحة بتطلع حاجة تشتغل بيها: أمر شراء، قايمة تجهيز للفرع، ميزانية.')}</p>
        <ul>
          <li>${I('cart')} ${t('Buy for demand, from a tested forecast', 'شراء على قد الطلب، من توقّع متجرّب')}</li>
          <li>${I('truck')} ${t('Each branch gets what it sells, from the nearest warehouse', 'كل فرع ياخد اللي بيبيعه، من أقرب مخزن')}</li>
          <li>${I('tag')} ${t('Discounts with a policy, promotions as tests', 'خصم بسياسة، وعروض كتجربة')}</li>
          <li>${I('store')} ${t('A profile for each of the 80 branches', 'ملف لكل فرع من الـ 80')}</li>
        </ul>
      </div>
      <svg class="threads" viewBox="0 0 200 200" fill="none" stroke="#fff" stroke-width="2"><circle cx="100" cy="100" r="90"/><circle cx="100" cy="100" r="70"/><circle cx="100" cy="100" r="50"/><circle cx="100" cy="100" r="30"/><path d="M10 100h180M100 10v180"/></svg>
    </div>
    <div class="login-form">
      <form id="lf" autocomplete="on">
        <div><h2>${t('Sign in', 'تسجيل الدخول')}</h2><p class="muted small">${t('One account for the manager.', 'حساب واحد للمدير.')}</p></div>
        <div class="field"><label>${t('Username', 'اسم المستخدم')}</label><input type="text" name="username" value="manager" autocomplete="username" required></div>
        <div class="field"><label>${t('Password', 'كلمة السر')}</label><input type="password" name="password" autocomplete="current-password" required autofocus></div>
        <div class="err" id="lerr"></div>
        <button class="btn primary" type="submit">${t('Sign in', 'دخول')}</button>
        <button class="btn ghost" type="button" id="llang">${I('globe')} ${t('العربية', 'English')}</button>
      </form>
    </div>
  </div>`;
  $('#llang').onclick = () => { setLang(S.lang === 'ar' ? 'en' : 'ar'); renderLogin(); };
  $('#lf').onsubmit = async e => {
    e.preventDefault();
    const f = new FormData(e.target);
    try {
      S.me = await post('/api/login', { username: f.get('username'), password: f.get('password') });
      await startApp();
    } catch (err) { $('#lerr').textContent = t('Wrong username or password', 'اسم المستخدم أو كلمة السر غلط'); }
  };
}

const NAV = [
  ['today', 'dashboard', 'Today', 'النهارده'],
  ['_', '', 'Plans', 'الخطط'],
  ['purchase', 'cart', 'Purchase plan', 'خطة الشراء'],
  ['distribution', 'truck', 'Distribution', 'خطة التوزيع'],
  ['pricing', 'tag', 'Pricing & discounts', 'التسعير والخصم'],
  ['marketing', 'megaphone', 'Marketing budget', 'ميزانية التسويق'],
  ['_', '', 'Follow-up', 'المتابعة'],
  ['branches', 'store', 'Branches', 'الفروع'],
  ['report', 'file', 'Monthly report', 'تقرير الشهر'],
  ['assistant', 'spark', 'Khayt · assistant', 'خيط · المساعد'],
];

function renderShell() {
  setLang(S.lang);
  $('#app').innerHTML = `
  <div class="shell">
    <aside class="side" id="side">
      <div class="brand"><div class="mark">ق</div><div><b>${t('Cottonil', 'قطونيل')}</b><span>${t('Manager board', 'لوحة المدير')}</span></div></div>
      <nav class="nav">${NAV.map(([id, ic, en, ar]) => id === '_' ? `<div class="nav-label">${t(en, ar)}</div>` : `<a href="#/${id}" data-nav="${id}">${I(ic)}<span>${t(en, ar)}</span></a>`).join('')}</nav>
      <div class="side-foot">
        <button id="bdark">${isDark() ? I('sun') + ' ' + t('Light mode','الوضع الفاتح') : I('moon') + ' ' + t('Dark mode','الوضع الداكن')}</button>
        <button id="blang">${I('globe')} ${t('العربية', 'English')}</button>
        <button id="bpass">${I('key')} ${t('Change password', 'تغيير كلمة السر')}</button>
        <button id="bout">${I('logout')} ${t('Sign out', 'خروج')}</button>
      </div>
    </aside>
    <div class="main">
      <header class="top no-print"><div class="top-in">
        <button class="icon-btn menu-btn" id="bmenu">${I('menu')}</button>
        <label class="ask">${I('spark')}<input id="ask" placeholder="${esc(t('Ask Khayt: “Zamalek branch”, “socks”, “December”…', 'اسأل خيط: "فرع الزمالك"، "الشرابات"، "ديسمبر"…'))}"></label>
        <div class="spacer"></div>
        <a class="chip navy" id="cyc" href="#/today">${I('calendar')}<span>…</span></a>
        <div style="position:relative"><button class="icon-btn" id="bbell">${I('bell')}<span class="dot hidden" id="bdot"></span></button><div class="drop hidden" id="drop"></div></div>
        <span class="chip">${I('people')} ${t('Manager', 'المدير')}</span>
      </div></header>
      <main id="view"></main>
    </div>
  </div>`;
  $('#blang').onclick = () => { setLang(S.lang === 'ar' ? 'en' : 'ar'); renderShell(); route(); refreshToday(); };
  $('#bdark').onclick = () => { applyDark(!isDark()); renderShell(); route(); refreshToday(); };
  $('#bout').onclick = async () => { await post('/api/logout'); S.me = null; renderLogin(); };
  $('#bpass').onclick = () => passwordModal(false);
  $('#bmenu').onclick = () => $('#side').classList.toggle('open');
  $('#ask').addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.value.trim()) { location.hash = '#/assistant?q=' + encodeURIComponent(e.target.value.trim()); e.target.value = ''; } });
  $('#bbell').onclick = e => { e.stopPropagation(); $('#drop').classList.toggle('hidden'); };
  document.addEventListener('click', e => { if (!e.target.closest('#drop')) $('#drop') && $('#drop').classList.add('hidden'); });
}

function passwordModal(forced) {
  modal(`<h2>${forced ? t('Choose your own password', 'اختار كلمة سر خاصة بيك') : t('Change password', 'تغيير كلمة السر')}</h2>
    <p class="muted small">${forced ? t('This is the first sign-in with the default password.', 'ده أول دخول بكلمة السر الافتراضية.') : ''}</p>
    <form id="pf" class="grid" style="gap:12px">
      <div class="field"><label>${t('Current password', 'كلمة السر الحالية')}</label><input type="password" name="old" required></div>
      <div class="field"><label>${t('New password (8+ characters)', 'كلمة السر الجديدة (8 حروف أو أكتر)')}</label><input type="password" name="new" minlength="8" required></div>
      <div class="err" id="perr"></div>
      <div class="modal-actions">${forced ? '' : `<button type="button" class="btn" data-close>${t('Cancel', 'إلغاء')}</button>`}<button class="btn primary">${t('Save', 'حفظ')}</button></div>
    </form>`, (root, close) => {
    $('#pf', root).onsubmit = async e => {
      e.preventDefault();
      const f = new FormData(e.target);
      try { await post('/api/password', { old: f.get('old'), new: f.get('new') }); close(); toast(t('Password changed', 'اتغيرت كلمة السر')); }
      catch (err) { $('#perr', root).textContent = err.message; }
    };
  });
}

async function refreshToday() {
  try { S.today = await api('/api/today'); } catch (e) { return; }
  const c = S.today.cycle;
  const el = $('#cyc');
  if (el) $('span', el).innerHTML = `${t('Cycle', 'دورة')} ${monOnly(c.month)} · ${N(`${c.done}/${c.items.length}`)}`;
  const dot = $('#bdot');
  if (dot) { dot.textContent = S.today.alerts.length; dot.classList.toggle('hidden', !S.today.alerts.length); }
  const drop = $('#drop');
  if (drop) drop.innerHTML = `<div style="padding:6px 8px 8px" class="small muted">${t('Alerts from the numbers', 'تنبيهات من الأرقام')}</div>` + alertsHTML(S.today.alerts);
}

const alertsHTML = list => list.map(a => `<a class="alert ${a.level}" href="${a.link}"><div class="ic">${I(a.icon)}</div><div><b>${N(t(a.en, a.ar))}</b><span>${N(t(a.sub_en, a.sub_ar))}</span></div><div class="go">${I('arrow')}</div></a>`).join('');

async function startApp() {
  S.meta = await api('/api/meta');
  renderShell();
  if (!location.hash || location.hash === '#/' || location.hash === '#') location.hash = '#/today';
  await route();
  refreshToday();
  if (S.me.must_change) passwordModal(true);
}

async function boot() {
  setLang(S.lang);
  try { S.me = await api('/api/me'); await startApp(); } catch (e) { if (!S.me) renderLogin(); }
  window.addEventListener('hashchange', () => { if (S.me) route(); });
}

// ---------------------------------------------------------------- router
const ROUTES = [];
const page = (re, fn, nav) => ROUTES.push([re, fn, nav]);
async function route() {
  const [path, qs] = location.hash.split('?');
  const q = new URLSearchParams(qs || '');
  const r = ROUTES.find(([re]) => re.test(path)) || ROUTES[0];
  const m = path.match(r[0]) || [];
  $$('[data-nav]').forEach(a => a.classList.toggle('on', a.dataset.nav === r[2]));
  $('#side') && $('#side').classList.remove('open');
  const view = $('#view');
  view.innerHTML = `<div class="page"><div class="loading">${t('Loading…', 'بيحمّل…')}</div></div>`;
  window.scrollTo(0, 0);
  try { await r[1](view, q, ...m.slice(1)); }
  catch (e) { if (e.message !== 'login') view.innerHTML = `<div class="page"><div class="card">${esc(e.message)}</div></div>`; }
}

// ---------------------------------------------------------------- Today
page(/^#\/today$/, async (view) => {
  const d = await api('/api/today');
  S.today = d;
  const k = d.kpis, c = d.cycle;
  const h = new Date().getHours();
  const hello = h < 12 ? t('Good morning', 'صباح الخير') : t('Good evening', 'مساء الخير');
  view.innerHTML = `<div class="page">
    <div class="head hello"><div><h1>${hello}</h1><p>${dateLong(d.today)} · ${t('data complete to', 'الداتا كاملة لحد')} ${mon(S.meta.data_to)}</p></div>
      <div class="actions"><a class="btn" href="#/report">${I('file')} ${t('Monthly report', 'تقرير الشهر')}</a></div></div>
    <div class="grid g4">
      ${kpi(t(`Expected demand · ${monOnly(c.month)}`, `الطلب المتوقع · ${monOnly(c.month)}`), N(nf(k.next_month_demand)), t(`pieces · ${big(k.quarter_demand)} for the quarter`, `قطعة · ${big(k.quarter_demand)} للربع`), true, 'target')}
      ${kpi(t('Net sales FY2026', 'صافي المبيعات FY2026'), N(big(k.net_sales)), `<span class="up">${N(sign(k.net_sales_g) + '%')}</span> ${t('vs FY2025', 'عن FY2025')}`)}
      ${kpi(t('Real growth (pieces)', 'النمو الحقيقي (قطع)'), N(sign(k.units_g, 1) + '%'), t(`the rest is price: ${sign(k.price_g)}% per piece`, `والباقي سعر: ${sign(k.price_g)}% في القطعة`))}
      ${kpi(t('Gross margin', 'هامش الربح الإجمالي'), N(nf(k.margin, 1) + '%'), t('FY2026', 'FY2026'))}
    </div>
    <div class="grid g-7-5 mt">
      <div class="card">
        <div class="cycle-top">${Charts.ring(c.done / c.items.length)}<div><h3>${t(`${mon(c.month)} cycle`, `دورة ${mon(c.month)}`)}</h3>
          <p class="sub" style="margin:0">${t(`${c.done} of ${c.items.length} done · each item opens the page that does it`, `${c.done} من ${c.items.length} اتعملوا · كل بند بيفتح الصفحة اللي بتعمله`)}</p></div></div>
        <div id="tasks">${c.items.map(i => `
          <div class="task ${i.done ? 'done' : ''}">
            ${i.auto ? `<span class="st ${i.done ? 'done' : ''}">${i.done ? I('check') : ''}</span>` : `<button class="st ${i.done ? 'done' : ''}" data-check="${i.id}" data-done="${i.done ? 1 : 0}" title="${t('Click to toggle check', 'اضغط لتبديل حالة الإنجاز')}">${i.done ? I('check') : ''}</button>`}
            <div class="tx"><b>${N(t(i.en, i.ar))}</b><span>${i.when ? t('saved ', 'اتحفظت ') + N(i.when) : N(t(i.hint_en, i.hint_ar))}</span></div>
            <div style="display:flex; gap:6px; align-items:center;">
              ${!i.auto ? `<button class="btn sm ${i.done ? 'teal' : ''}" data-check="${i.id}" data-done="${i.done ? 1 : 0}">${i.done ? I('check') + ' ' + t('Done', 'تمت') : I('check') + ' ' + t('Mark done', 'علّم كمكتمل')}</button>` : ''}
              <a class="btn sm ${i.done ? '' : 'primary'}" href="${i.link}">${i.done ? t('View', 'عرض') : t('Open', 'افتح')}</a>
            </div>
          </div>`).join('')}</div>
      </div>
      <div class="card"><h3>${t('Alerts from the numbers', 'تنبيهات من الأرقام')}</h3><p class="sub">${t('They change when the data changes.', 'بتتغير لما الداتا تتغير.')}</p>${alertsHTML(d.alerts)}</div>
    </div>
    <div class="card mt"><div class="card-head"><div><h3>${t('Monthly demand – last two years and the next four months', 'الطلب الشهري – آخر سنتين والـ 4 شهور الجاية')}</h3>
      <p class="sub">${t('pieces sold, all channels · forecast = the AI model tested on 6 hidden months', 'القطع المتباعة في كل القنوات · التوقّع = موديل الـ AI اللي اتختبر على 6 شهور مخفية')}</p></div></div><div id="cdem"></div></div>
    <div class="grid g-7-5 mt">
      <div class="card"><div class="card-head"><div><h3>${t('Branches to visit for the stock count', 'فروع للجرد')}</h3><p class="sub">${t('largest gap between what was sent and what was sold or is on the shelf', 'أكبر فرق بين اللي اتبعت واللي اتباع أو على الرف')}</p></div>
        <a class="btn sm ghost" href="#/branches?sort=gap">${t('All branches', 'كل الفروع')}</a></div>
        <div class="tbl-wrap"><table class="tbl"><thead><tr><th>${t('Branch', 'الفرع')}</th><th>${t('Governorate', 'المحافظة')}</th><th class="n">${t('Pieces not accounted for', 'قطع مش متحسوبة')}</th><th class="n">${t('Stock cover', 'المخزون يكفي')}</th></tr></thead>
        <tbody>${d.watch.map(b => `<tr class="click" data-go="#/branches/${b.branch_id}"><td><b>${esc(b.branch_name_ar)}</b> <span class="muted small">${b.branch_id}</span></td><td>${esc(b.governorate_ar)}</td><td class="n">${nf(b.stock_gap)}</td><td class="n">${nf(b.months_cover, 1)} ${t('mo', 'شهر')}</td></tr>`).join('')}</tbody></table></div>
      </div>
      <div class="card"><h3>${t('Latest saved work', 'آخر حاجات اتحفظت')}</h3><p class="sub">${t('plans, policy and tests saved on this board', 'الخطط والسياسة والتجارب اللي اتحفظت هنا')}</p>
        ${d.log.length ? `<ul class="log">${d.log.map(l => `<li><span class="num">${esc(l.when)}</span><span>${N(S.lang === 'ar' && l.what_ar ? l.what_ar : l.what)}</span></li>`).join('')}</ul>` : `<p class="muted">${t('Nothing saved yet – start with the purchase plan.', 'لسه مفيش حاجة اتحفظت – ابدأ بخطة الشراء.')}</p>`}
      </div>
    </div></div>`;
  const hist = Object.entries(d.demand.hist), fc = Object.entries(d.demand.forecast);
  const labels = [...hist.map(x => x[0]), ...fc.map(x => x[0])].map(monShort);
  const actual = [...hist.map(x => x[1]), ...fc.map(() => null)];
  const fcs = [...hist.map((x, i) => (i === hist.length - 1 ? x[1] : null)), ...fc.map(x => x[1])];
  Charts.lines($('#cdem'), labels, [{ name: t('actual', 'الحقيقي'), color: Charts.C.navy, values: actual }, { name: t('forecast', 'التوقّع'), color: Charts.C.teal, values: fcs, dash: true, dots: true }],
    { height: 260, shadeFrom: hist.length, shadeLabel: t('forecast', 'التوقّع') });
  $$('[data-check]', view).forEach(b => b.onclick = async () => { await post('/api/checks', { item: b.dataset.check, done: b.dataset.done !== '1' }); route(); refreshToday(); });
  $$('[data-go]', view).forEach(r => r.onclick = () => { location.hash = r.dataset.go; });
}, 'today');

// ---------------------------------------------------------------- Assistant «خيط»
const SUGG = [['What should we do this month?', 'نعمل إيه الشهر ده؟'], ['Zamalek branch', 'فرع الزمالك'], ['Socks', 'الشرابات'], ['December', 'ديسمبر'],
  ['Cairo', 'القاهرة'], ['Stock', 'المخزون'], ['Discounts', 'الخصم'], ['Marketing budget', 'ميزانية التسويق']];
page(/^#\/assistant$/, async (view, q) => {
  view.innerHTML = `<div class="page" style="max-width:900px">
    <div class="card chat">
      <div class="chat-head"><div class="bot">${I('spark')}</div><div><h3>${t('Khayt', 'خيط')}</h3><p class="sub" style="margin:0">${t('Answers from Cottonil’s numbers and opens the right page.', 'بيجاوب من أرقام قطونيل ويفتحلك الصفحة الصح.')}</p></div></div>
      <div class="msgs" id="msgs"></div>
      <div class="sugg">${SUGG.map(s => `<button data-q="${esc(t(s[0], s[1]))}">${esc(t(s[0], s[1]))}</button>`).join('')}</div>
      <form class="chat-in" id="cf"><input class="input" id="cq" placeholder="${t('Ask about a branch, a category, a governorate, a month…', 'اسأل عن فرع، فئة، محافظة، شهر…')}" autocomplete="off"><button class="btn primary">${I('send', 'flip')}</button></form>
    </div></div>`;
  const draw = () => {
    const el = $('#msgs');
    el.innerHTML = (S.chat.length ? S.chat : [{ me: false, answer: t('Hi, I am Khayt. Ask me about any branch, category, governorate or month – I answer from the data and open the page that acts on it.',
      'أهلاً، أنا خيط. اسألني عن أي فرع أو فئة أو محافظة أو شهر – بجاوب من الداتا وبفتحلك الصفحة اللي تتصرف منها.'), facts: [], links: [] }])
      .map(m => m.me ? `<div class="msg me">${esc(m.q)}</div>` : `<div class="msg"><div>${N(m.answer)}</div>
        ${m.facts && m.facts.length ? `<div class="facts">${m.facts.map(f => `<div><span>${esc(f[0])}</span><b class="num">${esc(f[1])}</b></div>`).join('')}</div>` : ''}
        ${m.links && m.links.length ? `<div class="links">${m.links.map(l => `<a class="btn sm" href="${l.href}">${esc(t(l.en, l.ar))} ${I('arrow', 'flip')}</a>`).join('')}</div>` : ''}</div>`).join('');
    el.scrollTop = el.scrollHeight;
  };
  const ask = async (text) => {
    if (!text) return;
    S.chat.push({ me: true, q: text });
    draw();
    const a = await post('/api/assistant', { q: text, lang: S.lang });
    S.chat.push(a);
    draw();
  };
  $('#cf').onsubmit = e => { e.preventDefault(); const v = $('#cq').value.trim(); $('#cq').value = ''; ask(v); };
  $$('[data-q]', view).forEach(b => b.onclick = () => ask(b.dataset.q));
  draw();
  if (q.get('q')) { const v = q.get('q'); history.replaceState(null, '', '#/assistant'); ask(v); }
}, 'assistant');

// ---------------------------------------------------------------- Monthly report
page(/^#\/report$/, async (view) => {
  const d = await api('/api/report');
  const fy = d.fy[d.fy.length - 1], c = d.cycle, p = d.purchase, dist = d.distribution, mk = d.marketing;
  const fq = Object.entries(d.forecast_quarter);
  const actions = d.bridge.actions;
  view.innerHTML = `<div class="page" style="max-width:980px">
    ${head(t(`Monthly report · ${mon(d.month)}`, `تقرير الشهر · ${mon(d.month)}`), t(`Cottonil · manager board · generated ${d.generated}`, `قطونيل · لوحة المدير · اتعمل ${d.generated}`),
      `<button class="btn" id="rsent">${I('check')} ${t('Mark as sent', 'علّم إنه اتبعت')}</button><button class="btn primary" onclick="window.print()">${I('print')} ${t('Print / PDF', 'طباعة / PDF')}</button>`)}
    <div class="grid g4">
      ${kpi(t('Net sales FY2026', 'صافي المبيعات FY2026'), N(big(fy.net_sales)), N(sign(fy.net_sales_g) + '%'))}
      ${kpi(t('Real growth (pieces)', 'النمو الحقيقي'), N(sign(fy.units_g, 1) + '%'), t('pieces sold', 'القطع المتباعة'))}
      ${kpi(t('Gross margin', 'الهامش'), N(nf(fy.margin_pct, 1) + '%'), '')}
      ${kpi(t('Demand next 3 months', 'طلب الـ 3 شهور الجاية'), N(big(fq.reduce((a, x) => a + x[1], 0))), t('pieces', 'قطعة'))}
    </div>
    <div class="card mt"><h3>${t('This month’s cycle', 'دورة الشهر')} · ${N(`${c.done}/${c.items.length}`)}</h3>
      ${c.items.map(i => `<div class="task ${i.done ? 'done' : ''}"><span class="st ${i.done ? 'done' : ''}">${i.done ? I('check') : ''}</span><div class="tx"><b>${esc(t(i.en, i.ar))}</b><span>${i.when ? N(i.when) : i.done ? t('done', 'اتعمل') : t('not yet', 'لسه')}</span></div></div>`).join('')}</div>
    <div class="grid g2 mt">
      <div class="card"><h3>${t('Purchase plan', 'خطة الشراء')}</h3>
        ${p ? `<p class="sub">${t('saved', 'اتحفظت')} ${N(p.saved)} · ${t('service level', 'مستوى الخدمة')} ${N(p.service + '%')}</p>
          <div class="tbl-wrap"><table class="tbl"><thead><tr><th>${t('Category', 'الفئة')}</th><th class="n">${t('Forecast', 'التوقّع')}</th><th class="n">${t('To buy', 'نشتري')}</th></tr></thead>
          <tbody>${p.rows.slice(0, 8).map(r => `<tr><td>${esc(cat(r.category_en))}</td><td class="n">${nf(r.forecast)}</td><td class="n">${nf(r.to_buy)}</td></tr>`).join('')}</tbody>
          <tfoot><tr><td>${t('Total (all 16)', 'الإجمالي (الـ 16 فئة)')}</td><td class="n">${nf(p.rows.reduce((a, r) => a + r.forecast, 0))}</td><td class="n">${nf(p.total)}</td></tr></tfoot></table></div>`
          : `<p class="muted">${t('Not saved yet.', 'لسه ما اتحفظتش.')}</p>`}</div>
      <div class="card"><h3>${t('Distribution', 'التوزيع')} · ${mon(d.month)}</h3>
        ${dist ? `<div class="facts"><div><span>${t('Pieces to send', 'قطع هتتبعت')}</span><b class="num">${nf(dist.total)}</b></div><div><span>${t('Usual month', 'الشهر المعتاد')}</span><b class="num">${nf(dist.old)}</b></div>
          <div><span>${t('Trips', 'نقلات')}</span><b class="num">${nf(dist.trips)}</b></div><div><span>${t('Transport saved', 'توفير النقل')}</span><b class="num">${big(dist.transport_saved)}</b></div></div>`
          : `<p class="muted">${t('Not saved yet.', 'لسه ما اتحفظتش.')}</p>`}
        <h3 class="mt">${t('Pricing', 'التسعير')}</h3>
        <p class="sub">${t('Policy', 'السياسة')}: ${t('max discount', 'أقصى خصم')} ${N(nf(d.policy.max_discount) + '%')} · ${t('floor margin', 'أقل هامش')} ${N(nf(d.policy.floor_margin) + '%')}${d.policy.saved ? '' : ' · ' + t('default, not saved', 'افتراضية، ما اتحفظتش')}</p>
        ${d.promos.length ? d.promos.map(x => `<div class="small">• ${esc(cat(x.category))} −${N(nf(x.discount) + '%')} · ${t(x.weeks + ' weeks', weeksAr(x.weeks))} · ${t('needs', 'محتاج')} ${N(sign(x.uplift_needed_pct) + '%')} ${t('sales to pay back', 'بيع زيادة عشان يغطي نفسه')}</div>`).join('') : `<p class="muted small">${t('No promotion test saved.', 'مفيش تجربة عرض متسجلة.')}</p>`}
      </div>
    </div>
    <div class="grid g2 mt">
      <div class="card"><h3>${t('Marketing', 'التسويق')}</h3>
        ${mk ? `<p class="sub">${t('Monthly budget', 'ميزانية الشهر')} ${N(egp(mk.budget))} · ${t('paused in the test', 'متوقف في التجربة')} ${N(egp(mk.paused_budget))}</p>
          ${mk.pairs.map(x => `<div class="small">• ${t('pause', 'نوقف')} ${esc(x.pause)} ↔ ${t('keep', 'نكمّل')} ${esc(x.keep)}</div>`).join('')}` : `<p class="muted">${t('Not saved yet.', 'لسه ما اتحفظتش.')}</p>`}</div>
      <div class="card"><h3>${t('Where the extra profit comes from (a year)', 'الربح الزيادة جاي منين (في السنة)')}</h3>
        <p class="sub">${t('from', 'من')} ${N(big(d.bridge.base))} ${t('to', 'لـ')} ${N(big(d.bridge.new))} ${t('EGP gross profit', 'جنيه إجمالي ربح')}</p>
        ${actions.map(a => `<div class="task"><div class="tx"><b>${esc(t(a.action, a.action_ar))}</b></div><span>${N('+' + big(a.profit))}</span></div>`).join('')}</div>
    </div>
    <div class="card mt"><h3>${t('Alerts', 'التنبيهات')}</h3>${d.alerts.map(a => `<div class="task"><div class="tx"><b>${N(t(a.en, a.ar))}</b><span style="white-space:normal">${N(t(a.sub_en, a.sub_ar))}</span></div></div>`).join('')}</div>
    ${Object.keys(d.notes).length ? `<div class="card mt"><h3>${t('Branch notes', 'ملاحظات الفروع')}</h3>${Object.entries(d.notes).map(([b, n]) => `<div class="task"><div class="tx"><b>${b}</b><span style="white-space:normal">${esc(n)}</span></div></div>`).join('')}</div>` : ''}
  </div>`;
  $('#rsent').onclick = async () => { await post('/api/checks', { item: 'report', done: true }); toast(t('Marked as sent', 'اتعلّم إنه اتبعت')); refreshToday(); };
}, 'report');
