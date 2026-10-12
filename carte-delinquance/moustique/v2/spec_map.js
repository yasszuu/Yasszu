// ------------------------------------------------------------------ données
let BB = [], YEARS = {}, EXPT = {}, ORD_H = [], CHIK = [];
function setup(){
  BB = GEO.b.map(r => [d3.min(r, p => p[0]), d3.min(r, p => p[1]), d3.max(r, p => p[0]), d3.max(r, p => p[1])]);
  YEARS = Object.fromEntries(Object.entries(DEPY).filter(([, y]) => y));
  ORD_H = Object.keys(YEARS).sort((a, b) => YEARS[a] - YEARS[b]);
  for (const c of ORD_H){ if (c === "06"){ EXPT[c] = T_MENT2; continue; }
    for (let t = S("m13"); t < Ed("m16"); t += 0.01){ const y = yearAt(t); if (y !== null && y >= YEARS[c] - 0.001){ EXPT[c] = t; break; } } }
  const rnd = d3.randomLcg(5), south = Object.keys(YEARS).filter(c => { const r = GEO.d[c][0]; return d3.mean(r, p => p[1]) < 45.6; });
  for (let i = 0; i < 70; i++){ const c = south[Math.floor(rnd()*south.length)], r = GEO.d[c].reduce((a, b) => a.length > b.length ? a : b);
    const [x0, x1] = d3.extent(r, p => p[0]), [y0, y1] = d3.extent(r, p => p[1]); let p;
    for (let k = 0; k < 30; k++){ p = [lerp(x0, x1, rnd()), lerp(y0, y1, rnd())]; if (d3.polygonContains(r, p)) break; }
    CHIK.push({p, t:(POPS_CHIK[i % POPS_CHIK.length] || M("m19", 0.4)) + Math.floor(i/POPS_CHIK.length)*0.07}); }
}
function depFill(code, a, flash=0, color=MOS){ if (a <= 0) return; const rings = GEO.d[code]; if (!rings) return;
  const [r, g, b] = color.map(c => Math.round(lerp(c, 255, flash)));
  ctx.save(); path(rings); ctx.fillStyle = `rgba(${r},${g},${b},${0.7*Math.min(a, 1)})`; ctx.fill();
  ctx.lineJoin = "round"; ctx.strokeStyle = `rgba(255,255,255,${0.75*Math.min(a, 1)})`; ctx.lineWidth = 2.2; ctx.stroke(); ctx.restore(); }
// véhicule (PNG) en tête d'itinéraire, retourné selon le sens de la marche
function vehicle(img, pts, k, h, a){ if (!img || a <= 0) return; const e = P(...along(pts, k)), b = P(...along(pts, Math.min(1, k + 0.02))), w = h*img.width/img.height, flip = b[0] < e[0] - 0.5 ? -1 : 1;
  ctx.save(); ctx.globalAlpha = Math.min(a, 1); ctx.translate(e[0], e[1] - h*0.35); ctx.scale(flip*a, a); ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 24; ctx.shadowOffsetY = 10;
  ctx.drawImage(img, -w/2, -h/2, w, h); ctx.restore(); }
