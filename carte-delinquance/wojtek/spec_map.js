// ------------------------------------------------------------------ données
let BB = [], BLASTS = [];
function setup(){
  BB = GEO.b.map(r => [d3.min(r, p => p[0]), d3.min(r, p => p[1]), d3.max(r, p => p[0]), d3.max(r, p => p[1])]);
  const rnd = d3.randomLcg(3); for (let i = 0; i < 26; i++) BLASTS.push({p:[CASSINO[0] + (rnd() - 0.5)*0.5, CASSINO[1] + (rnd() - 0.5)*0.35], t:S("w12") + 0.4 + rnd()*(Ed("w12") - S("w12") + 0.3), r:50 + rnd()*70});
}
// bateau (PNG) en tête d'itinéraire, retourné selon le sens de la marche
function vehicle(img, pts, k, h, a){ if (!img || a <= 0) return; const e = P(...along(pts, k)), b = P(...along(pts, Math.min(1, k + 0.02))), w = h*img.width/img.height, flip = b[0] < e[0] - 0.5 ? -1 : 1;
  ctx.save(); ctx.globalAlpha = Math.min(a, 1); ctx.translate(e[0], e[1] - h*0.3); ctx.scale(flip*a, a); ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 24; ctx.shadowOffsetY = 10;
  ctx.drawImage(img, -w/2, -h/2, w, h); ctx.restore(); return e; }
function cross(x, y, a, s=34){ if (a <= 0) return; ctx.save(); ctx.globalAlpha = Math.min(a, 1); ctx.strokeStyle = RED; ctx.lineWidth = 14; ctx.lineCap = "round"; ctx.shadowColor = "rgba(0,0,0,.8)"; ctx.shadowBlur = 12;
  const k = EB(clamp(a)); ctx.beginPath(); ctx.moveTo(x - s*k, y - s*k); ctx.lineTo(x + s*k, y + s*k); ctx.moveTo(x + s*k, y - s*k); ctx.lineTo(x - s*k, y + s*k); ctx.stroke(); ctx.restore(); }
function city(p, name, a, t, color=Y1, below=true){ if (a <= 0) return; const [x, y] = P(...p); pulse(x, y, t, a, color, 120); pin(x, y, EB(clamp(a*1.4)), color, 18);
  if (name) label(name, x, y + (below ? 86 : -82), {size:58, alpha:Math.min(a, 1), stroke:12}); }
