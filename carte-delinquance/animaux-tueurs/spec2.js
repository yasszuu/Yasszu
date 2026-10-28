// ------------------------------------------------------------------ carte
let BB = [];
function setup(){ BB = GEO.b.map(r => [d3.min(r, p => p[0]), d3.min(r, p => p[1]), d3.max(r, p => p[0]), d3.max(r, p => p[1])]); }
function zone(rings, a, color=[255, 59, 48]){ if (a <= 0) return; ctx.save(); path(rings); ctx.fillStyle = `rgba(${color},${0.5*Math.min(a, 1)})`; ctx.fill();
  ctx.lineJoin = "round"; ctx.strokeStyle = `rgba(255,255,255,${0.6*Math.min(a, 1)})`; ctx.lineWidth = 2; ctx.stroke(); ctx.restore(); }
function hot(p, a, t, color=RED, r=16, max=120){ if (a <= 0) return; const [x, y] = P(...p); pulse(x, y, t, a, color, max); pin(x, y, EB(clamp(a*1.3)), color, r); }
function renderMap(t){
  CAM = camera(t);
  ctx.fillStyle = "#0b1622"; ctx.fillRect(-60, -60, W + 120, H + 120);
  drawTiles();
  ctx.save(); ctx.strokeStyle = "rgba(255,255,255,.3)"; ctx.lineWidth = 1.5; ctx.lineJoin = "round";
  GEO.b.forEach((r, i) => { if (inView(BB[i])){ path([r]); ctx.stroke(); } }); ctx.restore();
  // ---- accroche : les 5 foyers s'allument
  const hA = 1 - prog(t, Ed("t1"), Ed("t1") + 0.5);
  HOT.forEach((p, i) => hot(p, prog(t, S("t1") + 0.4 + i*0.35, S("t1") + 0.7 + i*0.35)*hA, t + i*0.3, RED, 12, 90));
  // ---- N°5 loup : Inde, Uttar Pradesh
  flagFill("IND", "in", EO(prog(t, M("t2", 0.72), M("t2", 0.9)))*(1 - prog(t, S("t3") + 0.9, S("t3") + 1.3)));
  hot(UP, prog(t, Ed("t2") - 0.2, Ed("t2") + 0.1)*(1 - prog(t, S("t3") + 0.9, S("t3") + 1.3)), t);
  // ---- N°4 lion : Tanzanie
  flagFill("TZA", "tz", EO(prog(t, M("t3", 0.78), M("t3", 0.95)))*(1 - prog(t, S("t4") + 0.9, S("t4") + 1.3)));
  [[35.5, -3.5], [38.5, -10.5], [33.5, -8], [36.8, -7.5]].forEach((p, i) => hot(p, prog(t, M("t3", 0.88) + i*0.15, M("t3", 0.95) + i*0.15)*(1 - prog(t, S("t4") + 0.9, S("t4") + 1.3)), t + i*0.2, RED, 11, 70));
  // ---- N°3 hippo : lacs et fleuves d'Afrique
  LAKES.forEach((p, i) => { const t0 = POPS_L[i % POPS_L.length] + Math.floor(i/POPS_L.length)*0.12 || M("t4", 0.65); hot(p, prog(t, t0 - 0.05, t0 + 0.15)*(1 - prog(t, S("t5") + 0.9, S("t5") + 1.3)), t + i*0.25, "#3ec9ff", 13, 90); });
  // ---- N°2 chien : Afrique puis Inde (1 sur 3)
  zone(GEO.ssa, prog(t, T_59 - 0.2, T_59 + 0.3)*(1 - prog(t, S("t6") + 0.9, S("t6") + 1.3))*0.7);
  flagFill("IND", "in", EO(prog(t, T_IND2 - 0.1, T_IND2 + 0.4))*(1 - prog(t, S("t6") + 0.9, S("t6") + 1.3)));
  // ---- N°1 moustique : toute l'Afrique subsaharienne, Nigeria en tête
  const ssa = prog(t, M("t6", 0.6), M("t6", 0.75));
  zone(GEO.ssa, ssa*(0.85 + 0.15*Math.sin(t*6)));
  flagFill("NGA", "ng", EO(prog(t, T_NG - 0.1, T_NG + 0.4)));
  hot(NG, prog(t, T_NG, T_NG + 0.2), t, Y1, 16, 160);
  const red = prog(t, T_700 - 0.1, T_700 + 0.2)*(1 - prog(t, S("t7"), S("t7") + 0.6));
  if (red > 0){ ctx.fillStyle = `rgba(200,0,0,${0.18*red})`; ctx.fillRect(-60, -60, W + 120, H + 120); }
  const vg = ctx.createRadialGradient(W/2, H/2, H*0.45, W/2, H/2, H*0.85); vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,.32)"); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  const tg = ctx.createLinearGradient(0, 0, 0, 760); tg.addColorStop(0, "rgba(0,0,0,.42)"); tg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 760);
}
// ------------------------------------------------------------------ rendu
const HITS = TL.sfx.filter(s => s.name === "impact").map(s => [s.t, 0.06, 10]);
HITS.push(...ENT.map(k => [T_CRY(k) + 0.05, 0.04, 6]));
let PH = {};
function render(t){
  let p = 0, sx = 0, sy = 0;
  for (const [ti, amp, sh] of HITS) if (t >= ti){ const d = t - ti; p += amp*Math.exp(-d*8); sx += sh*Math.exp(-d*7)*Math.sin(d*50); sy += sh*0.7*Math.exp(-d*7)*Math.cos(d*43); }
  ctx.save(); ctx.translate(W/2 + sx, H/2 + sy); ctx.scale(1.04 + p, 1.04 + p); ctx.translate(-W/2, -H/2);
  renderMap(t); motionBlur(t);
  overlay(t);
  ctx.restore();
  const fl = Math.exp(-t*7); if (fl > 0.02){ ctx.fillStyle = `rgba(255,255,255,${0.6*fl})`; ctx.fillRect(0, 0, W, H); }
}
function counter(n, t, t0, t1, y, o={}){ const a = EB(prog(t, t0, t0 + 0.2))*(1 - prog(t, t1, t1 + 0.25)); if (a <= 0) return;
  txt(n, W/2, y, {size:fit(n, o.size || 190, W - 2*MARGIN), color:o.color || Y1, scale:a, alpha:Math.min(a, 1), stroke:22, glow:o.glow || "rgba(255,214,10,.45)"}); }
