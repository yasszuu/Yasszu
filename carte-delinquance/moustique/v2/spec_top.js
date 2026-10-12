// ------------------------------------------------------------------ lieux
const MENTON = [7.5, 43.78], GENES = [8.93, 44.41], SEA = [103, 11], SING = [103.8, 1.3], PARIS = [2.35, 48.86];
const R_ALB = [[103.8,1.3],[95,6],[80,6.5],[62,13],[48,12.5],[43.3,12.6],[38,21],[33.6,27.8],[32.5,30.2],[32.3,31.4],[26,34],[20.5,38.2],[19.45,41.3]];
const R_USA = [[139.7,35.3],[155,32],[180,26],[210,19],[240,12],[266,7.2],[279.5,8.9],[278.5,12.5],[273.5,18.5],[268,24],[264.6,29.6]];   // longitudes continues (> 180) pour traverser le Pacifique
const R_ITA = [[-95.0,29.4],[-88,25.6],[-81.5,24.2],[-72,29],[-52,35],[-28,37.5],[-12,36.4],[-5.6,35.95],[0,37.3],[5,39.2],[8.3,42.6],[8.93,44.38]];
const COAST = [[8.93,44.41],[8.47,44.31],[8.2,44.08],[7.92,43.88],[7.68,43.79],[7.5,43.78]];
const RHONE = [[5.37,43.3],[4.85,43.75],[4.75,44.3],[4.85,44.95],[4.84,45.4],[4.84,45.76]];
const LANES = [[4.4,51.9],[139.7,35.3],[151.2,-33.9],[55.3,25.3],[121.5,31.2],[-46.3,-24],[241.8,33.7],[18.4,-33.9]];
// ------------------------------------------------------------------ calendrier
const T_2004 = near("impact", S("m01"), M("m01", 0.3)), T_MENT = near("pop", M("m01", 0.5), Ed("m01")), T_80 = near("impact", S("m02"), Ed("m02"));
const T_TITLE = near("impact", S("m03"), Ed("m03")), T_ASIA = near("pop", S("m04"), Ed("m04")), T_XX = near("hit", S("m06"), Ed("m06")), T_PNEUS = near("pop", M("m06", 0.5), Ed("m06"));
const T_ALB = near("impact", S("m08"), Ed("m08")), T_USA = near("impact", S("m09"), Ed("m09")), T_ITA = near("impact", S("m10"), Ed("m10")), T_MENT2 = near("pop", M("m11", 0.5), Ed("m11"));
const T_FLOC = near("pop", S("m12"), Ed("m12")), T_FROID = near("impact", S("m12"), Ed("m12")), T_SW = near("hit", S("m14"), Ed("m14")), T_PAR = near("hit", S("m15"), Ed("m15"));
const T_81 = near("impact", S("m16"), Ed("m16")), T_45 = near("hit", S("m16"), Ed("m16")), T_PIQ = near("pop", S("m17"), M("m17", 0.3));
const T_DENG = near("hit", S("m18"), M("m18", 0.55)), T_CHIK = near("hit", M("m18", 0.55), Ed("m18")), T_800 = near("impact", S("m19"), Ed("m19")), T_STAY = near("impact", S("m20"), Ed("m20"));
const POPS_LANES = SFX("pop").filter(x => x > M("m07", 0.45) && x < Ed("m07")), POPS_CHIK = SFX("pop").filter(x => x > S("m19") && x < Ed("m19"));
// ------------------------------------------------------------------ itinéraires
const pathLen = pts => { const d = [0]; for (let i = 1; i < pts.length; i++) d.push(d[i-1] + Math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1])); return d; };
function along(pts, k){ const d = pathLen(pts), L = d[d.length - 1]*clamp(k); let i = 1; while (i < pts.length - 1 && d[i] < L) i++;
  const q = (L - d[i-1])/(d[i] - d[i-1] || 1); return [lerp(pts[i-1][0], pts[i][0], q), lerp(pts[i-1][1], pts[i][1], q)]; }
const upto = (pts, k) => { const d = pathLen(pts), L = d[d.length - 1]*clamp(k), out = [pts[0]]; for (let i = 1; i < pts.length && d[i] < L; i++) out.push(pts[i]); out.push(along(pts, k)); return out; };
const ROUTES = [[R_ALB, S("m08") + 0.2, M("m08", 0.8), 4.3, 5.3], [R_USA, S("m09") + 0.5, M("m09", 0.8), 4.1, 5.2], [R_ITA, S("m10") + 0.4, M("m10", 0.8), 4.1, 5.5]];
const routeKeys = ([pts, a, b, z0, z1], first) => d3.range(0, 9).map(i => { const k = i/8, p = along(pts, Math.min(1, k + 0.05)); return [lerp(a, b, k), view(p[0], p[1], lerp(z0, z1, k*k)), i ? LIN : EX]; });
// ------------------------------------------------------------------ caméra
