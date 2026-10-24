const TWIN = [[S("l04"), Ed("l04") + 0.2], [S("l08"), CL.a], [S("l11"), Ed("l11") + 0.2], [S("l13"), Ed("l13") + 0.2], [S("l15"), Ed("l15") + 0.2], [S("l16"), M("l16", 0.45)]];
const HITS = TL.sfx.filter(s => ["impact", "hit"].includes(s.name)).map(s => [s.t, s.name === "hit" ? 0.035 : 0.06, s.name === "hit" ? 5 : 10]);
HITS.push([0.03, 0.08, 12], [2.2, 0.05, 6]);
let PH = {}, CLIPF = {};
const inClip = t => t > CL.a + 0.35 && t < CL.b - 0.35;
const prepBase = window.prep;
window.prep = async t => {
  const jobs = [inClip(t) ? Promise.resolve() : prepBase(t)];
  if (t >= CL.a && t < CL.b){ const f = Math.min(Math.floor((t - CL.a)*30), 149), key = "c" + f;
    if (!CLIPF[key]){ for (const k of Object.keys(CLIPF)) delete CLIPF[k];
      jobs.push(new Promise(r => { const i = new Image(); i.onload = () => { CLIPF[key] = i; r(); }; i.onerror = r; i.src = `../lw3d/clip/${String(f).padStart(4, "0")}.jpg`; })); } }
  await Promise.all(jobs);
};
function clipAlpha(t){ return Math.min(EO(prog(t, CL.a, CL.a + 0.35)), 1 - prog(t, CL.b - 0.35, CL.b)); }
function drawClip(t){
  if (t < CL.a || t >= CL.b) return; const f = Math.min(Math.floor((t - CL.a)*30), 149), img = CLIPF["c" + f]; if (!img) return;
  const a = clipAlpha(t), z = 1 + 0.12*(1 - EO(prog(t, CL.a, CL.a + 0.35)));
  ctx.save(); ctx.globalAlpha = a; ctx.translate(W/2, H/2); ctx.scale(z, z); ctx.drawImage(img, -W/2, -H/2, W, H); ctx.restore();
  const fl = Math.exp(-(t - CL.a)*9); if (fl > 0.02){ ctx.save(); ctx.fillStyle = `rgba(255,255,255,${0.4*fl})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
}
function render(t){
  let p = 0, sx = 0, sy = 0;
  for (const [ti, amp, sh] of HITS) if (t >= ti){ const d = t - ti; p += amp*Math.exp(-d*8); sx += sh*Math.exp(-d*7)*Math.sin(d*50); sy += sh*0.7*Math.exp(-d*7)*Math.cos(d*43); }
  ctx.save(); ctx.translate(W/2 + sx, H/2 + sy); ctx.scale(1.04 + p, 1.04 + p); ctx.translate(-W/2, -H/2);
  const ca = clipAlpha(t)*(t >= CL.a && t < CL.b ? 1 : 0);
  if (ca < 0.999){ renderMap(t); motionBlur(t); } else { ctx.fillStyle = "#000"; ctx.fillRect(-60, -60, W + 120, H + 120); }
  drawClip(t);
  overlay(t, 1 - ca);
  ctx.restore();
  const fl = Math.exp(-t*7); if (fl > 0.02){ ctx.fillStyle = `rgba(255,255,255,${0.6*fl})`; ctx.fillRect(0, 0, W, H); }
}
function overlay(t, mapA){
  elephantIntro(t);
  // ---- photos au centre (~2-3 s chacune)
  const L = [780, 585], Pt = [600, 760];
  photo(PH.p01, t, T_PH1 - 0.05, M("l02", 0.85), 1010, ...L);
  photo(PH.p03, t, T_JUNGLE, Ed("l04") + 0.25, 1010, ...L);
  photo(PH.p04, t, P5[0], M("l05", 0.36), 1010, ...Pt);
  photo(PH.p05, t, P6[0], P6[1] - 0.1, 1010, ...L);
  photo(PH.p06, t, P6[1], Ed("l06") + 0.15, 1010, ...Pt);
  photo(PH.p07, t, P7[0], P7[1] - 0.1, 1010, ...L);
  photo(PH.p08, t, P7[1], P7[2] - 0.1, 1010, ...L);
  photo(PH.p09, t, P7[2], Ed("l07") + 0.2, 1010, ...L);
  photo(PH.p10, t, T_PAINT, CL.a + 0.1, 1010, ...L);
  photo(PH.p11, t, T_CANTON, Ed("l10") + 0.3, 1010, ...L);
  photo(PH.p12, t, T_GEN, SHIP[0] - 0.1, 1010, ...Pt);
  photo(PH.p14, t, T_PARADE, Ed("l12") + 0.1, 1010, ...L);
  photo(PH.p16, t, P14[0], P14[1] - 0.1, 1010, ...L);
  photo(PH.p15, t, P14[1], Ed("l14") + 0.2, 1010, ...L);
  photo(PH.p18, t, T_PH18, Ed("l16") + 0.25, 1010, ...L);
  // ---- accroche (sans sous-titres) et appel final
  kin("2003", W/2, 480, t, T_2003, {size:190, color:Y1, out:T_PH1 - 0.2});
  kin("TAÏWAN EN DEUIL", W/2, 480, t, T_PH1 - 0.1, {size:100, out:T_86 - 0.15});
  kin("86 ANS", W/2, 480, t, T_86, {size:170, color:Y1, out:Ed("l01") + 0.3});
  kin("LIN WANG", W/2, 480, t, T_NAME, {size:150, color:Y1, out:T_WAR - 0.15});
  kin("LA GUERRE", W/2, 480, t, T_WAR, {size:150, color:RED, out:Ed("l02") + 0.3});
  const hd = EB(prog(t, T_TITLE, T_TITLE + 0.3))*(1 - prog(t, S("l04") - 0.1, S("l04") + 0.25));
  if (hd > 0){ txt("L'ÉLÉPHANT", W/2, 520, {size:fit("L'ÉLÉPHANT", 130, W - 2*MARGIN), alpha:Math.min(hd, 1), stroke:16, scale:hd}); txt("SOLDAT", W/2, 670, {size:180, color:Y1, alpha:Math.min(hd, 1), stroke:20, scale:hd, glow:"rgba(255,214,10,.45)"}); }
  if (t > S("l18")){ const o1 = M("l18", 0.55);
    kin("ET TOI ?", W/2, 470, t, S("l18") + 0.1, {size:130, color:Y1, out:o1}); kin("TU CONNAISSAIS", W/2, 610, t, S("l18") + 0.6, {size:100, out:o1}); kin("LIN WANG ?", W/2, 730, t, S("l18") + 0.9, {size:130, color:Y1, out:o1});
    const a = EB(prog(t, o1 + 0.2, o1 + 0.6)); txt("DIS-LE", W/2, 560, {size:120, color:Y1, scale:a, alpha:Math.min(a, 1), stroke:16});
    const b = EB(prog(t, o1 + 0.4, o1 + 0.8)); txt("EN COMMENTAIRE !", W/2, 680, {size:fit("EN COMMENTAIRE !", 84, W - 2*MARGIN), scale:b, alpha:Math.min(b, 1), stroke:13}); }
  // ---- frise des années
  const yv = yearAt(t), ya = mapA*(yv === null ? 0 : d3.max(TWIN, ([a, b]) => prog(t, a - 0.1, a + 0.2)*(1 - prog(t, b, b + 0.3))));
  if (ya > 0){ const base = Math.round(yv);
    for (let j = -1; j <= 1; j++){ const v = base + j, x = W/2 + (v - yv)*280; if (x < MARGIN || x > W - MARGIN) continue; const act = clamp(1 - Math.abs(v - yv));
      txt(String(v), x, 450, {size:44 + act*40, color:act > 0.5 ? Y1 : "#fff", alpha:Math.min(ya, 1)*(0.35 + 0.65*act)*clamp(Math.min(x - MARGIN, W - MARGIN - x)/80), stroke:9, glow:act > 0.5 ? "rgba(255,214,10,.45)" : null}); } }
  // ---- sous-titres
  let cur = null; for (const g of CAPS) if (g.s <= t) cur = g;
  if (cur && t <= cur.e + 0.25){ const a = EB(prog(t, cur.s, cur.s + 0.15));
    const segs = cur.g.map((w, i) => ({t:(i ? " " : "") + w.w.replace(/[.,]+$/, "").toUpperCase(), c:w.hi ? Y1 : "#fff"}));
    richLine(segs, W/2, 300, {size:80, scale:0.8 + 0.2*a, alpha:Math.min(a*2, 1), stroke:16}); }
}
// éléphant (PNG) + barrissement : il entre en se balançant, lève la trompe, puis sort
function elephantIntro(t){
  const img = PH.eleph; if (!img || t > 2.4) return;
  const a = EB(prog(t, 0, 0.45)), out = E(prog(t, 1.75, 2.35)), sway = Math.sin(t*6)*0.03;
  const h = 640, w = h*img.width/img.height;
  ctx.save(); ctx.translate(W/2 + Math.sin(t*9)*8*(1 - out) - out*950, 1400 + out*80); ctx.rotate(sway); ctx.scale(a, a);
  ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 18; ctx.drawImage(img, -w/2, -h, w, h); ctx.restore();
}
