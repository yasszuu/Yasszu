const TL = __TL__, DUR = TL.duration;
const W = 1080, H = 1920, TS = 256, ZMIN = 3, ZMAX = __ZMAX__, MARGIN = 150;      // marge latérale des textes (zone sûre TikTok)
const cv = document.getElementById("c"), ctx = cv.getContext("2d");
const BUF = document.createElement("canvas"); BUF.width = W; BUF.height = H; const bctx = BUF.getContext("2d");
const clamp = (x, a=0, b=1) => Math.max(a, Math.min(b, x)), lerp = (a, b, k) => a + (b - a)*k;
const prog = (t, a, b) => clamp((t - a)/(b - a));
const E = d3.easeCubicInOut, EO = d3.easeCubicOut, EB = d3.easeBackOut.overshoot(1.8), EX = d3.easeExpInOut, LIN = d3.easeLinear;
const Y1 = "#ffd60a", RED = "#ff3b30", MOS = [255, 59, 48], ICE = "#9fe3ff";
const V = Object.fromEntries(TL.vo.map(v => [v.id, v]));
const S = k => V[k].start, Ed = k => V[k].end, M = (k, f) => S(k) + (Ed(k) - S(k))*f;
const SFX = n => TL.sfx.filter(s => s.name === n).map(s => s.t);
const near = (n, a, b) => SFX(n).find(x => x >= a && x <= b);
// ------------------------------------------------------------------ lieux
// ------------------------------------------------------------------ itinéraires
const pathLen = pts => { const d = [0]; for (let i = 1; i < pts.length; i++) d.push(d[i-1] + Math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1])); return d; };
function along(pts, k){ const d = pathLen(pts), L = d[d.length - 1]*clamp(k); let i = 1; while (i < pts.length - 1 && d[i] < L) i++;
  const q = (L - d[i-1])/(d[i] - d[i-1] || 1); return [lerp(pts[i-1][0], pts[i][0], q), lerp(pts[i-1][1], pts[i][1], q)]; }
const upto = (pts, k) => { const d = pathLen(pts), L = d[d.length - 1]*clamp(k), out = [pts[0]]; for (let i = 1; i < pts.length && d[i] < L; i++) out.push(pts[i]); out.push(along(pts, k)); return out; };
// ------------------------------------------------------------------ caméra
const mx = lon => (lon + 180)/360*TS;
const my = lat => { const r = lat*Math.PI/180; return (1 - Math.log(Math.tan(r) + 1/Math.cos(r))/Math.PI)/2*TS; };
const view = (lon, lat, z, dy=-90) => [mx(lon), my(lat) - dy/2**z, W/2**z];