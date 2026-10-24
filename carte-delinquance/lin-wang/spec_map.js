// ------------------------------------------------------------------ données
let BB = [], CANDLES = [];
function setup(){
  BB = GEO.b.map(r => [d3.min(r, p => p[0]), d3.min(r, p => p[1]), d3.max(r, p => p[0]), d3.max(r, p => p[1])]);
  const ring = GEO.c.TWN.reduce((a, b) => a.length > b.length ? a : b), rnd = d3.randomLcg(4);
  while (CANDLES.length < 40){ const p = [120.1 + rnd()*1.9, 22.0 + rnd()*3.3]; if (d3.polygonContains(ring, p)) CANDLES.push({p, t: S("l17") + rnd()*1.6}); }
}
function vehicle(img, pts, k, h, a){ if (!img || a <= 0) return; const e = P(...along(pts, k)), b = P(...along(pts, Math.min(1, k + 0.02))), w = h*img.width/img.height, flip = b[0] < e[0] - 0.5 ? -1 : 1;
  ctx.save(); ctx.globalAlpha = Math.min(a, 1); ctx.translate(e[0], e[1] - h*0.3); ctx.scale(flip*a, a); ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 24; ctx.shadowOffsetY = 10;
  ctx.drawImage(img, -w/2, -h/2, w, h); ctx.restore(); return e; }
