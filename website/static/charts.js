/* Tiny SVG charts (no library needed, works offline). Rules: title = the insight, one highlight colour, light grid. */
const Charts = (() => {
  const C = { blue: '#2a78d6', orange: '#eb6834', aqua: '#1baf7a', grey: '#b5b4ae', light: '#b9d3f2', ink: '#52514e', grid: '#ecebe7', red: '#d03b3b' };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const nice = (max) => { if (max <= 0) return 1; const p = Math.pow(10, Math.floor(Math.log10(max))); const n = max / p; const st = [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10].find(s => n <= s); return st * p; };
  const fmt = v => Math.abs(v) >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : Math.abs(v) >= 1e3 ? (v / 1e3).toFixed(0) + 'K' : (Math.round(v * 10) / 10).toString();

  function frame(w, h, pad, maxY, minY = 0, fmtY = fmt) {
    const top = nice(maxY), bottom = minY < 0 ? -nice(-minY) : 0, ticks = 4;
    const y = v => pad.t + (h - pad.t - pad.b) * (1 - (v - bottom) / (top - bottom));
    let g = '';
    for (let i = 0; i <= ticks; i++) {
      const v = bottom + (top - bottom) * i / ticks;
      g += `<line x1="${pad.l}" x2="${w - pad.r}" y1="${y(v)}" y2="${y(v)}" stroke="${C.grid}"/>` +
           `<text x="${pad.l - 6}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="${C.ink}">${esc(fmtY(v))}</text>`;
    }
    return { y, g };
  }

  // bars: [{label, value, color?, text?}]
  function bars(el, data, o = {}) {
    const w = o.width || el.clientWidth || 600, h = o.height || 260, pad = { t: 18, r: 12, b: o.rotate ? 70 : 34, l: 52 };
    const maxV = Math.max(...data.map(d => d.value), 0), minV = Math.min(...data.map(d => d.value), 0);
    const { y, g } = frame(w, h, pad, maxV * 1.12, minV * 1.12, o.fmtY || fmt);
    const bw = (w - pad.l - pad.r) / data.length;
    let s = g;
    data.forEach((d, i) => {
      const x = pad.l + i * bw + bw * 0.15, top = y(Math.max(d.value, 0)), bot = y(Math.min(d.value, 0));
      s += `<rect x="${x}" y="${top}" width="${bw * 0.7}" height="${Math.max(bot - top, 1)}" rx="3" fill="${d.color || o.color || C.blue}"><title>${esc(d.label)}: ${esc(d.text || fmt(d.value))}</title></rect>`;
      if (o.labels !== false) s += `<text x="${x + bw * 0.35}" y="${top - 5}" text-anchor="middle" font-size="11" fill="${C.ink}">${esc(d.text || fmt(d.value))}</text>`;
      const lx = x + bw * 0.35, ly = h - pad.b + 16;
      s += o.rotate ? `<text transform="translate(${lx},${ly - 6}) rotate(-35)" text-anchor="end" font-size="11" fill="${C.ink}">${esc(d.label)}</text>`
                    : `<text x="${lx}" y="${ly}" text-anchor="middle" font-size="11" fill="${C.ink}">${esc(d.label)}</text>`;
    });
    el.innerHTML = `<svg class="chart" style="direction:ltr" viewBox="0 0 ${w} ${h}" role="img">${s}</svg>`;
  }

  // horizontal bars: [{label, value, color?, text?}]
  function hbars(el, data, o = {}) {
    const w = o.width || el.clientWidth || 600, row = o.row || 24, pad = { t: 6, r: 60, b: 6, l: o.labelWidth || 130 };
    const h = pad.t + pad.b + row * data.length, maxV = nice(Math.max(...data.map(d => d.value)) * 1.05);
    let s = '';
    data.forEach((d, i) => {
      const y = pad.t + i * row, bw = (w - pad.l - pad.r) * Math.max(d.value, 0) / maxV;
      s += `<text x="${pad.l - 8}" y="${y + row * 0.65}" text-anchor="end" font-size="12" fill="${C.ink}">${esc(d.label)}</text>` +
           `<rect x="${pad.l}" y="${y + 4}" width="${Math.max(bw, 1)}" height="${row - 8}" rx="3" fill="${d.color || o.color || C.blue}"></rect>` +
           `<text x="${pad.l + bw + 6}" y="${y + row * 0.65}" font-size="11.5" fill="${C.ink}">${esc(d.text || fmt(d.value))}</text>`;
    });
    el.innerHTML = `<svg class="chart" style="direction:ltr" viewBox="0 0 ${w} ${h}" role="img">${s}</svg>`;
  }

  // lines: series [{name, color, values:[...]}], labels [...]
  function lines(el, labels, series, o = {}) {
    const w = o.width || el.clientWidth || 600, h = o.height || 260, pad = { t: 16, r: 16, b: 30, l: 52 };
    const all = series.flatMap(s => s.values.filter(v => v != null));
    const { y, g } = frame(w, h, pad, Math.max(...all) * 1.08, Math.min(0, ...all), o.fmtY || fmt);
    const x = i => pad.l + (w - pad.l - pad.r) * (labels.length === 1 ? 0.5 : i / (labels.length - 1));
    let s = g;
    const step = Math.ceil(labels.length / (o.ticks || 8));
    labels.forEach((l, i) => { if (i % step === 0 && (labels.length - 1 - i >= step / 2 || i === labels.length - 1)) s += `<text x="${x(i)}" y="${h - 8}" text-anchor="${i === labels.length - 1 ? 'end' : i === 0 ? 'start' : 'middle'}" font-size="11" fill="${C.ink}">${esc(l)}</text>`; });
    series.forEach(se => {
      const pts = se.values.map((v, i) => v == null ? null : `${x(i)},${y(v)}`).filter(Boolean).join(' ');
      s += `<polyline points="${pts}" fill="none" stroke="${se.color}" stroke-width="${se.width || 2.4}" ${se.dash ? 'stroke-dasharray="5 4"' : ''} stroke-linejoin="round"/>`;
      if (o.dots) se.values.forEach((v, i) => { if (v != null) s += `<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${se.color}"><title>${esc(labels[i])}: ${fmt(v)}</title></circle>`; });
    });
    el.innerHTML = `<svg class="chart" style="direction:ltr" viewBox="0 0 ${w} ${h}" role="img">${s}</svg>` +
      (series.length > 1 ? `<div class="legend">${series.map(s => `<span style="--c:${s.color}">${esc(s.name)}</span>`).join('')}</div>` : '');
  }

  // waterfall: base, steps [{label, value}], total label
  function waterfall(el, baseLabel, base, steps, totalLabel, o = {}) {
    const w = o.width || el.clientWidth || 700, h = o.height || 320, pad = { t: 22, r: 12, b: 64, l: 52 };
    const total = base + steps.reduce((a, b) => a + b.value, 0);
    const { y, g } = frame(w, h, pad, total * 1.1, 0, fmt);
    const items = [{ label: baseLabel, from: 0, to: base, color: C.grey }];
    let run = base;
    steps.forEach(st => { items.push({ label: st.label, from: run, to: run + st.value, color: C.blue, delta: st.value }); run += st.value; });
    items.push({ label: totalLabel, from: 0, to: total, color: C.orange });
    const bw = (w - pad.l - pad.r) / items.length;
    let s = g;
    items.forEach((it, i) => {
      const x = pad.l + i * bw + bw * 0.14, top = y(Math.max(it.from, it.to)), bot = y(Math.min(it.from, it.to));
      s += `<rect x="${x}" y="${top}" width="${bw * 0.72}" height="${Math.max(bot - top, 2)}" rx="3" fill="${it.color}"/>`;
      s += `<text x="${x + bw * 0.36}" y="${top - 6}" text-anchor="middle" font-size="11.5" font-weight="700" fill="${C.ink}">${it.delta != null ? '+' + fmt(it.delta) : fmt(it.to)}</text>`;
      const words = String(it.label).split(' '), linesTxt = [];
      words.forEach(wd => { const l = linesTxt[linesTxt.length - 1]; if (l && (l + ' ' + wd).length <= 12) linesTxt[linesTxt.length - 1] = l + ' ' + wd; else linesTxt.push(wd); });
      linesTxt.slice(0, 4).forEach((l, k) => { s += `<text x="${x + bw * 0.36}" y="${h - pad.b + 15 + k * 12}" text-anchor="middle" font-size="10" fill="${C.ink}">${esc(l)}</text>`; });
    });
    el.innerHTML = `<svg class="chart" style="direction:ltr" viewBox="0 0 ${w} ${h}" role="img">${s}</svg>`;
  }

  return { C, bars, hbars, lines, waterfall, fmt };
})();
