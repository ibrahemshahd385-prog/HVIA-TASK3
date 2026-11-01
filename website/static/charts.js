/* Small SVG charts (no library, works offline). Three colours: navy, grey, teal – one highlight at a time. */
const Charts = (() => {
  const C = { navy: '#2F4B7C', grey: '#D5DCE6', teal: '#3AA6A0', mid: '#9AA8BA', ink: '#4A5568', grid: '#EDF1F6', tealT: '#E8F5F4' };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const nice = max => { if (max <= 0) return 1; const p = Math.pow(10, Math.floor(Math.log10(max))); const n = max / p; return [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10].find(s => n <= s) * p; };
  const fmt = v => Math.abs(v) >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : Math.abs(v) >= 1e3 ? (v / 1e3).toFixed(0) + 'K' : Math.abs(v) >= 100 ? Math.round(v).toString() : (Math.round(v * 10) / 10).toString();
  const step = max => { const raw = max / 4, p = Math.pow(10, Math.floor(Math.log10(raw))); return [1, 2, 2.5, 5, 10].find(s => raw / p <= s) * p; };
  const rtl = () => document.documentElement.dir === 'rtl';
  const svg = (w, h, s) => `<svg class="chart" style="direction:ltr" viewBox="0 0 ${w} ${h}" role="img">${s}</svg>`;
  const legend = (series) => series.length > 1 ? `<div class="legend">${series.map(s => `<span class="${s.dash ? 'dash' : s.box ? 'box' : ''}" style="--c:${s.color}">${esc(s.name)}</span>`).join('')}</div>` : '';

  function axis(w, h, pad, maxY, fmtY) {
    const ticks = 4, top = maxY > 0 ? step(maxY) * ticks : 1, y = v => pad.t + (h - pad.t - pad.b) * (1 - v / top);
    let g = '';
    for (let i = 0; i <= ticks; i++) {
      const v = top * i / ticks;
      g += `<line x1="${pad.l}" x2="${w - pad.r}" y1="${y(v)}" y2="${y(v)}" stroke="${C.grid}"/>` +
           `<text x="${pad.l - 8}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="${C.ink}">${esc(fmtY(v))}</text>`;
    }
    return { y, g };
  }

  // vertical (grouped) bars. series: [{name, color, values}]
  function bars(el, labels, series, o = {}) {
    const w = o.width || el.clientWidth || 600, h = o.height || 250, pad = { t: 22, r: 10, b: 34, l: 50 }, f = o.fmt || fmt;
    const all = series.flatMap(s => s.values);
    const { y, g } = axis(w, h, pad, Math.max(...all, 0) * 1.12, o.fmtY || f);
    const gw = (w - pad.l - pad.r) / labels.length, bw = gw * 0.72 / series.length;
    let s = g;
    labels.forEach((lab, i) => {
      series.forEach((se, k) => {
        const v = se.values[i], x = pad.l + i * gw + gw * 0.14 + k * bw, top = y(Math.max(v, 0));
        const col = (se.colors && se.colors[i]) || se.color;
        s += `<rect x="${x}" y="${top}" width="${bw - 2}" height="${Math.max(y(0) - top, 1)}" rx="3" fill="${col}"><title>${esc(lab)} · ${esc(se.name || '')}: ${esc(f(v))}</title></rect>`;
        if (o.values !== false && series.length === 1) s += `<text x="${x + bw / 2 - 1}" y="${top - 6}" text-anchor="middle" font-size="11" fill="${C.ink}">${esc(f(v))}</text>`;
      });
      s += `<text x="${pad.l + i * gw + gw / 2}" y="${h - pad.b + 18}" text-anchor="middle" font-size="11" fill="${C.ink}">${esc(lab)}</text>`;
    });
    el.innerHTML = svg(w, h, s) + legend(series.map(x => ({ ...x, box: true })));
  }

  // horizontal (grouped) bars, mirrored in Arabic. rows: labels; series [{name, color, values}]
  function hbars(el, rows, series, o = {}) {
    const w = o.width || el.clientWidth || 600, f = o.fmt || fmt, lw = o.labelWidth || 120, vw = 58;
    const per = o.row || (series.length > 1 ? 30 : 24), h = 6 + per * rows.length;
    const maxV = nice(Math.max(...series.flatMap(s => s.values), 0) * 1.02), span = w - lw - vw - 12;
    const R = rtl();
    let s = '';
    rows.forEach((lab, i) => {
      const y0 = 3 + i * per, bh = (per - 8) / series.length;
      s += `<text x="${R ? w - 4 : lw - 8}" y="${y0 + per / 2 + 4}" text-anchor="end" font-size="12" fill="${C.ink}">${esc(lab)}</text>`;
      series.forEach((se, k) => {
        const v = se.values[i], bw = Math.max(span * Math.max(v, 0) / maxV, 1), yy = y0 + 4 + k * bh;
        const x = R ? w - lw - 4 - bw : lw;
        const col = (se.colors && se.colors[i]) || se.color;
        s += `<rect x="${x}" y="${yy}" width="${bw}" height="${bh - 2}" rx="3" fill="${col}"><title>${esc(lab)} · ${esc(se.name || '')}: ${esc(f(v))}</title></rect>`;
        s += `<text x="${R ? x - 6 : x + bw + 6}" y="${yy + bh / 2 + 3}" text-anchor="${R ? 'end' : 'start'}" font-size="11" fill="${C.ink}">${esc(f(v))}</text>`;
      });
    });
    el.innerHTML = svg(w, h, s) + legend(series.map(x => ({ ...x, box: true })));
  }

  // lines. series [{name, color, values (null = gap), dash}]; o.shadeFrom = index where the forecast starts
  function lines(el, labels, series, o = {}) {
    const w = o.width || el.clientWidth || 600, h = o.height || 250, pad = { t: 16, r: 14, b: 30, l: 50 }, f = o.fmt || fmt;
    const all = series.flatMap(s => s.values.filter(v => v != null));
    const { y, g } = axis(w, h, pad, Math.max(...all) * 1.1, o.fmtY || f);
    const x = i => pad.l + (w - pad.l - pad.r) * (labels.length === 1 ? 0.5 : i / (labels.length - 1));
    let s = '';
    if (o.shadeFrom != null) {
      const x0 = x(o.shadeFrom) - (x(1) - x(0)) / 2;
      s += `<rect x="${x0}" y="${pad.t}" width="${w - pad.r - x0}" height="${h - pad.t - pad.b}" fill="${C.tealT}"/>` +
           `<text x="${(x0 + w - pad.r) / 2}" y="${pad.t + 14}" text-anchor="middle" font-size="11" fill="${C.teal}">${esc(o.shadeLabel || 'forecast')}</text>`;
    }
    s += g;
    const every = Math.max(1, Math.ceil(labels.length / (o.ticks || Math.max(3, Math.min(7, Math.floor(w / 120))))));
    labels.forEach((l, i) => {
      if (i % every === 0 || i === labels.length - 1) {
        if (i !== labels.length - 1 && labels.length - 1 - i < every) return;
        s += `<text x="${x(i)}" y="${h - 9}" text-anchor="${i === 0 ? 'start' : i === labels.length - 1 ? 'end' : 'middle'}" font-size="11" fill="${C.ink}">${esc(l)}</text>`;
      }
    });
    series.forEach(se => {
      const pts = se.values.map((v, i) => v == null ? null : `${x(i)},${y(v)}`).filter(Boolean).join(' ');
      s += `<polyline points="${pts}" fill="none" stroke="${se.color}" stroke-width="${se.width || 2.4}" ${se.dash ? 'stroke-dasharray="5 4"' : ''} stroke-linejoin="round" stroke-linecap="round"/>`;
      se.values.forEach((v, i) => { if (v != null && (o.dots || se.dots)) s += `<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${se.color}"><title>${esc(labels[i])}: ${esc(f(v))}</title></circle>`; });
    });
    // invisible hover targets
    labels.forEach((l, i) => {
      const vals = series.map(se => se.values[i] == null ? null : `${se.name}: ${f(se.values[i])}`).filter(Boolean).join(' · ');
      s += `<rect x="${x(i) - 6}" y="${pad.t}" width="12" height="${h - pad.t - pad.b}" fill="transparent"><title>${esc(l)} – ${esc(vals)}</title></rect>`;
    });
    el.innerHTML = svg(w, h, s) + legend(series);
  }

  function ring(pct, size = 58) {
    const r = size / 2 - 5, c = 2 * Math.PI * r;
    return `<svg class="ring" viewBox="0 0 ${size} ${size}"><circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="${C.grey}" stroke-width="6"/>` +
      `<circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="${C.teal}" stroke-width="6" stroke-linecap="round" stroke-dasharray="${c * pct} ${c}" transform="rotate(-90 ${size / 2} ${size / 2})"/>` +
      `<text x="50%" y="54%" text-anchor="middle" font-size="13" font-weight="700" fill="${C.navy}" style="direction:ltr">${Math.round(pct * 100)}%</text></svg>`;
  }

  return { C, bars, hbars, lines, ring, fmt, nice };
})();
