// ------------------------------------------------------------------ données
let BB = [], PH = {}, BEARS = [], LIGHTS = [];
{ const r = d3.randomLcg(9); for (let i = 0; i < 40; i++) LIGHTS.push([25.575 + r()*0.04, 45.64 + r()*0.03]); }
function setup(){
  BB = GEO.b.map(r => [d3.min(r, p => p[0]), d3.min(r, p => p[1]), d3.max(r, p => p[0]), d3.max(r, p => p[1])]);
  const ro = GEO.c.ROU.slice().sort((a, b) => b.length - a.length)[0], rnd = d3.randomLcg(5);
  while (BEARS.length < 80){ const q = along(ARC, rnd()), p = [q[0] + (rnd() - 0.5)*0.9, q[1] + (rnd() - 0.5)*0.6]; if (d3.polygonContains(ro, p)) BEARS.push({p, d:rnd()}); }
}
const HITS = TL.sfx.filter(s => ["impact", "hit"].includes(s.name)).map(s => [s.t, s.name === "hit" ? 0.035 : 0.06, s.name === "hit" ? 5 : 10]);
HITS.push([0.05, 0.08, 12]);
const night = t => E(prog(t, S("r04") - 0.3, S("r04") + 0.4))*(1 - E(prog(t, Ed("r04") + 0.6, Ed("r04") + 1.2)));
// ------------------------------------------------------------------ carte
function renderMap(t){
  CAM = camera(t);
  ctx.fillStyle = "#0b1622"; ctx.fillRect(-60, -60, W + 120, H + 120);
  drawTiles();
  ctx.save(); ctx.strokeStyle = "rgba(255,255,255,.32)"; ctx.lineWidth = 2; ctx.lineJoin = "round";
  GEO.b.forEach((r, i) => { if (inView(BB[i])){ path([r]); ctx.stroke(); } }); ctx.restore();
  // ce n'est pas la Russie
  flagFill("RUS", "ru", EO(prog(t, T_RUS - 0.45, T_RUS))*(1 - prog(t, Ed("r01") + 0.1, Ed("r01") + 0.4)), prog(t, T_RUS, T_RUS + 0.2));
  // la Roumanie, puis l'arc des Carpates
  flagFill("ROU", "ro", EO(prog(t, T_ROU - 0.05, T_ROU + 0.4))*(1 - prog(t, T_CARP + 0.1, T_CARP + 0.45)));
  const cA = prog(t, T_CARP, T_CARP + 0.2)*(1 - prog(t, S("r03") - 0.1, S("r03") + 0.3));
  if (cA > 0){ const k = E(prog(t, T_CARP, T_CARP + 0.9)), pp = upto(ARC, k).map(p => P(...p));
    ctx.save(); ctx.globalAlpha = cA; ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.beginPath(); pp.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    ctx.strokeStyle = "rgba(255,214,10,.28)"; ctx.lineWidth = 70; ctx.stroke(); ctx.strokeStyle = Y1; ctx.lineWidth = 8; ctx.setLineDash([22, 14]); ctx.stroke(); ctx.restore(); }
  const bA = 1 - prog(t, S("r03") - 0.1, S("r03") + 0.3);
  if (bA > 0) BEARS.forEach((b, i) => { const t0 = T_BEARS + (i/80)*0.9, a = EB(prog(t, t0, t0 + 0.3))*bA*(1 - 0.55*prog(t, T_BARS - 0.1, T_BARS + 0.2)); if (a > 0){ const [x, y] = P(...b.p); bearIcon(x, y, 46, a); } });
  // Brașov : traces de pattes depuis la forêt, puis les signalements
  const pA = prog(t, T_PAW - 0.1, T_PAW)*(1 - prog(t, Ed("r04") + 0.5, Ed("r04") + 0.9));
  if (pA > 0) for (let i = 0; i < 10; i++){ const q = i/9, t0 = T_PAW + q*1.6; if (t < t0) break;
    const p0 = along(PAWS, q), p1 = along(PAWS, Math.min(1, q + 0.02)), [x0, y0] = P(...p0), [x1, y1] = P(...p1), an = Math.atan2(y1 - y0, x1 - x0);
    const side = i % 2 ? 1 : -1; paw(x0 - Math.sin(an)*side*26, y0 + Math.cos(an)*side*26, an + Math.PI/2, 44, pA*EB(prog(t, t0, t0 + 0.2))); }
  SIGHT.forEach((p, i) => { const t0 = T_SIGHT + i*0.18*(Ed("r03") - S("r03"))/4.7, a = prog(t, t0, t0 + 0.15)*pA; if (a <= 0) return; const [x, y] = P(...p); pulse(x, y, t + i*0.3, a, RED, 90); alertPin(x, y, EB(prog(t, t0, t0 + 0.3))*pA); });
  // nuit
  const n = night(t);
  if (n > 0){ ctx.save(); ctx.globalCompositeOperation = "multiply"; ctx.fillStyle = `rgba(${lerp(255, 75, n)},${lerp(255, 95, n)},${lerp(255, 165, n)},1)`; ctx.fillRect(-60, -60, W + 120, H + 120); ctx.restore();
    ctx.save(); ctx.globalCompositeOperation = "screen"; LIGHTS.forEach(p => { const [x, y] = P(...p), g = ctx.createRadialGradient(x, y, 0, x, y, 45);
      g.addColorStop(0, `rgba(255,235,170,${0.9*n})`); g.addColorStop(0.12, `rgba(255,200,110,${0.45*n})`); g.addColorStop(1, "rgba(255,190,90,0)"); ctx.fillStyle = g; ctx.fillRect(x - 45, y - 45, 90, 90); }); ctx.restore(); }
  const vg = ctx.createRadialGradient(W/2, H/2, H*0.42*(1 - 0.35*n), W/2, H/2, H*0.85); vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, `rgba(0,0,0,${0.38 + 0.45*n})`); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  const tg = ctx.createLinearGradient(0, 0, 0, 620); tg.addColorStop(0, "rgba(0,0,0,.42)"); tg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 620);
}
function bearIcon(x, y, h, a){ const img = PH.bearO; if (!img || a <= 0) return; const w = h*img.width/img.height;
  ctx.save(); ctx.translate(x, y); ctx.scale(a, a); ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 8; ctx.drawImage(img, -w/2, -h, w, h); ctx.restore(); }
