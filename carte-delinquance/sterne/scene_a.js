<script>
const WORLD = __WORLD__, TL = __TL__;
const TEX = {world:"__TEXWORLD__", eu:"__TEXWORLD__"};
const IMG_SRC = __IMGS__;
const EU_BOX = [0, 0.001, 0, 0.001];                     // pas de texture régionale (zoom continental max)

const W = 1080, H = 1920, MAPY = 1080;
const Y1 = "#ffd60a", Y2 = "#ffe45c", ORANGE = "#ff9f1c", RED = "#ff3b30", CYAN = "#3ec9ff", ICE = "#9fe3ff";
const cv = document.getElementById("c"), ctx = cv.getContext("2d");
const proj = d3.geoOrthographic().clipAngle(90).translate([W/2, MAPY]).precision(0.3);
const path = d3.geoPath(proj, ctx), measure = d3.geoPath(proj);
const C = TL.cue, V = Object.fromEntries(TL.vo.map(v => [v.id, v]));
const S = k => V[k].start, Ed = k => V[k].end, DUR = TL.duration, M = (k, f) => S(k) + (Ed(k) - S(k))*f;

const countries = topojson.feature(WORLD, WORLD.objects.countries).features;
const CTRY = n => countries.find(f => f.properties.name === n);
const borders = topojson.mesh(WORLD, WORLD.objects.countries, (a,b) => a !== b);
const greenland = CTRY("Greenland"), antarctica = CTRY("Antarctica"), uk = CTRY("United Kingdom");

const IMG = {};
const loadImg = (k, src) => new Promise(r => { const i = new Image(); i.onload = () => { IMG[k] = i; r(); }; i.src = src; });
const clamp = (x,a=0,b=1) => Math.max(a, Math.min(b, x));
const prog = (t,a,b) => clamp((t-a)/(b-a));
const lerp = (a,b,k) => a + (b-a)*k;
const E = d3.easeCubicInOut, EO = d3.easeCubicOut, EB = d3.easeBackOut.overshoot(1.8), EBig = d3.easeBackOut.overshoot(3);

// ------------------------------------------------------------------ lieux & routes (Egevang et al. 2010 ; Newcastle Univ. 2016)
const COLONY = [-20.5, 74.4], STOP = [-35, 47], SPLIT = [-21, 13], WEDDELL = [-28, -67], FARNE = [-1.65, 55.63];
const R_OUT = [COLONY, [-24, 68], [-30, 58], STOP, [-30, 35], [-24, 22], SPLIT];
const R_AFR = [SPLIT, [-18.5, 5], [-5, -5], [7, -18], [13, -30], [16, -40], [5, -55], [-12, -63], WEDDELL];
const R_BRA = [SPLIT, [-28, 4], [-33, -8], [-38, -22], [-45, -38], [-45, -52], [-38, -62], WEDDELL];
const R_BACK = [WEDDELL, [-18, -52], [-10, -35], [-8, -18], [-18, -2], [-35, 12], [-48, 25], [-50, 40], [-42, 54], [-30, 64], [-24, 70], COLONY];
const R_G82 = [FARNE, [-8, 48], [-18, 30], [-20, 12], [-8, -2], [5, -18], [14, -32], [30, -42], [60, -46], [95, -48], [125, -50], [160, -60],
  [-160, -70], [-130, -72], [-95, -71], [-60, -66], [-35, -55], [-25, -35], [-28, -12], [-32, 8], [-38, 25], [-30, 42], [-15, 52], FARNE];
function densify(pts, step=1.0){
  const out = [pts[0]];
  for (let i = 1; i < pts.length; i++){
    const ip = d3.geoInterpolate(pts[i-1], pts[i]), n = Math.max(2, Math.ceil(d3.geoDistance(pts[i-1], pts[i])*180/Math.PI/step));
    for (let j = 1; j <= n; j++) out.push(ip(j/n));
  }
  // lissage (moyenne glissante) pour des courbes douces
  const sm = out.map((p, i) => { if (i === 0 || i === out.length - 1) return p; let x = 0, y = 0, c = 0;
    for (let k = -3; k <= 3; k++){ const q = out[clamp(i + k, 0, out.length - 1)]; x += q[0]; y += q[1]; c++; } return [x/c, y/c]; });
  const cum = [0]; for (let i = 1; i < sm.length; i++) cum.push(cum[i-1] + d3.geoDistance(sm[i-1], sm[i]));
  return {pts:sm, cum, len:cum[cum.length-1]};
}
const RT = {out:densify(R_OUT), afr:densify(R_AFR), bra:densify(R_BRA), back:densify(R_BACK), g82:densify(R_G82, 1.5)};
function routeAt(r, k){
  const d = clamp(k)*r.len; let i = d3.bisectLeft(r.cum, d); i = Math.max(1, Math.min(r.pts.length - 1, i));
  const f = (d - r.cum[i-1])/Math.max(1e-9, r.cum[i] - r.cum[i-1]);
  return {p:d3.geoInterpolate(r.pts[i-1], r.pts[i])(clamp(f)), i, a:r.pts[i-1], b:r.pts[i]};
}