function city(p, a, t, color=Y1, r=18){ if (a <= 0) return; const [x, y] = P(...p); pulse(x, y, t, a, color, 120); pin(x, y, EB(clamp(a*1.4)), color, r); }
function glow(rings, a){ if (a <= 0) return; ctx.save(); path(rings); ctx.fillStyle = `rgba(255,214,10,${0.16*a})`; ctx.fill(); ctx.lineJoin = "round"; ctx.lineWidth = 5; ctx.strokeStyle = `rgba(255,255,255,${0.85*a})`; ctx.stroke(); ctx.restore(); }
function renderMap(t){
  CAM = camera(t);
  ctx.fillStyle = "#0b1622"; ctx.fillRect(-60, -60, W + 120, H + 120);
  drawTiles();
  ctx.save(); ctx.strokeStyle = "rgba(255,255,255,.3)"; ctx.lineWidth = 1.5; ctx.lineJoin = "round";
  GEO.b.forEach((r, i) => { if (inView(BB[i])){ path([r]); ctx.stroke(); } }); ctx.restore();
  // ---- drapeaux
  flagFill("TWN", "tw", EO(prog(t, 2.0, 2.6))*(1 - prog(t, S("l03") + 0.2, S("l03") + 0.6)) + EO(prog(t, T_TW - 0.1, T_TW + 0.4))*(1 - prog(t, S("l13") + 0.2, S("l13") + 0.6)) + EO(prog(t, S("l16") + 0.5, S("l16") + 1.0)));
  flagFill("MMR", "mm", EO(prog(t, S("l04") + 0.5, S("l04") + 1.0))*(1 - prog(t, M("l05", 0.3), M("l05", 0.4))));
  flagFill("JPN", "jp", EO(prog(t, M("l05", 0.38), M("l05", 0.5)))*(1 - prog(t, S("l06") + 0.1, S("l06") + 0.5)));
  glow(GEO.c.CHN, prog(t, M("l08", 0.4), M("l08", 0.6))*(1 - prog(t, CL.a, CL.a + 0.3)));
  // ---- tout le voyage (titre)
  const jA = prog(t, S("l03") + 0.3, S("l03") + 0.5)*(1 - prog(t, S("l04") - 0.1, S("l04") + 0.3));
  if (jA > 0){ lineLL(upto(JOURNEY, E(prog(t, S("l03") + 0.4, T_TITLE + 0.3))), jA, Y1, 7, [18, 12]); city(MYIT, jA, t, "#fff", 14); city(TAIPEI, jA*prog(t, T_TITLE, T_TITLE + 0.3), t); }
  // ---- jungle birmane / armée japonaise / attaque chinoise
  city(HUKAWNG, prog(t, S("l04") + 0.7, S("l04") + 1.0)*(1 - prog(t, M("l05", 0.3), M("l05", 0.4))), t);
  const jpA = prog(t, M("l05", 0.42), M("l05", 0.5))*(1 - prog(t, S("l06"), S("l06") + 0.4));
  if (jpA > 0) arrow(R_JAPAN, E(prog(t, M("l05", 0.45), M("l05", 0.85))), jpA, RED, 10);
  const atA = prog(t, S("l06") + 0.3, S("l06") + 0.6)*(1 - prog(t, Ed("l07"), Ed("l07") + 0.4));
  if (atA > 0){ arrow(R_ATTACK, E(prog(t, S("l06") + 0.5, M("l06", 0.55))), atA, Y1, 11); city(MYIT, atA*prog(t, M("l06", 0.5), M("l06", 0.6)), t, RED, 16); }
  // ---- la marche jusqu'à Canton
  const mA = prog(t, M("l08", 0.05), M("l08", 0.15))*(1 - prog(t, M("l11", 0.3), M("l11", 0.5)));
  if (mA > 0){ const k = marchK(t), pts = upto(R_MARCH, k); lineLL(pts, mA, Y1, 9, [16, 10]); const [x, y] = P(...along(R_MARCH, k)); pulse(x, y, t, mA*(k < 1 ? 1 : 0), Y1, 70); pin(x, y, mA, Y1, 15);
    city(CANTON, mA*prog(t, M("l10", 0.6), M("l10", 0.7)), t); }
  // ---- le bateau vers Taïwan
  const sA = prog(t, SHIP[0] - 0.3, SHIP[0])*(1 - prog(t, S("l12") + 0.4, S("l12") + 0.9));
  if (sA > 0){ const k = E(prog(t, ...SHIP)); lineLL(upto(R_SHIP, k), sA, "#fff", 7, [18, 14]); vehicle(PH.ship, R_SHIP, k, 110, sA*(1 - prog(t, SHIP[1] + 0.2, SHIP[1] + 0.6))); city(KAOH, sA*prog(t, SHIP[1] - 0.1, SHIP[1]), t); }
  // ---- zoo de Taipei, parade de 1986
  city(TAIPEI, prog(t, S("l13") + 0.5, S("l13") + 0.8)*(1 - prog(t, S("l15") + 0.2, S("l15") + 0.5)), t);
  const pA = prog(t, S("l15") + 0.4, S("l15") + 0.7)*(1 - prog(t, Ed("l15"), Ed("l15") + 0.4));
  if (pA > 0){ const k = E(prog(t, S("l15") + 0.6, Ed("l15") - 0.3)); lineLL(upto(R_PARADE, k), pA, Y1, 10, [14, 10]);
    const e = along(R_PARADE, k); city(e, pA, t, RED, 16);
    for (let i = 0; i < 14; i++){ const q = i/13, pp = along(R_PARADE, q), [x, y] = P(pp[0] + (i % 2 ? 0.006 : -0.006), pp[1]); if (q > k + 0.02) continue; ctx.save(); ctx.globalAlpha = pA*0.9; ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(x, y, 6, 0, 7); ctx.fill(); ctx.restore(); } }
  // ---- 2003 : hommage dans tout Taïwan
  const cA = prog(t, S("l17"), S("l17") + 0.3)*(1 - prog(t, S("l18") + 0.5, S("l18") + 1.0));
  if (cA > 0) CANDLES.forEach(c => { const a = EB(prog(t, c.t, c.t + 0.3))*cA; if (a <= 0) return; const [x, y] = P(...c.p); pulse(x, y, t + c.t, a*0.6, Y1, 50); pin(x, y, a, Y1, 8); });
  const vg = ctx.createRadialGradient(W/2, H/2, H*0.45, W/2, H/2, H*0.85); vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, `rgba(0,0,0,${0.32 + 0.25*prog(t, S("l16"), S("l16") + 0.6)})`); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  const tg = ctx.createLinearGradient(0, 0, 0, 560); tg.addColorStop(0, "rgba(0,0,0,.38)"); tg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 560);
}