function paw(x, y, an, r, a){ if (a <= 0) return; ctx.save(); ctx.globalAlpha = Math.min(a, 1); ctx.translate(x, y); ctx.rotate(an); ctx.scale(Math.min(a, 1.2), Math.min(a, 1.2));
  ctx.fillStyle = "#1a0f08"; ctx.strokeStyle = "rgba(255,255,255,.85)"; ctx.lineWidth = 4; ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 8;
  ctx.beginPath(); ctx.ellipse(0, r*0.25, r*0.62, r*0.5, 0, 0, 7); ctx.stroke(); ctx.fill();
  for (let k = 0; k < 4; k++){ const ax = (k - 1.5)*r*0.42, ay = -r*0.5 - (k === 1 || k === 2 ? r*0.15 : 0); ctx.beginPath(); ctx.ellipse(ax, ay, r*0.18, r*0.24, 0, 0, 7); ctx.stroke(); ctx.fill(); }
  ctx.restore(); }
function alertPin(x, y, a){ if (a <= 0) return; ctx.save(); ctx.translate(x, y); ctx.scale(a, a); ctx.fillStyle = RED; ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 16;
  ctx.beginPath(); ctx.arc(0, 0, 30, 0, 7); ctx.fill(); ctx.lineWidth = 5; ctx.strokeStyle = "#fff"; ctx.stroke(); ctx.shadowColor = "transparent"; ctx.fillStyle = "#fff"; ctx.font = "900 44px M"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText("!", 0, 3); ctx.restore(); }
