function txt(s, x, y, o={}){
  const {size=60, weight=900, color="#fff", alpha=1, stroke=14, scale=1, glow=null, align="center"} = o; if (alpha <= 0.003 || scale <= 0.01) return;
  ctx.save(); ctx.globalAlpha = Math.min(alpha, 1); ctx.translate(x, y); ctx.scale(scale, scale); ctx.font = `${weight} ${size}px M`; ctx.textAlign = align; ctx.textBaseline = "middle";
  ctx.lineJoin = "round"; ctx.lineWidth = stroke; ctx.strokeStyle = "rgba(0,0,0,.82)"; ctx.strokeText(s, 0, 0);
  ctx.shadowColor = glow || "rgba(0,0,0,.6)"; ctx.shadowBlur = glow ? 30 : 14; ctx.shadowOffsetY = glow ? 0 : 4; ctx.fillStyle = color; ctx.fillText(s, 0, 0); ctx.restore();
}
function fit(s, size, maxW){ ctx.font = `900 ${size}px M`; const w = ctx.measureText(s).width; return w > maxW ? size*maxW/w : size; }
function richLine(segs, x, y, o={}){
  let {size=56, scale=1} = o; ctx.font = `900 ${size}px M`;
  let total = d3.sum(segs, s => ctx.measureText(s.t).width); if (total > W - 2*MARGIN){ size *= (W - 2*MARGIN)/total; ctx.font = `900 ${size}px M`; }
  const widths = segs.map(s => ctx.measureText(s.t).width); total = d3.sum(widths); let cx = x - total*scale/2;
  segs.forEach((s, i) => { txt(s.t, cx, y, {...o, size, align:"left", color:s.c}); cx += widths[i]*scale; });
}
function kin(str, x, y, t, t0, o={}){
  const {size=110, color="#fff", out=1e9, step=0.03} = o;
  const outK = prog(t, out, out + 0.25); if (t < t0 || outK >= 1) return;
  const sz = fit(str, size, W - 2*MARGIN);
  ctx.save(); ctx.globalAlpha = 1 - outK; ctx.translate(x, y - 40*outK); ctx.font = `900 ${sz}px M`;
  const chars = [...str], ws = chars.map(c => ctx.measureText(c).width), tot = d3.sum(ws); let cx = -tot/2;
  chars.forEach((c, i) => { const a = EB(prog(t, t0 + i*step, t0 + i*step + 0.22)), w = ws[i];
    if (a > 0){ ctx.save(); ctx.translate(cx + w/2, -sz*0.3*(1 - Math.min(a, 1))); ctx.scale(a, a);
      ctx.lineJoin = "round"; ctx.lineWidth = sz*0.15; ctx.strokeStyle = "rgba(0,0,0,0.85)"; ctx.strokeText(c, -w/2, sz*0.35);
      ctx.shadowColor = color === "#fff" ? "rgba(0,0,0,.6)" : color; ctx.shadowBlur = color === "#fff" ? 10 : 26; ctx.fillStyle = color; ctx.fillText(c, -w/2, sz*0.35); ctx.restore(); }
    cx += w; });
  ctx.restore();
}
function pin(x, y, a, color=Y1, r=14){ if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = Math.min(a, 1); ctx.fillStyle = color; ctx.shadowColor = color; ctx.shadowBlur = 20;
  ctx.beginPath(); ctx.arc(x, y, r*Math.min(a, 1.3), 0, 7); ctx.fill(); ctx.lineWidth = 4; ctx.strokeStyle = "#fff"; ctx.shadowBlur = 0; ctx.stroke(); ctx.restore(); }
function pulse(x, y, t, a, color=Y1, max=110){ if (a <= 0) return;
  for (let k = 0; k < 2; k++){ const ph = (t*0.9 + k*0.5) % 1; ctx.save(); ctx.globalAlpha = (1 - ph)*a; ctx.strokeStyle = color; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(x, y, 16 + ph*max, 0, 7); ctx.stroke(); ctx.restore(); } }