// ------------------------------------------------------------------ progression des tracés
const kOut  = t => Math.max(E(prog(t, C.south[0] + 0.3, Ed("s07")))*0.32, t >= S("s09") - 0.3 ? 0.32 + E(prog(t, S("s09") - 0.3, C.stop[1]))*0.18 : 0,
                            t >= C.split[0] ? 0.5 + E(prog(t, C.split[0], M("s10", 0.3)))*0.5 : 0);
const kAfr  = t => E(prog(t, M("s10", 0.3), Ed("s10") + 0.4));
const kBra  = t => E(prog(t, M("s10", 0.55), Ed("s10") + 0.8));
const kBack = t => E(prog(t, C.north[0] + 0.3, Ed("s14")));
const kG82  = t => E(prog(t, M("s15", 0.18), M("s15", 0.92)));

// ------------------------------------------------------------------ caméras
function fit(feature, center, w, h){
  proj.rotate([-center[0], -center[1]]).scale(1).translate([0,0]);
  const [[x0,y0],[x1,y1]] = measure.bounds(feature);
  proj.translate([W/2, MAPY]);
  return {lon:center[0], lat:center[1], s: Math.min(w/(x1-x0), h/(y1-y0))};
}
const GRN0 = {lon:-30, lat:70, s:1350}, GRN = {lon:-29, lat:69.5, s:1480};          // ouverture : niveau continent
const ATL = {lon:-22, lat:5, s:400}, ATL2 = {lon:-28, lat:2, s:430};
const GRNC = {lon:-24, lat:71, s:1300};
const NATL = {lon:-32, lat:52, s:900}, MIDA = {lon:-22, lat:12, s:620}, SATL = {lon:-12, lat:-30, s:560};
const ANT = {lon:-30, lat:-62, s:900}, ANTW = {lon:-25, lat:-55, s:620};
const POLES = {lon:-25, lat:4, s:360};
const UKV = {lon:-3, lat:54, s:1250}, G82V = {lon:40, lat:-35, s:380};
const SPACE = {lon:-25, lat:20, s:150};