// ------------------------------------------------------------------ rendu
function render(t){
  let p = 0, sx = 0, sy = 0;
  for (const [ti, amp, sh] of HITS) if (t >= ti){ const d = t - ti; p += amp*Math.exp(-d*8); sx += sh*Math.exp(-d*7)*Math.sin(d*50); sy += sh*0.7*Math.exp(-d*7)*Math.cos(d*43); }
  ctx.save(); ctx.translate(W/2 + sx, H/2 + sy); ctx.scale(1.04 + p, 1.04 + p); ctx.translate(-W/2, -H/2);
  renderMap(t); motionBlur(t); overlay(t);
  ctx.restore();
  const fl = Math.exp(-t*7); if (fl > 0.02){ ctx.fillStyle = `rgba(255,255,255,${0.6*fl})`; ctx.fillRect(0, 0, W, H); }
}
function beast(img, t, t0, t1, o={}){
  if (!img) return; const {h=640, y=1450, from=0, to=-1100, dx=0} = o;
  const a = EB(prog(t, t0, t0 + 0.4)), out = E(prog(t, t1, t1 + 0.4)); if (a <= 0 || out >= 1) return;
  const w = h*img.width/img.height, br = 1 + 0.02*Math.sin(t*6);
  ctx.save(); ctx.translate(W/2 + dx + from*(1 - Math.min(a, 1)) + to*out, y); ctx.rotate(Math.sin(t*3)*0.02); ctx.scale(a*br, a/br);
  ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 18; ctx.drawImage(img, -w/2, -h, w, h); ctx.restore();
}
// barres comparatives : Roumanie vs reste de l'UE (hors pays nordiques)
function bars(t){
  const a = prog(t, T_BARS - 0.1, T_BARS + 0.1)*(1 - prog(t, Ed("r02") + 0.1, Ed("r02") + 0.4)); if (a <= 0) return;
  const base = 1560, bw = 230, items = [[W/2 - 170, 560, "ro", T_BARS], [W/2 + 170, 400, "eu", T_BARS + 0.15]];
  ctx.save(); ctx.globalAlpha = Math.min(a, 1);
  for (const [x, hmax, f, t0] of items){ const k = EO(prog(t, t0, t0 + 0.6)), h = hmax*k + 4, img = FLAG[f]; if (!img) continue;
    ctx.save(); ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 30; ctx.fillStyle = "#fff"; ctx.fillRect(x - bw/2 - 8, base - h - 8, bw + 16, h + 8); ctx.restore();
    ctx.save(); ctx.beginPath(); ctx.rect(x - bw/2, base - h, bw, h); ctx.clip(); if (f === "ro") ctx.drawImage(img, x - bw/2, base - h, bw, h); else { const ar = img.width/img.height, fh = Math.max(h, bw/ar), fw = fh*ar; ctx.drawImage(img, x - fw/2, base - fh, fw, fh); } ctx.restore();
    if (f === "ro" && k > 0.9){ const c = EB(prog(t, T_WIN, T_WIN + 0.35)); if (c > 0) bearIcon(x, base - h - 10, 150, c); } }
  ctx.restore(); }
