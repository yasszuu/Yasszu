const TWIN = [[S("m08"), Ed("m11") + 0.2], [S("m13"), Ed("m16") + 0.2]];
const HITS = TL.sfx.filter(s => ["impact", "hit"].includes(s.name)).map(s => [s.t, s.name === "hit" ? 0.05 : 0.075, s.name === "hit" ? 7 : 14]);
HITS.push([0.03, 0.08, 10], [1.35, 0.06, 8]);
let PH = {};
function render(t){
  let p = 0, sx = 0, sy = 0;
  for (const [ti, amp, sh] of HITS) if (t >= ti){ const d = t - ti; p += amp*Math.exp(-d*8); sx += sh*Math.exp(-d*7)*Math.sin(d*50); sy += sh*0.7*Math.exp(-d*7)*Math.cos(d*43); }
  ctx.save(); ctx.translate(W/2 + sx, H/2 + sy); ctx.scale(1.04 + p, 1.04 + p); ctx.translate(-W/2, -H/2);
  renderMap(t); motionBlur(t);
  overlay(t);
  ctx.restore();
  const rf = t >= T_DENG ? Math.exp(-(t - T_DENG)*7) + (t >= T_CHIK ? Math.exp(-(t - T_CHIK)*7) : 0) : 0; if (rf > 0.02){ ctx.fillStyle = `rgba(255,40,30,${0.3*Math.min(rf, 1)})`; ctx.fillRect(0, 0, W, H); }
  const fl = Math.exp(-t*7); if (fl > 0.02){ ctx.fillStyle = `rgba(255,255,255,${0.6*fl})`; ctx.fillRect(0, 0, W, H); }
}
