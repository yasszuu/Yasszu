// ------------------------------------------------------------------ données
let BB = [], PH = {}, FLOCK = [], FARMS = [];
function setup(){
  BB = GEO.b.map(r => [d3.min(r, p => p[0]), d3.min(r, p => p[1]), d3.max(r, p => p[0]), d3.max(r, p => p[1])]);
  const rings = GEO.c.NZL.slice().sort((a, b) => b.length - a.length).slice(0, 2), rnd = d3.randomLcg(11);
  while (FLOCK.length < 70){ const p = [166.5 + rnd()*12, -46.6 + rnd()*12.2]; if (rings.some(r => d3.polygonContains(r, p))) FLOCK.push({p, d:rnd(), keep:rnd() < 0.2, s:0.8 + rnd()*0.4, f:rnd() < 0.5 ? 1 : -1}); }
  FLOCK.sort((a, b) => a.p[1] - b.p[1]).reverse();
  const r2 = d3.randomLcg(3); for (let i = 0; i < 60; i++) FARMS.push({p:[FARM[0] - 0.09 + r2()*0.2, FARM[1] - 0.1 + r2()*0.17], d:r2(), s:0.7 + r2()*0.5, f:r2() < 0.5 ? 1 : -1});
  FARMS.sort((a, b) => b.p[1] - a.p[1]);
}
const HITS = TL.sfx.filter(s => ["impact", "hit"].includes(s.name)).map(s => [s.t, s.name === "hit" ? 0.035 : 0.06, s.name === "hit" ? 5 : 10]);
HITS.push([0.05, 0.08, 12]);
// ------------------------------------------------------------------ carte
function renderMap(t){
  CAM = camera(t);
  ctx.fillStyle = "#0b1622"; ctx.fillRect(-60, -60, W + 120, H + 120);
  drawTiles();
  ctx.save(); ctx.strokeStyle = "rgba(255,255,255,.3)"; ctx.lineWidth = 2; ctx.lineJoin = "round";
  GEO.b.forEach((r, i) => { if (inView(BB[i])){ path([r]); ctx.stroke(); } }); ctx.restore();
  flagFill("NZL", "nz", EO(prog(t, T_FLAG - 0.05, T_FLAG + 0.45))*(1 - prog(t, T_HUM - 0.1, T_HUM + 0.3)));
  // 1982 : 3 « humains » (1 = 1 million) puis 70 moutons (1 = 1 million) qui pleuvent sur le pays
  const hA = prog(t, T_HUM - 0.05, T_HUM)*(1 - prog(t, Ed("n02") + 0.1, Ed("n02") + 0.4));
  if (hA > 0) [[174.76, -36.85], [172.64, -43.53], [174.78, -41.29]].forEach((p, i) => { const a = EB(prog(t, T_HUM + i*0.14, T_HUM + i*0.14 + 0.3))*hA; const [x, y] = P(...p); person(x, y, 120, a, "#fff"); });
  const fl = 1 - prog(t, S("n03") + 0.1, S("n03") + 0.5), back = prog(t, S("n04") + 0.3, S("n04") + 0.8);
  FLOCK.forEach((s, i) => { let a = 0;
    if (t < S("n03") + 0.6) a = EB(prog(t, T_MOU + i*0.016, T_MOU + i*0.016 + 0.35))*fl;
    else if (t > S("n04")) a = back*(s.keep ? 1 : 1 - prog(t, T_DOWN + s.d*0.6, T_DOWN + s.d*0.6 + 0.25));
    if (a > 0){ const [x, y] = P(...s.p), drop = (1 - clamp(a))*-160; sheep(x, y + drop, 64*s.s, a, s.f); } });
  // la ferme : toujours plus de moutons sur les collines
  const fA = prog(t, S("n03") + 0.5, S("n03") + 0.8)*(1 - prog(t, S("n04") + 0.1, S("n04") + 0.4));
  if (fA > 0) FARMS.forEach((s, i) => { const t0 = S("n03") + 0.8 + (i/60)**0.8*(T_PLUS - S("n03") - 0.6), a = EB(prog(t, t0, t0 + 0.3))*fA; if (a > 0){ const [x, y] = P(...s.p); sheep(x, y, 100*s.s, a, s.f); } });
  const vg = ctx.createRadialGradient(W/2, H/2, H*0.42, W/2, H/2, H*0.85); vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,.38)"); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  const tg = ctx.createLinearGradient(0, 0, 0, 620); tg.addColorStop(0, "rgba(0,0,0,.42)"); tg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 620);
}
function sheep(x, y, h, a, f=1){ const img = PH.sheepO; if (!img || a <= 0) return; const w = h*img.width/img.height;
  ctx.save(); ctx.translate(x, y); ctx.scale(a*f, a); ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 10; ctx.shadowOffsetY = 4; ctx.drawImage(img, -w/2, -h, w, h); ctx.restore(); }
