function baseCamera(t){
  let i = 0; while (i < KEYS.length - 2 && t > KEYS[i+1][0]) i++;
  const [ta, va] = KEYS[i], [tb, vb, eb] = KEYS[i+1], k = (eb || E)(prog(t, ta, tb));
  const v = d3.interpolateZoom(va, vb)(k); return {cx:v[0], cy:v[1], z:Math.log2(W/v[2])};
}
// caméra « vivante » : pendant les plans calmes, enchaînement de petits zooms / balayages (~1,7 s chacun)
const BEAT_PAT = [[150, -70, 0.2], [-160, 45, 0.06], [70, 110, -0.15], [-120, -90, 0.22], [165, 60, -0.08], [-80, -115, 0.15]];
const BEATS = []; let bi = 0;
for (let i = 0; i < KEYS.length - 1; i++){ const ta = KEYS[i][0], tb = KEYS[i+1][0], e = KEYS[i+1][2], d = tb - ta;
  if (e === EX || e === EO || d < 3.0) continue; const n = Math.max(2, Math.round(d/3.4)), pts = [[ta + 0.05, [0, 0, 0]]];
  for (let j = 1; j < n; j++) pts.push([ta + d*j/n, BEAT_PAT[bi++ % BEAT_PAT.length]]);
  pts.push([tb - 0.05, [0, 0, 0]]); BEATS.push(pts); }
function beatOffset(t){
  for (const pts of BEATS){ if (t < pts[0][0] || t > pts[pts.length - 1][0]) continue;
    let j = 0; while (j < pts.length - 2 && t > pts[j+1][0]) j++;
    const [a, oa] = pts[j], [b, ob] = pts[j+1], k = E(prog(t, a, b)); return oa.map((v, q) => lerp(v, ob[q], k)); }
  return [0, 0, 0];
}
function camera(t){ const c = baseCamera(t), [dx, dy, dz] = beatOffset(t), z = c.z + dz; return {cx:c.cx + dx/2**z, cy:c.cy + dy/2**z, z}; }
let CAM = camera(0);
const wrapLon = lon => { const c = CAM.cx/TS*360 - 180; return lon + 360*Math.round((c - lon)/360); };
const P = (lon, lat) => { const s = 2**CAM.z; return [(mx(wrapLon(lon)) - CAM.cx)*s + W/2, (my(lat) - CAM.cy)*s + H/2]; };
// ------------------------------------------------------------------ tuiles
const TILES = {};
function visibleTiles(cam, z){
  const s = 2**cam.z, n = 2**z, out = [], m = 1.12;
  const tx0 = Math.floor((cam.cx - W*m/2/s)*n/TS), tx1 = Math.floor((cam.cx + W*m/2/s)*n/TS);
  const ty0 = Math.floor((cam.cy - H*m/2/s)*n/TS), ty1 = Math.floor((cam.cy + H*m/2/s)*n/TS);
  for (let x = tx0; x <= tx1; x++) for (let y = ty0; y <= ty1; y++) if (y >= 0 && y < n) out.push([z, ((x % n) + n) % n, y, x]);
  return out;
}
const levelFor = z => Math.max(ZMIN, Math.min(ZMAX, Math.floor(z + 0.5)));
window.plan = () => { const set = new Set();
  for (let f = 0; f < DUR*30; f++){ const c = camera(f/30), L = levelFor(c.z);
    for (const zz of [L, Math.max(ZMIN, L - 1)]) for (const [z, x, y] of visibleTiles(c, zz)) set.add(`${z}/${x}/${y}`); }
  return [...set]; };
