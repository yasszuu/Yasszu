// ------------------------------------------------------------------ lieux
const TAIPEI = [121.53, 25.05], HUKAWNG = [96.6, 26.6], LEDO = [95.73, 27.29], MYIT = [97.4, 25.38], CANTON = [113.26, 23.13], KAOH = [120.3, 22.62], TOKYO = [139.7, 35.7];
const R_ATTACK = [[95.73,27.29],[96.2,26.9],[96.6,26.5],[97.0,25.9],[97.4,25.38]];
const R_MARCH = [[97.4,25.38],[98.0,25.1],[98.5,25.0],[99.2,25.1],[100.4,25.3],[101.6,25.0],[102.8,24.9],[104.6,24.7],[106.7,24.0],[108.6,23.4],[110.6,23.3],[112.2,23.2],[113.26,23.13]];
const R_SHIP = [[113.26,23.13],[113.6,22.45],[114.8,22.2],[116.6,22.4],[118.4,22.5],[119.6,22.6],[120.28,22.62]];
const R_JAPAN = [[139.7,35.7],[131,33],[124,28],[114,23],[106,20],[100,21],[97.6,24.2]];
const R_PARADE = [[121.523,25.072],[121.535,25.06],[121.545,25.04],[121.56,25.02],[121.581,24.998]];
const JOURNEY = [...R_MARCH, ...R_SHIP.slice(1), [120.6, 23.6], TAIPEI];
// ------------------------------------------------------------------ calendrier
const pops = (k, a=0, b=1) => SFX("pop").filter(x => x >= M(k, a) - 0.05 && x <= M(k, b) + 0.05);
const T_2003 = near("impact", S("l01"), M("l01", 0.3)), T_PH1 = pops("l01")[0], T_86 = near("impact", M("l01", 0.6), Ed("l01"));
const T_NAME = pops("l02")[0], T_WAR = near("hit", S("l02"), Ed("l02")), T_TITLE = near("impact", S("l03"), Ed("l03"));
const T_JUNGLE = pops("l04")[0], P5 = pops("l05"), T_CAMION = near("hit", S("l05"), Ed("l05")), P6 = pops("l06"), T_DOUZE = near("impact", S("l06"), Ed("l06"));
const P7 = pops("l07"), T_PAINT = pops("l08")[0], T_CANTON = pops("l10")[0], T_GEN = pops("l11")[0], T_TW = near("impact", S("l11"), Ed("l11")) || Ed("l11");
const T_PARADE = pops("l12")[0], T_ZOO = pops("l13")[0], P14 = pops("l14"), T_ROCK = near("hit", S("l15"), Ed("l15")), T_PH18 = pops("l16")[0];
const SHIP = [M("l11", 0.55), M("l11", 0.92)];
const CL = {a: S("l09") - 0.55, b: S("l09") - 0.55 + 5.0};      // plan 3D (150 images)
// ------------------------------------------------------------------ itinéraires
const pathLen = pts => { const d = [0]; for (let i = 1; i < pts.length; i++) d.push(d[i-1] + Math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1])); return d; };
function along(pts, k){ const d = pathLen(pts), L = d[d.length - 1]*clamp(k); let i = 1; while (i < pts.length - 1 && d[i] < L) i++;
  const q = (L - d[i-1])/(d[i] - d[i-1] || 1); return [lerp(pts[i-1][0], pts[i][0], q), lerp(pts[i-1][1], pts[i][1], q)]; }
const upto = (pts, k) => { const d = pathLen(pts), L = d[d.length - 1]*clamp(k), out = [pts[0]]; for (let i = 1; i < pts.length && d[i] < L; i++) out.push(pts[i]); out.push(along(pts, k)); return out; };
const MARCH_A = [M("l08", 0.1), Ed("l08") - 0.2], MARCH_B = [S("l10") - 0.2, M("l10", 0.62)];
const marchK = t => t < CL.a + 0.5 ? 0.55*E(prog(t, ...MARCH_A)) : 0.55 + 0.45*E(prog(t, ...MARCH_B));
// ------------------------------------------------------------------ caméra