function arrow(pts, k, alpha, color=Y1, w=10){
  if (k <= 0 || alpha <= 0) return;
  const line = d3.line().curve(d3.curveCatmullRom)(pts.map(p => P(...p))), path = new Path2D(line);
  const tmp = document.createElementNS("http://www.w3.org/2000/svg", "path"); tmp.setAttribute("d", line);
  const L = tmp.getTotalLength(), e = tmp.getPointAtLength(L*k), e0 = tmp.getPointAtLength(Math.max(0, L*k - 8));
  ctx.save(); ctx.globalAlpha = Math.min(alpha, 1); ctx.lineCap = "round"; ctx.lineWidth = w; ctx.strokeStyle = color; ctx.shadowColor = "rgba(0,0,0,.75)"; ctx.shadowBlur = 10;
  ctx.setLineDash([L*k, L]); ctx.stroke(path); ctx.setLineDash([]);
  const an = Math.atan2(e.y - e0.y, e.x - e0.x); ctx.translate(e.x, e.y); ctx.rotate(an); ctx.fillStyle = color;
  ctx.beginPath(); ctx.moveTo(w*2.6, 0); ctx.lineTo(-w*1.4, -w*2.1); ctx.lineTo(-w*1.4, w*2.1); ctx.closePath(); ctx.fill(); ctx.restore();
}
let GEO = null; const FLAG = {};
function path(rings){ ctx.beginPath(); for (const r of rings) r.forEach(([lon, lat], i) => { const [x, y] = P(lon, lat); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); }
function bbox(rings){ let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const r of rings) for (const [lon, lat] of r){ const [x, y] = P(lon, lat); x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  return [x0, y0, x1, y1]; }
function flagFill(id, flag, k, gray=0){
  if (k <= 0) return; const rings = GEO.c[id], img = FLAG[flag]; if (!img) return;
  const [x0, y0, x1, y1] = bbox(rings), w = x1 - x0, h = y1 - y0; if (x1 < -200 || x0 > W + 200 || y1 < -200 || y0 > H + 200) return;
  const cx = (x0 + x1)/2, cy = (y0 + y1)/2, sc = 1 + 0.06*Math.sin(Math.PI*clamp(k*1.4))*(k < 1 ? 1 : 0);
  ctx.save(); ctx.translate(cx, cy); ctx.scale(sc, sc); ctx.translate(-cx, -cy);
  for (const [o, al] of [[14, .18], [8, .22], [4, .25]]){ ctx.save(); ctx.translate(0, o); path(rings); ctx.fillStyle = `rgba(0,0,0,${al*Math.min(1, k*2)})`; ctx.fill(); ctx.restore(); }
  ctx.save(); path(rings); ctx.clip(); const R = Math.hypot(w, h)/2*EO(clamp(k*1.25)); ctx.beginPath(); ctx.arc(cx, cy, Math.max(1, R), 0, 7); ctx.clip();
  if (gray > 0) ctx.filter = `grayscale(${gray}) brightness(${1 - 0.45*gray})`;
  const ar = img.width/img.height, fw = Math.max(w, h*ar), fh = fw/ar; ctx.drawImage(img, cx - fw/2, cy - fh/2, fw, fh);
  ctx.filter = "none";
  const g = ctx.createLinearGradient(x0, y0, x1, y1); g.addColorStop(0, "rgba(255,255,255,.14)"); g.addColorStop(1, "rgba(0,0,0,.16)"); ctx.fillStyle = g; ctx.fillRect(x0, y0, w, h);
  ctx.restore();
  ctx.save(); path(rings); ctx.lineJoin = "round"; ctx.strokeStyle = `rgba(255,255,255,${0.95*clamp(k*2)*(1 - 0.5*gray)})`; ctx.lineWidth = 5; ctx.stroke(); ctx.restore();
  ctx.restore();
}