function camLerp(a, b, k, fly, ease=E){
  const e = ease(k);
  let s = Math.exp(lerp(Math.log(a.s), Math.log(b.s), e));
  if (fly){ const dist = d3.geoDistance([a.lon,a.lat],[b.lon,b.lat])*180/Math.PI;
    s *= 1 - clamp(dist/14, 0, 0.45)*Math.sin(Math.PI*e); }
  let dl = b.lon - a.lon; if (dl > 180) dl -= 360; if (dl < -180) dl += 360;
  return {lon:a.lon + dl*e, lat:lerp(a.lat,b.lat,e), s};
}
const push = (c, k) => ({...c, s:c.s*(1 + 0.05*k)});
// suivi de la sterne sur une route
const g82Cam = t => { const {p} = routeAt(RT.g82, kG82(t)); const k = prog(t, M("s15", 0.18), M("s15", 0.4)); return {lon:p[0], lat:lerp(20, -38, E(k)), s:360}; };
const follow = (rk, kf, s, dlat=-4) => t => { const {p} = routeAt(RT[rk], kf(t)); return {lon:p[0], lat:p[1] + dlat, s}; };
// aperçu (hook) : la route se dessine, la caméra suit la tête du tracé — jamais la Terre entière
const pvOut  = t => E(prog(t, C.preview[0] + 0.3, Ed("s02") - 0.2));
const pvBra  = t => E(prog(t, M("s02", 0.55), S("s03") + 0.8));
const pvBack = t => E(prog(t, S("s03") + 0.6, Ed("s03") - 0.1));
function pvCam(t){
  let p;
  if (t < M("s02", 0.55) + 0.4) p = routeAt(RT.out, pvOut(t)).p;
  else if (t < S("s03") + 0.8) p = routeAt(RT.bra, pvBra(t)).p;
  else p = routeAt(RT.back, pvBack(t)).p;
  return {lon:p[0], lat:p[1] - 3, s:1350};
}
const kLife = t => E(prog(t, C.life[0] + 0.4, Ed("s17")));
const lifeCam = t => { const {p} = routeAt(RT.out, kLife(t)); return {lon:p[0], lat:p[1] - 2, s:1400}; };
const SMIN = 1300;                                       // en dessous, on verrait le bord du globe / l'espace
const GRNC2 = {lon:-23, lat:72.5, s:1650}, NATL2 = {lon:-33, lat:49, s:1550}, SPLITV = {lon:-17, lat:-4, s:1320};
const ANT2 = {lon:-30, lat:-63, s:1450}, ANTB = {lon:-25, lat:-60, s:1500}, GRNS = {lon:-35, lat:70, s:1400};
const UKV2 = {lon:-2, lat:55, s:1700}, NATL3 = {lon:-25, lat:58, s:1350};
const SHOTS = [
  [C.preview[0], C.preview[0] + 0.6, t => pvCam(t), false],
  [C.preview[0] + 0.6, Ed("s03"), t => pvCam(t), false],
  [C.green[0], C.green[0] + 1.3, GRNC2, true],
  [C.colony[0] - 0.4, C.colony[0], {...GRNC2, s:GRNC2.s*1.06}, false],
  [C.south[0], C.south[0] + 0.6, follow("out", kOut, 1450, -2), false],
  [C.south[0] + 0.6, Ed("s07"), follow("out", kOut, 1450, -2), false],
  [C.anta[0], C.anta[0] + 1.8, ANT2, true],                                  // grand balayage jusqu'à l'Antarctique
  [M("s08", 0.75), Ed("s08") + 0.3, NATL2, true],                              // et retour en Atlantique Nord
  [C.stop[0], C.stop[1], {...NATL2, s:NATL2.s*1.12}, false],
  [C.split[0] - 0.2, C.split[0] + 0.8, SPLITV, false],
  [C.split[0] + 0.8, Ed("s10") + 0.4, {...SPLITV, lat:-12, s:1300}, false],
  [C.arrive[0], C.arrive[1], ANT2, false],
  [C.summers[0], C.summers[0] + 0.9, ANTB, false],                            // été en Antarctique…
  [M("s13", 0.45), M("s13", 0.45) + 1.4, GRNS, true],                          // …puis balayage jusqu'au Groenland
  [C.north[0], C.north[0] + 0.8, follow("back", kBack, 1350, 0), true],
  [C.north[0] + 0.8, Ed("s14"), follow("back", kBack, 1350, 0), false],
  [C.farne[0], C.farne[0] + 1.0, UKV2, true],
  [M("s15", 0.18), M("s15", 0.18) + 0.8, t => g82Cam(t), false],              // tour du monde : seule vue « espace » avec la Lune
  [M("s15", 0.18) + 0.8, M("s15", 0.92), t => g82Cam(t), false],
  [C.life[0], C.life[0] + 1.2, t => lifeCam(t), false],
  [C.life[0] + 1.2, Ed("s17") + 0.2, t => lifeCam(t), false],
  [C.moon[0], C.moon[0] + 1.0, SPACE, false],
  [C.g100[0], C.g100[0] + 1.0, GRNC2, false],
  [C.outro, C.outro + 2.0, {...GRNC2, s:GRNC2.s*0.9}, false],
];
// zoom minimum imposé hors des deux plans « espace » (tour du monde 2016, Terre-Lune)
const spaceOK = t => Math.max(prog(t, M("s15", 0.18), M("s15", 0.18) + 0.8)*(1 - prog(t, C.life[0], C.life[0] + 1.2)),
                              prog(t, C.moon[0], C.moon[0] + 1.0)*(1 - prog(t, C.g100[0], C.g100[0] + 1.0)));
function camera(t){ const c = camera0(t), m = SMIN*(1 - spaceOK(t)); return {...c, s:Math.max(c.s, m)}; }
function camera0(t){
  if (t < C.preview[0]) return camLerp(GRN0, GRN, prog(t, 0, C.preview[0]), false, d3.easeSinOut);
  let prev = GRN, tPrev = C.preview[0];
  for (const [a, b, cam, fly] of SHOTS){
    const cb = typeof cam === "function" ? cam(Math.min(t, b)) : cam;
    if (t < a) return push(prev, prog(t, tPrev, a)*0.6);
    if (t < b){
      if (typeof cam === "function" && a - tPrev <= 0.01) return cb;
      return camLerp(a - tPrev > 0.01 ? push(prev, 0.6) : prev, cb, prog(t, a, b), fly);
    }
    prev = typeof cam === "function" ? cam(b) : cam; tPrev = b;
  }
  return push(prev, prog(t, tPrev, DUR));
}
function yearAt(t){
  let seg = TL.ticker[0];
  for (const s of TL.ticker) if (t >= s[0]) seg = s;
  return {v: lerp(seg[2], seg[3], prog(t, seg[0], seg[1])), step: seg[4]};
}
const MOIS = ["JANV.", "FÉVR.", "MARS", "AVRIL", "MAI", "JUIN", "JUIL.", "AOÛT", "SEPT.", "OCT.", "NOV.", "DÉC."];
const moisName = v => MOIS[((Math.round(v) - 1) % 12 + 12) % 12];
