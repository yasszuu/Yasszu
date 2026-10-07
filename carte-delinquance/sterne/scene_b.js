
// ------------------------------------------------------------------ dessin : carte
const rnd = d3.randomLcg(11);
const stars = d3.range(420).map(() => [rnd()*W, rnd()*H, rnd()*1.7+0.3, rnd()]);
const visible = p => d3.geoDistance(p, [-proj.rotate()[0], -proj.rotate()[1]]) < Math.PI/2 - 0.03;
const vproj = p => visible(p) ? proj(p) : null;
function routeLine(r, k, alpha, color="#fff", w=7, dash=[16, 11]){
  if (k <= 0 || alpha <= 0) return;
  const {p, i} = routeAt(r, k), pts = r.pts.slice(0, i).concat([p]);
  ctx.save(); ctx.globalAlpha = alpha; ctx.lineCap = "round"; ctx.lineJoin = "round";
  ctx.setLineDash(dash); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.shadowColor = "rgba(0,0,0,.85)"; ctx.shadowBlur = 10;
  ctx.beginPath(); path({type:"LineString", coordinates:pts}); ctx.stroke(); ctx.restore();
}
// la sterne (image fournie) qui vole le long d'une route, orientée selon la direction à l'écran
function ternSprite(r, k, h, alpha, t){
  const img = IMG.sterne; if (!img || alpha <= 0) return;
  const {p, a, b} = routeAt(r, k), xy = vproj(p); if (!xy) return;
  const pa = proj(a), pb = proj(b), dir = pb && pa ? Math.sign(pb[0] - pa[0]) || 1 : 1;
  const w = h*img.width/img.height, bob = Math.sin(t*5)*4;
  pulse(xy[0], xy[1], t, alpha*0.8, Y1, 60);
  ctx.save(); ctx.globalAlpha = alpha; ctx.translate(xy[0], xy[1] - h*0.25 + bob); ctx.scale(dir > 0 ? -1 : 1, 1); ctx.rotate(Math.sin(t*3)*0.04);
  ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 18; ctx.shadowOffsetY = 10;
  ctx.drawImage(img, -w/2, -h/2, w, h); ctx.restore();
}
function label(str, lonlat, dx, dy, a, o={}){
  const p = vproj(lonlat); if (!p || a <= 0) return;
  txt(str, p[0] + dx, p[1] + dy, {size:46, stroke:10, scale:Math.max(a, 0.001), alpha:Math.min(a, 1), ...o});
}
function capGlow(feature, a, color="255,214,10"){
  if (a <= 0) return;
  ctx.save(); ctx.beginPath(); path(feature); ctx.fillStyle = `rgba(${color},${0.45*a})`; ctx.fill();
  ctx.strokeStyle = `rgba(255,255,255,${0.9*a})`; ctx.lineWidth = 3.5; ctx.shadowColor = `rgb(${color})`; ctx.shadowBlur = 24; ctx.stroke(); ctx.restore();
}
// étiquette ancrée : épingle + trait pointillé + nom
function place(name, ll, a, t, o={}){
  const p = vproj(ll); if (!p || a <= 0) return;
  const {dx=-140, dy=-190, color=Y1} = o;
  pulse(p[0], p[1], t, Math.min(a, 1), color === RED ? RED : Y2); pin(p[0], p[1], a, color, 14);
  dashed(p[0], p[1], p[0] + dx, p[1] + dy + 30, Math.min(a, 1)); txt(name, p[0] + dx, p[1] + dy, {size:52, scale:a, stroke:11});
}

