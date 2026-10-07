
// ------------------------------------------------------------------ plans 3D (Blender) : images préchargées par prep(t)
const CLIPF = {};
const clipAt = t => TL.clips.find(c => t >= c.a && t < c.b);
window.prep = async t => {
  const c = clipAt(t); if (!c) return;
  const f = Math.min(Math.floor((t - c.a)*30), Math.round((c.b - c.a)*30) - 1), key = c.name + f;
  if (CLIPF[key]) return;
  for (const k of Object.keys(CLIPF)) delete CLIPF[k];
  await new Promise(r => { const i = new Image(); i.onload = () => { CLIPF[key] = i; r(); }; i.onerror = r;
    i.src = `clips/${c.name}/${String(f).padStart(4, "0")}.jpg`; });
};
function clipAlpha(t){ const c = clipAt(t); return c ? Math.min(EO(prog(t, c.a, c.a + 0.3)), 1 - prog(t, c.b - 0.3, c.b)) : 0; }
function drawClip(t){
  const c = clipAt(t); if (!c) return;
  const f = Math.min(Math.floor((t - c.a)*30), Math.round((c.b - c.a)*30) - 1), img = CLIPF[c.name + f]; if (!img) return;
  const a = EO(prog(t, c.a, c.a + 0.3)), out = prog(t, c.b - 0.3, c.b);
  const z = 1 + 0.18*(1 - a);                                         // plongée à l'entrée
  ctx.save(); ctx.globalAlpha = a*(1 - out);
  ctx.translate(W/2, H/2); ctx.scale(z, z); ctx.drawImage(img, -W/2, -H/2, W, H); ctx.restore();
  const fl = Math.exp(-(t - c.a)*9);
  if (fl > 0.02){ ctx.save(); ctx.fillStyle = `rgba(255,255,255,${0.5*fl})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
  ctx.save(); ctx.globalAlpha = a*(1 - out); const g = ctx.createLinearGradient(0, 0, 0, H*0.25);
  g.addColorStop(0, "rgba(0,0,0,0.45)"); g.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H*0.25); ctx.restore();
}

// ------------------------------------------------------------------ sous-titres (groupes de 2-3 mots)
const CAPS = TL.vo.filter(v => !["s01", "s02", "s03", "s20"].includes(v.id)).map(v => {
  const words = [];
  for (const w of v.cap.split(/\s+/)){ const o = {hi:/\*/.test(w), w:w.replace(/\*/g, "")};
    const p = words[words.length-1];
    if (p && ((/^[:;!?…]$/.test(o.w)) || (/^\d+$/.test(p.w) && /^\d{3}/.test(o.w)))) { p.w += " " + o.w; p.hi = p.hi || o.hi; } else words.push(o); }
  const groups = []; let cur = [];
  for (const w of words){ const len = cur.map(x => x.w).join(" ").length + w.w.length + 1;
    if (cur.length && len > 15){ groups.push(cur); cur = []; } cur.push(w); if (/[.,:!?…]$/.test(w.w)){ groups.push(cur); cur = []; } }
  if (cur.length) groups.push(cur);
  const tot = d3.sum(groups, g => g.map(x => x.w).join(" ").length + 4); let acc = 0;
  return groups.map(g => { const l = g.map(x => x.w).join(" ").length + 4; const s = v.start + (v.end - v.start)*acc/tot; acc += l;
    return {g, s, e:v.start + (v.end - v.start)*acc/tot}; });
}).flat();

// ------------------------------------------------------------------ rendu
function render(t){
  const ca = clipAlpha(t);
  if (ca < 0.999) renderMap(t); else { ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H); }
  drawClip(t);
  overlay(t, ca);
}
const nfmt = v => Math.round(v).toLocaleString("fr-FR").replace(/ | /g, " ");
function overlay(t, pa){
  const mapA = 1 - pa;
  // --- titre : seulement pendant l'accroche
  const hd = EO(prog(t, C.title, C.title + 0.5)) * (1 - prog(t, S("s04") - 0.6, S("s04") - 0.2)) * mapA;
  if (hd > 0){ txt("LA STERNE", W/2, 225, {size:108, alpha:hd, stroke:14}); txt("ARCTIQUE", W/2, 340, {size:116, color:Y1, alpha:hd, stroke:14, glow:"rgba(255,214,10,.45)"}); }
  // --- frise des mois
  const show = TL.ticker.some(s => t >= s[0] - 0.3 && t <= s[1] + 2.2) && t < Ed("s14") + 0.8;
  const fa = (show ? 1 : 0) * mapA;
  if (fa > 0){
    const {v} = yearAt(t), y = 430, gap = 250;
    ctx.save(); ctx.globalAlpha = fa; ctx.strokeStyle = Y1; ctx.lineWidth = 4; ctx.shadowColor = "rgba(0,0,0,.8)"; ctx.shadowBlur = 8;
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); ctx.restore();
    const base = Math.round(v);
    for (let j = -3; j <= 3; j++){
      const yv = base + j, x = W/2 + (yv - v)*gap; if (x < -150 || x > W + 150) continue;
      const act = clamp(1 - Math.abs(yv - v));
      ctx.save(); ctx.globalAlpha = fa; ctx.fillStyle = Y1; ctx.fillRect(x - 2, y - 14, 4, 28); ctx.restore();
      txt(moisName(yv), x, y + 66 + act*16, {size:42 + act*34, color:act > 0.5 ? ORANGE : Y1, alpha:fa*(0.5 + 0.5*act), stroke:8, glow:act > 0.5 ? "rgba(255,159,28,0.6)" : null});
    }
  }
  // --- compteur de kilomètres (texte simple)
  const km = 35000*(0.55*kOut(t) + 0.45*Math.max(kAfr(t), kBra(t))) + 35900*kBack(t);
  const kmA = EO(prog(t, C.south[0], C.south[0] + 0.4))*(1 - prog(t, C.farne[0] - 0.2, C.farne[0] + 0.2))*mapA;
  if (kmA > 0) richLine([{t:nfmt(km), c:Y1}, {t:" KM", c:"#fff"}], W/2, 600, {size:58, alpha:kmA, stroke:12});
  const g82A = EO(prog(t, M("s15", 0.18), M("s15", 0.25)))*(1 - prog(t, C.life[0], C.life[0] + 0.4))*mapA;
  if (g82A > 0) richLine([{t:nfmt(96000*kG82(t)), c:Y1}, {t:" KM", c:"#fff"}], W/2, 520, {size:72, alpha:g82A, stroke:13});
  const lifeKm = d3.easeQuadIn(prog(t, S("s17") - 0.2, M("s17", 0.5)))*2100000;
  const lkA = EO(prog(t, S("s17") - 0.3, S("s17")))*(1 - prog(t, M("s17", 0.45), M("s17", 0.5)))*mapA;
  if (lkA > 0) richLine([{t:nfmt(lifeKm), c:Y1}, {t:" KM", c:"#fff"}], W/2, 520, {size:72, alpha:lkA, stroke:13});
  // --- textes cinétiques (un seul bloc à la fois)
  kin("100 GRAMMES", W/2, 620, t, M("s01", 0.15), {size:96, color:Y1, out:Ed("s01") - 0.1});
  kin("+ DE 70 000 KM", W/2, 620, t, C.k70, {size:100, color:Y1, out:Ed("s03") - 0.3});
  kin("JUIN", W/2, 640, t, M("s04", 0.25), {size:120, color:Y1, out:M("s04", 0.52)});
  kin("2 ÉTÉS PAR AN", W/2, 1600, t, M("s13", 0.2), {size:100, color:"#fff", out:Ed("s13") + 0.2});
  kin("EN 10 MOIS", W/2, 640, t, M("s15", 0.88), {size:96, out:Ed("s15") + 0.3});
  kin("30 ANS", W/2, 640, t, M("s16", 0.4), {size:150, color:Y1, out:Ed("s16") + 0.1});
  kin("+ DE 2 MILLIONS", W/2, 600, t, M("s17", 0.5), {size:96, color:Y1, out:Ed("s17") + 0.2});
  kin("DE KILOMÈTRES", W/2, 710, t, M("s17", 0.62), {size:76, out:Ed("s17") + 0.2});
  kin("100 GRAMMES", W/2, 620, t, M("s19", 0.4), {size:110, color:Y1, out:Ed("s19") + 0.4});
  // --- Terre → Lune : 3 allers-retours
  const mo = EB(prog(t, C.moon[0] + 0.6, C.moon[0] + 1.1))*(1 - prog(t, C.moon[1], C.moon[1] + 0.4))*mapA;
  if (mo > 0 && IMG.lune){
    const L = IMG.lune, ms = 230*Math.min(mo, 1.1), mx = W/2 + 40, my = 520;
    ctx.save(); ctx.shadowColor = "rgba(200,220,255,.5)"; ctx.shadowBlur = 50; ctx.globalAlpha = Math.min(mo, 1);
    ctx.drawImage(L, mx - ms/2, my - ms/2, ms, ms); ctx.restore();
    txt("LUNE", mx, my - ms/2 - 30, {size:46, alpha:Math.min(mo, 1), stroke:10});
    for (let i = 0; i < 3; i++){
      const k = E(prog(t, S("s18") + 0.25 + i*0.45, S("s18") + 0.9 + i*0.45)); if (k <= 0) continue;
      const wdt = 60 + i*45, y0 = MAPY - 160, y1 = my + ms/2 - 10, n = 60;
      ctx.save(); ctx.globalAlpha = Math.min(mo, 1); ctx.setLineDash([14, 10]); ctx.strokeStyle = Y1; ctx.lineWidth = 6; ctx.shadowColor = "rgba(0,0,0,.8)"; ctx.shadowBlur = 8;
      ctx.beginPath();
      for (let q = 0; q <= n*k; q++){ const a = q/n*2*Math.PI; const x = W/2 + (i % 2 ? -1 : 1)*Math.sin(a)*wdt + 20*Math.sin(a/2), y = lerp(y0, y1, (1 - Math.cos(a))/2);
        q ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
      ctx.stroke(); ctx.restore();
    }
    kin("× 3", W/2, 1420, t, S("s18") + 1.6, {size:170, color:Y1, out:C.moon[1]});
  }
  // --- stickers : la sterne (image fournie) — dans la mer, jamais sur un pays
  sticker("sterne", 560, 1700, 300, t, 0.5, C.preview[0] + 0.4, {rot:0.03});
  sticker("sterne", 300, 1680, 240, t, C.colony[0] + 0.2, C.south[0], {rot:0.03, flip:true});
  sticker("sterne", W/2, 1560, 380, t, C.g100[0] + 0.2, C.outro + 0.1, {rot:0.03});
  // --- outro
  const oa = EB(prog(t, C.outro + 0.3, C.outro + 0.8));
  if (oa > 0){
    txt("Tu connaissais", W/2, 330, {size:74, weight:800, scale:oa, stroke:12});
    txt("la sterne arctique ?", W/2, 425, {size:74, weight:800, color:Y1, scale:oa, stroke:12});
    const na = EB(prog(t, C.outro + 2.0, C.outro + 2.5));
    if (na > 0) richLine([{t:"DIS-LE ", c:Y1}, {t:"EN COMMENTAIRE !", c:"#fff"}], W/2, 545, {size:56, scale:na, alpha:Math.min(na, 1), stroke:12});
  }
  // --- sous-titres : gros, en haut, par groupes de 2-3 mots
  let cur = null;
  for (const g of CAPS) if (g.s <= t) cur = g;
  if (cur && t <= cur.e + 0.25 && t >= S("s04") - 0.1){
    const a = EB(prog(t, cur.s, cur.s + 0.15));
    const segs = cur.g.map((w, i) => ({t:(i ? " " : "") + w.w.replace(/[.,]+$/, "").toUpperCase(), c:w.hi ? Y1 : "#fff"}));
    richLine(segs, W/2, 300, {size:84, weight:900, scale:0.8 + 0.2*a, alpha:Math.min(a*2, 1), stroke:16});
  }
}
