// ------------------------------------------------------------------ données
let BB = [], PH = {};
function setup(){ BB = GEO.b.map(r => [d3.min(r, p => p[0]), d3.min(r, p => p[1]), d3.max(r, p => p[0]), d3.max(r, p => p[1])]); }
const HITS = TL.sfx.filter(s => ["impact", "hit"].includes(s.name)).map(s => [s.t, s.name === "hit" ? 0.035 : 0.06, s.name === "hit" ? 5 : 10]);
HITS.push([0.05, 0.08, 12]);
// ------------------------------------------------------------------ carte
function renderMap(t){
  CAM = camera(t);
  ctx.fillStyle = "#0b1622"; ctx.fillRect(-60, -60, W + 120, H + 120);
  drawTiles();
  ctx.save(); ctx.strokeStyle = "rgba(255,255,255,.35)"; ctx.lineWidth = 2; ctx.lineJoin = "round";
  GEO.b.forEach((r, i) => { if (inView(BB[i])){ path([r]); ctx.stroke(); } }); ctx.restore();
  // drapeau : « on est à Singapour » puis « le symbole du pays »
  flagFill("SGP", "sg", EO(prog(t, T_FLAG - 0.05, T_FLAG + 0.45))*(1 - prog(t, S("s04") + 0.6, S("s04") + 1.0)));
  // le prince arrive de Bintan
  const pA = prog(t, PRINCE[0] - 0.2, PRINCE[0])*(1 - prog(t, T_FAUVE + 0.6, T_FAUVE + 1.0));
  if (pA > 0){ const k = E(prog(t, ...PRINCE)); arrow(R_PRINCE, Math.max(0.01, k), pA, Y1, 12);
    if (k >= 1) city(RIVER, pA*prog(t, PRINCE[1], PRINCE[1] + 0.2), t, Y1, 16); }
  // Singapour → Gir : l'arc de 4 000 km
  const aA = prog(t, ARC[0] - 0.2, ARC[0])*(1 - prog(t, Ed("s05") + 0.2, Ed("s05") + 0.6));
  if (aA > 0){ city(SG, aA, t, "#fff", 14); flight(SG, GIR, E(prog(t, ...ARC)), aA, Y1, 10, -0.18);
    const g = prog(t, T_GIR - 0.05, T_GIR + 0.25); if (g > 0){ const [x, y] = P(...GIR); pulse(x, y, t, aA, RED, 150); badge(PH.lion, x, y - 150, 120, EB(g)*aA); pin(x, y, aA*EB(g), RED, 18); } }
  // le Merlion
  const mA = prog(t, T_MER - 0.1, T_MER + 0.2)*(1 - prog(t, DUR - 1.2, DUR - 0.8));
  if (mA > 0){ const [x, y] = P(...MERLION); pulse(x, y, t, mA, Y1, 160); pin(x, y, EB(mA), Y1, 20);
    txt("MERLION", x, y + 80, {size:60, alpha:mA, stroke:12, scale:0.7 + 0.3*EB(mA)}); }
  const vg = ctx.createRadialGradient(W/2, H/2, H*0.42, W/2, H/2, H*0.85); vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,.38)"); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  const tg = ctx.createLinearGradient(0, 0, 0, 620); tg.addColorStop(0, "rgba(0,0,0,.42)"); tg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 620);
}
// pastille ronde avec la tête du lion (repère « les lions sont ici »)
function badge(img, x, y, r, a){ if (!img || a <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(a, a); ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 24; ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(0, 0, r + 8, 0, 7); ctx.fill(); ctx.shadowColor = "transparent";
  ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.clip(); ctx.fillStyle = "#e9c46a"; ctx.fillRect(-r, -r, 2*r, 2*r);
  const s = 2*r/(0.34*img.width); ctx.drawImage(img, -img.width*0.33*s, -img.height*0.17*s, img.width*s, img.height*s); ctx.restore(); }
// ------------------------------------------------------------------ rendu
function render(t){
  let p = 0, sx = 0, sy = 0;
  for (const [ti, amp, sh] of HITS) if (t >= ti){ const d = t - ti; p += amp*Math.exp(-d*8); sx += sh*Math.exp(-d*7)*Math.sin(d*50); sy += sh*0.7*Math.exp(-d*7)*Math.cos(d*43); }
  ctx.save(); ctx.translate(W/2 + sx, H/2 + sy); ctx.scale(1.04 + p, 1.04 + p); ctx.translate(-W/2, -H/2);
  renderMap(t); motionBlur(t); overlay(t);
  ctx.restore();
  const fl = Math.exp(-t*7); if (fl > 0.02){ ctx.fillStyle = `rgba(255,255,255,${0.6*fl})`; ctx.fillRect(0, 0, W, H); }
  for (const tf of [T_ZERO, T_TIGRE]){ const f = t >= tf ? Math.exp(-(t - tf)*9) : 0; if (f > 0.02){ ctx.fillStyle = `rgba(255,255,255,${0.35*f})`; ctx.fillRect(0, 0, W, H); } }
}
// animal découpé : entrée en rebond, petite respiration, sortie
function beast(img, t, t0, t1, o={}){
  if (!img) return; const {h=640, y=1450, from=0, to=-1100, sway=0.02} = o;
  const a = EB(prog(t, t0, t0 + 0.4)), out = E(prog(t, t1, t1 + 0.4)); if (a <= 0 || out >= 1) return;
  const w = h*img.width/img.height, br = 1 + 0.015*Math.sin(t*5);
  ctx.save(); ctx.translate(W/2 + from*(1 - Math.min(a, 1)) + to*out, y); ctx.rotate(Math.sin(t*4)*sway); ctx.scale(a*br, a/br);
  ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 18; ctx.drawImage(img, -w/2, -h, w, h); ctx.restore();
}
function overlay(t){
  // ---- intro : le lion rugit
  beast(PH.lionO, t, 0, 1.25, {h:700, y:1500, to:-1150});
  // ---- accroche (sans sous-titres) : SINGA + PURA
  const hA = 1 - prog(t, Ed("s01") + 0.15, Ed("s01") + 0.4);
  if (t > S("s01") && hA > 0){
    kin("SINGAPOUR", W/2, 470, t, S("s01") + 0.25, {size:150, out:T_SINGA - 0.15});
    const a = EB(prog(t, T_SINGA, T_SINGA + 0.3)), b = EB(prog(t, T_PURA, T_PURA + 0.3)), e = EB(prog(t, T_EQ, T_EQ + 0.3));
    if (a > 0){ txt("SINGA", W/2 - 190, 450, {size:120, color:Y1, scale:a, alpha:Math.min(a, 1)*hA, stroke:16, glow:"rgba(255,214,10,.45)"}); txt("LION", W/2 - 190, 570, {size:80, scale:a, alpha:Math.min(a, 1)*hA, stroke:13}); }
    if (b > 0){ txt("PURA", W/2 + 200, 450, {size:120, color:Y1, scale:b, alpha:Math.min(b, 1)*hA, stroke:16, glow:"rgba(255,214,10,.45)"}); txt("VILLE", W/2 + 200, 570, {size:80, scale:b, alpha:Math.min(b, 1)*hA, stroke:13}); }
  }
  // ---- « 0 lion »
  const zA = EB(prog(t, T_ZERO, T_ZERO + 0.3))*(1 - prog(t, Ed("s02") + 0.1, Ed("s02") + 0.35));
  if (zA > 0){ txt("0", W/2, 560, {size:330, color:RED, scale:zA, alpha:Math.min(zA, 1), stroke:26, glow:"rgba(255,59,48,.5)"});
    txt("LION", W/2, 760, {size:120, scale:zA, alpha:Math.min(zA, 1), stroke:16}); }
  const sil = prog(t, S("s02") + 0.1, S("s02") + 0.4)*(1 - prog(t, Ed("s02") + 0.05, Ed("s02") + 0.3));
  if (sil > 0){ silhouette(PH.lionS, W/2, 1500, 560, EB(clamp(sil*1.2)), 0.85);
    const c = E(prog(t, T_ZERO, T_ZERO + 0.35)); if (c > 0) cross(W/2, 1230, 330, c, sil); }
  // ---- le fauve mystère, puis « c'est un lion ! »
  const fA = prog(t, T_FAUVE, T_FAUVE + 0.35)*(1 - prog(t, Ed("s04") + 0.1, Ed("s04") + 0.45));
  if (fA > 0){ const rv = prog(t, T_REVEAL - 0.05, T_REVEAL + 0.3), sc = EB(clamp(fA*1.1));
    silhouette(PH.lionS, W/2, 1500, 600, sc, 1 - rv);
    if (rv > 0){ ctx.save(); ctx.globalAlpha = rv; beastAt(PH.lionO, W/2, 1500, 600, sc*(1 + 0.12*Math.sin(Math.PI*rv))); ctx.restore(); }
    const q = 1 - rv; if (q > 0) txt("?", W/2 + 230 + Math.sin(t*6)*8, 820, {size:200, color:Y1, scale:sc, alpha:q*Math.min(fA, 1), stroke:20, glow:"rgba(255,214,10,.5)"}); }
  // ---- en fait… un tigre
  const tA = prog(t, S("s06") + 0.45, S("s06") + 0.8)*(1 - prog(t, Ed("s06") + 0.2, Ed("s06") + 0.55));
  if (tA > 0){ const k = E(prog(t, T_TIGRE - 0.35, T_TIGRE + 0.15)), sc = EB(clamp(tA*1.1));
    ctx.save(); ctx.translate(W/2, 1500); ctx.scale(sc, sc);
    const h = 620, w = h*PH.lionO.width/PH.lionO.height;
    ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 18; ctx.drawImage(PH.lionO, -w/2, -h, w, h); ctx.shadowColor = "transparent";
    if (k > 0){ const xw = -w/2 + (w + 40)*k; ctx.save(); ctx.beginPath(); ctx.rect(-w/2 - 20, -h - 20, xw + w/2 + 20, h + 40); ctx.clip(); ctx.drawImage(PH.tiger, -w/2, -h, w, h); ctx.restore();
      if (k < 1){ ctx.fillStyle = "rgba(255,255,255,.9)"; ctx.shadowColor = "#fff"; ctx.shadowBlur = 30; ctx.fillRect(xw - 4, -h - 20, 8, h + 40); } }
    ctx.restore(); }
  // ---- aujourd'hui : le lion revient, fier
  beast(PH.roar, t, T_MER + 0.55, DUR - 1.3, {h:430, y:1560, from:1100, to:1100, sway:0.01});
  // ---- frise des années
  const yv = yearAt(t), ya = yv === null ? 0 : Math.max(prog(t, S("s04"), S("s04") + 0.2)*(1 - prog(t, M("s04", 0.25), M("s04", 0.35))), prog(t, S("s07"), S("s07") + 0.2)*(1 - prog(t, M("s07", 0.6), M("s07", 0.7))));
  if (ya > 0){ const base = Math.round(yv);
    for (let j = -1; j <= 1; j++){ const v = base + j, x = W/2 + (v - yv)*300; if (x < MARGIN || x > W - MARGIN) continue; const act = clamp(1 - Math.abs(v - yv));
      txt(String(v), x, 470, {size:56 + act*70, color:act > 0.5 ? Y1 : "#fff", alpha:Math.min(ya, 1)*(0.35 + 0.65*act)*clamp(Math.min(x - MARGIN, W - MARGIN - x)/80), stroke:10, glow:act > 0.5 ? "rgba(255,214,10,.45)" : null}); } }
  // ---- appel final
  if (t > S("s08") - 0.1){
    const a = EB(prog(t, T_CTA1, T_CTA1 + 0.35)); txt("TU LE SAVAIS ?", W/2, 520, {size:fit("TU LE SAVAIS ?", 130, W - 2*MARGIN), color:Y1, scale:a, alpha:Math.min(a, 1), stroke:18, glow:"rgba(255,214,10,.45)"});
    const b = EB(prog(t, T_CTA2, T_CTA2 + 0.35)); txt("DIS-LE EN COMMENTAIRE", W/2, 660, {size:fit("DIS-LE EN COMMENTAIRE", 80, W - 2*MARGIN), scale:b, alpha:Math.min(b, 1), stroke:13}); }
  // ---- sous-titres
  let cur = null; for (const g of CAPS) if (g.s <= t) cur = g;
  if (cur && t <= cur.e + 0.25){ const a = EB(prog(t, cur.s, cur.s + 0.15));
    const segs = cur.g.map((w, i) => ({t:(i ? " " : "") + w.w.replace(/[.,]+$/, "").toUpperCase(), c:w.hi ? Y1 : "#fff"}));
    richLine(segs, W/2, 300, {size:84, scale:0.8 + 0.2*a, alpha:Math.min(a*2, 1), stroke:16}); }
}
function beastAt(img, x, y, h, s){ const w = h*img.width/img.height; ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 18; ctx.drawImage(img, -w/2, -h, w, h); ctx.restore(); }
function silhouette(img, x, y, h, s, a){ if (!img || a <= 0 || s <= 0) return; const w = h*img.width/img.height;
  ctx.save(); ctx.globalAlpha = Math.min(a, 1); ctx.translate(x, y); ctx.scale(s, s); ctx.shadowColor = "rgba(255,214,10,.55)"; ctx.shadowBlur = 50; ctx.drawImage(img, -w/2, -h, w, h); ctx.restore(); }
function cross(x, y, r, k, a){ ctx.save(); ctx.globalAlpha = Math.min(a, 1); ctx.strokeStyle = RED; ctx.lineCap = "round"; ctx.lineWidth = 34; ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 20;
  const k1 = clamp(k*2), k2 = clamp(k*2 - 1); ctx.beginPath(); ctx.moveTo(x - r, y - r); ctx.lineTo(x - r + 2*r*k1, y - r + 2*r*k1); ctx.stroke();
  if (k2 > 0){ ctx.beginPath(); ctx.moveTo(x + r, y - r); ctx.lineTo(x + r - 2*r*k2, y - r + 2*r*k2); ctx.stroke(); } ctx.restore(); }
// variantes du lion : silhouette noire, version « tigre » (pelage orangé + rayures)
function tint(img, f){ const c = document.createElement("canvas"); c.width = img.width; c.height = img.height; const g = c.getContext("2d"); g.drawImage(img, 0, 0); f(g, c.width, c.height); return c; }
const toSil = img => tint(img, (g, w, h) => { g.globalCompositeOperation = "source-in"; g.fillStyle = "#06090d"; g.fillRect(0, 0, w, h); });
const toTiger = img => tint(img, (g, w, h) => {
  g.globalCompositeOperation = "source-atop"; g.globalAlpha = 0.55; g.fillStyle = "#ff7b00"; g.fillRect(0, 0, w, h); g.globalAlpha = 1;
  const rnd = d3.randomLcg(7); g.fillStyle = "rgba(15,10,5,.85)";
  for (let i = 0; i < 26; i++){ const x = w*(0.22 + 0.7*i/26) + (rnd() - 0.5)*w*0.02, y0 = h*(0.25 + rnd()*0.1), len = h*(0.18 + rnd()*0.22), th = w*(0.008 + rnd()*0.01), sk = (rnd() - 0.5)*w*0.05;
    g.beginPath(); g.moveTo(x - th, y0); g.quadraticCurveTo(x + sk, y0 + len/2, x - th*0.3, y0 + len); g.lineTo(x + th*0.3, y0 + len); g.quadraticCurveTo(x + sk + th*2, y0 + len/2, x + th, y0); g.fill(); }
});
window.ready = Promise.all([fetch("geo.json").then(r => r.json()).then(j => { GEO = j; setup(); }),
  ...["sg", "in"].map(f => load(f, `flags/${f}.svg`)),
  img("lion", "assets/lion.png"), img("roar", "assets/lion_rugit.png"),
  document.fonts.load("900 60px M"), document.fonts.load("800 60px M")]).then(() => { PH.lionO = outlined(PH.lion); PH.lionS = toSil(PH.lion); PH.tiger = toTiger(outlined(PH.lion)); return true; });