function renderMap(t){
  const cam = camera(t), camB = camera(Math.max(0, t - 1/30));
  const dz = Math.log(cam.s/camB.s)*30, zoomSpeed = dz > 0 ? dz*0.4 : -dz*0.06;   // flou très léger
  proj.rotate([-cam.lon, -cam.lat]).scale(cam.s);
  const zk = prog(cam.s, 470, 1600);
  const bg = ctx.createRadialGradient(W/2, MAPY, 50, W/2, MAPY, H*0.8);
  bg.addColorStop(0, "#0a1630"); bg.addColorStop(1, "#010208");
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  if (zk < 1){
    for (const [x,y,r,p] of stars){ ctx.globalAlpha = (1-zk)*(0.3 + 0.7*Math.abs(Math.sin(t*1.1 + p*30)));
      ctx.fillStyle = "#dfe6ff"; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); }
    ctx.globalAlpha = 1;
    const g = ctx.createRadialGradient(W/2, MAPY, cam.s*0.95, W/2, MAPY, cam.s*1.22);
    g.addColorStop(0, `rgba(80,150,255,${0.55*(1-zk)})`); g.addColorStop(1, "rgba(80,150,255,0)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  drawGlobe(cam, 1 - zk, 0.9);
  ctx.drawImage(glc, 0, 0);
  const blur = clamp(zoomSpeed*0.3, 0, 0.45);
  if (blur > 0.05) for (let i = 1; i <= 3; i++){
    const k = 1 + blur*0.02*i; ctx.save(); ctx.globalAlpha = 0.2; ctx.translate(W/2, MAPY); ctx.scale(k, k); ctx.translate(-W/2, -MAPY); ctx.drawImage(glc, 0, 0); ctx.restore(); }
  ctx.save(); ctx.beginPath(); path(borders); ctx.strokeStyle = `rgba(255,255,255,${0.12 + 0.12*zk})`; ctx.lineWidth = 1.3; ctx.stroke(); ctx.restore();

  // ---- hook : Groenland + route complète en aperçu
  capGlow(greenland, prog(t, 0.6, 1.4)*(1 - prog(t, C.preview[0], C.preview[0] + 0.6)) + prog(t, C.green[0] + 0.6, C.green[0] + 1.2)*(1 - prog(t, C.south[0], C.south[0] + 0.5)));
  const pv = prog(t, C.preview[0] + 0.3, Ed("s02") - 0.3), pvOut = 1 - prog(t, C.green[0], C.green[0] + 0.5);
  if (pv > 0 && pvOut > 0){
    routeLine(RT.out, E(prog(pv, 0, 0.4)), pvOut, "#fff", 6); routeLine(RT.bra, E(prog(pv, 0.35, 0.6)), pvOut, "#fff", 6);
    routeLine(RT.back, E(prog(pv, 0.55, 1)), pvOut, Y1, 7);
    capGlow(antarctica, prog(pv, 0.5, 0.7)*pvOut, "120,200,255");
  }
  // ---- Groenland : colonie
  const ga = EB(prog(t, C.green[0] + 0.9, C.green[0] + 1.3))*(1 - prog(t, C.south[0] + 0.4, C.south[0] + 0.8));
  place("GROENLAND", COLONY, ga, t, {dx:-170, dy:-200});
  // ---- trajet aller
  const outA = clamp(prog(t, C.south[0], C.south[0] + 0.3)) * (1 - prog(t, C.summers[0] - 0.2, C.summers[0] + 0.3));
  if (outA > 0){
    routeLine(RT.out, kOut(t), outA, "#fff", 7);
    routeLine(RT.afr, kAfr(t), outA, "#fff", 7); routeLine(RT.bra, kBra(t), outA, "#fff", 7);
    const kk = kOut(t); if (kk < 1) ternSprite(RT.out, kk, 120, outA, t);
    else { ternSprite(RT.afr, kAfr(t), 100, outA, t); ternSprite(RT.bra, kBra(t), 100, outA, t + 0.5); }
  }
  // ---- Antarctique (destination annoncée puis arrivée)
  const an = EB(prog(t, M("s08", 0.4), M("s08", 0.55)))*(1 - prog(t, M("s08", 0.8), Ed("s08")))
           + EB(prog(t, C.arrive[0] + 0.6, C.arrive[0] + 1.0))*(1 - prog(t, C.summers[0], C.summers[0] + 0.4));
  capGlow(antarctica, Math.min(an, 1), "120,200,255"); place("ANTARCTIQUE", WEDDELL, an, t, {dx:150, dy:-220});
  // ---- pause en Atlantique Nord
  const st = EB(prog(t, C.stop[0] + 0.6, C.stop[0] + 1.0))*(1 - prog(t, C.split[0], C.split[0] + 0.4));
  if (st > 0){ const p = vproj(STOP); if (p){ ctx.save(); ctx.globalAlpha = Math.min(st, 1); ctx.strokeStyle = Y1; ctx.lineWidth = 6; ctx.setLineDash([14, 10]);
    ctx.shadowColor = "rgba(0,0,0,.7)"; ctx.shadowBlur = 10; ctx.beginPath(); ctx.arc(p[0], p[1], 120*Math.max(st, 0.01), 0, 7); ctx.stroke(); ctx.restore();
    txt("PAUSE", p[0], p[1] - 150, {size:60, color:Y1, scale:st, stroke:12}); } }
  // ---- séparation des routes
  label("AFRIQUE", [5, 8], 0, 0, EB(prog(t, M("s10", 0.35), M("s10", 0.45)))*(1 - prog(t, C.arrive[0], C.arrive[0] + 0.4)), {size:52});
  label("BRÉSIL", [-48, -10], 0, 0, EB(prog(t, M("s10", 0.6), M("s10", 0.7)))*(1 - prog(t, C.arrive[0], C.arrive[0] + 0.4)), {size:52});
  // ---- deux étés par an : les deux pôles éclairés
  const su = prog(t, C.summers[0] + 0.8, C.summers[0] + 1.4)*(1 - prog(t, C.north[0], C.north[0] + 0.5));
  if (su > 0){ capGlow(greenland, su); capGlow(antarctica, su);
    label("ÉTÉ", [-40, 72], 0, 0, EB(prog(t, C.summers[0] + 1.0, C.summers[0] + 1.4))*su, {size:56, color:Y1});
    label("ÉTÉ", [-30, -72], 0, 0, EB(prog(t, C.summers[0] + 1.4, C.summers[0] + 1.8))*su, {size:56, color:Y1}); }
  // ---- retour en S vers le nord (jaune)
  const bA = clamp(prog(t, C.north[0], C.north[0] + 0.3))*(1 - prog(t, C.farne[0], C.farne[0] + 0.5));
  if (bA > 0){ routeLine(RT.out, 1, bA*0.5, "#fff", 5); routeLine(RT.bra, 1, bA*0.5, "#fff", 5); routeLine(RT.afr, 1, bA*0.5, "#fff", 5);
    routeLine(RT.back, kBack(t), bA, Y1, 9, [1, 0]); if (kBack(t) < 1) ternSprite(RT.back, kBack(t), 120, bA, t); }
  // ---- record 2016 : Angleterre → tour du monde
  const fa = EB(prog(t, C.farne[0] + 0.7, C.farne[0] + 1.1))*(1 - prog(t, M("s15", 0.25), M("s15", 0.35)));
  place("ANGLETERRE", FARNE, fa, t, {dx:-150, dy:-200});
  const gA = clamp(prog(t, M("s15", 0.15), M("s15", 0.2)))*(1 - prog(t, C.life[0] + 0.6, C.life[0] + 1.2));
  if (gA > 0){ routeLine(RT.g82, kG82(t), gA, Y1, 9, [1, 0]); if (kG82(t) < 1) ternSprite(RT.g82, kG82(t), 110, gA, t); }

  const vg = ctx.createRadialGradient(W/2, H/2, H*0.42, W/2, H/2, H*0.8);
  vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,0.35)");
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
}