window.prep = async t => {
  const jobs = [], c = camera(t), L = levelFor(c.z);
  for (const [z, x, y] of [...visibleTiles(c, L), ...visibleTiles(c, Math.max(ZMIN, L - 1))]){ const k = `${z}/${x}/${y}`; if (k in TILES) continue;
    jobs.push(new Promise(r => { const i = new Image(); i.onload = () => { TILES[k] = i; r(); }; i.onerror = () => { TILES[k] = null; r(); }; i.src = `tiles/${k}.jpg`; })); }
  await Promise.all(jobs);
};
function drawTiles(){
  const L = levelFor(CAM.z), s = 2**CAM.z;
  for (const zz of [Math.max(ZMIN, L - 1), L]){ const ts = TS*2**(CAM.z - zz);
    for (const [z, x, y, xr] of visibleTiles(CAM, zz)){ const img = TILES[`${z}/${x}/${y}`]; if (!img) continue;
      const sx = (xr*TS/2**z - CAM.cx)*s + W/2, sy = (y*TS/2**z - CAM.cy)*s + H/2;
      ctx.drawImage(img, Math.floor(sx), Math.floor(sy), Math.ceil(ts) + 1, Math.ceil(ts) + 1); } }
}
// ------------------------------------------------------------------ outils de dessin
__HELPERS__
function inView(bb, pad=80){ const [a, b] = P(bb[0], bb[3]), [c, d] = P(bb[2], bb[1]); return c > -pad && a < W + pad && d > -pad && b < H + pad; }
function label(s, x, y, o={}){ ctx.font = `900 ${o.size || 56}px M`; const w = ctx.measureText(s).width; txt(s, clamp(x, MARGIN + w/2, W - MARGIN - w/2), y, o); }
function lineLL(pts, alpha, color, w, dash=null){ if (alpha <= 0 || pts.length < 2) return null; const pp = pts.map(p => P(...p));
  ctx.save(); ctx.globalAlpha = Math.min(alpha, 1); ctx.lineCap = "round"; ctx.lineJoin = "round"; if (dash) ctx.setLineDash(dash);
  ctx.beginPath(); pp.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
  ctx.strokeStyle = "rgba(0,0,0,.5)"; ctx.lineWidth = w + 8; ctx.stroke(); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.stroke(); ctx.restore(); return pp[pp.length - 1]; }
// arc (courbe) entre deux points, tracé jusqu'à k
const arcPts = (a, b, k, bend=0.25) => { const mxl = (a[0] + b[0])/2, myl = (a[1] + b[1])/2, dx = b[0] - a[0], dy = b[1] - a[1];
  const c = [mxl - dy*bend, myl + dx*bend + Math.abs(dx)*0.12]; return d3.range(0, 41).map(i => i/40*k).map(q => [(1-q)**2*a[0] + 2*(1-q)*q*c[0] + q*q*b[0], (1-q)**2*a[1] + 2*(1-q)*q*c[1] + q*q*b[1]]); };
function flight(a, b, k, alpha, color=Y1, w=8, bend=0.25){ if (k <= 0 || alpha <= 0) return; const e = lineLL(arcPts(a, b, k, bend), alpha, color, w, [20, 12]);
  if (e && k < 1){ pulse(e[0], e[1], 0, alpha*0.8, color, 40); pin(e[0], e[1], alpha, color, 13); } }
function photo(img, t, t0, t1, cy=1010, w=640, h=800){
  if (!img) return 0; const a = EB(prog(t, t0, t0 + 0.35)), out = E(prog(t, t1, t1 + 0.3)); if (a <= 0 || out >= 1) return 0;
  const kb = 1.04 + 0.08*prog(t, t0, t1 + 0.3), ar = img.width/img.height, dw = Math.max(w, h*ar)*kb, dh = dw/ar;
  ctx.save(); ctx.translate(W/2, cy + 80*out); ctx.scale(a*(1 - 0.3*out), a*(1 - 0.3*out)); ctx.globalAlpha = 1 - out;
  ctx.fillStyle = "#fff"; ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 16; ctx.fillRect(-w/2 - 12, -h/2 - 12, w + 24, h + 24); ctx.shadowColor = "transparent";
  ctx.beginPath(); ctx.rect(-w/2, -h/2, w, h); ctx.clip(); ctx.drawImage(img, -dw/2, -dh/2, dw, dh); ctx.restore();
  const fl = t >= t0 ? Math.exp(-(t - t0)*9) : 0; if (fl > 0.02){ ctx.save(); ctx.fillStyle = `rgba(255,255,255,${0.45*fl})`; ctx.fillRect(-60, -60, W + 120, H + 120); ctx.restore(); }
  return 1 - out;
}
function vehicle(img, pts, k, h, a){ if (!img || a <= 0) return; const e = P(...along(pts, k)), b = P(...along(pts, Math.min(1, k + 0.02))), w = h*img.width/img.height, flip = b[0] < e[0] - 0.5 ? -1 : 1;
  ctx.save(); ctx.globalAlpha = Math.min(a, 1); ctx.translate(e[0], e[1] - h*0.3); ctx.scale(flip*a, a); ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 24; ctx.shadowOffsetY = 10;
  ctx.drawImage(img, -w/2, -h/2, w, h); ctx.restore(); return e; }
