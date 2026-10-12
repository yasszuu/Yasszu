const TWIN = [[S("w04"), Ed("w04") + 0.2], [S("w09"), Ed("w12") + 0.2], [S("w15"), M("w17", 0.8)]];
const HITS = TL.sfx.filter(s => ["impact", "hit"].includes(s.name)).map(s => [s.t, s.name === "hit" ? 0.035 : 0.06, s.name === "hit" ? 5 : 10]);
HITS.push([0.03, 0.08, 12], [2.1, 0.05, 6]);
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
function overlay(t){
  bearIntro(t);
  photo(PH.combat, t, T_COMBAT, M("w08", 0.62), 1010, 700, 525);
  photo(PH.maitre, t, POPS16[1] - 0.05, Ed("w16") + 0.3, 1010, 700, 395);
  // ---- accroche
  kin("1944", W/2, 540, t, T_1944, {size:200, color:Y1, out:M("w01", 0.4)});
  kin("UN OURS", W/2, 480, t, M("w01", 0.38), {size:130, out:T_POL - 0.15}); kin("A COMBATTU", W/2, 610, t, M("w01", 0.48), {size:110, color:Y1, out:T_POL - 0.15});
  kin("DANS L'ARMÉE", W/2, 480, t, T_POL, {size:110, out:Ed("w01") + 0.25}); kin("POLONAISE", W/2, 610, t, T_POL + 0.1, {size:130, color:Y1, out:Ed("w01") + 0.25});
  ["UN GRADE", "DES RATIONS", "DE LA BIÈRE"].forEach((w, i) => kin(w, W/2, 560, t, POPS2[i] - 0.05, {size:130, color:i === 2 ? Y1 : "#fff", out:i < 2 ? POPS2[i + 1] - 0.15 : Ed("w02") + 0.15}));
  const hd = EB(prog(t, T_TITLE, T_TITLE + 0.3))*(1 - prog(t, S("w04") - 0.1, S("w04") + 0.25));
  if (hd > 0){ txt("WOJTEK", W/2, 480, {size:170, color:Y1, alpha:Math.min(hd, 1), stroke:20, scale:hd, glow:"rgba(255,214,10,.45)"}); txt("L'OURS SOLDAT", W/2, 630, {size:fit("L'OURS SOLDAT", 110, W - 2*MARGIN), alpha:Math.min(hd, 1), stroke:16, scale:hd}); }
  // ---- histoire
  kin("UN OURSON", W/2, 600, t, T_OURSON, {size:140, color:Y1, out:Ed("w06") + 0.15});
  ["CONSERVES", "CHOCOLAT", "COUTEAU"].forEach((w, i) => kin(w, W/2, 600, t, POPS7[i] - 0.05, {size:130, out:i < 2 ? POPS7[i + 1] - 0.12 : T_JOY - 0.4}));
  kin("« LE GUERRIER", W/2, 540, t, T_JOY - 0.1, {size:110, out:Ed("w07") + 0.2}); kin("JOYEUX »", W/2, 670, t, T_JOY, {size:140, color:Y1, out:Ed("w07") + 0.2});
  kin("CIGARETTES", W/2, 470, t, M("w08", 0.78), {size:120, color:Y1, out:Ed("w08") + 0.2});
  kin("INTERDITS", W/2, 620, t, T_INTERD, {size:140, color:RED, out:Ed("w10") + 0.2});
  kin("ENRÔLÉ", W/2, 520, t, T_SOLDAT - 0.15, {size:120, out:Ed("w11") + 0.2}); kin("SOLDAT", W/2, 670, t, T_SOLDAT, {size:170, color:Y1, out:Ed("w11") + 0.2});
  kin("MAI 1944", W/2, 600, t, S("w12") + 0.2, {size:150, color:Y1, out:T_CASS - 0.1});
  kin("LA PLUS VIOLENTE", W/2, 600, t, M("w12", 0.75), {size:100, color:RED, out:Ed("w12") + 0.2});
  if (t < T_45) counter(Math.round(lerp(0, 45, E(prog(t, M("w13", 0.45), T_45)))) + " KG", t, M("w13", 0.45), T_45 - 0.02, 620, {size:200});
  else { counter("45 KG", t, T_45, Ed("w13") + 0.15, 620, {size:220}); kin("PAR CAISSE", W/2, 790, t, T_45 + 0.1, {size:100, out:Ed("w13") + 0.15}); }
  kin("EMBLÈME", W/2, 600, t, T_EMBL, {size:140, color:Y1, out:T_CAPO - 0.3});
  kin("CAPORAL", W/2, 620, t, T_CAPO, {size:170, color:Y1, out:Ed("w14") + 0.25});
  kin("ZOO D'ÉDIMBOURG", W/2, 470, t, POPS16[0] - 0.05, {size:96, color:Y1, out:Ed("w16") + 0.3});
  kin("1963", W/2, 560, t, S("w17") + 0.3, {size:180, color:Y1, out:Ed("w17") + 0.2}); kin("21 ANS", W/2, 720, t, M("w17", 0.7), {size:130, out:Ed("w17") + 0.2});
  kin("STATUES", W/2, 620, t, POPS18[0] - 0.1, {size:150, color:Y1, out:Ed("w18") + 0.2});
  if (t > S("w19")){ const o1 = M("w19", 0.55);
    kin("ET TOI ?", W/2, 470, t, S("w19") + 0.1, {size:130, color:Y1, out:o1}); kin("D'AUTRES ANIMAUX", W/2, 610, t, S("w19") + 0.7, {size:100, out:o1}); kin("SOLDATS ?", W/2, 730, t, S("w19") + 1.0, {size:130, color:Y1, out:o1});
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
    const segs = cur.g.map((w, i) => ({t:(i ? " " : "") + w.w.replace(/[.,]+$/, "").toUpperCase(), c:w.hi ? Y1 : "#fff"}));
    richLine(segs, W/2, 300, {size:80, scale:0.8 + 0.2*a, alpha:Math.min(a*2, 1), stroke:16}); }
}
// ours (PNG) + grognement : il charge vers la caméra, puis sort
function bearIntro(t){
  const img = PH.bear; if (!img || t > 2.2) return;
  const a = EB(prog(t, 0, 0.4)), out = E(prog(t, 1.6, 2.15)), roar = Math.sin(Math.PI*clamp(t/2.0));
  const h = 640*(1 + 0.06*roar), w = h*img.width/img.height;
  ctx.save(); ctx.translate(W/2 + Math.sin(t*45)*6*roar + out*900, 1400 + out*120); ctx.scale(a*(1 + 0.15*out), a*(1 + 0.15*out));
  ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 18; ctx.drawImage(img, -w/2, -h, w, h); ctx.restore();
}