// pictogramme « humain »
function person(x, y, h, a, color="#fff"){ if (a <= 0) return; ctx.save(); ctx.translate(x, y); ctx.scale(a, a); ctx.fillStyle = color; ctx.strokeStyle = "rgba(0,0,0,.75)"; ctx.lineWidth = h*0.06; ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 16;
  ctx.beginPath(); ctx.arc(0, -h*0.78, h*0.17, 0, 7); ctx.stroke(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-h*0.27, 0); ctx.lineTo(-h*0.27, -h*0.4); ctx.quadraticCurveTo(-h*0.27, -h*0.56, -h*0.12, -h*0.56); ctx.lineTo(h*0.12, -h*0.56); ctx.quadraticCurveTo(h*0.27, -h*0.56, h*0.27, -h*0.4); ctx.lineTo(h*0.27, 0); ctx.closePath(); ctx.stroke(); ctx.fill(); ctx.restore(); }
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
  if (!img) return; const {h=640, y=1450, to=-1100} = o;
  const a = EB(prog(t, t0, t0 + 0.4)), out = E(prog(t, t1, t1 + 0.4)); if (a <= 0 || out >= 1) return;
  const w = h*img.width/img.height, hop = Math.abs(Math.sin(t*9))*30*(1 - out);
  ctx.save(); ctx.translate(W/2 + to*out, y - hop); ctx.rotate(Math.sin(t*9)*0.04); ctx.scale(a, a);
  ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 18; ctx.drawImage(img, -w/2, -h, w, h); ctx.restore();
}
// 1 humain au centre, n moutons qui poppent en couronne autour
function ratio(t, t0, n, out, cy=1250, R=330){
  const a = EB(prog(t, t0 - 0.3, t0)), o = E(prog(t, out, out + 0.35)); if (a <= 0 || o >= 1) return;
  ctx.save(); ctx.globalAlpha = 1 - o; ctx.translate(W/2, cy); ctx.scale(1 - 0.2*o, 1 - 0.2*o); ctx.translate(-W/2, -cy);
  ctx.fillStyle = "rgba(0,0,0,.35)"; ctx.beginPath(); ctx.arc(W/2, cy, (R + 120)*Math.min(a, 1), 0, 7); ctx.fill();
  person(W/2, cy + 80, 230, a, Y1);
  for (let i = 0; i < n; i++){ const ang = -Math.PI/2 + i/n*Math.PI*2, rr = R*(n > 8 ? (i % 2 ? 0.86 : 1.08) : 1), b = EB(prog(t, t0 + i*0.06, t0 + i*0.06 + 0.3));
    sheep(W/2 + Math.cos(ang)*rr, cy + Math.sin(ang)*rr + 45, n > 8 ? 95 : 140, b, Math.cos(ang) > 0 ? 1 : -1); }
  ctx.restore(); }