function city(p, a, t, color=Y1, r=18){ if (a <= 0) return; const [x, y] = P(...p); pulse(x, y, t, a, color, 120); pin(x, y, EB(clamp(a*1.4)), color, r); }
function glow(rings, a){ if (a <= 0) return; ctx.save(); path(rings); ctx.fillStyle = `rgba(255,214,10,${0.16*a})`; ctx.fill(); ctx.lineJoin = "round"; ctx.lineWidth = 5; ctx.strokeStyle = `rgba(255,255,255,${0.85*a})`; ctx.stroke(); ctx.restore(); }
// flou de mouvement pendant les balayages / zooms rapides
function motionBlur(t){
  const a = camera(t), b = camera(t + 1/30), s = 2**a.z;
  let dx = (b.cx - a.cx)*s, dy = (b.cy - a.cy)*s; const dz = b.z - a.z, sp = Math.hypot(dx, dy);
  if ((sp < 5 && Math.abs(dz) < 0.012) || sp > 2000) return;
  const cap = Math.min(1, 140/Math.max(sp, 1)); dx *= cap; dy *= cap;
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); bctx.clearRect(0, 0, W, H); bctx.drawImage(cv, 0, 0);
  const N = 5, st = clamp(Math.max(sp/60, Math.abs(dz)/0.08));
  for (let i = 1; i <= N; i++){ const q = i/N, sc = 2**(-clamp(dz, -0.12, 0.12)*q*1.2);
    ctx.globalAlpha = 0.2*st; ctx.save(); ctx.translate(W/2 - dx*q*0.9, H/2 - dy*q*0.9); ctx.scale(sc, sc); ctx.drawImage(BUF, -W/2, -H/2); ctx.restore(); }
  ctx.restore();
}
// ------------------------------------------------------------------ sous-titres + frise
const CAPS = TL.vo.filter(v => !NOCAP.includes(v.id)).map(v => {
  const words = [];
  for (const w of v.cap.split(/\s+/)){ const o = {hi:/\*/.test(w), w:w.replace(/\*/g, "")}; const p = words[words.length-1];
    if (p && (/^[:;!?…%]$/.test(o.w) || (/^\d+$/.test(p.w) && /^\d{3}/.test(o.w)))) { p.w += " " + o.w; p.hi = p.hi || o.hi; } else words.push(o); }
  const groups = []; let cur = [];
  for (const w of words){ const len = cur.map(x => x.w).join(" ").length + w.w.length + 1;
    if (cur.length && len > 14){ groups.push(cur); cur = []; } cur.push(w); if (/[.,:!?…]$/.test(w.w)){ groups.push(cur); cur = []; } }
  if (cur.length) groups.push(cur);
  const tot = d3.sum(groups, g => g.map(x => x.w).join(" ").length + 4); let acc = 0;
  return groups.map(g => { const l = g.map(x => x.w).join(" ").length + 4; const s = v.start + (v.end - v.start)*acc/tot; acc += l; return {g, s, e:v.start + (v.end - v.start)*acc/tot}; });
}).flat();
function yearAt(t){ let v = null; for (const [t0, t1, y0, y1] of TL.ticker) if (t >= t0) v = lerp(y0, y1, E(prog(t, t0, t1))); return v; }
function outlined(img, r=9){ const c = document.createElement("canvas"); c.width = img.width + 2*r; c.height = img.height + 2*r; const g = c.getContext("2d");
  for (let a = 0; a < 32; a++) g.drawImage(img, r + Math.cos(a/32*6.283)*r, r + Math.sin(a/32*6.283)*r);
  g.globalCompositeOperation = "source-in"; g.fillStyle = "#fff"; g.fillRect(0, 0, c.width, c.height); g.globalCompositeOperation = "source-over"; g.drawImage(img, r, r); return c; }
window.renderAt = render;
const load = (k, src) => new Promise(r => { const i = new Image(); i.onload = () => { FLAG[k] = i; r(); }; i.onerror = r; i.src = src; });
const img = (k, src, f) => new Promise(r => { const i = new Image(); i.onload = () => { PH[k] = f ? f(i) : i; r(); }; i.onerror = r; i.src = src; });