function overlay(t){
  beast(PH.bearO, t, 0, 1.25, {h:620, y:1520, to:-1200});
  // ---- accroche : 8 000 ours… pas la Russie
  if (t > S("r01") && t < Ed("r01") + 0.5){ const o = Ed("r01") + 0.1;
    kin("EN EUROPE", W/2, 450, t, S("r01") + 0.2, {size:110, out:T_CNT - 0.1});
    const a = EB(prog(t, T_CNT, T_CNT + 0.3))*(1 - prog(t, o, o + 0.25)), n = 8000*E(prog(t, T_CNT, T_8000));
    if (a > 0){ txt(fmt(n), W/2, 470, {size:220, color:Y1, scale:a*(1 + 0.08*Math.exp(-(t - T_8000)*8)*(t > T_8000 ? 1 : 0)), alpha:Math.min(a, 1), stroke:24, glow:"rgba(255,214,10,.5)"}); txt("OURS", W/2, 640, {size:110, scale:a, alpha:Math.min(a, 1), stroke:15}); }
    const r = EB(prog(t, T_RUS, T_RUS + 0.3))*(1 - prog(t, o, o + 0.25)); if (r > 0){ txt("PAS LA RUSSIE", W/2, 1450, {size:fit("PAS LA RUSSIE", 110, W - 2*MARGIN), color:RED, scale:r, alpha:Math.min(r, 1), stroke:16, glow:"rgba(255,59,48,.45)"}); } }
  bars(t);
  // ---- les yeux dans le noir
  const e = prog(t, T_EYES - 0.05, T_EYES + 0.1)*(1 - prog(t, S("r05") + 0.2, S("r05") + 0.5));
  if (e > 0){ const bl = Math.abs(Math.sin((t - T_EYES)*2.2)) > 0.08 ? 1 : 0.1;
    for (const dx of [-60, 60]){ ctx.save(); ctx.globalAlpha = e; ctx.fillStyle = "#ffe36a"; ctx.shadowColor = "#ffd60a"; ctx.shadowBlur = 50; ctx.beginPath(); ctx.ellipse(W/2 + 200 + dx*1.2, 1250, 40, 26*bl, 0, 0, 7); ctx.fill(); ctx.restore(); } }
  // ---- appel final : la tente… et l'ours
  if (t > S("r05") - 0.1){ const a = EB(prog(t, S("r05"), S("r05") + 0.35));
    tent(W/2 - 220, 1560, 300, a); beast(PH.bearO, t, M("r05", 0.35), DUR, {h:480, y:1620, from:700, dx:170});
    const c = EB(prog(t, T_CTA1, T_CTA1 + 0.35)); txt("ET TOI ?", W/2, 470, {size:140, color:Y1, scale:c, alpha:Math.min(c, 1), stroke:18, glow:"rgba(255,214,10,.45)"});
    const d = EB(prog(t, T_CTA2, T_CTA2 + 0.35)); txt("TU OSERAIS ?", W/2, 610, {size:100, scale:d, alpha:Math.min(d, 1), stroke:14}); }
  // ---- sous-titres
  let cur = null; for (const g of CAPS) if (g.s <= t) cur = g;
  if (cur && t <= cur.e + 0.25){ const a = EB(prog(t, cur.s, cur.s + 0.15));
    const segs = cur.g.map((w, i) => ({t:(i ? " " : "") + w.w.replace(/[.,]+$/, "").toUpperCase(), c:w.hi ? Y1 : "#fff"}));
    richLine(segs, W/2, 300, {size:84, scale:0.8 + 0.2*a, alpha:Math.min(a*2, 1), stroke:16}); }
}
function tent(x, y, w, a){ if (a <= 0) return; ctx.save(); ctx.translate(x, y); ctx.scale(a, a); ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 30; ctx.lineJoin = "round";
  ctx.fillStyle = "#ff7a1a"; ctx.strokeStyle = "#fff"; ctx.lineWidth = 10; ctx.beginPath(); ctx.moveTo(-w/2, 0); ctx.lineTo(0, -w*0.72); ctx.lineTo(w/2, 0); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.shadowColor = "transparent"; ctx.fillStyle = "#3a1d08"; ctx.beginPath(); ctx.moveTo(-w*0.14, 0); ctx.lineTo(0, -w*0.42); ctx.lineTo(w*0.14, 0); ctx.closePath(); ctx.fill(); ctx.restore(); }
window.ready = Promise.all([fetch("geo.json").then(r => r.json()).then(j => { GEO = j; setup(); }),
  ...["ro", "ru", "eu"].map(f => load(f, `flags/${f}.svg`)), img("bear", "assets/ours.png"),
  document.fonts.load("900 60px M"), document.fonts.load("800 60px M")]).then(() => { PH.bearO = outlined(PH.bear, 8); return true; });