function renderMap(t){
  CAM = camera(t);
  ctx.fillStyle = "#0b1622"; ctx.fillRect(-60, -60, W + 120, H + 120);
  drawTiles();
  ctx.save(); ctx.strokeStyle = "rgba(255,255,255,.3)"; ctx.lineWidth = 1.5; ctx.lineJoin = "round";
  GEO.b.forEach((r, i) => { if (inView(BB[i])){ path([r]); ctx.stroke(); } }); ctx.restore();
  // ---- drapeaux
  flagFill("POL", "pl", EO(prog(t, T_POL - 0.1, T_POL + 0.45))*(1 - prog(t, S("w03") - 0.1, S("w03") + 0.4)) + EO(prog(t, POPS18[1] - 0.1, POPS18[1] + 0.4)));
  flagFill("IRN", "ir", EO(prog(t, T_IRAN - 0.1, T_IRAN + 0.45))*(1 - prog(t, M("w05", 0.2), M("w05", 0.4))));
  [["IRQ", "iq"], ["SYR", "sy"], [null, null], ["EGY", "eg"]].forEach(([id, fl], i) => { if (id) flagFill(id, fl, EO(prog(t, HITS9[i] - 0.15, HITS9[i] + 0.35))*(1 - prog(t, S("w10"), S("w10") + 0.5))); });
  const palA = prog(t, HITS9[2] - 0.15, HITS9[2] + 0.2)*(1 - prog(t, S("w10"), S("w10") + 0.5));
  if (palA > 0){ ctx.save(); path(GEO.c.PAL); ctx.fillStyle = `rgba(255,214,10,${0.35*palA})`; ctx.fill(); ctx.lineWidth = 4; ctx.strokeStyle = `rgba(255,255,255,${0.9*palA})`; ctx.stroke(); ctx.restore(); }
  flagFill("ITA", "it", EO(prog(t, M("w11", 0.55), M("w11", 0.8)))*(1 - prog(t, S("w12") + 0.2, S("w12") + 0.7)));
  flagFill("SCT", "gb-sct", EO(prog(t, T_SCOT - 0.1, T_SCOT + 0.45))*(1 - prog(t, S("w16") + 0.1, S("w16") + 0.5)) + EO(prog(t, POPS18[0] - 0.1, POPS18[0] + 0.4)));
  // ---- tout le voyage (titre)
  const jA = prog(t, S("w03") + 0.3, S("w03") + 0.5)*(1 - prog(t, S("w04") - 0.1, S("w04") + 0.3));
  if (jA > 0){ lineLL(upto(JOURNEY, E(prog(t, S("w03") + 0.4, T_TITLE + 0.2))), jA, Y1, 7, [18, 12]); city(TEHRAN, null, jA*0.8, t, "#fff"); city(EDIN, null, jA*prog(t, T_TITLE, T_TITLE + 0.3), t); }
  // ---- des camps soviétiques jusqu'à Téhéran, puis Hamadan
  const uA = prog(t, S("w05"), S("w05") + 0.3)*(1 - prog(t, M("w06", 0.9), Ed("w06") + 0.2));
  if (uA > 0){ arrow(R_USSR, E(prog(t, S("w05") + 0.3, M("w05", 0.85))), uA, "#fff", 9); arrow(R_HAM, E(prog(t, S("w06") - 0.2, T_HAM)), uA*prog(t, S("w06") - 0.3, S("w06")), Y1, 9); }
  city(HAMADAN, "HAMADAN", prog(t, T_HAM - 0.05, T_HAM + 0.2)*(1 - prog(t, S("w09") + 0.2, S("w09") + 0.5)), t);
  // ---- route terrestre jusqu'en Égypte
  const lA = prog(t, S("w09"), S("w09") + 0.3)*(1 - prog(t, M("w10", 0.3), M("w10", 0.5)));
  if (lA > 0){ const k = landK(t); lineLL(upto(R_LAND, k), lA, Y1, 9); const [x, y] = P(...along(R_LAND, k)); pulse(x, y, t, lA*(k < 1 ? 1 : 0), Y1, 70); pin(x, y, lA, Y1, 15); }
  // ---- bateau vers l'Italie (animaux interdits → enrôlé)
  const s1 = prog(t, SEA1[0] - 0.3, SEA1[0])*(1 - prog(t, S("w12"), S("w12") + 0.4));
  if (s1 > 0){ const k = E(prog(t, ...SEA1)); lineLL(upto(R_SEA1, k), s1, "#fff", 7, [18, 14]); const e = vehicle(PH.ship, R_SEA1, k, 110, s1);
    if (e) cross(e[0], e[1] - 40, prog(t, T_INTERD, T_INTERD + 0.25)*(1 - prog(t, T_SOLDAT - 0.4, T_SOLDAT - 0.1)), 48); }
  // ---- Mont-Cassin : explosions
  const cA = prog(t, S("w12") + 0.3, S("w12") + 0.6)*(1 - prog(t, Ed("w14"), Ed("w14") + 0.4));
  if (cA > 0){ for (const b of BLASTS){ const ph = (t - b.t)/0.9; if (ph < 0 || ph > 1) continue; const [x, y] = P(...b.p);
      ctx.save(); ctx.globalAlpha = (1 - ph)*cA; ctx.fillStyle = `rgba(255,${Math.round(160 - 120*ph)},40,${0.55*(1 - ph)})`; ctx.beginPath(); ctx.arc(x, y, b.r*EO(ph), 0, 7); ctx.fill();
      ctx.strokeStyle = "#ffd27a"; ctx.lineWidth = 5; ctx.stroke(); ctx.restore(); }
    city(CASSINO, "MONT-CASSIN", cA*prog(t, T_CASS - 0.1, T_CASS + 0.2), t, RED); }
  // ---- bateau vers l'Écosse
  const s2 = prog(t, SEA2[0] - 0.3, SEA2[0])*(1 - prog(t, S("w16") + 0.2, S("w16") + 0.6));
  if (s2 > 0){ const k = E(prog(t, ...SEA2)); lineLL(upto(R_SEA2, k), s2, "#fff", 7, [18, 14]); vehicle(PH.ship, R_SEA2, k, 90, s2*(1 - prog(t, SEA2[1], SEA2[1] + 0.4))); }
  // ---- Édimbourg
  city(EDIN, "ÉDIMBOURG", prog(t, S("w16") + 0.3, S("w16") + 0.6)*(1 - prog(t, Ed("w17"), Ed("w17") + 0.4)), t);
  // ---- les statues : Édimbourg et Cracovie
  const stA = prog(t, POPS18[0] - 0.2, POPS18[0])*(1 - prog(t, S("w19") + 2.5, S("w19") + 3));
  if (stA > 0){ city(EDIN, null, EB(prog(t, POPS18[0], POPS18[0] + 0.3))*stA, t); city(KRAKOW, null, EB(prog(t, POPS18[1], POPS18[1] + 0.3))*stA, t);
    flight(EDIN, KRAKOW, E(prog(t, POPS18[0] + 0.1, POPS18[1] + 0.2)), stA, "#fff", 6, 0.12); }
  const vg = ctx.createRadialGradient(W/2, H/2, H*0.45, W/2, H/2, H*0.85); vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, `rgba(0,0,0,${0.32 + 0.3*prog(t, S("w17"), S("w17") + 0.6)*(1 - prog(t, S("w18"), S("w18") + 0.5))})`); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  const tg = ctx.createLinearGradient(0, 0, 0, 560); tg.addColorStop(0, "rgba(0,0,0,.38)"); tg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 560);
}
