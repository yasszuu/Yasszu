function overlay(t){
  mosquitoIntro(t);
  // ---- photos et PNG au centre
  photo(PH.pneus, t, T_PNEUS, Ed("m06") + 0.6);
  pngPop(PH.pneu, t, S("m07") + 0.1, M("m07", 0.42), 520, true);
  photo(PH.menton, t, T_MENT2 + 0.35, Ed("m11") + 0.2);
  pngPop(PH.flocon, t, T_FLOC, Ed("m12"), 460);
  photo(PH.pique, t, T_PIQ, Ed("m17") + 0.15);
  // ---- accroche
  kin("2004", W/2, 540, t, T_2004, {size:200, color:Y1, out:M("m01", 0.3)});
  kin("UN MINUSCULE", W/2, 480, t, M("m01", 0.3), {size:110, out:T_MENT - 0.15}); kin("MOUSTIQUE", W/2, 610, t, M("m01", 0.36), {size:130, color:Y1, out:T_MENT - 0.15});
  kin("À MENTON", W/2, 540, t, T_MENT, {size:130, color:Y1, out:Ed("m01") + 0.2});
  kin("20 ANS PLUS TARD", W/2, 470, t, S("m02") + 0.05, {size:100, out:Ed("m02") + 0.1});
  if (t < T_80) counter(fmt(lerp(1, 80, d3.easeExpIn(prog(t, S("m02") + 0.6, T_80)))), t, S("m02") + 0.6, T_80 - 0.02, 640, {size:200});
  else { counter("+ DE 80", t, T_80, Ed("m02") + 0.1, 640, {size:190}); kin("DÉPARTEMENTS", W/2, 800, t, T_80 + 0.1, {size:100, out:Ed("m02") + 0.1}); }
  const hd = EB(prog(t, T_TITLE, T_TITLE + 0.3))*(1 - prog(t, S("m04") - 0.2, S("m04") + 0.15));
  if (hd > 0){ txt("LE MOUSTIQUE", W/2, 480, {size:fit("LE MOUSTIQUE", 120, W - 2*MARGIN), alpha:Math.min(hd, 1), stroke:16, scale:hd}); txt("TIGRE", W/2, 630, {size:170, color:Y1, alpha:Math.min(hd, 1), stroke:20, scale:hd, glow:"rgba(255,214,10,.45)"}); }
  // ---- histoire
  kin("TOUT COMMENCE ICI", W/2, 600, t, S("m04") + 0.9, {size:100, color:Y1, out:Ed("m04") + 0.1});
  kin("DES SIÈCLES", W/2, 600, t, S("m05") + 0.3, {size:130, out:Ed("m05") + 0.15});
  kin("XXe SIÈCLE", W/2, 600, t, T_XX - 0.05, {size:130, color:Y1, out:T_PNEUS - 0.15});
  kin("VIEUX PNEUS", W/2, 470, t, T_PNEUS + 0.1, {size:110, color:Y1, out:Ed("m06") + 0.6});
  kin("EAU DE PLUIE", W/2, 470, t, M("m07", 0.12), {size:110, color:Y1, out:M("m07", 0.42)});
  kin("PAR BATEAU", W/2, 600, t, M("m07", 0.55), {size:130, color:Y1, out:Ed("m07") + 0.2});
  kin("RÉSISTENT", W/2, 480, t, T_FLOC + 0.1, {size:120, out:Ed("m12") + 0.1}); kin("AU FROID", W/2, 610, t, T_FROID, {size:140, color:ICE, out:Ed("m12") + 0.1});
  kin("CACHÉ DANS LES CAMIONS", W/2, 600, t, M("m13", 0.55), {size:96, color:Y1, out:Ed("m13") + 0.15});
  if (t < T_81) counter(fmt(Object.values(EXPT).filter(x => x <= t).length), t, S("m16") + 0.3, T_81 - 0.02, 620, {size:200});
  else { counter("81", t, T_81, T_45 - 0.15, 620, {size:240}); kin("DÉPARTEMENTS", W/2, 790, t, T_81 + 0.1, {size:100, out:T_45 - 0.15}); }
  kin("4 SUR 5", W/2, 640, t, T_45, {size:200, color:Y1, out:Ed("m16") + 0.2});
  kin("DENGUE", W/2, 560, t, T_DENG - 0.05, {size:150, color:RED, out:Ed("m18") + 0.15}); kin("CHIKUNGUNYA", W/2, 710, t, T_CHIK - 0.05, {size:130, color:RED, out:Ed("m18") + 0.15});
  kin("RECORD", W/2, 600, t, S("m19") + 0.4, {size:160, color:Y1, out:M("m19", 0.42)});
  if (t < T_800) counter(fmt(lerp(0, 800, E(prog(t, M("m19", 0.42), T_800)))), t, M("m19", 0.42), T_800 - 0.02, 620, {size:200, color:RED, glow:"rgba(255,59,48,.5)"});
  else { counter("+ DE 800", t, T_800, Ed("m19") + 0.15, 620, {size:190, color:RED, glow:"rgba(255,59,48,.5)"}); kin("CAS EN 2025", W/2, 790, t, T_800 + 0.1, {size:100, out:Ed("m19") + 0.15}); }
  kin("POUR RESTER", W/2, 620, t, T_STAY - 0.1, {size:130, color:Y1, out:Ed("m20") + 0.3});
  if (t > S("m21")){ const o1 = M("m21", 0.5);
    kin("ET TOI ?", W/2, 470, t, S("m21") + 0.1, {size:130, color:Y1, out:o1}); kin("DANS TON", W/2, 610, t, S("m21") + 0.7, {size:100, out:o1}); kin("DÉPARTEMENT ?", W/2, 730, t, S("m21") + 1.0, {size:110, color:Y1, out:o1});
    const a = EB(prog(t, o1 + 0.2, o1 + 0.6)); txt("DIS-LE", W/2, 560, {size:120, color:Y1, scale:a, alpha:Math.min(a, 1), stroke:16});
    const b = EB(prog(t, o1 + 0.4, o1 + 0.8)); txt("EN COMMENTAIRE !", W/2, 680, {size:fit("EN COMMENTAIRE !", 84, W - 2*MARGIN), scale:b, alpha:Math.min(b, 1), stroke:13}); }
  // ---- frise des années
  const yv = yearAt(t), ya = yv === null ? 0 : d3.max(TWIN, ([a, b]) => prog(t, a - 0.1, a + 0.2)*(1 - prog(t, b, b + 0.3)));
  if (ya > 0){ const base = Math.round(yv);
    for (let j = -1; j <= 1; j++){ const v = base + j, x = W/2 + (v - yv)*280; if (x < MARGIN || x > W - MARGIN) continue; const act = clamp(1 - Math.abs(v - yv));
      txt(String(v), x, 450, {size:44 + act*40, color:act > 0.5 ? Y1 : "#fff", alpha:Math.min(ya, 1)*(0.35 + 0.65*act)*clamp(Math.min(x - MARGIN, W - MARGIN - x)/80), stroke:9, glow:act > 0.5 ? "rgba(255,214,10,.45)" : null}); } }
  // ---- sous-titres
  let cur = null; for (const g of CAPS) if (g.s <= t) cur = g;
  if (cur && t <= cur.e + 0.25){ const a = EB(prog(t, cur.s, cur.s + 0.15));
    const segs = cur.g.map((w, i) => ({t:(i ? " " : "") + w.w.replace(/[.,]+$/, "").toUpperCase().replace("XXE", "XXe").replace("1ER", "1er"), c:w.hi ? Y1 : "#fff"}));
    richLine(segs, W/2, 300, {size:80, scale:0.8 + 0.2*a, alpha:Math.min(a*2, 1), stroke:16}); }
}
// moustique (PNG) + bzz : vol en zigzag au centre, puis il s'échappe
function mosquitoIntro(t){
  const img = PH.mosq; if (!img || t > 2.0) return;
  const a = EB(prog(t, 0, 0.35)), out = E(prog(t, 1.35, 1.95));
  const x = W/2 + Math.sin(t*7.3)*90 + Math.sin(t*17)*18 + out*800, y = 1000 + Math.cos(t*5.1)*70 + Math.sin(t*23)*14 - out*700, h = 560, w = h*img.width/img.height;
  ctx.save(); ctx.translate(x, y); ctx.scale(a*(1 - 0.5*out), a*(1 - 0.5*out));
  ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 36; ctx.shadowOffsetY = 30; ctx.drawImage(img, -w/2, -h/2, w, h); ctx.restore();
}
// PNG d'objet au centre (pneu, flocon) : apparition avec rebond, légère oscillation, puis sortie
function pngPop(img, t, t0, t1, h, drops=false){
  if (!img) return; const a = EB(prog(t, t0, t0 + 0.35)), out = E(prog(t, t1, t1 + 0.3)); if (a <= 0 || out >= 1) return;
  const w = h*img.width/img.height, bob = Math.sin((t - t0)*3)*12;
  ctx.save(); ctx.translate(W/2, 1020 + bob + out*300); ctx.scale(a*(1 - 0.3*out), a*(1 - 0.3*out)); ctx.globalAlpha = 1 - out;
  ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 18; ctx.drawImage(img, -w/2, -h/2, w, h); ctx.restore();
  if (drops) for (let i = 0; i < 9; i++){ const ph = ((t - t0)*1.3 + i/9) % 1, x = W/2 + (i - 4)*48 + Math.sin(i*3.1)*20, y = 640 + ph*360;
    ctx.save(); ctx.globalAlpha = (1 - out)*Math.min(a, 1)*(1 - ph)*0.9; ctx.fillStyle = "#7fd4ff"; ctx.strokeStyle = "#fff"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x, y - 18); ctx.quadraticCurveTo(x + 11, y, x, y + 9); ctx.quadraticCurveTo(x - 11, y, x, y - 18); ctx.fill(); ctx.stroke(); ctx.restore(); }
}