function overlay(t){
  beast(PH.sheepO, t, 0, 1.2, {h:560, y:1480, to:-1150});
  // ---- accroche : 22 moutons pour 1 habitant
  ratio(t, T_22, 22, Ed("n01") + 0.15);
  if (t > S("n01")){ const o = Ed("n01") + 0.15;
    kin("22 MOUTONS", W/2, 470, t, S("n01") + 0.35, {size:140, color:Y1, out:o}); kin("PAR HABITANT", W/2, 610, t, T_HAB - 0.1, {size:100, out:o}); }
  // ---- pièces : l'État paie
  const cA = prog(t, T_COIN - 0.1, T_COIN)*(1 - prog(t, Ed("n03"), Ed("n03") + 0.3));
  if (cA > 0) for (let i = 0; i < 26; i++){ const t0 = T_COIN + (i*0.37 % 1)*1.0, k = prog(t, t0, t0 + 1.3); if (k <= 0 || k >= 1) continue;
    const x = MARGIN + ((i*173) % (W - 2*MARGIN)), y = -80 + k*(H*0.75), sp = Math.cos((t - t0)*9 + i);
    ctx.save(); ctx.globalAlpha = cA*(1 - prog(k, 0.8, 1)); ctx.translate(x, y); ctx.scale(sp, 1); ctx.fillStyle = "#ffcc1a"; ctx.strokeStyle = "#a66b00"; ctx.lineWidth = 8; ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 14;
    ctx.beginPath(); ctx.arc(0, 0, 46, 0, 7); ctx.fill(); ctx.stroke(); ctx.shadowColor = "transparent"; ctx.fillStyle = "#a66b00"; ctx.font = "900 56px M"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText("$", 0, 3); ctx.restore(); }
  // ---- aujourd'hui : 4 par personne
  ratio(t, T_4, 4, Ed("n04") + 0.25);
  // ---- frise des années
  const yv = yearAt(t), ya = yv === null ? 0 : Math.max(prog(t, M("n02", 0.1), M("n02", 0.2))*(1 - prog(t, Ed("n02"), Ed("n02") + 0.3)), prog(t, S("n04"), S("n04") + 0.2)*(1 - prog(t, M("n04", 0.65), M("n04", 0.75))));
  if (ya > 0){ const base = Math.round(yv);
    for (let j = -1; j <= 1; j++){ const v = base + j, x = W/2 + (v - yv)*300; if (x < MARGIN || x > W - MARGIN) continue; const act = clamp(1 - Math.abs(v - yv));
      txt(String(v), x, 470, {size:56 + act*70, color:act > 0.5 ? Y1 : "#fff", alpha:Math.min(ya, 1)*(0.35 + 0.65*act)*clamp(Math.min(x - MARGIN, W - MARGIN - x)/80), stroke:10, glow:act > 0.5 ? "rgba(255,214,10,.45)" : null}); } }
  // ---- appel final : les moutons encerclent
  if (t > S("n05") - 0.1){
    const n = 14, k = E(prog(t, S("n05"), DUR - 0.6));
    for (let i = 0; i < n; i++){ const ang = i/n*Math.PI*2 + t*0.25, rr = lerp(900, 430, k), b = EB(prog(t, S("n05") + i*0.04, S("n05") + i*0.04 + 0.3));
      sheep(W/2 + Math.cos(ang)*rr, 1250 + Math.sin(ang)*rr*1.1 + 60, 150, b, Math.cos(ang) > 0 ? -1 : 1); }
    person(W/2, 1330, 260, EB(prog(t, S("n05"), S("n05") + 0.35)), Y1);
    const a = EB(prog(t, T_CTA1, T_CTA1 + 0.35)); txt("ET TOI ?", W/2, 470, {size:140, color:Y1, scale:a, alpha:Math.min(a, 1), stroke:18, glow:"rgba(255,214,10,.45)"});
    const b = EB(prog(t, T_CTA2, T_CTA2 + 0.35)); txt("COMBIEN DE JOURS ?", W/2, 610, {size:fit("COMBIEN DE JOURS ?", 92, W - 2*MARGIN), scale:b, alpha:Math.min(b, 1), stroke:14}); }
  // ---- sous-titres
  let cur = null; for (const g of CAPS) if (g.s <= t) cur = g;
  if (cur && t <= cur.e + 0.25){ const a = EB(prog(t, cur.s, cur.s + 0.15));
    const segs = cur.g.map((w, i) => ({t:(i ? " " : "") + w.w.replace(/[.,]+$/, "").toUpperCase(), c:w.hi ? Y1 : "#fff"}));
    richLine(segs, W/2, 300, {size:84, scale:0.8 + 0.2*a, alpha:Math.min(a*2, 1), stroke:16}); }
}
window.ready = Promise.all([fetch("geo.json").then(r => r.json()).then(j => { GEO = j; setup(); }),
  load("nz", "flags/nz.svg"), img("sheep", "assets/mouton.png"),
  document.fonts.load("900 60px M"), document.fonts.load("800 60px M")]).then(() => { PH.sheepO = outlined(PH.sheep, 7); return true; });