function renderMap(t){
  CAM = camera(t);
  ctx.fillStyle = "#0b1622"; ctx.fillRect(-60, -60, W + 120, H + 120);
  drawTiles();
  ctx.save(); ctx.strokeStyle = "rgba(255,255,255,.3)"; ctx.lineWidth = 1.5; ctx.lineJoin = "round";
  GEO.b.forEach((r, i) => { if (inView(BB[i])){ path([r]); ctx.stroke(); } }); ctx.restore();
  const depLines = prog(t, 1.2, 1.6)*(1 - prog(t, S("m04") - 0.2, S("m04") + 0.4)) + prog(t, S("m12"), S("m12") + 0.4);
  if (depLines > 0){ ctx.save(); ctx.globalAlpha = 0.22*Math.min(depLines, 1); ctx.strokeStyle = "#fff"; ctx.lineWidth = 1.2; for (const r of Object.values(GEO.d)){ path(r); ctx.stroke(); } ctx.restore(); }
  // ---- drapeaux
  flagFill("FRA", "fr", EO(prog(t, 1.4, 1.95))*(1 - prog(t, M("m01", 0.45), M("m01", 0.58))) + EO(prog(t, S("m12") + 0.4, S("m12") + 0.9))*(1 - prog(t, S("m13") - 0.1, S("m13") + 0.4)));
  flagFill("ALB", "al", EO(prog(t, T_ALB - 0.1, T_ALB + 0.4))*(1 - prog(t, S("m09"), S("m09") + 0.5)));
  flagFill("USA", "us", EO(prog(t, T_USA - 0.1, T_USA + 0.4))*(1 - prog(t, S("m10") + 0.2, S("m10") + 0.7)));
  flagFill("ITA", "it", EO(prog(t, T_ITA - 0.1, T_ITA + 0.4))*(1 - prog(t, M("m11", 0.3), M("m11", 0.5))));
  // ---- Menton (accroche)
  const m1 = prog(t, T_MENT - 0.1, T_MENT)*(1 - prog(t, S("m02"), S("m02") + 0.3));
  if (m1 > 0){ const [x, y] = P(...MENTON); pulse(x, y, t, m1, Y1, 140); pin(x, y, EB(prog(t, T_MENT, T_MENT + 0.3))*m1, Y1, 20); label("MENTON", x, y - 82, {size:60, alpha:m1, stroke:12}); }
  // ---- 80 départements (accroche) : ils s'allument dans l'ordre
  const h2 = 1 - prog(t, S("m03") + 0.2, S("m03") + 0.6);
  ORD_H.forEach((c, i) => { const ti = S("m02") + 0.7 + i*1.7/ORD_H.length; depFill(c, EO(prog(t, ti, ti + 0.15))*h2, 1 - prog(t, ti, ti + 0.3)); });
  // ---- Asie du Sud-Est : le foyer d'origine
  const asA = prog(t, S("m04") + 0.6, S("m04") + 1.0)*(1 - prog(t, M("m07", 0.55), M("m07", 0.65)));
  if (asA > 0){ const [x, y] = P(...SEA); const R = 150*(1 + 0.05*Math.sin(t*4));
    ctx.save(); ctx.globalAlpha = 0.9*asA; ctx.setLineDash([22, 14]); ctx.lineDashOffset = -t*40; ctx.strokeStyle = Y1; ctx.lineWidth = 7; ctx.beginPath(); ctx.arc(x, y, R*EB(prog(t, T_ASIA - 0.3, T_ASIA + 0.2)), 0, 7); ctx.stroke(); ctx.restore();
    pulse(x, y, t, asA*prog(t, T_ASIA - 0.1, T_ASIA), MOS.length ? RED : Y1, 120); pin(x, y, EB(prog(t, T_ASIA, T_ASIA + 0.3))*asA, RED, 18); }
  // ---- routes maritimes du monde
  const lnA = prog(t, M("m07", 0.48), M("m07", 0.6))*(1 - prog(t, S("m08"), S("m08") + 0.5));
  if (lnA > 0) LANES.forEach((d, i) => { const t0 = POPS_LANES[i] || M("m07", 0.6); flight(SING, d, E(prog(t, t0 - 0.2, t0 + 1.0)), lnA, i % 2 ? "#fff" : Y1, 6, 0.15); });
  // ---- les trois traversées
  ROUTES.forEach(([pts, a, b], i) => { const A = prog(t, a - 0.3, a)*(1 - prog(t, b + 1.0, b + 1.6)); if (A <= 0) return; const k = E(prog(t, a, b));
    lineLL(upto(pts, k), A, "#fff", 7, [18, 14]); const [x0, y0] = P(...pts[0]); pin(x0, y0, A, "#fff", 12);
    const e = P(...along(pts, k)); pulse(e[0], e[1], t, A*(k < 1 ? 1 : 0), Y1, 70); vehicle(PH.cargo, pts, k, 120, A*(1 - prog(t, b, b + 0.4))); });
  // ---- la côte ligure jusqu'à Menton
  const coA = prog(t, S("m11"), S("m11") + 0.3)*(1 - prog(t, S("m12") - 0.2, S("m12") + 0.2));
  if (coA > 0){ const k = E(prog(t, S("m11") + 0.3, M("m11", 0.78))); lineLL(upto(COAST, k), coA, Y1, 9); const [gx, gy] = P(...GENES); pin(gx, gy, coA, "#fff", 13);
    const [x, y] = P(...MENTON), a = EB(prog(t, T_MENT2, T_MENT2 + 0.3))*coA; pulse(x, y, t, a, Y1, 130); pin(x, y, a, Y1, 20); label("MENTON", x, y - 82, {size:60, alpha:prog(t, T_MENT2, T_MENT2 + 0.3)*coA, stroke:12}); }
  // ---- départements colonisés, année par année
  const dA = 1 - prog(t, S("m21") + 2, S("m21") + 2.5);
  for (const [c, tc] of Object.entries(EXPT)) if (t > tc) depFill(c, EO(prog(t, tc, tc + 0.25))*dA, 1 - prog(t, tc, tc + 0.4) + 0.4*Math.exp(-Math.max(0, t - T_81)*4)*(t > T_81 ? 1 : 0));
  // ---- le camion remonte la vallée du Rhône
  const trA = prog(t, S("m13") + 0.3, S("m13") + 0.6)*(1 - prog(t, Ed("m13"), Ed("m13") + 0.4));
  if (trA > 0){ const k = E(prog(t, S("m13") + 0.5, M("m13", 0.92))); lineLL(upto(RHONE, k), trA, Y1, 8, [16, 12]); vehicle(PH.truck, RHONE, k, 130, trA); }
  // ---- Sud-Ouest, centre, Paris
  for (const [p, nm, t0, t1] of [[[0.4, 44.0], "SUD-OUEST", T_SW - 0.6, M("m14", 0.58)], [[2.6, 46.3], "CENTRE", M("m14", 0.66), Ed("m14") + 0.1], [PARIS, "PARIS", T_PAR - 0.3, Ed("m15") + 0.2]]){
    const a = prog(t, t0, t0 + 0.25)*(1 - prog(t, t1, t1 + 0.25)); if (a <= 0) continue; const [x, y] = P(...p);
    pulse(x, y, t, a, Y1, 130); pin(x, y, EB(prog(t, t0, t0 + 0.3))*a, Y1, 18); label(nm, x, y + 86, {size:60, alpha:a, stroke:12, scale:0.8 + 0.2*EB(prog(t, t0, t0 + 0.3))}); }
  // ---- foyers de chikungunya
  const chA = prog(t, S("m19"), S("m19") + 0.3)*(1 - prog(t, S("m20") + 0.3, S("m20") + 0.8));
  if (chA > 0) CHIK.forEach(({p, t: t0}) => { const [x, y] = P(...p), a = EB(prog(t, t0, t0 + 0.25))*chA; if (a <= 0) return; pulse(x, y, t + t0, a*0.6, "#ff2d55", 60); pin(x, y, a, "#ff2d55", 10); });
  // ---- froid : voile givré
  const fr = prog(t, T_FLOC - 0.1, T_FLOC + 0.3)*(1 - prog(t, Ed("m12") - 0.2, Ed("m12") + 0.3));
  if (fr > 0){ const g = ctx.createRadialGradient(W/2, H/2, H*0.25, W/2, H/2, H*0.75); g.addColorStop(0, "rgba(160,220,255,0)"); g.addColorStop(1, `rgba(170,225,255,${0.55*fr})`); ctx.fillStyle = g; ctx.fillRect(-60, -60, W + 120, H + 120); }
  const vg = ctx.createRadialGradient(W/2, H/2, H*0.45, W/2, H/2, H*0.85); vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,.32)"); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  const tg = ctx.createLinearGradient(0, 0, 0, 560); tg.addColorStop(0, "rgba(0,0,0,.38)"); tg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 560);
}
