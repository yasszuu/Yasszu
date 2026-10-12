// ------------------------------------------------------------------ lieux
const HAMADAN = [48.51, 34.8], TEHRAN = [51.39, 35.69], NAPLES = [14.27, 40.84], CASSINO = [13.81, 41.49], EDIN = [-3.19, 55.95], KRAKOW = [19.94, 50.06];
const R_USSR = [[52.97,40.02],[51.6,38.9],[49.46,37.47],[50.4,36.6],[51.39,35.69]];
const R_HAM = [[51.39,35.69],[50.1,35.35],[48.51,34.8]];
const R_LAND = [[48.51,34.8],[47.06,34.31],[44.36,33.31],[40.28,33.04],[36.29,33.51],[35.5,32.6],[34.8,31.9],[33.2,31.0],[32.3,30.6],[31.2,30.9],[29.92,31.2]];
const R_SEA1 = [[29.92,31.2],[27,32.9],[22.5,35.3],[18.6,37.0],[15.9,38.0],[15.62,38.25],[15.2,39.3],[14.6,40.2],[14.27,40.84]];
const R_SEA2 = [[14.27,40.84],[12.3,39.6],[9.5,38.4],[5,37.6],[0,36.8],[-5.6,35.95],[-9.6,37.2],[-10.2,43.2],[-8.2,47.6],[-6.3,50.2],[-5.6,52.6],[-5.3,54.6],[-4.9,55.65],[-4.25,55.86]];
const JOURNEY = [...R_USSR, ...R_HAM.slice(1), ...R_LAND.slice(1), ...R_SEA1.slice(1), ...R_SEA2.slice(1), [-3.19, 55.95]];
// ------------------------------------------------------------------ calendrier
const T_1944 = near("impact", S("w01"), M("w01", 0.4)), T_POL = near("impact", M("w01", 0.5), Ed("w01"));
const POPS2 = SFX("pop").filter(x => x > S("w02") && x < Ed("w02")), T_TITLE = near("impact", S("w03"), Ed("w03")), T_IRAN = near("impact", S("w04"), Ed("w04"));
const T_HAM = near("pop", S("w06"), M("w06", 0.3)), T_OURSON = near("pop", M("w06", 0.4), Ed("w06"));
const POPS7 = SFX("pop").filter(x => x > S("w07") && x < M("w07", 0.6)), T_JOY = near("impact", S("w07"), Ed("w07")), T_COMBAT = near("pop", S("w08"), M("w08", 0.2));
const HITS9 = SFX("hit").filter(x => x > S("w09") && x < Ed("w09")), T_INTERD = near("hit", S("w10"), Ed("w10")), T_SOLDAT = near("impact", S("w11"), Ed("w11"));
const T_CASS = near("impact", S("w12"), Ed("w12")), T_45 = near("impact", S("w13"), Ed("w13")), T_EMBL = near("pop", S("w14"), Ed("w14")), T_CAPO = near("impact", S("w14"), Ed("w14"));
const T_SCOT = near("impact", S("w15"), Ed("w15")), POPS16 = SFX("pop").filter(x => x > S("w16") && x < Ed("w16")), POPS18 = SFX("pop").filter(x => x > S("w18") && x < Ed("w18"));
// ------------------------------------------------------------------ itinéraires
const pathLen = pts => { const d = [0]; for (let i = 1; i < pts.length; i++) d.push(d[i-1] + Math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1])); return d; };
function along(pts, k){ const d = pathLen(pts), L = d[d.length - 1]*clamp(k); let i = 1; while (i < pts.length - 1 && d[i] < L) i++;
  const q = (L - d[i-1])/(d[i] - d[i-1] || 1); return [lerp(pts[i-1][0], pts[i][0], q), lerp(pts[i-1][1], pts[i][1], q)]; }
const upto = (pts, k) => { const d = pathLen(pts), L = d[d.length - 1]*clamp(k), out = [pts[0]]; for (let i = 1; i < pts.length && d[i] < L; i++) out.push(pts[i]); out.push(along(pts, k)); return out; };
const fracAt = (pts, idx) => { const d = pathLen(pts); return d[idx]/d[d.length - 1]; };
// route terrestre : passage aux villes calé sur « l'Irak, la Syrie, la Palestine, l'Égypte »
const LAND_T = [[S("w09") + 0.2, 0], [HITS9[0], fracAt(R_LAND, 2)], [HITS9[1], fracAt(R_LAND, 4)], [HITS9[2], fracAt(R_LAND, 6)], [HITS9[3], 1]];
const landK = t => { if (t <= LAND_T[0][0]) return 0; for (let i = 1; i < LAND_T.length; i++) if (t <= LAND_T[i][0]) return lerp(LAND_T[i-1][1], LAND_T[i][1], E(prog(t, LAND_T[i-1][0], LAND_T[i][0]))); return 1; };
const SEA1 = [M("w10", 0.15), M("w11", 0.6)], SEA2 = [S("w15") - 0.1, M("w15", 0.92)];
// ------------------------------------------------------------------ caméra