const fmt = n => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
const NAMES = {t2: ["N°5", "LE LOUP", "loup"], t3: ["N°4", "LE LION", "lion"], t4: ["N°3", "L'HIPPOPOTAME", "hippo"], t5: ["N°2", "LE CHIEN", "chien"], t6: ["N°1", "LE MOUSTIQUE", "moustique"]};
function animal(img, t, t0, t1, h){
  if (!img) return; const a = EB(prog(t, t0, t0 + 0.35)), out = E(prog(t, t1, t1 + 0.35)); if (a <= 0 || out >= 1) return;
  const w = h*img.width/img.height, sh = Math.exp(-Math.max(0, t - t0 - 0.05)*5)*Math.sin((t - t0)*55)*8;
  ctx.save(); ctx.globalAlpha = 1 - out; ctx.translate(W/2 + sh, 1360 + out*260); ctx.scale(a*(1 - 0.25*out), a*(1 - 0.25*out));
  ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 18; ctx.drawImage(img, -w/2, -h, w, h); ctx.restore();
}
function overlay(t){
  // ---- accroche
  kin("QUEL ANIMAL", W/2, 460, t, S("t1") + 0.05, {size:120, out:T_OU - 0.2}); kin("TUE LE PLUS", W/2, 590, t, M("t1", 0.2), {size:120, color:Y1, out:T_OU - 0.2});
  kin("D'HUMAINS ?", W/2, 720, t, M("t1", 0.38), {size:120, out:T_OU - 0.2});
  kin("ET OÙ ?", W/2, 590, t, T_OU, {size:190, color:Y1, out:Ed("t1") + 0.4});
  // ---- les 5 animaux
  for (const k of ENT){ const [rk, nm, im] = NAMES[k], t0 = T_CRY(k), t1 = S(k) + 1.5;
    animal(PH[im], t, t0, t1, im === "moustique" ? 520 : 600);
    kin(rk, W/2, 440, t, t0, {size:190, color:Y1, out:t1 + 0.1}); kin(nm, W/2, 600, t, t0 + 0.2, {size:120, out:t1 + 0.1}); }
  kin("QUELQUES", W/2, 560, t, M("t2", 0.42), {size:120, out:Ed("t2") + 0.3}); kin("VICTIMES", W/2, 700, t, M("t2", 0.5), {size:130, color:Y1, out:Ed("t2") + 0.3});
  const cnt = (v, t0, t1, mx, o={}) => { if (t < t0) return; if (t < t0 + 0.6) counter("≈ " + fmt(lerp(0, mx, E(prog(t, t0 - 0.05, t0 + 0.55)))), t, t0 - 0.05, t1, 600, o); else counter(v, t, t0 + 0.55, t1, 600, o);
    kin("MORTS / AN", W/2, 760, t, t0 + 0.3, {size:96, out:t1}); };
  cnt("≈ 200", T_200 - 0.55, Ed("t3") + 0.3, 200);
  cnt("≈ 500", T_500 - 0.55, Ed("t4") + 0.3, 500);
  cnt("≈ 59 000", T_59 - 0.55, M("t5", 0.84), 59000, {size:170});
  kin("1 SUR 3", W/2, 600, t, T_IND2, {size:170, color:Y1, out:Ed("t5") + 0.3});
  cnt("+ 700 000", T_700 - 0.55, M("t6", 0.84), 700000, {size:180, color:RED, glow:"rgba(255,59,48,.55)"});
  kin("EN TÊTE", W/2, 600, t, T_NG, {size:150, color:Y1, out:Ed("t6") + 0.3});
  kin("TU L'AURAIS", W/2, 520, t, S("t7"), {size:120}); kin("DEVINÉ ?", W/2, 660, t, S("t7") + 0.2, {size:150, color:Y1});
}
